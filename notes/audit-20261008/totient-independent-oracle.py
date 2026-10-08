"""Independent exact reference; not an artifact produced by the llmXive canary."""

import json
import math
import time
from fractions import Fraction
from pathlib import Path

started = time.monotonic()
limits = (1000, 10000, 100000, 1000000)
moduli = (5, 7, 11)
# Trial factorization of each integer; independent of a totient-array sieve.
primes = []
for candidate in range(2, math.isqrt(max(limits)) + 1):
    if all(candidate % p for p in primes if p * p <= candidate):
        primes.append(candidate)


def phi(n):
    remaining = n
    value = n
    for p in primes:
        if p * p > remaining:
            break
        if remaining % p == 0:
            value = value // p * (p - 1)
            while remaining % p == 0:
                remaining //= p
    if remaining > 1:
        value = value // remaining * (remaining - 1)
    return value


for n in range(1, 501):
    assert phi(n) == sum(math.gcd(k, n) == 1 for k in range(1, n + 1)), n
counts = {p: [0] * p for p in moduli}
rows = []
for n in range(1, max(limits) + 1):
    value = phi(n)
    for p in moduli:
        counts[p][value % p] += 1
    if n in limits:
        for p in moduli:
            cs = counts[p]
            assert sum(cs) == n
            den = n - cs[0]
            assert sum(cs[1:]) == den and den > 0
            u = Fraction(sum(abs(p * c - n) for c in cs), 2 * p * n)
            c = Fraction(sum(abs((p - 1) * v - den) for v in cs[1:]), 2 * (p - 1) * den)
            rows.append(
                dict(
                    N=n,
                    p=p,
                    residue_counts=list(cs),
                    conditional_denominator=den,
                    unconditional_tv=float(u),
                    conditional_tv=float(c),
                    unconditional_tv_exact=str(u),
                    conditional_tv_exact=str(c),
                )
            )
result = dict(
    method="Independent per-integer trial factorization using Euler product; gcd oracle checked n=1..500",
    input_domain="1 <= n <= N; conditional population excludes phi(n) divisible by p",
    pipeline_generated=False,
    elapsed_s=round(time.monotonic() - started, 3),
    rows=rows,
)
Path(__file__).with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
for r in rows:
    print(
        f"N={r['N']:7d} p={r['p']:2d} uncond={r['unconditional_tv']:.8f} cond={r['conditional_tv']:.8f}"
    )
print(f"Elapsed: {result['elapsed_s']}s")
