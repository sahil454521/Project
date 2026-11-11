"""Run candidate programs in a separate, resource-limited process."""
import json
import subprocess
import sys
from pathlib import Path

_RUNNER = str(Path(__file__).with_name("_runner.py"))

# shortcut: a subprocess with time and memory limits stops runaway code, not hostile code.
# Run inside a container with no network before pointing this at a model you do not trust.


def run(sources, entry, inputs, max_steps=20_000, timeout=2):
    """Return results[source][input] = {"ok": value} or {"error": exception name}."""
    job = json.dumps({"sources": sources, "entry": entry, "inputs": inputs, "timeout": timeout,
                      "max_steps": max_steps})
    try:
        proc = subprocess.run([sys.executable, "-I", _RUNNER], input=job, capture_output=True,
                              text=True, timeout=600)
        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        # shortcut: one candidate that kills the child fails its whole batch; isolate per
        # candidate if that ever shows up in results.
        return [[{"error": "Crash"}] * len(inputs) for _ in sources]
