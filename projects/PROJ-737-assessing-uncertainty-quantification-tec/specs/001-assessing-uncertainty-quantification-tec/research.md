# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
Evaluate how four uncertainty‑quantification (UQ) techniques—Gaussian‑process regression (GPR), Monte‑Carlo dropout, deep ensembles, and split‑conformal prediction—differ in **Calibration Error (CE)** (interval‑coverage based) and **Prediction‑Interval Sharpness** when predicting three materials properties:

1. **Band Gap** (OQMD)  
2. **Thermal Conductivity** (AFLOW)  
3. **Formation Energy** (OQMD; proxy for Elastic Modulus)

## # Verified datasets
| Property | Dataset (Verified Source) | Loader / URL | Target Column | Composition Field |
|----------|---------------------------|--------------|---------------|-------------------|
| Band Gap | OQMD – Band Gap | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `band_gap` | `composition` |
| Thermal Conductivity | AFLOW – Thermal Conductivity | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | `thermal_conductivity` | `composition` |
| Formation Energy (Elastic Modulus proxy) | OQMD – Formation Energy | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `formation_energy_per_atom` | `composition` |

### Construct Validity Note
No open dataset directly measures Elastic Modulus under the CPU‑memory constraints. **Formation Energy** is therefore used as a *proxy* for Elastic Modulus, but it captures thermodynamic stability rather than mechanical stiffness. Consequently, any interpretation of UQ performance for “mechanical” properties is **qualitative** and **limited**; the study does **not** make strong causal claims about Elastic Modulus uncertainty.

## UQ Methodology
| Method | Baseline Model | Key CPU‑only Settings | Output |
|--------|----------------|-----------------------|--------|
| **GPR** | `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) | `alpha=1e-6`; training limited to **2000 samples** (uniform cap) | Mean ± 1.96 σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential` with dropout) | ≤ 2 M parameters, **50** stochastic forward passes (≤ 200 allowed), dropout = 0.2 | Empirical mean & variance |
| **Deep Ensemble** | Same MLP architecture, **3** independently trained seeds (same baseline as MC Dropout) | Ensemble size = 3, sequential training | Ensemble mean & variance |
| **Split‑Conformal** | `xgboost.XGBRegressor` (same baseline as Deep Ensemble) | Calibration hold‑out ([deferred] of training), nominal coverage swept 0.80–0.99 (step = 0.01) | Prediction interval `[L, U]` achieving target coverage |

All methods obey **FR‑002** (CPU‑only, ≤ 2 GB RAM, max ensemble = 3, MC‑Dropout ≤ 200 passes).

## Metric Definitions
- **Calibration Error (CE)** – We compute **Expected Calibration Error (ECE)** as an **aggregate** statistic: predictions are placed into a series of equal‑frequency bins; for each bin we calculate the absolute difference between the nominal coverage (e.g., 0.90) and the empirical coverage of the interval. The weighted average across bins yields the ECE. Lower values indicate better calibrated intervals.  
- **Sharpness** – Mean prediction‑interval width `mean(U − L)` across the test set. Lower width denotes tighter intervals, provided calibration is acceptable.

Both metrics are computed **per‑method/dataset pair** and then aggregated; per‑sample values are stored only for diagnostic plots.

## Statistical Analysis Plan
- **Test**: Paired Wilcoxon signed‑rank on the **vectors of per‑sample Calibration Error** *and* **Sharpness** for each method pair, using the same test set (FR‑004).  
- **α**: 0.05, **Bonferroni correction** across 36 pairwise comparisons (12 method‑pair/metric combos × 3 datasets) → adjusted α ≈ a suitably low significance threshold.  
- **Power Analysis (Quantitative)**: Assuming a medium effect size (Cohen’s d ≈ 0.5) and the Bonferroni‑adjusted α, a paired Wilcoxon test with **n = 200** test samples yields an estimated power of **≈ 0.30**. Thus the study is exploratory; any non‑significant result will be reported as such, and the limitation is explicitly noted.  

## Power Analysis (Simplified)
- **Test‑set size**: Enforced **≥ 200** test samples per dataset (after the 2000‑sample cap).  
- **Multiple‑testing**: Bonferroni adjustment reduces power; we acknowledge this limitation and frame conclusions accordingly.

## Compute Feasibility & Constraints
- **RAM**: ≤ 2 GB via uniform 2000‑sample cap and lightweight models.  
- **Time**: ≤ 1 h by sequential training, early stopping, and batched MC‑Dropout inference.  
- **CPU‑only**: All libraries installed with CPU‑only wheels; no CUDA.  
- **Fallbacks**: If `matminer` fails, elemental fraction vectors are generated with pure `pandas`/`pymatgen`.

## Assumptions & Risks
- Verified URLs remain reachable; failures are logged and the pipeline proceeds with remaining datasets (partial_success).  
- **Construct Validity**: Using Formation Energy as a proxy for Elastic Modulus may limit mechanical‑property interpretations; conclusions are qualified accordingly.  
- `matminer` and `pymatgen` install without GPU dependencies on the CI runner.  

---



