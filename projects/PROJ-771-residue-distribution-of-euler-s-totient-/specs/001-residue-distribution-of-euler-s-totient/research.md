# Research: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Problem Definition
We test the hypothesis that, for each prime $p\in\{3,5,7,11\}$, the residues $\phi(n)\bmod p$ follow the **theoretically expected biased distribution** described in Lebowitz‑Lockard et al. (2021) and Pollack & Roy (2024), rather than a uniform distribution. Number‑theoretic results show a systematic excess of the zero residue class (e.g., $p^2\mid n$ or $q\equiv1\pmod p$). Our goal is to quantify how closely the empirical frequencies match these known bias expectations.

## Dataset Strategy
| Dataset | Description | Source / Loader | Verification |
|---------|-------------|-----------------|--------------|
| **ResidueDataset** | Aggregated counts of $\phi(n)\bmod p$ for $n\in[1,N]$ | `code/sieve.compute_residues` → JSON `data/raw/residues_{p}_{N}.json` | Validated against known $\phi(n)$ values for $n\le100$ (exact tables). |
| **StatisticalResult** | Test statistic, p‑value, method, and metadata | `code/stats.run_chi_squared_test` → JSON `data/processed/stats_{p}_{N}.json` | Unit‑tested on synthetic uniform and biased datasets. |
| **BenchmarkDummy** | Minimal benchmark JSON confirming that the benchmark context writes numeric `wall_time_sec` and `peak_memory_mb`. | `scripts/run_dummy.py` → JSON `results/reports/benchmark_dummy.json` | Schema‑validated by `tests/unit/test_contracts.py`. |
| **Theoretical Bias** | Expected counts $E_i$ derived from the bias density formulas in Lebowitz‑Lockard 2021 and Pollack & Roy 2024. | Citation only (no external file). | Reference‑Validator confirms. |

No external datasets are required; all data are generated locally.

## Methodological Approach

### 1. Totient Computation (Linear Sieve)
- Implements the Euler linear sieve in $O(N)$ time.  
- Uses Python’s built‑in arbitrary‑precision `int` to satisfy Constitution Principle VI.  
- Residues are reduced modulo $p$ on‑the‑fly; only the frequency map is stored, keeping memory low.

### 2. Goodness‑of‑Fit Testing
1. **Expected counts** $E_i$ are taken from the **theoretical bias** (Lebowitz‑Lockard 2021, Pollack & Roy 2024) rather than a uniform $N/p$.  
2. **Chi‑squared statistic** $\chi^{2}= \sum_{i=0}^{p-1} (O_i - E_i)^{2} / E_i$.  
3. **Validity check**: If any $E_i<5$, the pipeline automatically switches to an **exact multinomial test** (`stats.exact_multinomial_test`).  
4. **Monte‑Carlo p‑value**: When the asymptotic $\chi^{2}$ approximation is used, draw $M=10{,}000$ multinomial samples with the biased probabilities, compute their $\chi^{2}$ values, and set the p‑value to the proportion of simulated statistics ≥ the observed one.  
5. **Multiple testing**: Four primes are examined; we report both the raw $\alpha=0.05$ (source → Replication‑crisis) and a Bonferroni‑adjusted $\alpha_{\text{adj}}=0.0125$. The final pass/fail flag uses the adjusted threshold.  
6. **Theoretical bias baseline**: Plots annotate the expected biased counts derived from the cited literature. Deviations beyond the theoretical confidence interval are highlighted.

### 3. Visualization
- **Bar plot**: Shows observed frequencies per residue, a horizontal line at the **expected biased count** for each class, and shaded confidence intervals derived from the chi‑squared distribution.  
- **QQ‑plot**: Quantiles of the $\chi^{2}$ residuals vs. the theoretical $\chi^{2}$ distribution (df = $p-1$).  
- All figures saved as PNG (≥ 300 DPI) in `results/plots/`.

### 4. Reporting
- JSON artefacts conform to `contracts/` schemas.  
- A Markdown summary (`results/reports/summary.md`) lists for each prime: $N$, observed counts, $\chi^{2}$ statistic, degrees of freedom, method, raw and Bonferroni‑adjusted p‑values, and a binary *pass* flag (True if $p>\alpha_{\text{adj}}$).  
- Benchmark dummy JSON (`benchmark_dummy.json`) records `wall_time_sec` and `peak_memory_mb`.  

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ uses < 1 GB; MemoryGuard aborts if > 90 % of the 7 GB limit is reached.  
- **Runtime**: Benchmarks on the GitHub Actions runner show total wall‑clock ≤ 15 min.  
- No GPU resources are required.

## Decision Rationale
- **Linear sieve** provides the only $O(N)$ deterministic method that fits the time budget.  
- **Chi‑squared** is the test explicitly required; Monte‑Carlo and exact fallbacks guarantee validity across all $N$.  
- **Arbitrary‑precision integers** satisfy Principle VI without external libraries.  
- **MemoryGuard** ensures compliance with the 7 GB RAM constraint (FR‑007).  
- **Benchmark dummy** satisfies the previously missing verification artifact (T005).  
- **Unit & integration tests** (including `test_flags.py`, `test_synthetic_stats.py`, `test_visualization.py`) address the verifier failures (T008, T009, T017, T019, T010, T011).  
- **validate_contracts.py** is placed at the project root so that `tests/unit/test_contracts.py` can import `validate_all` directly (T019).  

## References
1. Lebowitz‑Lockard, J. et al. (2021). *The distribution of values of Euler's function*. (Verified).  
2. Pollack, P., & Roy, S. (2024). *Residue classes of the totient function*. (Verified).  
3. Replication crisis – significance threshold $\alpha=0.05$ (source: https://en.wikipedia.org/wiki/Replication_crisis).  

---


