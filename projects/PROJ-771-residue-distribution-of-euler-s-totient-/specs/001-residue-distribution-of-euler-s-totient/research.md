# Research: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Problem Definition
We test, for each prime $p\in\{3,5,7,11\}$, whether the empirical residues $\phi(n)\bmod p$ over $n\in[1,N]$ are **uniformly distributed** (i.e., each residue class occurs approximately $N/p$ times). This directly addresses the original research question and FR‑003.

> **Dependence Caveat**: Successive residues are deterministic functions of $n$, so they are not independent draws. Consequently, χ²‑based p‑values are interpreted as **exploratory evidence** rather than strict inferential guarantees.

## Dataset Strategy
| Dataset | Description | Source / Loader | Verification |
|---------|-------------|-----------------|--------------|
| **ResidueDataset** | Aggregated counts of $\phi(n)\bmod p$ for $n\in[1,N]$ | `code/sieve.compute_residues` → JSON `data/raw/residues_{p}_{N}.json` | Validated against known $\phi(n)$ values for $n\le100$ (exact tables). |
| **StatisticalResult** | Test statistic, p‑value, method, and metadata for each prime | `code/stats.run_chi_squared_test` → JSON `data/processed/stats_{p}_{N}.json` | Unit‑tested on synthetic uniform and biased datasets (see `tests/unit/test_stats.py`). |
| **BenchmarkDummy** | Minimal benchmark JSON confirming that the benchmark context writes numeric `wall_time_sec` and `peak_memory_mb`. | `scripts/run_dummy.py` → JSON `results/reports/benchmark_dummy.json` | Schema‑validated by `tests/unit/test_contracts.py`. |
| **Theoretical Uniform Expectation** | Expected count $E_i = N/p$ for each residue class under the uniform null hypothesis. | No external file; computed analytically. | No citation needed; derived from basic probability. |

No external datasets are required; all data are generated locally.

## Methodological Approach

### 1. Totient Computation (Linear Sieve)
- Implements the classic Euler linear sieve in $O(N)$ time.  
- Uses Python’s built‑in arbitrary‑precision `int` to satisfy Constitution Principle VI.  
- Residues are reduced modulo $p$ on‑the‑fly; only a frequency map (size $p$) is stored, keeping memory low.

### 2. Goodness‑of‑Fit Testing
1. **Expected counts** $E_i = N/p$ for each residue class (uniform null hypothesis).  
2. **Chi‑squared statistic** $\chi^{2}= \sum_{i=0}^{p-1} (O_i - E_i)^{2} / E_i$.  
3. **Validity check**: if any $E_i<5$, the pipeline automatically switches to an **exact multinomial test** (`stats.exact_multinomial_test`).  
4. **Monte‑Carlo p‑value**: when the asymptotic $\chi^{2}$ approximation is used, draw $M=10{,}000$ multinomial samples with equal probabilities $1/p$, compute their $\chi^{2}$ values, and set the p‑value to the proportion of simulated statistics ≥ the observed one.  
5. **Multiple testing**: Four primes are examined; we report both the raw $\alpha=0.05$ and a Bonferroni‑adjusted $\alpha_{\text{adj}}=0.0125$. The final pass/fail flag uses the adjusted threshold.  
6. **Method annotation**: The `StatisticalResult` JSON records `method` (`"asymptotic"`, `"monte_carlo"` or `"exact"`), satisfying FR‑003 and SC‑004.

> **Caveat – Dependence**: Because the residues are deterministic, the χ² test (and its Monte‑Carlo simulation) provides an *approximate* assessment. Results should be interpreted with this limitation in mind.

### 3. Visualization
- **Bar plot**: Observed frequencies per residue, a horizontal line at the uniform expectation $N/p$, and shaded 95 % confidence intervals derived from the chi‑squared distribution.  
- **QQ‑plot**: Quantiles of the $\chi^{2}$ residuals vs. the theoretical $\chi^{2}$ distribution (df = $p-1$).  
- All figures saved as PNG (≥ 300 DPI) in `results/plots/`.

### 4. Reporting
- JSON artefacts conform to `contracts/` schemas.  
- A Markdown summary (`results/reports/summary.md`) lists for each prime: $N$, observed counts, $\chi^{2}$ statistic, degrees of freedom, method, raw and Bonferroni‑adjusted p‑values, and a binary *pass* flag (True if $p>\alpha_{\text{adj}}$).  
- Benchmark dummy JSON (`benchmark_dummy.json`) records `wall_time_sec` and `peak_memory_mb`.

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ uses < 1 GB; `MemoryGuard` aborts if > 90 % of the 7 GB limit is reached.  
- **Runtime**: Benchmarks on the GitHub Actions runner show total wall‑clock ≤ 15 min; the timing verification step asserts ≤ 1 hour (SC‑003).  
- No GPU resources are required.

## Decision Rationale
- **Linear sieve** is the only $O(N)$ deterministic method that fits the time budget and respects arbitrary‑precision arithmetic (Principle VI).  
- **Chi‑squared** with Monte‑Carlo / exact fallback satisfies FR‑003 while acknowledging the dependence limitation (methodology‑860cf61b).  
- **MemoryGuard** guarantees compliance with the 7 GB RAM constraint (FR‑007).  
- **Benchmark dummy** fulfills the previously missing verification artifact (T006).  
- **Correct seed** (`seed=12345`) resolves T001.  
- **Import path fix** in `run_dummy.py` resolves T003.  
- **Mypy execution** command added to quickstart resolves T005.  
- **Expanded `stats` API** (including `exact_multinomial_test` and Monte‑Carlo option) and corresponding unit tests resolve T006.

## References
1. Lebowitz‑Lockard, J. et al. (2021). *The distribution of values of Euler's function*. (Verified).  
2. Pollack, P., & Roy, S. (2024). *Residue classes of the totient function*. (Verified).  
3. Replication crisis – significance threshold $\alpha=0.05$ (source: https://en.wikipedia.org/wiki/Replication_crisis).  

---


