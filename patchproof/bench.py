"""Build the benchmark: buggy variants of the seed programs plus an input/expected-output oracle."""
import inspect
import random
from dataclasses import dataclass

from .mutate import mutants
from .sandbox import run
from .seeds import SEEDS


@dataclass
class Task:
    id: str
    entry: str
    reference: str
    buggy: str
    order: int      # how many mutations were injected
    inputs: list
    expected: list  # reference output per input
    failing: list   # indexes of inputs the buggy program gets wrong


def build(seed=0, n_tests=40, order1=4, order2=2):
    tasks = []
    for func, gen in SEEDS.items():
        name = func.__name__
        rng = random.Random(f"{seed}:{name}")
        reference = inspect.getsource(func)
        inputs = [gen(rng) for _ in range(n_tests)]
        firsts = mutants(reference)
        seconds = [rng.choice(mutants(m)) for m in rng.sample(firsts, min(len(firsts), 12))]
        candidates = [(m, 1) for m in firsts] + [(m, 2) for m in seconds]
        rng.shuffle(candidates)
        results = run([reference] + [m for m, _ in candidates], name, inputs)
        expected = results[0]
        assert all("ok" in r for r in expected), f"reference {name} failed on its own inputs"
        left, seen = {1: order1, 2: order2}, set()
        for (buggy, order), outputs in zip(candidates, results[1:]):
            failing = [i for i, o in enumerate(outputs) if o != expected[i]]
            signature = repr(outputs)  # same behaviour = same bug, keep one
            if not failing or signature in seen or not left[order]:
                continue
            seen.add(signature)
            left[order] -= 1
            tasks.append(Task(f"{name}-{len(tasks)}", name, reference, buggy, order,
                              inputs, expected, failing))
    return tasks
