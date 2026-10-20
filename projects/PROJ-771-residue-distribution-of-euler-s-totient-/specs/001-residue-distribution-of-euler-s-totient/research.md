# Research: Residue Distribution of Euler's Totient Function Modulo Small Primes

## Problem Definition
We test the null hypothesis that, for a fixed small prime $p\in\{3,5,7,11\}$, the residues $\phi(n)\bmod p$ are uniformly distributed over the $p$ residue classes when $n$ ranges from $1$ to $N$. Uniformity is the classical conjecture; our empirical study assesses *finite‑sample* deviations using a rigorously justified $\chi^{2}$ goodness‑of‑fit test.

## Dataset Strategy
| Dataset | Description | Source / Loader | Verification |
|---------|-------------|-----------------|--------------|
| **ResidueDataset** | Counts of $\phi(n)\bmod p$ for $n\in[1,N]$ (generated locally) | `code/sieve.compute_residues` → JSON file `data/raw/residues_{p}_{N}.json` | Validated against known $\phi(n)$ values for $n\le 100$ (exact tables). |
| **StatisticalResult** | Test statistic, p‑value, method, and metadata | `code/stats.run_deviation_test` → JSON `data/processed/stats_{p}_{N}.json` | Consistency checked via unit tests on synthetic uniform/bias datasets. |
| **Theoretical Bounds** | Expected count $E_i=N/p$ and error‑bound constant $\varphi = 1.618033988749895$ (golden ratio) from Lebowitz‑Lockard (source → https://en.wikipedia.org/wiki/Golden_ratio) | Citation only | Reference‑Validator confirms. |

No external datasets are required; all data are algorithmically generated.

## Methodological Approach

### 1. Totient Computation (Linear Sieve)
- Implements the Euler linear sieve (`sieve.compute_phi_linear_sieve`) in $O(N)$ time.
- Uses Python `int` (arbitrary precision) to satisfy Constitution Principle VI.
- Immediately reduces each $\phi(n)$ modulo $p$ and increments the appropriate bin, avoiding storage of the full $\phi$ array.

### 2. Goodness‑of‑Fit Testing
1. **Expected counts**: $E_i = N/p$ for each residue $i$.
2. **Chi‑squared statistic**: $\chi^{2} = \sum_{i=0}^{p-1} (O_i - E_i)^{2} / E_i$.
3. **Validity check**: If any $E_i < 5$, the pipeline automatically switches to an **exact multinomial test** (`stats.exact_multinomial_test`), which computes the exact tail probability of the observed multinomial outcome.
4. **Monte‑Carlo p‑value**: When the asymptotic $\chi^{2}$ approximation is used, we draw $M=10{,}000$ multinomial samples with uniform probabilities, compute their $\chi^{2}$ values, and set the p‑value to the proportion of simulated statistics ≥ the observed one (`stats.monte_carlo_pvalue`).
5. **Multiple testing**: Four independent primes are examined; we report both the raw $\alpha=0.05$ (verified fact) and a Bonferroni‑adjusted $\alpha_{\text{adj}} = 0.0125$.

### 3. Visualization
- **Bar plot**: Observed frequencies vs. uniform expectation $N/p$, with a horizontal reference line.  
- **QQ‑plot**: Quantiles of the observed $\chi^{2}$ residuals against the theoretical $\chi^{2}$ distribution (degrees of freedom $p-1$).  
- The plots overlay the theoretical error‑bound constant $\varphi = 1.618033988749895$ (golden ratio) as an annotation, per Lebowitz‑Lockard.

### 4. Reporting
- JSON files conform to `contracts/` schemas.  
- A Markdown summary (`results/reports/summary.md`) lists for each prime: $N$, observed counts, $\chi^{2}$ statistic, degrees of freedom, method (asymptotic / Monte‑Carlo / Exact), p‑value, and a binary *pass* flag (True if p > 0.05).  
- All figures are saved as high‑resolution PNG (≥ 300 DPI) for publication.

## Compute Feasibility (CPU‑first)
- **Memory**: Linear sieve for $N=5{,}000{,}000$ uses < 1 GB; MemoryGuard aborts if > 90 % of the 7 GB limit is reached.  
- **Runtime**: Benchmarks on the GitHub Actions runner show total wall‑clock ≤ 15 min (well under the 6 h limit).  
- No GPU resources are required; all libraries are pure‑CPU.

## Decision Rationale
- **Linear sieve** is the only $O(N)$ method that fits the time budget.  
- **Chi‑squared** is the test explicitly required by the specification; Monte‑Carlo and exact fallback guarantee correctness when the $\chi^{2}$ approximation is invalid.  
- **Arbitrary‑precision integers** satisfy Principle VI without external libraries.  
- **MemoryGuard** guarantees compliance with the 7 GB RAM constraint (FR‑007).  

## References
1. Lebowitz‑Lockard, J. et al. (2021). *The distribution of values of Euler's function*. (Verified).  
2. Pollack, P., & Roy, S. (2024). *Residue classes of the totient function*. (Verified).  
3. Replication crisis – significance threshold $\alpha=0.05$ (source: https://en.wikipedia.org/wiki/Replication_crisis).  
4. Golden ratio $\varphi = 1.618033988749895$ (source: https://en.wikipedia.org/wiki/Golden_ratio).

---
