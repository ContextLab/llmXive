# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
Evaluate how four uncertainty‑quantification (UQ) techniques—Gaussian‑process regression (GPR), Monte‑Carlo dropout, deep ensembles, and split‑conformal prediction—differ in **Expected Calibration Error (ECE)** and **Prediction‑Interval Sharpness** when predicting three materials properties:

1. **Band Gap** (OQMD)  
2. **Thermal Conductivity** (AFLOW)  
3. **Formation Energy** (OQMD; proxy for Elastic Modulus)

## Dataset Strategy

The plan uses three open‑access datasets verified in the project’s “# Verified datasets” block.

| Property | Dataset (Verified Source) | Loader / URL | Variable Fit |
|----------|---------------------------|--------------|--------------|
| **Band Gap** | OQMD – Band Gap | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | Contains column `band_gap` (target) and composition strings for featurization. |
| **Thermal Conductivity** | AFLOW – Thermal Conductivity | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | Contains column `thermal_conductivity` (target) and composition strings. |
| **Formation Energy** (proxy for Elastic Modulus) | OQMD – Formation Energy | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | Contains column `formation_energy_per_atom` (target) and composition strings. |

**Dataset Variable Fit Assessment**  
All three datasets provide a numeric target column and composition strings compatible with `matminer`. No open Elastic Modulus dataset exists; the substitution with Formation Energy is **explicitly documented** and treated as a proxy (see “Construct Validity” below).

### Construct Validity Note
Elastic Modulus measures mechanical stiffness, while Formation Energy reflects thermodynamic stability. They are correlated but not equivalent. Because an open, directly downloadable Elastic Modulus dataset is unavailable, Formation Energy is used as a scientifically reasonable proxy. All conclusions about UQ performance on Elastic Modulus will be **qualitative** and qualified accordingly.

## UQ Methodology

| Method | Baseline Model | Key Settings (CPU‑only) | Output |
|--------|----------------|--------------------------|--------|
| **GPR** | `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) | `alpha=1e-6`, training capped at **2000 samples** (uniform cap across all methods) | Mean ± 1.96·σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential` with dropout) | ≤ 2 M parameters, **50** stochastic passes (≤ 200 allowed), dropout = 0.2 | Empirical mean & variance |
| **Deep Ensemble** | Same MLP architecture, trained **3** times with different seeds | Ensemble size = 3, sequential training | Ensemble mean & variance |
| **Split‑Conformal** | `xgboost.XGBRegressor` | Calibration hold‑out (a designated subset of the training data), nominal coverage α swept **0.80‑0.99** (step = 0.01) | Prediction interval `[L, U]` achieving target coverage |

All models respect FR‑002 (CPU‑only, ≤ 2 GB RAM, no GPU, max ensemble = 3, MC‑Dropout passes ≤ 200).

## Metric Definitions

- **Expected Calibration Error (ECE)**: Standard binning‑based ECE. Predictions are grouped into *M* equal‑probability bins, compute `|mean(confidence) − empirical_coverage|` per bin, average. Lower is better.  
- **Sharpness**: Mean prediction‑interval width `mean(U − L)` across the test set. Lower indicates tighter intervals, assuming adequate calibration.  

Both metrics are computed per‑method, per‑dataset and saved to `results/metrics_*.csv`.

## Statistical Analysis Plan (Revised)

- **Wilcoxon Signed‑Rank Test** is applied separately to the vectors of per‑sample **ECE values** and **Sharpness values** for each pair of methods, using the *same* test set (paired design, FR‑004).  
- **α**: 0.05, **Bonferroni correction** across the 18 pairwise comparisons (6 method pairs × 3 datasets) → adjusted α ≈ 0.00278.  
- **Effect size**: Reported via rank‑biserial correlation with 95 % bootstrap confidence intervals.  
- **Sensitivity Analysis**: For split‑conformal, sweep nominal coverage α ∈ {0.80,…,0.99}; record empirical coverage and interval width; plot coverage‑error curve (SC‑004).  

## Power Analysis (Concrete Strategy)

- **Test set size**: Enforce **≥ 200** test samples per dataset (subject to the 2000‑sample cap).  
- **Bootstrap**: Perform a sufficient number of bootstrap resamples of the paired differences to obtain confidence intervals for the Wilcoxon statistic., improving robustness under the stringent Bonferroni α.  
- **Effect‑size reporting**: Alongside p‑values, report rank‑biserial correlation and its bootstrap confidence interval.  
- **Transparency**: Any residual power limitation will be explicitly reported in the final results table.

## Compute Feasibility & Constraints

- **RAM**: ≤ 2 GB via uniform training cap (2000 samples) and lightweight models.  
- **Time**: ≤ 1 h by sequential training, early stopping, and batched MC‑Dropout inference.  
- **CPU‑only**: All libraries installed with CPU‑only wheels; no CUDA.  
- **Fallbacks**: If `matminer` fails, elemental fraction vectors are generated with pure `pandas`/`pymatgen`.  

## Assumptions & Risks

- Verified URLs remain reachable; failures are logged and the pipeline proceeds with remaining datasets (partial_success).  
- **Construct Validity**: Formation Energy as a proxy may affect direct mechanical‑property interpretations; conclusions will be qualified (see Construct Validity).  
- `matminer` and `pymatgen` install without GPU dependencies on the CI runner.  

---


