"""python -m patchproof --repairer search|llm  ->  results/<label>.json + results/RESULTS.md"""
import argparse
import json
from pathlib import Path

from . import repair
from .bench import build
from .evaluate import evaluate

RESULTS = Path("results")


def report():
    runs = {p.stem: json.loads(p.read_text()) for p in sorted(RESULTS.glob("*.json"))}
    lines = ["# Results", "",
             "k = tests shown to the repairer. A patch is *plausible* if it passes those k tests, "
             "*correct* if it also passes every hidden test, *overfit* if it does not.", ""]
    series = []
    for label, rows in runs.items():
        lines += [f"## {label}", "",
                  "| k | tasks | plausible | correct | overfit (of plausible) |", "|--:|--:|--:|--:|--:|"]
        rates = []
        for r in rows:
            plausible = r["correct"] + r["overfit"]
            rates.append(100 * r["overfit"] / plausible if plausible else 0)
            lines.append(f"| {r['k']} | {r['tasks']} | {plausible / r['tasks']:.0%} | "
                         f"{r['correct'] / r['tasks']:.0%} | {rates[-1]:.0f}% |")
        lines.append("")
        series.append((label, [r["k"] for r in rows], rates))
    if series:
        lines += ["## Overfit rate vs. tests shown", "", "```mermaid", "xychart-beta",
                  f'    title "Plausible patches that fail hidden tests ({", ".join(s[0] for s in series)})"',
                  f'    x-axis "tests shown (k)" {json.dumps([str(k) for k in series[0][1]])}',
                  '    y-axis "overfit %" 0 --> 100']
        lines += [f"    line {json.dumps([round(v, 1) for v in rates])}" for _, _, rates in series]
        lines += ["```", ""]
    (RESULTS / "RESULTS.md").write_text("\n".join(lines))


def main():
    p = argparse.ArgumentParser(prog="patchproof")
    p.add_argument("--repairer", choices=["search", "llm"], default="search")
    p.add_argument("--model", default="claude-opus-5-5", help="model id for --repairer llm")
    p.add_argument("--k", type=int, nargs="+", default=[1, 2, 3, 5, 10, 20])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    tasks = build(args.seed)
    repairer, label = (repair.search, "search") if args.repairer == "search" \
        else (repair.llm(args.model), args.model)
    rows = evaluate(tasks, repairer, args.k, args.seed, args.workers)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{label}.json").write_text(json.dumps(rows, indent=2))
    report()
    print((RESULTS / "RESULTS.md").read_text())


main()
