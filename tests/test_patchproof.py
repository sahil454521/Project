import ast
import unittest

from patchproof.bench import build
from patchproof.evaluate import score, split
from patchproof.mutate import mutants
from patchproof.repair import search
from patchproof.sandbox import run

SRC = "def f(a, b):\n    if a < b:\n        return a + 1\n    return b\n"


class Mutate(unittest.TestCase):
    def test_mutants_are_distinct_valid_programs(self):
        ms = mutants(SRC)
        self.assertEqual(len(ms), len(set(ms)))
        self.assertNotIn(ast.unparse(ast.parse(SRC)), ms)
        self.assertTrue(any("a <= b" in m for m in ms) and any("a - 1" in m for m in ms))
        for m in ms:
            ast.parse(m)

    def test_source_is_left_unchanged(self):
        self.assertEqual(mutants(SRC), mutants(SRC))


class Sandbox(unittest.TestCase):
    def test_value_error_and_infinite_loop(self):
        ok, boom, loop, noisy = run(
            [SRC, "def f(a, b):\n    return a / 0\n", "def f(a, b):\n    while True:\n        pass\n",
             "def f(a, b):\n    print('x')\n    return [a, (b,)]\n"], "f", [[1, 2]])
        self.assertEqual(ok, [{"ok": 2}])
        self.assertEqual(boom, [{"error": "ZeroDivisionError"}])
        self.assertEqual(loop, [{"error": "Timeout"}])
        self.assertEqual(noisy, [{"ok": [1, [2]]}])  # prints ignored, tuples normalised

    def test_loop_cannot_swallow_the_timeout(self):
        src = "def f():\n    while True:\n        try:\n            pass\n        except Exception:\n            pass\n"
        self.assertEqual(run([src], "f", [[]]), [[{"error": "Timeout"}]])


class Bench(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = build()

    def test_deterministic_and_every_bug_is_observable(self):
        self.assertEqual([t.buggy for t in self.tasks], [t.buggy for t in build()])
        self.assertGreater(len(self.tasks), 100)
        for t in self.tasks:
            self.assertTrue(t.failing)
            self.assertNotEqual(t.buggy, ast.unparse(ast.parse(t.reference)))

    def test_split_shows_a_failing_test_and_hides_the_rest(self):
        t = self.tasks[0]
        visible, hidden = split(t, 5)
        self.assertEqual(len(visible), 5)
        self.assertIn(visible[0], t.failing)
        self.assertEqual(sorted(visible + hidden), list(range(len(t.inputs))))

    def test_scoring_separates_correct_overfit_and_unrepaired(self):
        t = self.tasks[0]
        self.assertEqual(score(t, lambda *_: t.reference, 3), "correct")
        self.assertEqual(score(t, lambda *_: t.buggy, 3), "unrepaired")
        self.assertEqual(score(t, lambda *_: None, 3), "unrepaired")

        def memorise(buggy, entry, tests):  # passes exactly the tests it was shown
            return f"def {entry}(*args):\n    return dict({[(repr(list(a)), w) for a, w in tests]!r}).get(repr(list(args)))\n"
        self.assertEqual(score(t, memorise, 3), "overfit")

    def test_search_repairs_a_single_mutation_given_every_test(self):
        t = next(t for t in self.tasks if t.order == 1)
        patch = search(t.buggy, t.entry, [(a, e["ok"]) for a, e in zip(t.inputs, t.expected)])
        self.assertEqual(run([patch], t.entry, t.inputs)[0], t.expected)


if __name__ == "__main__":
    unittest.main()
