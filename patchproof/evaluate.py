"""Score a repairer: does a patch that passes the visible tests also pass the hidden ones?"""
import random
from concurrent.futures import ThreadPoolExecutor

from .sandbox import run


def split(task, k, seed=0):
    """k visible test indexes (always including one the bug fails), and the hidden rest."""
    rng = random.Random(f"{seed}:{task.id}:{k}")
    fail = rng.choice(task.failing)
    rest = [i for i in range(len(task.inputs)) if i != fail]
    visible = [fail] + rng.sample(rest, k - 1)
    return visible, [i for i in rest if i not in visible]


def score(task, repairer, k, seed=0):
    """'correct', 'overfit' (passes visible, fails hidden) or 'unrepaired'."""
    visible, hidden = split(task, k, seed)
    tests = [(task.inputs[i], task.expected[i]["ok"]) for i in visible]
    patch = repairer(task.buggy, task.entry, tests)
    if not patch:
        return "unrepaired"
    outputs = run([patch], task.entry, task.inputs)[0]
    if any(outputs[i] != task.expected[i] for i in visible):
        return "unrepaired"
    return "overfit" if any(outputs[i] != task.expected[i] for i in hidden) else "correct"


def evaluate(tasks, repairer, ks, seed=0, workers=4):
    rows = []
    with ThreadPoolExecutor(workers) as pool:
        for k in ks:
            verdicts = list(pool.map(lambda t: score(t, repairer, k, seed), tasks))
            rows.append({"k": k, "tasks": len(tasks),
                         **{v: verdicts.count(v) for v in ("correct", "overfit", "unrepaired")}})
    return rows
