# Finite-range residue imbalance of Euler's totient

## Research question
Across n <= N for N = 10^3, 10^4, 10^5 and 10^6, how does the discrepancy
from uniformity of phi(n) modulo p differ between the unconditional population
and the population conditioned on p not dividing phi(n), for p in {5, 7, 11}?
Does the finite-range conditional discrepancy decrease consistently with N, or
are there reversals across these moduli and scales?

## Scientific motivation and prior work
Lebowitz-Lockard, Pollack and Singha Roy (2021), "Distribution mod p of Euler's
totient and the sum of proper divisors", arXiv:2105.12850,
https://arxiv.org/abs/2105.12850, prove asymptotic uniformity of the totient
values COPRIME to p across the p-1 nonzero classes, for p >= 5 in the stated
range. This is not unconditional uniformity across all p classes. Confusing
these populations makes a computational comparison scientifically misleading.
This is a bounded computational replication/finite-range illustration, not a
claim of a new theorem or a novel asymptotic result. Cite the actual theorem
with its assumptions and distinguish it from our finite-range measurements.

## Method and scope
Compute phi(n) exactly by an integer sieve, including phi(1)=1, through one
million on a CPU. No external dataset is needed: the mathematical objects are
the study population, computed exactly, not invented observational data.
Validate small n independently by counting coprime integers using gcd. For each
N and p, export integer residue counts, zero-residue mass, conditional counts,
and total variation distance to the appropriate uniform reference. Use the
conventional TV definition half the sum of absolute frequency differences.
Report denominators explicitly; the unconditional denominator is N, the
conditional denominator excludes all zero residues. Check counts sum exactly.
Produce a compact table, a plot of conditional/unconditional TV against N,
and a short reproducible methods/results paper. Report any nonmonotonicity
honestly. These are deterministic census summaries: no iid chi-square tests,
KS tests, p-values, bootstrap significance, or made-up sampling uncertainty.
Finite computation cannot prove asymptotic convergence.

## Bounded acceptance criteria
A clean CPU rerun under five minutes produces the exact count tables, summary
CSV/JSON, figures and an interpretable paper. Independently verify the small-n
sieve, count conservation, conditional denominators and TV calculations. A
single analysis script plus a small test module is sufficient; aim for 8-12
substantive research tasks. No package framework, API, GPU, statistical model,
new dataset hunt, extra moduli, or production service is needed. Keep the
research question and the exact computations intact if replanning is needed.
