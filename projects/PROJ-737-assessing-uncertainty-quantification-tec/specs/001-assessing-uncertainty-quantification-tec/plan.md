# Implementation Plan: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Branch**: `001-assessing-uncertainty-quantification-tec` | **Date**: 2026-10-26 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-assessing-uncertainty-quantification-tec/spec.md`

## Summary
Deliver a single reproducible CPU‑only Python pipeline (`code/pipeline.py`) that:

1. **Downloads** three open‑source materials property datasets (Band Gap from OQMD, Elastic Modulus from Materials Project, Thermal Conductivity from AFLOW) and records SHA‑256 checksums.  
2. **Featurises** compositions with `matminer`; falls back to elemental‑fraction vectors via `pymatgen` if needed.  
3. **Stratifies** each dataset into train/val/test splits, ensuring **≥ 300 test samples** per dataset (to satisfy FR‑008).  
4. **Trains** a **small MLP** (≤ 2 M parameters) that serves as the backbone for MC‑Dropout, Deep Ensembles, and Split‑Conformal, and **trains a GaussianProcessRegressor directly on the same feature vectors** (no MLP wrapper).  
5. **Generates** prediction intervals for each test sample using the four UQ methods (GPR, MC‑Dropout, Deep Ensembles, Split‑Conformal).  
6. **Computes** Calibration Error (ECE) and Sharpness for every method/dataset pair, writing `metrics_raw.csv`.  
7. **Runs** paired statistical tests:  
   - **Wilcoxon signed‑rank** (or paired t‑test) on continuous per‑sample vectors (absolute error, interval width).  
   - **McNemar’s test** on the binary coverage indicator.  
   - Bonferroni correction applied across all pairwise comparisons.  
   Results are saved to `statistical_report.csv`.  
8. **Sweeps** conformal nominal coverage from **0.90** to **0.99** (step = 0.01), recording coverage, average interval width, and calibration error for each threshold; results go to `sensitivity_report.csv`.  
9. **Writes** the required CSV artefacts under `results/`:  
   - `per_sample_errors.csv`  
   - `metrics_raw.csv`  
   - `statistical_report.csv`  
   - `sensitivity_report.csv`  
   - `uq_methods.csv`  
   - `pipeline_log.csv`  
10. **Logs** each step with timestamps, CPU seconds, and peak RAM; aborts gracefully if RAM exceeds 2 GB, preserving partial results (NFR‑002).

All random seeds are fixed; dependencies are pinned; every step records runtime and memory usage.

## Technical Context
| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `numpy`, `pandas`, `scikit-learn`, `torch`, `xgboost`, `matminer`, `pymatgen`, `datasets`, `psutil`, `scipy`, `statsmodels` |
| **Storage** | CSV files under `results/`; processed datasets under `data/processed/` |
| **Testing** | `pytest` with contract validation (`jsonschema`) |
| **Target Platform** | Linux GitHub Actions runner (2 CPU cores, ≤ 2 GB RAM, no GPU) |
| **Project Type** | Research pipeline / CLI |
| **Performance Goals** | ≤ 1 h total wall‑time, ≤ 2 GB peak RAM |
| **Constraints** | CPU‑only, ensemble ≤ 5, MC‑Dropout ≤ 50 passes, **training cap = 2000 samples** per dataset (FR‑003) |
| **Scale/Scope** | Three property datasets, four UQ methods, **≥ 300 test samples** per dataset for significance testing (FR‑008) |

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed seeds (`np.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`); deterministic URLs; single script `code/pipeline.py`. |
| **II. Verified Accuracy** | All external citations (datasets, libraries) come from the verified URLs listed in `research.md`. |
| **III. Data Hygiene** | SHA‑256 checksums recorded in `data/metadata.json`; transformations write new files; no in‑place mutation. |
| **IV. Single Source of Truth** | Every figure/table derives from rows in the CSV artefacts validated against contracts. |
| **V. Versioning Discipline** | Content hashes of artefacts are recorded in the project state file; any change updates `updated_at`. |
| **VI. Computational‑Budget Discipline** | Sample cap (2000), lightweight models, streaming where possible; RAM/CPU checks via `psutil`. |
| **VII. Statistical‑Rigor Standard** | Paired Wilcoxon for continuous metrics, McNemar for binary coverage, Bonferroni correction; power analysis (≥ 300 test samples → ≈ 0.80 power for medium effect size) satisfied. |

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Pipeline Phases & Data‑Model Entities
| Phase | FR / SC | Description | Data‑Model Entity |
|-------|----------|-------------|-------------------|
| **0. Setup** | FR‑001, FR‑002, FR‑003, NFR‑001, NFR‑002 | Install pinned deps, set seeds, create `results/` dir. | – |
| **1. Data Acquisition** | FR‑001, SC‑005, Constitution III | Download OQMD Band Gap, Materials Project Elastic Modulus (fallback CSV if needed), AFLOW Thermal Conductivity; verify SHA‑256. | `MaterialsDataset` |
| **2. Featurisation** | FR‑003 | `matminer` → composition features; fallback to elemental‑fraction vectors via `pymatgen`. | `MaterialsDataset` (features) |
| **3. Split** | FR‑003, FR‑008 | Stratified train/val/test; enforce **≥ 300 test samples** per dataset. | `MaterialsDataset` |
| **4. Baseline MLP Training** | FR‑002 | Train small MLP (deterministic) – reused for MC‑Dropout, Deep Ensembles, Conformal. | `UQMethod` (`deterministic_mlp`) |
| **5. UQ Methods** | FR‑007, FR‑002 | *GPR* – train `GaussianProcessRegressor` directly on features. *MC‑Dropout* – 50 stochastic passes. *Deep Ensembles* – 3 independently trained copies (≤ 5). *Split‑Conformal* – held‑out calibration set, coverage sweep. | `UQMethod` (four methods) |
| **6. Prediction & Intervals** | FR‑007 | Produce point predictions + intervals for every test sample. | `PerSampleResult` |
| **7. Metric Computation** | FR‑005, FR‑006, SC‑002 | Compute Calibration Error, Sharpness, Coverage; store per‑method rows. | `EvaluationMetric` |
| **8. Statistical Testing** | FR‑004, SC‑003 | Paired Wilcoxon on continuous metrics; McNemar on binary coverage; Bonferroni correction; store results. | `StatisticalTestResult` |
| **9. Sensitivity Sweep** | FR‑006, SC‑004 | Sweep nominal coverage 0.90‑0.99; record coverage, avg‑width, calibration error. | `EvaluationMetric` |
| **10. Output Generation** | FR‑005, SC‑001‑SC‑006 | Write six required CSVs (`per_sample_errors.csv`, `metrics_raw.csv`, `statistical_report.csv`, `sensitivity_report.csv`, `uq_methods.csv`, `pipeline_log.csv`). | All contract schemas |
| **11. Resource Monitoring** | NFR‑001, NFR‑02 | Log step‑wise CPU seconds, RAM; abort if limits exceeded, preserving partial results. | `PipelineExecution` |
| **12. Reproducibility Guarantees** | NFR‑003 | Fixed seeds, deterministic downloads, pinned `requirements.txt`. | – |

## Complexity Tracking
All FR/SC are covered; no extra constraints introduced. The plan now respects the correct statistical methods, dataset sources, and sample‑size requirements while removing the unsupported CostMetric entity.

--- End of Plan ---