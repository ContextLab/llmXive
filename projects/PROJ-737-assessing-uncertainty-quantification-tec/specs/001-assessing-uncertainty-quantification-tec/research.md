# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
We compare four uncertainty‑quantification (UQ) techniques—Gaussian Process Regression (GPR), Monte‑Carlo Dropout (MC‑Dropout), Deep Ensembles, and Split‑Conformal Prediction—on three materials‑property prediction tasks. The goal is to quantify **Calibration Error** and **Prediction‑Interval Sharpness**, test whether differences are statistically significant, and explore how conformal coverage thresholds affect performance.

## Verified Datasets
| Property | Dataset (Verified Source) | Loader / URL | Target Column | Composition Field |
|----------|---------------------------|--------------|---------------|-------------------|
| Band Gap | OQMD – Band Gap | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `band_gap` | `composition` |
| Thermal Conductivity | AFLOW – Thermal Conductivity | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | `thermal_conductivity` | `composition` |
| Elastic Modulus | OQMD – Elastic Modulus (same OQMD repo, different column) | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `elastic_modulus` | `composition` |

**Construct Validity Note**  
All three properties now come from open, programmatically downloadable sources. Elastic Modulus is obtained from the OQMD dataset’s `elastic_modulus` column, preserving the mechanical‑property arm of the study without relying on gated Materials Project data.

## UQ Methodology
| Method | Baseline Model | Key CPU‑only Settings | Output |
|--------|----------------|------------------------|--------|
| **GPR** | `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) – trained on the same feature vectors as the other methods | Training limited to 2000 samples; `alpha=1e-6` | Mean ± 1.96 σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential`) with dropout = 0.2 | ≤ 2 M parameters, **50** stochastic forward passes, dropout active at inference | Empirical mean & variance |
| **Deep Ensemble** | Same small MLP architecture, **3** independently seeded models (ensemble size = 3) | Sequential training, same hyper‑parameters as MC‑Dropout | Ensemble mean & variance |
| **Split‑Conformal** | Same small MLP (deterministic) used as the predictive model; calibration hold‑out set provides non‑conformity scores | Nominal coverage swept from **0.90** to **0.99** in 0.01 steps | Prediction interval `[L, U]` achieving target coverage |

All models respect **FR‑002** (CPU‑only, ≤ 2 GB RAM, ensemble ≤ 5, MC‑Dropout ≤ 50 passes). A deterministic MLP baseline is also recorded (status `success`) to isolate the effect of the UQ technique from the underlying predictor.

## Metric Definitions
* **Calibration Error (CE)** – Expected Calibration Error (ECE). Test predictions are binned into 10 equal‑frequency bins; for each bin we compute `|nominal_coverage – empirical_coverage|` and weight by bin size. The weighted sum yields the ECE. Lower values indicate better calibrated intervals.
* **Sharpness** – Mean prediction‑interval width `mean(U − L)` across the test set. Smaller widths denote tighter (sharper) intervals, provided calibration is acceptable.
* **Coverage** – Empirical proportion of test samples whose true value falls inside the prediction interval; reported for each conformal threshold during the sensitivity sweep.
* **Per‑sample absolute error** – `|prediction - ground_truth|`.
* **Per‑sample interval width** – `upper_bound - lower_bound`.
* **Per‑sample coverage indicator** – binary 1/0 whether `ground_truth` lies within `[L, U]`.

Per‑sample values are stored for diagnostic plots; aggregated scalar metrics are stored in `metrics_raw.csv`.

## Statistical Analysis Plan
1. **Paired Vectors** – For each dataset, construct paired vectors of per‑sample absolute errors, interval widths, and coverage indicators across the four UQ methods (same test set).
2. **Test** – Apply **Paired Wilcoxon signed‑rank** for every unordered method pair (6 pairs) on each of the three per‑sample metrics (absolute error, interval width, coverage) → 54 tests per dataset, 162 total.
3. **Multiple‑Comparison Correction** – Bonferroni correction: α_adj = 0.05 / 162 ≈ 0.00031.
4. **Power Analysis** – With **≥ 500 test samples** per dataset and a medium effect size (Cohen’s d ≈ 0.5), the Bonferroni‑adjusted paired Wilcoxon test yields an estimated power of **≈ 0.80**, which is acceptable for detecting meaningful differences.
5. **Reporting** – p‑values and a boolean `significant` flag (based on α_adj) are saved to `statistical_report.csv`.

## Compute Feasibility & Constraints
* **RAM** – ≤ 2 GB via 2000‑sample cap and lightweight models.
* **Time** – ≤ 1 h estimated: XGBoost & GPR training ≤ 5 min each; MLP training ≤ 10 min; MC‑Dropout inference (50 passes) ≤ 5 min; conformal sweep (10 thresholds) ≤ 5 min.
* **CPU‑only** – All libraries installed with CPU wheels; no CUDA calls.
* **Fallbacks** – If `matminer` import fails, elemental‑fraction vectors are generated with `pymatgen` only (pure Python).

## Assumptions & Risks
* Verified URLs remain reachable; any download failure is logged and the pipeline proceeds with the remaining datasets (`partial_success`).
* The **Elastic Modulus** open dataset is now sourced from OQMD, satisfying the mechanical‑property requirement without gated data.
* `matminer` and `pymatgen` install without GPU dependencies on the CI runner.
* Fixed seeds guarantee deterministic splits and model initialisation.

--- End of Research ---
