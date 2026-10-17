# Research: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Theoretical Background
- **Wigner Semicircle Law**: For an \(N\times N\) symmetric matrix with i.i.d. entries of variance \(1/N\), the empirical spectral distribution converges to the semicircle with support \([-2,2]\) (edge = **2**, source: arXiv:0812.2602).  
- **BBP Phase Transition**: Adding a rank‑\(k\) deterministic perturbation of spectral norm \(\theta\) yields outliers when \(\theta > 1\) (for the standard scaling). The predicted outlier location is \(\theta + 1/\theta\).

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **Synthetic matrices** | Generated in‑process (no external download) | `numpy.random.normal` (seeded) | Guarantees reproducibility; conforms to FR‑001. |
| **Perturbation patterns** | Deterministic construction (diagonal, block‑sparse, random‑sparse) | Custom Python functions | Structural fidelity enforced by schema (SC‑VII). |
| **Reference values** | Theoretical edge \(=2\) (verified arXiv:0812.2602) | Hard‑coded constant | Used for outlier detection; empirical bulk edge is recorded **only for diagnostics**. |

No external datasets are required; all data are created on the fly, satisfying the compute‑feasibility constraints.

## Methodology
1. **Matrix Generation (FR‑001)**  
   - For each run, draw a dense matrix \(W_N\) with entries \(\mathcal N(0,1/N)\).  
   - Use `numpy.random.default_rng(seed)`; seed recorded in `SimulationRun`.  

2. **Sparse Perturbation (FR‑002)**  
   - Build \(P_N\) of rank \(k\in\{1,2,5\}\).  
   - Pattern types:  
     * *Diagonal*: non‑zero entries only on the diagonal.  
     * *Block‑sparse*: random \(b\times b\) blocks (block size fixed at 10).  
     * *Random‑sparse*: support density \(p\in[0.05,0.5]\) chosen per sweep.  
   - Scale \(P_N\) to have spectral norm \(\theta\) (computed via `scipy.sparse.linalg.svds`).  

3. **Eigenvalue Computation (FR‑003, SC‑002)**  
   - Compute the top‑10 eigenvalues of \(A_N = W_N + P_N\) using `scipy.sparse.linalg.eigsh` with `which='LA'`, `tol=1e-10`, `maxiter=1000`.  
   - Record computation time (ms).  

4. **Outlier Detection (FR‑004)**  
   - **Primary rule**: flag eigenvalue \(\lambda\) as an outlier if  
     \[
     \lambda > 2.0 + 0.05.
     \]  
     The theoretical edge \(2\) is taken from the semicircle law; the tolerance \(0.05\) guards against numerical noise.  
   - **Diagnostic statistic**: compute the empirical bulk edge as the 99th percentile of the full spectrum and store it in `SimulationRun.empirical_bulk_edge` for later analysis **but do not use it to define outliers** (avoids circularity).  

5. **Parameter Sweep (FR‑005)**  
   - Grid over \(\theta\in[0.5, 3.0]\) with step 0.1, for each pattern type and rank.  
   - For each configuration, run **500** independent seeds (subject to CPU budget).  
   - With 500 repetitions, the standard error of an outlier probability is \(\sqrt{p(1-p)/500}\le0.022\), providing sufficient precision to locate the BBP threshold.  

6. **Sparsity Sensitivity (FR‑006)**  
   - For the *random‑sparse* pattern, additionally sweep support density \(p\in\{0.05,0.1,0.2,0.3,0.4,0.5\}\) while fixing \(\theta=1.5\).  

7. **Finite‑Size Analysis (addresses methodology‑7cd8bfa6)**  
   - Sweep matrix dimension \(N\in\{500,1000,1500,2000\}\) for a representative subset of \((k,\theta,\text{pattern})\) configurations.  
   - Record how the empirical bulk edge and outlier probability vary with \(N\) to quantify finite‑size effects.  
   - Include these results in the final figures and discuss any systematic shifts in the estimated \(\theta_c\).  

8. **Aggregation & Curve Fitting (FR‑007)**  
   - Compute `outlier_probability = outlier_count / total_runs`.  
   - Fit a sigmoid \(f(\theta)=\frac{1}{1+\exp[-a(\theta-\theta_c)]}\) via `scipy.optimize.curve_fit` to estimate \(\theta_c\) and its confidence interval (bootstrap 500 samples).  

## Statistical Rigor
- **Multiple Comparisons**: The sweep evaluates many \(\theta\) values; we report **bootstrap confidence intervals** for \(\theta_c\) instead of raw p‑values, thereby controlling the family‑wise error rate.  
- **Power Considerations**: With 500 repetitions per configuration, the standard error of an outlier probability is \(\sqrt{p(1-p)/500}\le0.022\), providing sufficient precision to distinguish the theoretical \(\theta_c\approx1\) from nearby values.  
- **Causal Claims**: All conclusions are **associational** (observational simulation) per FR‑007 and Constitution Principle I.  
- **Measurement Validity**: The Wigner matrix generation follows the standard Gaussian ensemble; the perturbation norm is enforced by explicit spectral scaling, guaranteeing the intended \(\theta\).  
- **Collinearity**: Rank \(k\) and sparsity density \(p\) are independent design factors; we never interpret their coefficients as independent effects in a regression model.

## Decision / Rationale (Compute)
- **CPU‑first**: All linear algebra fits comfortably on the CI runner using ARPACK; no GPU is needed (SC‑002).  
- **Scalable Sampling**: If memory pressure occurs for \(N=2000\), we fall back to streaming eigenvalue computation (process rows in chunks) — still CPU‑only.  

## Expected Deliverables
- JSON/Parquet files conforming to `contracts/*.schema.yaml`.  
- Reproducibility test (`tests/integration/test_t001.py`) confirming identical top eigenvalue across reruns within \(1\text{e-}6\).  
- Figures: (i) outlier probability vs. \(\theta\) for each pattern, (ii) \(\theta_c\) estimates across sparsity densities, (iii) finite‑size effect plots of bulk edge vs. \(N\).  

---


