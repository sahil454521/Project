# PatchProof

**Does an automated bug fix actually work, or does it only pass the tests it was shown?**

Program-repair tools, LLM-based or not, are usually scored by "the tests pass now". A patch
can pass every test it was given and still be wrong. PatchProof measures that gap. It injects
bugs into known-correct programs, shows a repairer only `k` of the tests, and scores each patch
against tests the repairer never saw.

## Result

139 buggy programs, 40 tests each, search-based repairer (`python -m patchproof`):

| tests shown (k) | plausible (passes shown tests) | correct (passes hidden tests too) | overfit, of plausible |
|--:|--:|--:|--:|
| 1 | 96% | 56% | 41% |
| 2 | 94% | 71% | 25% |
| 3 | 94% | 76% | 19% |
| 5 | 94% | 82% | 12% |
| 10 | 94% | 87% | 7% |
| 20 | 92% | 90% | 2% |

With one failing test as the bug report, the repairer "fixes" 96% of bugs, and 41% of those
fixes are wrong. "Tests pass" overstates the true repair rate by 40 points at k=1 and still by
7 points at k=10. Full output and chart: [results/RESULTS.md](results/RESULTS.md).

This reproduces, at small scale, the patch-overfitting effect reported for generate-and-validate
repair by Qi et al. (ISSTA 2015) and Smith et al. (FSE 2015).

## How it works

| Stage | File | What it does |
|---|---|---|
| Seeds | `patchproof/seeds.py` | 24 small reference programs with random input generators. The reference is the oracle. |
| Bug injection | `patchproof/mutate.py` | Single-point AST mutations (comparison, arithmetic, boolean, off-by-one). Up to 4 one-mutation and 2 two-mutation bugs per seed, deduplicated by behaviour. |
| Sandbox | `patchproof/sandbox.py`, `_runner.py` | Runs candidates in a child process with a memory limit and a **line-count budget** instead of a wall-clock timeout, so an infinite loop gets the same verdict on every machine. |
| Split | `patchproof/evaluate.py` | `k` visible tests, always including one the bug fails. The other `40 - k` stay hidden. |
| Repairers | `patchproof/repair.py` | `search`: first program within two mutations that passes the visible tests. `llm`: Claude, given the buggy code and the visible tests. |
| Scoring | `patchproof/evaluate.py` | The harness re-runs every patch itself: `correct`, `overfit` or `unrepaired`. |

Everything is seeded, so the table above regenerates exactly. The core has no dependencies
beyond Python 3.10+ on Linux or macOS.

## Run it

```bash
python -m unittest discover -s tests        # 8 tests, a few seconds
python -m patchproof                        # search baseline, about 2 minutes on 4 cores
python -m patchproof --k 1 5 --seed 1       # other settings

pip install anthropic                       # LLM arm
export ANTHROPIC_API_KEY=...
python -m patchproof --repairer llm         # about 830 API calls at the default settings
python -m patchproof --repairer llm --model claude-haiku-5-5
```

Each run writes `results/<label>.json` and rebuilds `results/RESULTS.md` with one table per
repairer, so models and the baseline line up side by side.

## Limits

- The search repairer draws patches from the same mutation operators that created the bugs.
  That is its best case; real bugs are less convenient.
- The programs are small single functions. The numbers show the overfitting effect, not how
  any tool performs on production code.
- The LLM arm is implemented but has no results committed yet; it needs an API key to run.
- The sandbox stops runaway code, not hostile code. Run it in a container before pointing it
  at a model you do not trust.
- One seed, no confidence intervals. `--seed` gives other samples.
