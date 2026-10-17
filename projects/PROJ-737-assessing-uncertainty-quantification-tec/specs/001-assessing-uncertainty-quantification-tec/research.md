# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
Evaluate how four uncertainty‑quantification (UQ) techniques—Gaussian‑process regression (GPR), Monte‑Carlo dropout, deep ensembles, and split‑conformal prediction—differ in **Expected Calibration Error (ECE)** and **Prediction‑Interval Sharpness** when predicting three materials properties:

1. **Band Gap** (OQMD)  
2. **Thermal Conductivity** (AFLOW)  
3. **Formation Energy** (OQMD; proxy for Elastic Modulus)

## Dataset Strategy
All three datasets are openly available via the HuggingFace `datasets` hub; they are programmatically downloadable without authentication.

| Property | Dataset (Verified Source) | Loader / URL | Target Column | Composition Field |
|----------|---------------------------|--------------|---------------|-------------------|
| Band Gap | OQMD – Band Gap | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `band_gap` | `composition` |
| Thermal Conductivity | AFLOW – Thermal Conductivity | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | `thermal_conductivity` | `composition` |
| Formation Energy (Elastic Modulus proxy) | OQMD – Formation Energy | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `formation_energy_per_atom` | `composition` |

**Variable Fit Assessment** – Each dataset supplies a numeric target and a composition string compatible with `matminer` featurizers. No open Elastic Modulus dataset exists; the substitution is explicitly documented (see “Construct Validity” below).

### Construct Validity Note
Elastic Modulus measures mechanical stiffness, whereas Formation Energy reflects thermodynamic stability. They are correlated but not interchangeable. Because an open Elastic Modulus dataset is unavailable, Formation Energy is used as a scientifically reasonable proxy, and all conclusions regarding mechanical stiffness are qualified as qualitative.

## UQ Methodology
| Method | Baseline Model | Key CPU‑only Settings | Output |
|--------|----------------|-----------------------|--------|
| **GPR** | `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) | `alpha=1e-6`; training limited to **2000 samples** (uniform cap) | Mean ± 1.96 σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential` with dropout) | ≤ 2 M parameters, **50** stochastic forward passes (≤ 200 allowed), dropout = 0.2 | Empirical mean & variance |
| **Deep Ensemble** | Same MLP architecture, **3** independently trained seeds | Ensemble size = 3, sequential training | Ensemble mean & variance |
| **Split‑Conformal** | `xgboost.XGBRegressor` | Calibration hold‑out (20 % of training), nominal coverage swept 0.80–0.99 (step = 0.01) | Prediction interval `[L, U]` achieving target coverage |

All methods adhere to **FR‑002** (CPU‑only, ≤ 2 GB RAM, max ensemble = 3, MC‑Dropout ≤ 200 passes).

## Metric Definitions
- **Expected Calibration Error (ECE)** – Standard binning approach: predictions are sorted into *M* equal‑probability bins; for each bin compute `|mean(confidence) − empirical_coverage|`; average across bins. Lower values indicate better calibrated intervals.  
- **Sharpness** – Mean prediction‑interval width `mean(U − L)` across the test set. Lower width denotes tighter intervals, provided calibration is acceptable.

Both metrics are computed **per‑sample** and aggregated per method/dataset; results are stored in `results/metrics_*.csv`.

## Statistical Analysis Plan (Revised)
- **Test**: Paired Wilcoxon signed‑rank on the **vectors of per‑sample ECE** and **Sharpness** for each method pair, using the same test set (FR‑004).  
- **α**: 0.05, **Bonferroni correction** across 18 pairwise comparisons (6 method pairs × 3 datasets) → adjusted α ≈ 0.00278.  
- **Effect size**: Rank‑biserial correlation with 95 % bootstrap confidence intervals (1000 resamples).  
- **Sensitivity Analysis**: For split‑conformal, sweep nominal coverage α ∈ {0.80,…,0.99}; record empirical coverage and interval width; plot coverage‑error curve (SC‑004).

## Power Analysis (Concrete Strategy)
- **Test‑set size**: Enforced **≥ 200** test samples per dataset (subject to the 2000‑sample cap).  
- **Bootstrap**: 1000 bootstrap resamples of paired differences to obtain confidence intervals for the Wilcoxon statistic, improving robustness under the stringent Bonferroni α.  
- **Effect‑size reporting**: Alongside p‑values, report rank‑biserial correlation and its bootstrap CI.  
- **Transparency**: Any residual power limitation will be explicitly reported in the final results table.

## Compute Feasibility & Constraints
- **RAM**: ≤ 2 GB via uniform 2000‑sample cap and lightweight models.  
- **Time**: ≤ 1 h by sequential training, early stopping, and batched MC‑Dropout inference.  
- **CPU‑only**: All libraries installed with CPU‑only wheels; no CUDA.  
- **Fallbacks**: If `matminer` fails, elemental fraction vectors are generated with pure `pandas`/`pymatgen`.

## Assumptions & Risks
- Verified URLs remain reachable; failures are logged and the pipeline proceeds with remaining datasets (partial_success).  
- **Construct Validity**: Using Formation Energy as a proxy may limit mechanical‑property interpretations; conclusions are qualified accordingly.  
- `matminer` and `pymatgen` install without GPU dependencies on the CI runner.  

---
