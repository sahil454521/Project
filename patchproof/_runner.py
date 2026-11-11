"""Child process: run candidate programs on inputs. Reads a JSON job on stdin."""
import copy
import json
import os
import resource
import signal
import sys


class Timeout(BaseException):  # BaseException so candidate code cannot swallow it
    pass


def _alarm(*_):
    raise Timeout


_steps = 0


def _trace(frame, event, arg):
    # A line budget, not a clock, decides what counts as an infinite loop: the same
    # candidate gets the same verdict on any machine, and loops die in milliseconds.
    global _steps
    _steps -= 1
    if _steps < 0:
        raise Timeout
    return _trace


def _arm(job):
    global _steps
    _steps = job["max_steps"]
    signal.setitimer(signal.ITIMER_REAL, job["timeout"])  # backstop for stalls inside C code
    sys.settrace(_trace)


def _disarm():
    sys.settrace(None)
    signal.setitimer(signal.ITIMER_REAL, 0)


def main():
    job = json.load(sys.stdin)
    out = os.fdopen(os.dup(1), "w")
    sys.stdout = open(os.devnull, "w")  # candidate prints must not corrupt the result
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    signal.signal(signal.SIGALRM, _alarm)
    results = []
    for source in job["sources"]:
        row, dead = [], None
        try:
            _arm(job)
            namespace = {}
            exec(source, namespace)
            func = namespace[job["entry"]]
            _disarm()
        except BaseException as e:
            _disarm()
            dead = type(e).__name__
        for args in job["inputs"]:
            if dead:  # a candidate that looped once is not retried on the remaining inputs
                row.append({"error": dead})
                continue
            try:
                args = copy.deepcopy(args)  # candidates may mutate their arguments
                _arm(job)
                value = func(*args)
                _disarm()
                row.append({"ok": json.loads(json.dumps(value))})
            except BaseException as e:
                _disarm()
                row.append({"error": type(e).__name__})
                if isinstance(e, Timeout):
                    dead = "Timeout"
        results.append(row)
    json.dump(results, out)


main()
