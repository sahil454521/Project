"""Reference programs. Each maps to a generator of random JSON-able argument lists.

Bugs are injected into these by mutate.py; the reference is the test oracle.
"""


def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a


def binary_search(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def is_palindrome(s):
    i, j = 0, len(s) - 1
    while i < j:
        if s[i] != s[j]:
            return False
        i += 1
        j -= 1
    return True


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def max_subarray(xs):
    best = cur = xs[0]
    for x in xs[1:]:
        cur = x if cur < 0 else cur + x
        if cur > best:
            best = cur
    return best


def merge_sorted(a, b):
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    return out + a[i:] + b[j:]


def run_length_encode(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append([s[i], j - i])
        i = j
    return out


def count_primes(n):
    count = 0
    for k in range(2, n + 1):
        d = 2
        while d * d <= k and k % d != 0:
            d += 1
        if d * d > k:
            count += 1
    return count


def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def bubble_sort(xs):
    xs = list(xs)
    for i in range(len(xs)):
        for j in range(len(xs) - 1 - i):
            if xs[j] > xs[j + 1]:
                xs[j], xs[j + 1] = xs[j + 1], xs[j]
    return xs


def to_roman(n):
    out = ""
    for value, sym in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                       (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out += sym
            n -= value
    return out


def collatz_steps(n):
    steps = 0
    while n > 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def merge_intervals(ivs):
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1]:
            if hi > out[-1][1]:
                out[-1][1] = hi
        else:
            out.append([lo, hi])
    return out


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i]
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[len(b)]


def digit_sum(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total


def leap_year(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def two_sum_sorted(xs, target):
    i, j = 0, len(xs) - 1
    while i < j:
        s = xs[i] + xs[j]
        if s == target:
            return [i, j]
        if s < target:
            i += 1
        else:
            j -= 1
    return []


def longest_run(xs):
    best = cur = 0
    for i in range(len(xs)):
        cur = cur + 1 if i > 0 and xs[i] == xs[i - 1] else 1
        if cur > best:
            best = cur
    return best


def int_sqrt(n):
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid * mid <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def median(xs):
    s = sorted(xs)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def balanced(s):
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def rotate(xs, k):
    if len(xs) == 0:
        return xs
    k = k % len(xs)
    return xs[len(xs) - k:] + xs[:len(xs) - k]


def grade(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def power_mod(base, exp, mod):
    result = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            result = result * base % mod
        base = base * base % mod
        exp //= 2
    return result


def _ints(r, n_max=8, lo=-9, hi=9, n_min=0):
    return [r.randint(lo, hi) for _ in range(r.randint(n_min, n_max))]


def _text(r, alphabet="ab", n_max=8):
    return "".join(r.choice(alphabet) for _ in range(r.randint(0, n_max)))


SEEDS = {
    gcd: lambda r: [r.randint(0, 60), r.randint(0, 60)],
    binary_search: lambda r: [sorted(set(_ints(r, 10, 0, 20))), r.randint(0, 20)],
    is_palindrome: lambda r: [_text(r, "ab", 7)],
    fib: lambda r: [r.randint(0, 25)],
    max_subarray: lambda r: [_ints(r, n_min=1)],
    merge_sorted: lambda r: [sorted(_ints(r, 6)), sorted(_ints(r, 6))],
    run_length_encode: lambda r: [_text(r, "ab", 10)],
    count_primes: lambda r: [r.randint(0, 60)],
    clamp: lambda r: [r.randint(-20, 20), r.randint(-10, 0), r.randint(0, 10)],
    bubble_sort: lambda r: [_ints(r)],
    to_roman: lambda r: [r.randint(1, 3999)],
    collatz_steps: lambda r: [r.randint(1, 60)],
    merge_intervals: lambda r: [[[a, a + r.randint(0, 5)] for a in _ints(r, 6, 0, 20)]],
    edit_distance: lambda r: [_text(r, "abc", 6), _text(r, "abc", 6)],
    digit_sum: lambda r: [r.randint(0, 99999)],
    leap_year: lambda r: [r.choice([r.randint(1800, 2400), r.randrange(1600, 2500, 100)])],
    two_sum_sorted: lambda r: [sorted(set(_ints(r, 8, 0, 15))), r.randint(0, 30)],
    longest_run: lambda r: [_ints(r, 10, 0, 2)],
    int_sqrt: lambda r: [r.choice([r.randint(0, 400), r.randint(0, 20) ** 2])],
    median: lambda r: [_ints(r, 9, n_min=1)],
    balanced: lambda r: [_text(r, "()", 8)],
    rotate: lambda r: [_ints(r, 7), r.randint(0, 10)],
    grade: lambda r: [r.randint(40, 100)],
    power_mod: lambda r: [r.randint(0, 20), r.randint(0, 20), r.randint(1, 30)],
}
