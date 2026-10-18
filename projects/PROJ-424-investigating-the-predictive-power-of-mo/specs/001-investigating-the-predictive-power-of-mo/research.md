# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Summary
The study quantifies how atomistic MD simulations (OPLS‑AA) predict experimental self‑diffusion coefficients for water, ethanol, and acetone.  By varying simulation duration (1 ns, 5 ns, 10 ns) and assessing convergence, we generate timescale‑accuracy curves (MAE vs. duration) with 95 % confidence bands, evaluate sensitivity to the MSD start‑time window, and report descriptive trend analysis with CI‑overlap checks.

## Dataset Strategy

| Dataset | Source / Path | Access Method | Validation |
|---|---|---|---|
| **Experimental benchmarks** | `data/raw/nist_refs.json` (local) | `json.load()` via `code/data/loader.py` | Manual curation from NIST; checksum recorded (Constitution III). |
| **Simulation trajectories** | `data/raw/simulations/{solvent}_{duration_ns}_seed{seed}.xtc` (generated) | `mdtraj.load()` or `openmm` trajectory objects | Energy and pressure stability checks; MSD linearity `$R^{2} \ge 0.95$` (Constitution VI). |

*No external URLs are required; all data are locally stored and versioned.*

## Methodological Approach

### 1. Simulation Protocol (Atomistic OPLS‑AA)
* **Force field**: OPLS‑AA (parameter files provided by OpenMM).  
* **System size**: ~150 molecules (≈3 k atoms) – sufficient for bulk diffusion while keeping runtime ≤ 12 h per trajectory.  
* **Ensemble**: NPT (T = 300 K, P = 1 bar) using Langevin dynamics.  
* **Durations**: 1 ns, 5 ns, 10 ns.  
* **Seeds**: 5 independent random seeds per condition (target). If cumulative wall‑clock exceeds 5.5 h, the pipeline automatically reduces to 3 seeds (fallback).  
* **Convergence check**: After discarding the first 10 % of simulation time, a linear regression on MSD vs. time is performed; only trajectories with `$R^{2} \ge 0.95$` are retained for diffusion coefficient calculation (FR‑003, Constitution VI).

### 2. Diffusion Coefficient Extraction
* **MSD calculation**: `code/analysis/msd_calculator.py` computes MSD for each trajectory.  
* **Linear fit**: Slope obtained via `scikit‑learn` `LinearRegression`; diffusion coefficient $D = \text{slope} / 6$.  
* **Scaling (optional CG)**: If a coarse‑grained force field is ever used, a literature‑based scaling factor (e.g., water 0.6, ethanol 0.7, acetone 0.7) is applied (FR‑007). In the primary atomistic workflow no scaling is performed.

### 3. Accuracy & Uncertainty Quantification
* **Metric**: Mean Absolute Error (MAE) = $\lvert D_{\text{sim}} - D_{\text{exp}} \rvert$.  
* **Bootstrap**: 1000 resampling iterations of the MAE distribution per duration (FR‑004). The 2.5 th and 97.5 th percentiles form the 95 % CI (SC‑003). If runtime > 5.5 h, the script falls back to 100 iterations and records this in `bootstrap_stats.json`.  
* **No hypothesis testing**: Sample size (N = 5 or 3) is insufficient for parametric tests; only descriptive statistics and CI‑overlap are reported (SC‑005).

### 4. Sensitivity Analysis
* **Variable**: Start‑time fraction for MSD fitting (0.1, 0.2, 0.3 of total trajectory).  
* **Procedure**: Re‑compute $D$ for each fraction, calculate coefficient of variation (CV = std/mean).  
* **Success threshold**: CV < 5 % for each solvent (SC‑002). Results stored in `sensitivity_report.json`.

### 5. Timescale‑Accuracy Curves & Trend Analysis
* **Plots**: MAE vs. simulation duration for each solvent, with 95 % confidence bands (FR‑008, SC‑001).  
* **CI‑overlap check**: Compare the 95 % CI of MAE at 1 ns with that at 10 ns; report descriptive overlap (SC‑005).  
* **Summary tables**: Mean MAE, CI bounds, and a short narrative of the trend (SC‑004).

## Scaling Factors (Optional CG Path)
* **Water**: 0.6  
* **Ethanol**: 0.7  
* **Acetone**: 0.7  
* **Reference**: Marrink et al., *J. Chem. Theory Comput.* 2007, 3, 1, 146‑156.  
These are only applied if a coarse‑grained force field is selected (FR‑007); the primary OPLS‑AA workflow does not use them.

## Decision Rationale

| Decision | Reasoning |
|---|---|
| **CPU‑first, OpenMM** | Atomistic OPLS‑AA systems of ~150 molecules run comfortably on 2‑core CPUs; no GPU required, satisfying the compute budget and the “No GPU required” constraint. |
| **Bootstrap over parametric tests** | With N ≤ 5 per condition, t‑tests would be under‑powered; bootstrap provides robust CI estimates without extra assumptions. |
| **Discard first [deferred] of trajectory** | Empirically removes the ballistic regime; aligns with typical practice and satisfies FR‑003 (deferred value now concretized). |
| **System‑size scaling for long runs** | Guarantees that any single trajectory stays under the 12 h wall‑clock limit (FR‑006). |
| **Fallback seed count** | Guarantees the entire pipeline finishes within the 6 h CI limit while still providing variance estimates (FR‑004). |

All methodological choices are fully reproducible, deterministic (seeded), and documented in the codebase.

---
