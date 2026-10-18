# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-18 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open North American bird occurrence records (historical 1970‑2000, recent 2005‑2020) and WorldClim climate rasters, (2) preprocesses them (breeding‑season filter, duplicate removal, spatial thinning, climate extraction), (3) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) using spatial block cross‑validation, (4) evaluates on recent records, (5) projects to a 2050 CMIP6 SSP2‑4.5 scenario, (6) computes niche‑stability metrics, (7) performs hierarchical bootstrap resampling with multiple‑comparison correction, and (8) generates a fully documented report. All artifacts are validated against JSON/YAML schemas in `contracts/`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `pygbif==0.13.0`, `tqdm==4.66.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`  
- **Storage**: Local filesystem under `data/`, `models/`, `metrics/`, `logs/`  
- **Testing**: `pytest` with schema‑validation fixtures  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h)  
- **Project Type**: Research‑pipeline CLI tool  
- **Constraints**: CPU‑only, open‑source data only, strict reproducibility (Constitution I‑VII)  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Pin exact versions in `code/requirements.txt`; set global seeds in `code/config.py`. |
| II. Verified Accuracy | PASS | All citations limited to the verified MaxEnt URLs; other datasets are explicitly marked “No verified source”. |
| III. Data Hygiene | PASS | Raw files stored unchanged; every transformation writes a new file; SHA‑256 checksums recorded in `data/manifest.json`. |
| IV. Single Source of Truth | PASS | All numbers read from JSON/YAML files in `metrics/` and `results/`. |
| V. Versioning Discipline | PASS | `code/versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact creation. |
| VI. Ecological Data Provenance | PASS | Occurrence CSVs include `source_id`, `download_timestamp`, `dataset_name`; raster provenance stored in `data/climate/provenance.yaml`. |
| VII. Model Evaluation Transparency | PASS | Metrics (AUC, TSS, delta suitability, p‑values, effect sizes) saved in `metrics/model_performance.json`. |

## Project Structure
```text
specs/001-predicting-species-distribution-shifts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── occurrence.schema.yaml
    ├── occurrence_record.schema.yaml
    ├── climate_raster.schema.yaml
    ├── climate_variable.schema.yaml
    ├── data_sufficiency.schema.yaml
    ├── model_artifact.schema.yaml
    ├── model_metrics.schema.yaml
    └── performance_metric.schema.yaml

code/
├── config.py
├── download.py
├── preprocess.py
├── train.py
├── evaluate.py
├── report.py
├── utils/
│   ├── spatial.py
│   ├── gpu_check.py
│   ├── stats.py
│   └── logging_config.py
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
└── .gitkeep   ← added to satisfy T001

logs/
├── download.log
├── preprocess.log
├── train.log
├── evaluate.log
└── .gitkeep   ← added to satisfy T001

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

.flake8   ← placed at repository root to satisfy T001
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Hierarchical bootstrap (FR‑010) | Needed to respect species‑level dependence; simple t‑test would inflate Type I error. | Ignoring hierarchy would breach FR‑010. |
| Spatial block CV (FR‑007) | Prevents spatial leakage; random split would over‑estimate AUC. | Random split rejected. |
| Checksum verification (T010) | Guarantees data integrity; without it the pipeline could silently use corrupted rasters. | Skipping checksum would violate FR‑001 and Constitution III. |
| Logging configuration (T003) | Required for reproducible audit trails; empty logs fail verification. | No‑log approach omitted required provenance. |
| .gitkeep in `metrics/` & `logs/` (T001) | Required directory placeholders for CI; missing files cause verification failure. | Omitted placeholders not acceptable. |
| GPU abort (FR‑004) | Enforces CPU‑only constraint on free‑tier runner. | Allowing CUDA would breach FR‑004. |

## Implementation Phases

| Phase | FR / SC addressed | Tasks (script → output) |
|-------|-------------------|--------------------------|
| **0 – Scaffold** | I‑VII, T001 | `main.py scaffold` → create missing `.gitkeep` files, place `.flake8` at root. |
| **1 – Data Acquisition** | FR‑001, FR‑002, T004, T010 | `download.py` → `data/raw/occurrence_*.csv`, `data/raw/climate/` GeoTIFFs, `data/manifest.json` (includes SHA‑256). |
| **2 – Preprocessing** | FR‑003, FR‑014, T003 | `preprocess.py` → `data/processed/features.csv`, `logs/preprocess.log`, `metrics/data_sufficiency.json`. |
| **3 – Power‑Analysis Gate** | FR‑011, FR‑006 | Inside `preprocess.py` → compute power for Cohen’s h = 0.50 (source: Wikipedia); flag species with `<100` records or power < 0.8; update `metrics/data_sufficiency.json`. |
| **4 – GPU Check** | FR‑004 | `utils/gpu_check.py` runs at start of `train.py`; aborts with clear log if CUDA detected. |
| **5 – Model Training** | FR‑004, FR‑007, FR‑008 | `train.py` → `models/*.pkl`, `logs/train.log`. Adds disclaimer `"Findings are associational and assume niche stability"` to all generated reports. |
| **6 – Evaluation & Projection** | FR‑005, FR‑009, FR‑010, SC‑001, SC‑003 | `evaluate.py` → `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`. Performs hierarchical bootstrap (10 000 iterations), Benjamini‑Hochberg correction, delta suitability calculation. |
| **7 – Report Generation** | SC‑001, SC‑003, FR‑008 | `report.py` → `reports/findings.md` (tables, figures, disclaimer). |
| **8 – Versioning & Hash Update** | V (Constitution V) | `versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact. |
| **9 – Testing** | All FR/SC | `pytest` validates schema compliance, reproducibility, and that no GPU is used. |

### Detailed Task List (≈12 tasks)

1. **Scaffold** – add missing `.gitkeep` files, verify `.flake8` at repo root.  
2. **Write `requirements.txt`** – pin exact versions (see Technical Context).  
3. **Implement `utils/gpu_check.py`** – abort if `torch.cuda.is_available()`; log outcome.  
4. **Develop `download.py`** –  
   - Paginated GBIF/eBird fetch via `pygbif` with exponential back‑off (max 3 retries).  
   - Stream WorldClim v2.1 and CMIP6 rasters using `requests` with `stream=True`; write each tile to disk immediately to keep RAM low.  
   - After each file finishes, compute SHA‑256 (`hashlib.sha256`) and record in `data/manifest.json`. Abort on mismatch (fulfills T010).  
5. **Add checksum verification logic** – invoked by `download.py` after each download.  
6. **Implement `preprocess.py`** – breeding‑season filter, duplicate removal, spatial thinning (95th‑percentile NN distance, fallback 10 km), climate extraction (`rasterio.sample`), nearest‑neighbor imputation for missing raster cells, logging of before/after counts (`logs/preprocess.log`).  
7. **Power analysis** – using `statsmodels.stats.power.NormalIndPower` to compute power for detecting Cohen’s h = 0.50; flag insufficient species (FR‑006, FR‑011).  
8. **Write `train.py`** – create spatial blocks (5 × 5 grid), train Random Forest (`n_estimators=500`), Bioclim (range envelope), MaxEnt‑style surrogate (logistic regression with L2). Save models as pickles, log durations, enforce CPU‑only.  
9. **Write `evaluate.py`** – compute AUC/TSS on recent records, project to 2050 climate, calculate `delta_suitability`, run hierarchical bootstrap (species → block), apply Benjamini‑Hochberg across the four threshold tests (0.49, 0.51, 0.55, 0.60). Save metrics JSON and summary CSV.  
10. **Add associational disclaimer** – `utils/logging_config.py` appends the disclaimer string to every generated Markdown report.  
11. **Create `report.py`** – generate Markdown tables, matplotlib/seaborn figures (ROC curves, bootstrap CI plots), embed disclaimer.  
12. **Run `versioning.py`** after each phase to update content hashes in the project state file.  

All tasks are deterministic, logged, and produce artifacts validated against the schemas in `contracts/`.

---
