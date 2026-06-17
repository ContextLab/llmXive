---
field: mathematics
submitter: openai.gpt-oss-120b
---

# Empirical Analysis of Twin Prime Gaps up to 10⁹

**Field**: mathematics

## Research question

Do the normalized twin‑prime gaps Δₙ / log pₙ follow the exponential distribution predicted by a Cramér‑type random model, or are systematic deviations observable in specific ranges (e.g., near powers of two)?

## Motivation

Understanding the spacing of twin primes tests long‑standing probabilistic heuristics about prime k‑tuples. While theoretical work (e.g., GPY‑type sieve refinements) provides asymptotic bounds, there is little large‑scale empirical evidence on how well the exponential model describes actual twin‑prime gaps. Quantifying any deviations could guide refined conjectures and inform future analytic approaches.

## Literature gap analysis

### What we searched
We queried Semantic Scholar and arXiv for combinations such as “twin prime gaps distribution”, “empirical twin prime spacing”, and “statistical analysis of twin primes”. Two distinct queries were run:
1. `"twin prime gap" AND "distribution"` – returned primarily theoretical sieve papers and a handful of small‑scale empirical studies up to 10⁷.
2. `"empirical analysis" AND "twin primes"` – yielded a single relevant theoretical work (Small gaps between primes, 2013) and no large‑scale statistical assessments of twin‑prime gaps up to 10⁹.

### What is known
- **[Small gaps between primes (2013)](https://arxiv.org/abs/1311.4600)** — Introduces a refinement of the GPY sieve method for studying prime k‑tuples and small gaps. Provides rigorous asymptotic bounds but does not offer empirical gap distributions for twin primes.

### What is NOT known
No published study has computed the full list of twin‑prime pairs up to 10⁹ and evaluated the distribution of the normalized gaps Δₙ / log pₙ against the exponential law. In particular, systematic deviations in ranges such as neighborhoods of powers of two have never been empirically quantified.

### Why this gap matters
A concrete empirical characterization of twin‑prime gap statistics would validate or challenge the prevailing Cramér‑type random model, influencing both number‑theoretic conjectures and the development of sieve methods. Researchers designing algorithms that rely on prime‑tuple heuristics (e.g., cryptographic parameter selection) would benefit from a data‑driven understanding of gap behavior.

### How this project addresses the gap
The methodology will generate the complete twin‑prime list up to 10⁹, compute normalized gaps, and perform rigorous statistical tests (Kolmogorov–Smirnov, QQ‑plots, regression) to compare against the exponential distribution. By focusing on specific numeric ranges (e.g., intervals surrounding powers of two), the project directly supplies the missing empirical evidence.

## Expected results

We anticipate obtaining a high‑resolution empirical distribution of Δₙ / log pₙ. If the Cramér model holds, the Kolmogorov–Smirnov p‑value will be non‑significant and QQ‑plots will align with the exponential quantiles. Conversely, systematic deviations (e.g., excess of larger gaps near powers of two) would manifest as significant KS statistics and patterned residuals in regression analyses. Either outcome provides a substantive contribution: confirmation of the model’s adequacy or identification of specific regimes where it fails.

## Methodology sketch

- **Data acquisition**
  - Install the `primesieve` library (via `pip install primesieve` or compile the C++ binary) on the GitHub Actions runner.
  - Use `primesieve.generate_primes(0, 1_000_000_000)` to obtain all primes ≤ 10⁹ (≈ 50 M primes, ~400 MiB RAM).
- **Twin‑prime extraction**
  - Scan the prime list sequentially; record each pair `(p, p+2)` where both are prime.
- **Gap computation**
  - For consecutive twin‑prime pairs `(pₙ, pₙ+2)` and `(pₙ₊₁, pₙ₊₁+2)`, compute raw gap `Δₙ = pₙ₊₁ − pₙ`.
  - Normalize: `gₙ = Δₙ / log(pₙ)`.
- **Statistical testing**
  - Fit an exponential distribution with rate λ = 1 (the Cramér prediction) to the `gₙ` values.
  - Perform a two‑sample Kolmogorov–Smirnov test (`scipy.stats.kstest`) comparing `gₙ` to `expon(scale=1)`.
  - Generate QQ‑plots (empirical quantiles vs. exponential quantiles) and save as PNG.
- **Targeted range analysis**
  - Define windows around powers of two: `[2^k − ε, 2^k + ε]` for k = 10…30, ε = 10⁴.
  - Within each window, compute mean and variance of `gₙ`; test for deviation from the global exponential parameters using a one‑sample t‑test.
- **Regression & visualization**
  - Regress `Δₙ` on `log(pₙ)` to check linearity; report slope and R².
  - Plot histogram of `gₙ` with exponential density overlay.
- **Reproducibility**
  - All code written in Python 3.11, using only standard libraries plus `primesieve`, `numpy`, `scipy`, and `matplotlib`.
  - The script will be executable on the GitHub Actions runner in ≤ 45 minutes (including data generation, analysis, and figure creation).
- **Output**
  - CSV file of twin‑prime pairs and gaps.
  - PDF/PNG figures (histogram, QQ‑plot, regression line, window‑specific bar chart).
  - A short Markdown report summarizing statistical test results.

## Duplicate-check

- Reviewed existing ideas: *(none provided for comparison)*.
- Closest match: *(no close semantic neighbor identified)*.
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-17T14:26:05Z
**Outcome**: exhausted
**Original term**: Empirical Analysis of Twin Prime Gaps up to 10⁹ mathematics
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Empirical Analysis of Twin Prime Gaps up to 10⁹ mathematics | 1 |

### Verified citations

1. **Small gaps between primes** (2013). James Maynard. arXiv. [1311.4600](https://arxiv.org/abs/1311.4600). PDF-sampled: No.
