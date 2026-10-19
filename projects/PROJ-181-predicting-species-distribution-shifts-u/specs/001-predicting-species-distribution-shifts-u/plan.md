# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-18 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open North American bird occurrence records (historical 1970‑2000, recent 2005‑2020) via the verified `pygbif` API, (2) streams WorldClim v2.1 climate rasters, (3) preprocesses the data (breeding‑season filter, duplicate removal, spatial thinning, climate extraction), (4) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) using spatial block cross‑validation, (5) evaluates on recent records, (6) projects to a 2050 CMIP6 SSP2‑4.5 scenario, (7) computes niche‑stability metrics and hierarchical bootstrap comparisons with Benjamini‑Hochberg correction, and (8) generates a fully documented markdown report. All artifacts are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `pygbif==0.13.0`, `tqdm==4.66.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `requests==2.32.3`  
- **Storage**: Local filesystem under `data/`, `models/`, `metrics/`, `logs/`  
- **Testing**: `pytest` with schema‑validation fixtures  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only, open‑source data only, strict reproducibility (Constitution I‑VII)  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Pin exact versions, set global seeds, deterministic scripts. |
| II. Verified Accuracy | PASS | All citations limited to verified URLs (see Research.md). |
| III. Data Hygiene | PASS | Raw files immutable, SHA‑256 checksums recorded in `data/manifest.json`. |
| IV. Single Source of Truth | PASS | All numbers read from JSON/YAML files in `metrics/` and `results/`. |
| V. Versioning Discipline | PASS | `code/versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact. |
| VI. Ecological Data Provenance | PASS | Occurrence CSVs include `source_id`, `download_timestamp`, `dataset_name`. |
| VII. Model Evaluation Transparency | PASS | Metrics saved with effect size, p‑value, seed, and full script versioning. |

## Project Structure
```text
specs/001-predicting-species-distribution-shifts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── climate_raster.schema.yaml
    ├── climate_variable.schema.yaml
    ├── data_sufficiency.schema.yaml
    ├── model_artifact.schema.yaml
    ├── model_metrics.schema.yaml
    ├── occurrence.schema.yaml
    └── occurrence_record.schema.yaml

code/
├── config.py
├── download.py
├── preprocess.py
├── train.py
├── evaluate.py
├── report.py
├── utils/
│   ├── gpu_check.py
│   ├── logging_config.py
│   └── spatial.py
├── versioning.py
└── main.py

data/
├── raw/
│   ├── occurrence_historical.csv
│   ├── occurrence_recent.csv
│   └── climate/
├── processed/
│   └── features.csv
└── manifest.json

models/
└── *.pkl

metrics/
├── model_performance.json
├── data_sufficiency.json
├── .gitkeep               ← satisfies T001
└── .gitkeep               ← placeholder

logs/
├── download.log
├── preprocess.log
├── train.log
├── evaluate.log
├── .gitkeep               ← satisfies T001
└── .gitkeep               ← placeholder

results/
├── summary_table.csv
└── .gitkeep

reports/
├── findings.md
└── .gitkeep

tests/
├── unit/
├── integration/
└── contract/
    └── schema_validation.py

.flake8                     ← placed at project root (satisfies T001)
requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Missing `.gitkeep` in `metrics/` & `logs/` | Required by T001 for CI directory placeholders. | Omit placeholders – verification fails. |
| `.flake8` not at repo root | Required by T001 & Constitution III. | Keep inside `code/` – violates spec. |
| No checksum verification (T010) | Guarantees data integrity; without it the pipeline could use corrupted rasters. | Trust download – violates Constitution III. |
| No logging configuration (T003) | Structured logs needed for reproducibility and audit trails (Constitution VI). | Print to stdout only – fails T003. |
| Potential GPU usage (FR‑004) | Must enforce CPU‑only execution on free CI. | Implicitly rely on torch – may invoke CUDA. |
| Long download time (T004) | Previous timeout; need robust streaming and retry logic. | Single large download – exceeds CI time budget. |

## Implementation Phases & FR/SC Coverage

| Phase | FR / SC addressed | Tasks (script → output) |
|-------|-------------------|--------------------------|
| **0 – Scaffold** | T001, Constitution I‑VII | `main.py scaffold` → creates missing `.gitkeep` files, places `.flake8` at repo root, generates empty `requirements.txt`. |
| **1 – Data Acquisition** | FR‑001, FR‑002, T004, T010 | `download.py` → `data/raw/occurrence_historical.csv`, `data/raw/occurrence_recent.csv`, `data/raw/climate/*.tif`; `data/manifest.json` (includes SHA‑256, size, download timestamp). |
| **2 – Preprocessing** | FR‑003, FR‑014, T003 | `preprocess.py` → `data/processed/features.csv`, `logs/preprocess.log`, `metrics/data_sufficiency.json`. Uses `utils.logging_config.py` for structured YAML logs. |
| **3 – Power‑Analysis Gate** | FR‑011, FR‑006 | Inside `preprocess.py` → computes power for Cohen’s h = 0.50 (source: Wikipedia) using `statsmodels`; flags species with `<100` records or power < 0.8 as `INSUFFICIENT_DATA`. Results stored in `metrics/data_sufficiency.json`. |
| **4 – GPU Check** | FR‑004 | `utils/gpu_check.py` runs at start of `train.py`; aborts with clear log if `torch.cuda.is_available()`. |
| **5 – Model Training** | FR‑004, FR‑007, FR‑008 | `train.py` → `models/*.pkl`, `logs/train.log`. Performs 5‑fold spatial block CV, trains Random Forest, Bioclim, MaxEnt‑style surrogate (logistic regression). |
| **6 – Evaluation & Projection** | FR‑005, FR‑009, FR‑010, SC‑001, SC‑003 | `evaluate.py` → `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`. Computes AUC/TSS, delta suitability, threshold sweep (0.49, 0.51, 0.55, 0.60), hierarchical bootstrap (10 000 iterations), Benjamini‑Hochberg correction. |
| **7 – Report Generation** | SC‑001, SC‑003, FR‑008 | `report.py` → `reports/findings.md` (tables, ROC curves, bootstrap CI plots, disclaimer). |
| **8 – Versioning & State Update** | Constitution V | `versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact. |
| **9 – Testing** | All FR/SC | `pytest` validates schema compliance, reproducibility, and that no GPU is invoked. |

### Detailed Task List (≈12 tasks)

1. **Scaffold** – create missing `.gitkeep` files, verify `.flake8` at root.  
2. **Write `requirements.txt`** – pin exact versions (see Technical Context).  
3. **Implement `utils/gpu_check.py`** – abort on CUDA detection.  
4. **Develop `download.py`** –  
   - Paginated GBIF/eBird fetch via `pygbif` (verified recipe).  
   - Stream WorldClim v2.1 and CMIP6 rasters with `requests` (`stream=True`).  
   - After each file download, compute SHA‑256, compare to checksum listed in the accompanying `.md5` file (converted to SHA‑256). Abort on mismatch.  
   - Record SHA‑256, file size, and download timestamp in `data/manifest.json`. |
5. **Add checksum verification logic** – integrated in step 4 (fulfills T010). |
6. **Implement `utils/logging_config.py`** – YAML config (`logging.config.dictConfig`) that writes structured logs to `logs/*.log`. |
7. **Implement `preprocess.py`** – breeding‑season filter, duplicate removal, spatial thinning (95th‑percentile NN distance, fallback 10 km), climate extraction (`rasterio.sample`), nearest‑neighbor imputation for missing raster cells, logging of before/after counts. |
8. **Power analysis** – using `statsmodels.stats.power.NormalIndPower` for Cohen’s h = 0.50 (source: Wikipedia). Flag insufficient species per FR‑006/FR‑011. |
9. **Write `train.py`** – spatial block CV, train three algorithms, enforce CPU‑only, save models, log durations. |
10. **Write `evaluate.py`** – compute AUC/TSS, project to 2050, delta suitability, threshold sweep, hierarchical bootstrap (10 000 iterations), Benjamini‑Hochberg correction, save metrics and summary CSV. |
11. **Create `report.py`** – generate Markdown report with tables, ROC curves, bootstrap CI plots, and disclaimer (`"Findings are associational and assume niche stability"`). |
12. **Run `versioning.py`** after each phase to update project state file. |

All tasks are deterministic, logged, and produce artifacts that validate against the schemas in `contracts/`.

---
