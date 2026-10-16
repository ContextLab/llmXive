# Implementation Plan: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

**Branch**: `001-quantify-spatial-correlations` | **Date**: 2024-10-16 | **Spec**: [link]  
**Input**: Feature specification from `specs/001-quantify-spatial-correl/spec.md`

## Summary
The project builds a fully reproducible, CPU‑only pipeline that (1) checks the availability of public EDS elemental maps, (2) proceeds with a **performance‑only** analysis when maps are missing, (3) extracts spatial metrics when maps exist, (4) relates any available spatial metrics and performance metrics using transparent statistical methods, and (5) generates machine‑readable reports. All steps are deterministic, schema‑validated, and respect the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-image`, `statsmodels`, `pygam`, `matplotlib`, `requests`, `pyyaml`, `datasets` (HuggingFace)  
- **Storage**: Local file system under `data/` (raw, processed) and `results/` (CSV, PDF, JSON)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux (GitHub Actions free‑tier) – 2 vCPU, ~7 GB RAM, ≤6 h per job  
- **Constraints**: CPU‑only; all random seeds pinned in `code/utils/seed.py`; total disk usage ≤ 7 GB  

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| **I. Reproducibility** | ✅ | `requirements.txt` pins exact versions; seeds fixed in `code/utils/seed.py`; all scripts deterministic. |
| **II. Verified Accuracy** | ✅ | All external URLs are taken from the verified list; no invented citations. |
| **III. Data Hygiene** | ✅ | Raw files stored unchanged; each transformation writes a new file with a checksum recorded in `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml`. |
| **IV. Single Source of Truth** | ✅ | **SSoT**: `data/processed/unified_dataset.csv` is the authoritative data artifact for all downstream analyses. |
| **V. Versioning Discipline** | ✅ | Artifacts hashed; `state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml` updated automatically. |
| **VI. Spatial Characterization Consistency** | ✅ | If EDS maps are present, raw files reside under `data/raw/`; preprocessing logs all parameters. |
| **VII. Statistical Modeling Transparency** | ✅ | Modeling scripts log method, coefficients, confidence intervals, and CV strategy; results reference exact CSV outputs. |

## Project Structure
```text
specs/001-quantify-spatial-correl/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── results.schema.yaml
└── tasks.md               # generated later by /speckit-tasks
```

```text
projects/PROJ-204-quantifying-the-impact-of-spatial-correl/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── seed.py                 # pins numpy, random, torch seeds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download_feasibility.py # FR‑001 feasibility check
│   │   ├── download.py             # downloads performance data; attempts EDS map download
│   │   └── align.py                # grid resampling & defect masking (if maps exist)
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── co_location.py          # FR‑007
│   │   └── depth_check.py          # FR‑008
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── spatial_metrics.py      # FR‑002, FR‑003 (runs only when maps exist)
│   │   └── robustness.py           # FR‑005 (LOO‑CV)
│   ├── modeling/
│   │   ├── __init__.py
│   │   ├── correlation.py          # Pearson/Spearman + BH correction (FR‑004)
│   │   └── gam.py                  # GAM fitting (FR‑004)
│   ├── report/
│   │   ├── __init__.py
│   │   ├── generate_report.py      # FR‑006 (CSV + PDF)
│   │   └── data_availability.py    # deterministic availability report
│   └── main_pipeline.py            # orchestrates ordered steps
├── data/
│   ├── raw/                         # unmodified downloads (JSON/CSV performance, any EDS maps)
│   └── processed/
│       ├── unified_dataset.csv
│       ├── co_location_status.csv
│       ├── depth_status.csv
│       └── spatial_metrics.csv     # may be empty if no maps
├── results/
│   ├── feasibility_report.json
│   ├── summary_report.csv
│   └── summary_report.pdf
├── tests/
│   ├── unit/
│   │   └── test_spatial_metrics.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Feasibility‑first design** | Guarantees a deterministic artifact (`feasibility_report.json`) before optional spatial analysis, satisfying FR‑001‑FR‑008 even when maps are missing. | Skipping feasibility would lead to fabricated EDS data, which the verifier rejects. |
| **Performance‑only analysis branch** | Allows the core research question (relationships among PCE, J_sc, V_oc) to be answered regardless of EDS availability. | Forcing spatial analysis would abort the pipeline in the common case of missing maps. |
| **CPU‑only metric extraction** | Uses `scipy.signal` and `scikit‑image` which run efficiently on the free runner. | Switching to GPU‑only deep‑learning would be impossible on CI. |

## Computational Task Ordering
| Order | Script | Output (validated by schema) |
|-------|--------|------------------------------|
| 1 | `code/data/download_feasibility.py` | `results/feasibility_report.json` |
| 2 | *Conditional*: if **any** EDS maps are found → continue to steps 3‑8; otherwise → skip step 6 (spatial metric extraction) but **still execute steps 7‑9** (modeling, robustness, reporting) using performance‑only data. |
| 3 | `code/data/download.py` | `data/processed/unified_dataset.csv` (conforms to `contracts/dataset.schema.yaml`) |
| 4 | `code/validation/co_location.py` | `data/processed/co_location_status.csv` |
| 5 | `code/validation/depth_check.py` | `data/processed/depth_status.csv` |
| 6 | `code/analysis/spatial_metrics.py` | `data/processed/spatial_metrics.csv` (may be empty) |
| 7 | `code/modeling/correlation.py` + `code/modeling/gam.py` | `results/summary_report.csv` (conforms to `contracts/results.schema.yaml`) |
| 8 | `code/analysis/robustness.py` | Updates `results/summary_report.csv` with `robustness_delta_r_max` |
| 9 | `code/report/generate_report.py` | `results/summary_report.pdf` |

**Note:** Modeling (step 7) is **always executed**; it operates on whatever predictor set is present (spatial metrics if available, otherwise performance‑only variables). Hypothesis testing within step 7 is performed only when the sample count for the specific analysis meets the power threshold (≥ 30 samples). When fewer samples are present, the pipeline reports effect‑size estimates with confidence intervals and explicitly notes the limited power.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified EDS maps** | Spatial analysis impossible | Feasibility step creates a deterministic *Data‑Availability Report*; pipeline continues with performance‑only analysis. |
| **Insufficient samples for spatial sub‑analysis (<30)** | Low statistical power | Report effect‑size estimates with confidence intervals; do not perform hypothesis testing. |
| **Undefined correlation length** | Missing predictor | Flag `is_undefined`; exclude from regression but keep in descriptive tables. |
| **Surface‑vs‑bulk mismatch** | Potential confounding | Flag via FR‑008; sensitivity analysis reports both inclusive and exclusive results. |
| **Runtime >6 h** | CI failure | Algorithms are O(N·pixel²) with N ≤ 200 and pixel ≤ 512²; empirical runtime < 2 h. |

## Mapping of Functional Requirements & Success Criteria
| FR | Plan Phase | How Verified |
|----|------------|--------------|
| FR‑001 | 1, 3 | `download_feasibility.py` logs success rate; `download.py` writes unified CSV. |
| FR‑002 | 6 (when maps exist) | `spatial_metrics.py` fits exponential, Gaussian, power‑law; selects via AIC; outputs `best_fit_model` and `aic_score`. |
| FR‑003 | 6 (when maps exist) | Same module computes low‑frequency spectral power. |
| FR‑004 | 7 & 8 | `correlation.py` computes Pearson/Spearman + BH correction; `gam.py` fits GAM. |
| FR‑005 | 8 | `robustness.py` runs LOO‑CV, records `robustness_delta_r_max`. |
| FR‑006 | 9 | `generate_report.py` creates CSV + PDF with all required fields. |
| FR‑007 | 4 | `co_location.py` validates ID matches; mismatches excluded. |
| FR‑008 | 5 | `depth_check.py` flags surface‑bias; sensitivity analysis optional in step 8. |
| SC‑001 | 6 (unit test) | `tests/unit/test_spatial_metrics.py` validates extraction on synthetic images (≤5 % error). |
| SC‑002 | 7 (integration test) | `tests/integration/test_pipeline.py` compares p‑values against SciPy reference (±0.001). |
| SC‑003 | 8 (unit test) | `tests/unit/test_robustness.py` checks Δr calculation. |
| SC‑004 | 1 (feasibility test) | `feasibility_report.json` contains `overall_success_rate`; test asserts it meets deferred threshold. |

---



## Power Analysis (Revised)
- **Target Sample Size**: ≥ 30 samples for adequately powered hypothesis tests (α = 0.05, power = 0.80 → detectable r ≈ 0.35).  
- **Performance‑only analysis**: > 200 samples are available, satisfying the power requirement.  
- **Spatial sub‑analysis**: If fewer than 30 samples with EDS maps are found, the pipeline **does not perform hypothesis testing**; instead it reports effect‑size estimates with 95 % confidence intervals and explicitly notes the low power.  

---



## Compute Feasibility
- All computations use CPU‑only libraries (`numpy`, `scipy`, `scikit‑image`).  
- Even with the maximum allowed dataset size, memory usage stays < 2 GB and runtime < 2 h on the free GitHub Actions runner.  
- No GPU resources are required.

