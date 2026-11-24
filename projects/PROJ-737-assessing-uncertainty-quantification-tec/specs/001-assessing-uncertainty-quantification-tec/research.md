# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
We compare four uncertainty‑quantification (UQ) techniques—Gaussian Process Regression (GPR), Monte‑Carlo Dropout (MC‑Dropout), Deep Ensembles, and Split‑Conformal Prediction—on three materials‑property prediction tasks (electronic, mechanical, thermal). The goal is to quantify **Calibration Error** and **Prediction‑Interval Sharpness**, test statistical significance of differences, and explore how conformal coverage thresholds affect performance.

## Verified Datasets
| Property | Dataset (Verified Source) | Loader / URL | Target Column | Composition Field |
|----------|---------------------------|--------------|---------------|-------------------|
| Band Gap | OQMD – Band Gap | `datasets.load_dataset("oqmd/oqmd", split="train")`<br>URL: `https://huggingface.co/datasets/oqmd/oqmd` | `band_gap` | `composition` |
| Elastic Modulus | Materials Project – Elastic Modulus (fallback to local CSV if API unavailable) | *Manual download required*; if unavailable, use `data/raw/elastic_modulus.csv` | `elastic_modulus` | `composition` |
| Thermal Conductivity | AFLOW – Thermal Conductivity | `datasets.load_dataset("aflow/aflow", name="thermal_conductivity")`<br>URL: `https://huggingface.co/datasets/aflow/aflow` | `thermal_conductivity` | `composition` |

*All three datasets are openly downloadable (or have a local fallback) and cover electronic, mechanical, and thermal domains as required.*

## UQ Methodology
| Method | Baseline Model | Key CPU‑only Settings | Output |
|--------|----------------|------------------------|--------|
| **GPR** | `sklearn.gaussian_process.GaussianProcessRegressor` (RBF kernel) trained **directly on the same feature vectors** as the MLP (no wrapper over deterministic predictions) | Trained on ≤ 2000 samples; `alpha=1e-6` | Mean ± 1.96 σ |
| **MC Dropout** | Small MLP (`torch.nn.Sequential`) with dropout = 0.2 | ≤ 2 M parameters, **50** stochastic forward passes at inference | Empirical mean & variance |
| **Deep Ensemble** | Same MLP architecture, **3** independently seeded models (ensemble size = 3) | Sequential training, identical hyper‑parameters | Ensemble mean & variance |
| **Split‑Conformal** | Same deterministic MLP; calibration hold‑out set provides non‑conformity scores | Nominal coverage swept from **0.90** to **0.99** in 0.01 steps | Prediction interval `[L, U]` achieving target coverage |

All models respect **FR‑002** (CPU‑only, ≤ 2 GB RAM, ensemble ≤ 5, MC‑Dropout ≤ 50 passes). The deterministic MLP baseline is also recorded (`method_id` `deterministic_mlp`) to isolate the effect of the UQ wrapper.

## Metric Definitions
* **Calibration Error (CE)** – Expected Calibration Error (ECE). Test predictions are binned into 10 equal‑frequency bins; for each bin compute `|nominal_coverage – empirical_coverage|`, weight by bin size, and sum. Lower is better.  
* **Sharpness** – Mean prediction‑interval width `mean(U − L)` across the test set. Smaller widths denote tighter intervals, provided calibration is acceptable.  
* **Coverage** – Empirical proportion of test samples whose true value lies inside the interval. Reported for each conformal threshold during the sweep.  
* **Per‑sample absolute error** – `|prediction - ground_truth|`.  
* **Per‑sample interval width** – `upper_bound - lower_bound`.  
* **Per‑sample coverage indicator** – binary 1/0 whether `ground_truth` lies within `[L, U]`.

Per‑sample values are stored for diagnostic plots; aggregated scalar metrics are stored in `metrics_raw.csv`.

## Statistical Analysis Plan
1. **Paired Vectors** – For each dataset, construct paired vectors of per‑sample absolute errors, interval widths, and coverage indicators across the four UQ methods (same test set).  
2. **Tests** –  
   - Apply **Paired Wilcoxon signed‑rank** (or paired t‑test) for the continuous metrics (absolute error, interval width) on every unordered method pair (6 pairs).  
   - Apply **McNemar’s test** for the binary coverage indicator on the same method pairs.  
3. **Multiple‑Comparison Correction** – Bonferroni correction: α_adj = 0.05 / (6 pairs × 3 metrics) ≈ 0.00278.  
4. **Power Analysis** – With **≥ 300 test samples** per dataset and a medium effect size (Cohen’s d ≈ 0.5), the Bonferroni‑adjusted paired tests yield an estimated power of **≈ 0.80**, satisfying FR‑008.  
5. **Reporting** – p‑values and a boolean `significant` flag (based on α_adj) are saved to `statistical_report.csv`.

## Compute Feasibility & Constraints
* **RAM** – ≤ 2 GB via 2000‑sample cap and lightweight models.  
* **Time** – ≤ 1 h estimated: XGBoost/GPR ≤ 5 min each; MLP training ≤ 10 min; MC‑Dropout inference (50 passes) ≤ 5 min; conformal sweep ≤ 5 min.  
* **CPU‑only** – All libraries installed with CPU wheels; no CUDA calls.  
* **Fallbacks** – If `matminer` import fails, elemental‑fraction vectors are generated with `pymatgen` only (pure Python).  

## Assumptions & Risks
* Verified URLs remain reachable; any download failure is logged and the pipeline proceeds with remaining datasets (`partial_success`).  
* The Elastic Modulus column from Materials Project is assumed to be present in the fallback CSV; no gated data is required.  
* `matminer` and `pymatgen` install without GPU dependencies on the CI runner.  
* Fixed seeds guarantee deterministic splits and model initialisation.

--- End of Research ---