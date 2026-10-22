# Implementation Plan: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Branch**: `001-assessing-uncertainty-quantification-tec` | **Date**: 2026-10-22 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-assessing-uncertainty-quantification-tec/spec.md`

## Summary
The project will deliver a single reproducible Python pipeline (`code/pipeline.py`) that:

1. **Downloads three open materials‑property datasets** (Band Gap, Elastic Modulus, Thermal Conductivity).  
   *Band Gap* and *Thermal Conductivity* are obtained from verified HuggingFace datasets (see `research.md`).  
   *Elastic Modulus* is extracted from the **OQMD** repository (same verified URL as Band Gap) by selecting the `elastic_modulus` column, providing a true mechanical‑property dataset in the open domain.
2. **Featurises compositions** via `matminer` (fallback to elemental fractions using `pymatgen`).
3. **Splits** each dataset into stratified train/validation/test sets (test ≥ 500 samples per dataset to satisfy power requirements).
4. **Trains four uncertainty‑quantification (UQ) models** under strict CPU‑only constraints (≤ 2 GB RAM, ≤ 1 h wall‑time):
   * **Gaussian Process Regression (GPR)** – `sklearn.gaussian_process.GaussianProcessRegressor`.
   * **Monte‑Carlo Dropout (MC‑Dropout)** – small MLP with dropout = 0.2, **50** stochastic forward passes.
   * **Deep Ensembles** – **3** independently seeded small MLPs (ensemble size = 3).
   * **Split‑Conformal Prediction** – the **same small MLP** used for MC‑Dropout/Deep Ensembles, with a calibration hold‑out set; nominal coverage swept from **0.90** to **0.99** in 0.01 steps.
   All neural‑network‑based methods share the **identical MLP architecture** to avoid confounding model differences. GPR uses the same feature vectors but a distinct algorithmic model, which is acceptable given its nature.
5. **Generates prediction intervals** for every test sample.
6. **Computes Calibration Error (ECE) and Sharpness** for each method/dataset pair; writes `metrics_raw.csv`.
7. **Runs paired Wilcoxon signed‑rank tests** on per‑sample absolute errors, interval widths, and binary coverage indicators across the four UQ methods; applies Bonferroni correction (α_adj set to a suitably stringent significance level). Power analysis with **≥ 500 test samples** per dataset yields an estimated power of **≈ 0.80** for medium effect sizes, satisfying statistical‑rigor standards.
8. **Sweeps conformal nominal coverage** from **0.90** to **0.99** (step = 0.01) and records results in `sensitivity_report.csv`.
9. **Writes all required CSV artefacts** under `results/`:
   * `per_sample_errors.csv`
   * `metrics_raw.csv`
   * `statistical_report.csv`
   * `sensitivity_report.csv`
   * `uq_methods.csv`
   * `pipeline_log.csv`
10. **Logs runtime and peak RAM** for each step; aborts gracefully if limits are exceeded, preserving partial results.

All random seeds are fixed, all dependencies are pinned, and every step records its runtime and peak memory usage.

## Technical Context
| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `numpy`, `pandas`, `scikit-learn`, `xgboost`, `torch`, `matminer`, `pymatgen`, `datasets`, `psutil`, `scipy`, `statsmodels` |
| **Storage** | CSV files under `results/`; processed datasets under `data/processed/` |
| **Testing** | `pytest` with contract validation (`jsonschema`) |
| **Target Platform** | Linux GitHub Actions runner (2 CPU cores, ≤ 2 GB RAM, no GPU) |
| **Project Type** | Research‑pipeline / CLI |
| **Performance Goals** | ≤ 1 h total wall‑time, ≤ 2 GB peak RAM |
| **Constraints** | CPU‑only, ensemble ≤ 5, MC‑Dropout ≤ 50 passes, training sample cap = **2000** per dataset, test set **≥ 500** samples per dataset |

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed seeds (`np.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`); deterministic data URLs; single script `code/pipeline.py`. |
| **II. Verified Accuracy** | All external citations (datasets, libraries) are drawn from verified URLs listed in `research.md`. |
| **III. Data Hygiene** | SHA‑256 checksums recorded in `data/metadata.json`; all transformations write new files; no in‑place mutation. |
| **IV. Single Source of Truth** | Every figure, statistic, and table originates from a row in `results/` validated against the contracts. |
| **V. Versioning Discipline** | Each artefact’s content hash is recorded in the project state file; any change updates the `updated_at` timestamp. |
| **VI. Computational‑Budget Discipline** | Sample cap (2000), lightweight models, streaming where possible; explicit RAM/CPU budget checks via `psutil`. |
| **VII. Statistical‑Rigor Standard** | Paired Wilcoxon tests on per‑sample metrics with Bonferroni correction; power analysis shows ≈ 0.80 power with ≥ 500 test samples; claims are limited to observed statistical significance. |

## Mapping of Functional Requirements (FR) and Success Criteria (SC) to Pipeline Phases & Data‑Model Entities
| Phase | FR / SC | Description | Data‑Model Entity |
|-------|----------|-------------|-------------------|
| **0. Setup** | FR‑001, FR‑002, FR‑003 | Install pinned deps, set seeds, create output dirs. | – |
| **1. Data Acquisition & Verification** | FR‑001, SC‑005, Constitution III | Download OQMD Band Gap, OQMD Elastic Modulus (same repo), AFLOW Thermal Conductivity. Verify SHA‑256. | `MaterialsDataset` |
| **2. Featurisation** | FR‑003 | `matminer` → composition features; fallback to `pymatgen`. | `MaterialsDataset` (features) |
| **3. Train‑Val‑Test Split** | FR‑003 | Stratified split by property range; enforce **≥ 500 test samples** per dataset. | `MaterialsDataset` |
| **4. Baseline Model Training** | FR‑002 | Train a **small MLP** (deterministic) used as baseline for MC‑Dropout, Deep Ensembles, and Conformal; also train GPR on same features. | `UQMethod` (baseline) |
| **5. UQ Method Implementation** | FR‑007, FR‑002 | *GPR* (sklearn GP), *MC‑Dropout* (MLP + dropout), *Deep Ensembles* (3 MLPs), *Split‑Conformal* (same MLP + calibration). | `UQMethod` |
| **6. Prediction & Interval Generation** | FR‑007 | Produce point predictions and interval bounds for every test sample. | `PerSampleResult` |
| **7. Metric Computation** | FR‑005, FR‑006, SC‑002 | Compute Expected Calibration Error (ECE), Sharpness, and coverage for each method/dataset pair; store per‑sample errors. | `EvaluationMetric` |
| **8. Statistical Testing** | FR‑004, SC‑003 | Paired Wilcoxon on per‑sample **absolute errors**, **interval widths**, and **coverage indicators** across the four UQ methods; Bonferroni correction; power analysis documented. | `StatisticalTestResult` |
| **9. Sensitivity Analysis** | FR‑006, SC‑004 | Sweep nominal coverage 0.90‑0.99, record `coverage`, `avg_interval_width`, `calibration_error`. | `EvaluationMetric` |
| **10. Output Generation** | FR‑005, SC‑001‑SC‑005 | Write **six** CSV files: `per_sample_errors.csv`, `metrics_raw.csv`, `statistical_report.csv`, `sensitivity_report.csv`, `uq_methods.csv`, `pipeline_log.csv`. | All schemas in `contracts/` |
| **11. Resource Monitoring** | NFR‑001, NFR‑002 | Log runtime & RAM; abort/partial‑success if limits exceeded. | `PipelineExecution` |
| **12. Reproducibility Guarantees** | NFR‑003 | Fixed seeds, deterministic downloads, `requirements.txt` pinned. | – |

## Complexity Tracking
All required artefacts are covered, no extra constraints introduced, and every FR/SC is explicitly mapped to a pipeline phase and a data‑model entity.
