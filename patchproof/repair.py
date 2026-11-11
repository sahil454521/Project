"""Repairers: (buggy_source, entry, visible_tests) -> patched source or None.

visible_tests is a list of (args, expected_value). Repairers never see the hidden tests.
"""
import re

from .mutate import mutants
from .sandbox import run


def search(buggy, entry, tests, budget=400):
    """Generate-and-validate baseline: first program within two mutations that passes."""
    first = mutants(buggy)
    candidates = list(first)
    for m in first:
        if len(candidates) >= budget:
            break
        candidates += mutants(m)
    candidates = list(dict.fromkeys(candidates))[:budget]
    results = run(candidates, entry, [args for args, _ in tests])
    for candidate, outputs in zip(candidates, results):
        if all(o == {"ok": want} for o, (_, want) in zip(outputs, tests)):
            return candidate
    return None


def llm(model="claude-opus-5-5"):
    import anthropic

    client = anthropic.Anthropic()

    def repair(buggy, entry, tests):
        cases = "\n".join(f"{entry}(*{args!r}) == {want!r}" for args, want in tests)
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            output_config={"effort": "medium"},
            # a safety decline is re-run on a fallback model instead of failing the task
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": (
                f"This Python function has a bug.\n\n```python\n{buggy}\n```\n\n"
                f"It must satisfy these checks, at least one of which currently fails:\n\n{cases}\n\n"
                "Reply with the corrected function in one ```python block and nothing else."
            )}],
        )
        if response.stop_reason == "refusal":
            return None
        text = "".join(b.text for b in response.content if b.type == "text")
        match = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
        return match.group(1) if match else text

    return repair
