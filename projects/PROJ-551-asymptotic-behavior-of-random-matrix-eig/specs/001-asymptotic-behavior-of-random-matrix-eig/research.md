# Research: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Theoretical Background
- **Wigner Semicircle Law**: For an \(N\times N\) symmetric matrix with i.i.d. entries of variance \(1/N\), the empirical spectral distribution converges to the semicircle with support \([-2,2]\); the edge is **2** (verified: arXiv:0812.2602, https://arxiv.org/abs/0812.2602).
- **BBP Phase Transition**: A rank-\(k\) deterministic perturbation of spectral norm \(\theta\) produces outliers when \(\theta > 1\) (standard scaling); predicted outlier location \(\theta + 1/\theta\).

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Synthetic matrices | Generated in‑process (no external download) | `numpy.random.default_rng(seed)` | Reproducible; FR‑001. No verified external dataset is needed or used. |
| Perturbation patterns | Deterministic construction | Custom Python functions | Structural fidelity per Constitution VII. |
| Reference values | Semicircle edge = 2 | arXiv:0812.2602 (verified) | Hard‑coded constant for outlier detection. |

No external datasets are required; all data are generated on the fly, satisfying compute‑feasibility constraints.

## Methodology
1. **Matrix Generation (FR‑001)**: \(W_N\) with entries \(\mathcal N(0,1/N)\), seeded RNG recorded in `SimulationRun`.
2. **Sparse Perturbation (FR‑002)**: rank \(k\in\{1,2,5\}\); patterns: diagonal, block‑sparse (block size 10), random‑sparse (density \(p\in[0.05,0.5]\)).  
   *Random‑sparse construction*: first draw a random support of density \(p\); then place exactly \(k\) non‑zero entries (spikes) on distinct rows/columns **within that support**, scaling the resulting matrix to spectral norm \(\theta\). This guarantees rank‑\(k\) while respecting the prescribed sparsity density, keeping `k` and `p` independent structural variables. The spectral norm is verified after construction.
3. **Eigenvalues (FR‑003, SC‑002, SC‑004)**: top‑10 via `eigsh(which='LA', tol=1e-10, maxiter=1000)`; wall‑clock time recorded.
4. **Outlier detection (FR‑004)**: An eigenvalue \(\lambda\) is flagged as an outlier iff  
   \[
   \lambda > 2 + \tau(N),\qquad \tau(N)=\max\bigl(0.05,\;2\cdot N^{-2/3}\bigr).
   \]  
   The term \(2\cdot N^{-2/3}\) approximates twice the Tracy‑Widom fluctuation scale (≈0.032 at \(N=500\), ≈0.013 at \(N=2000\)); we also enforce a floor of 0.05 so that for all \(N\) the tolerance exceeds the typical bulk‑edge noise. This N‑dependent cutoff avoids mis‑classification especially at smaller \(N\).
5. **Parameter sweep (FR‑005)**: \(\theta\) grid \([0.5,3.0]\) step 0.1 (raw run records retain **all** \(\theta\) values, including sub‑threshold \(\theta<1\)). All patterns and ranks are swept; repetitions are sized to the CPU budget (target 500 where the ≤6 h budget allows; fewer repetitions are recorded explicitly with `total_runs` and the power limitation noted).
6. **Sparsity sensitivity (FR‑006)**: \(p\in\{0.05,0.1,0.2,0.3,0.4,0.5\}\) at fixed \(\theta=1.5\).
7. **Finite‑size analysis**: \(N\in\{500,1000,1500,2000\}\) for representative configurations; quantify finite‑size shifts in bulk edge and outlier probability.
8. **Aggregation and fit (FR‑007)**:  
   - `aggregate_thresholds.py` reads the raw sweep Parquet, groups by configuration **excluding** any \(\theta_c\) fields, and writes `aggregated_thresholds.json` (no theta‑c fields).  
   - `threshold_fit.py` reads the **raw** run records (including \(\theta<1\)), fits a sigmoid \(f(\theta)=1/(1+\exp[-a(\theta-\theta_c)])\) via maximum‑likelihood, and writes `threshold_fit.json` validated against `threshold_fit.schema.yaml`. Non‑convergent fits are recorded with `fit_status: "failed"` and `theta_c_estimate` / `theta_c_confidence` set to `null` rather than NaN.
9. **Statistical Rigor**  
   - **Multiple comparisons**: bootstrap CIs for \(\theta_c\) rather than raw p‑values across the \(\theta\)-grid.  
   - **Power**: with \(R\) repetitions, SE of outlier probability ≤ \(0.5/\sqrt R\) (0.022 at \(R=500\)); if the compute budget forces fewer repetitions, the actual \(R\) is reported and the limitation acknowledged.  
   - **Causal claims**: associational only (simulation study; FR‑007).  
   - **Measurement validity**: standard Gaussian Wigner ensemble; perturbation norm enforced by explicit spectral scaling and verified.  
   - **Collinearity**: \(k\), \(p\), \(\theta\), \(N\) are independent design factors; no regression coefficients interpreted as independent effects.

## Decision / Rationale (Compute)
- **CPU‑first**: ARPACK on dense symmetric matrices up to \(N=2000\) fits easily within modest RAM capacities. (a 2000×2000 float64 matrix is 32 MB); no GPU needed (SC‑002). No GPU escape hatch required.
- **Budget control**: total work = (configs × repetitions) eigsh calls; the sweep driver caps repetitions so the full pipeline stays within the ≤6 h job limit, recording the achieved `total_runs` honestly.

## Expected Deliverables
- `data/processed/single_run_results.json`, `convergence_report.json`, `sweep_runs.parquet`, `sensitivity_results.parquet`, `finite_size_results.parquet`, `aggregated_thresholds.json`, `threshold_fit.json` — all schema‑valid and checksummed.
- Passing contract tests (no skips) and reproducibility integration test (top eigenvalue within 1e‑6 of the stored reference, e.g. A representative value for the reference configuration.).
- Figures: outlier probability vs \(\theta\); \(\theta_c\) vs density; finite‑size plots.

---


