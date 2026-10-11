# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
Evaluate how Gaussian‑process regression, Monte‑Carlo dropout, deep ensembles, and split‑conformal prediction differ in calibration error and prediction‑interval sharpness when predicting three materials properties: **Band Gap**, **Thermal Conductivity**, and **Formation Energy** (used as a proxy for Elastic Modulus).

## Dataset Strategy

The plan uses three open‑access datasets verified in the project’s “# Verified datasets” block.

| Property | Target Dataset (Verified Source) | URL / Loader | Variable Fit |
|----------|----------------------------------|--------------|--------------|
| **Band Gap** | OQMD (Band Gap) | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | Contains `band_gap` target; composition features available. |
| **Thermal Conductivity** | AFLOW (Thermal Conductivity) | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | Contains `thermal_conductivity` target; composition features available. |
| **Formation Energy** (proxy for Elastic Modulus) | OQMD (Formation Energy) | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | Contains `formation_energy_per_atom`; suitable as a fundamental property proxy. |

**Dataset Variable Fit Assessment**  
- All three datasets provide a numeric target column and compositional descriptors compatible with `matminer`.  
- No verified Elastic Modulus dataset exists; the substitution with Formation Energy is **explicitly documented** and **treated as a proxy**. This limitation is noted in the results interpretation (see “Construct Validity” discussion).

### Construct Validity Note
Elastic Modulus is a mechanical property distinct from Formation Energy. Because an open, directly downloadable Elastic Modulus dataset is unavailable, Formation Energy is used as a scientifically reasonable proxy reflecting bonding strength and material stability. All conclusions about UQ performance on Elastic Modulus are therefore **qualitative** and will be qualified accordingly.

## UQ Methodology

| Method | Baseline Model | Key Settings (CPU‑only) | Output |
|--------|----------------|--------------------------|--------|
| **GPR** | Stand‑alone `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) | `alpha=1e-6`, max samples = 2000 (downsample if larger) | Mean ± 1.96·σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential` with dropout) | 50 stochastic forward passes, dropout = 0.2, ≤ 2 M params | Empirical mean & variance |
| **Deep Ensemble** | Same MLP architecture, trained 3 times with different seeds | Sequential training, ensemble size = 3 | Ensemble mean & variance |
| **Split‑Conformal** | XGBoost regressor | [deferred] calibration hold‑out, nominal coverage α varied in sensitivity sweep | Prediction interval `[L, U]` achieving target coverage |

## Metric Definitions

- **Expected Calibration Error (ECE)**: The average absolute difference between the nominal confidence level and the empirical coverage across a set of prediction intervals. Computed per‑sample as `|α - empirical_coverage|` and then averaged.
- **Sharpness**: The average width of the prediction intervals, i.e., `mean(U - L)` across all test samples. Lower values indicate more informative (tighter) intervals, assuming calibration is adequate.

## Statistical Analysis Plan (Revised)

- **Wilcoxon Signed‑Rank Test** is applied to **per‑sample absolute errors** (for Sharpness) **and to per‑sample calibration residuals** (for Calibration Error). This respects the paired nature of the data because the same test set is used for all methods.
- **α = 0.05** significance threshold.
- **Bonferroni correction** is applied across the 18 pairwise comparisons (6 method pairs × 3 datasets), yielding an adjusted α = 0.05/18.
- **Sensitivity Analysis**: Sweep nominal coverage α from 0.80 to 0.99 (step = 0.01) for the split‑conformal method; record average interval width and empirical coverage error.

## Power Analysis

With a minimum test set size of **100 samples per dataset**, the Wilcoxon signed‑rank test provides roughly **[deferred] power** to detect a medium effect size (Cohen’s d ≈ 0.5) at the corrected α level. Smaller effects may remain undetected; this limitation will be transparently reported in the results.

## Compute Feasibility & Constraints

- **RAM**: ≤ 2 GB by capping dataset size (≤ 5 k samples per property) and limiting model footprints.  
- **Time**: ≤ 1 h by training models sequentially, using small MLPs, and limiting GPR to ≤ 2000 samples.  
- **Fallbacks**: If `matminer` fails, simple composition counts (e.g., element fractions) are generated with pure `pandas`.

## Assumptions & Risks

- `matminer` installs without GPU dependencies.  
- Verified URLs remain reachable; if a URL becomes unavailable, the pipeline logs the failure and continues with remaining datasets.  
- Using Formation Energy as a proxy may affect direct comparability to Elastic Modulus; results will be interpreted with this caveat.

---

