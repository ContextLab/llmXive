# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-11 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Implement a fully reproducible, CPU‑only pipeline that (1) downloads North American bird occurrence records (historical 1970‑2000, recent 2005‑2020) via the GBIF API, (2) downloads WorldClim v2.1 climate rasters (historical) and WorldClim CMIP6 SSP2‑4.5 future rasters (2050), (3) preprocesses the data (breeding‑season filter, duplicate removal, spatial thinning, climate extraction), (4) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) using spatial block cross‑validation, (5) evaluates models on recent data, (6) projects models onto future climate, (7) computes a niche‑stability metric (`delta_Suitability`) and runs hierarchical bootstrap resampling with multiple‑comparison correction, and (8) generates all required artifacts (models, metrics, logs, reports) while satisfying every functional requirement (FR‑001‑FR‑011) and success criterion (SC‑001‑SC‑003).

All steps are deterministic, checksum‑verified, and fully reproducible on a GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h). No GPU is used; the pipeline will abort if a CUDA device is detected (FR‑004).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn`, `geopandas`, `rasterio`, `pandas`, `numpy`, `pygbif`, `pyyaml`, `matplotlib`, `seaborn`, `statsmodels`, `tqdm`  
- **Storage**: Local file system under `data/`, `models/`, `metrics/`, `logs/`  
- **Testing**: `pytest` (unit & integration)  
- **Target Platform**: Linux CI runner (GitHub Actions free tier)  
- **Project Type**: Computational research pipeline / CLI tool  
- **Performance Goals**: End‑to‑end runtime ≤ 360 min, peak RAM ≤ 7 GB  
- **Constraints**: CPU‑only, open‑source data only, strict reproducibility (Constitution Principles I‑VII)

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| **I. Reproducibility** | PASS | Pin all package versions in `code/requirements.txt`; set random seeds (`np.random.seed`, `random.seed`, `sklearn` `random_state`) in `code/config.py`. |
| **II. Verified Accuracy** | PASS | All external citations are limited to the verified URLs listed in the “Verified datasets” block. |
| **III. Data Hygiene** | PASS | Raw files are stored under `data/raw/` unchanged; every transformation writes a new file under `data/processed/`. SHA‑256 checksums are recorded in `state/projects/PROJ-181-...yaml`. |
| **IV. Single Source of Truth** | PASS | All numbers used in the manuscript are read from JSON/YAML files in `metrics/` and `results/`. |
| **V. Versioning Discipline** | PASS | `code/versioning.py` computes content hashes after each artifact write and updates the project state file. |
| **VI. Ecological Data Provenance** | PASS | Occurrence CSVs contain `source_id`, `download_timestamp`, and `dataset_name`. Climate raster provenance is stored in `data/climate/provenance.yaml`. |
| **VII. Model Evaluation Transparency** | PASS | Every model’s AUC, TSS, `delta_Suitability`, p‑values, and effect sizes are saved in `metrics/model_metrics.json`. |

## Project Structure
```text
specs/001-predicting-species-distribution-shifts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── occurrence_record.schema.yaml
    ├── occurrence.schema.yaml
    ├── climate_raster.schema.yaml
    ├── climate_variable.schema.yaml
    ├── data_sufficiency.schema.yaml
    ├── model_artifact.schema.yaml
    ├── model_metrics.schema.yaml
    └── performance_metric.schema.yaml

code/
├── config.py                # Global constants, species list, seeds
├── download.py              # GBIF & WorldClim fetcher with checksum verification
├── preprocess.py            # Filtering, thinning, raster extraction, logging
├── train.py                 # Spatial block CV, model fitting
├── evaluate.py              # Projection, metric calculation, bootstrap
├── report.py                # Table/figure generation
├── utils/
│   ├── spatial.py
│   ├── gpu_check.py
│   ├── stats.py
│   └── logging_config.py   # Sets up Python logging to `logs/`
├── versioning.py            # Hash & timestamp updater
└── main.py                  # Orchestrates the pipeline

data/
├── raw/
│   ├── occurrence_1970_2000.csv
│   ├── occurrence_2005_2020.csv
│   └── climate/            # WorldClim GeoTIFF tiles
├── processed/
│   └── features.csv
└── manifest.json           # Records file paths, sizes, SHA‑256 checksums

models/
├── *.pkl                   # Serialized SDM artifacts
└── version.txt

metrics/
├── model_performance.json
├── data_sufficiency.json
└── .gitkeep                # Ensures directory exists in repo

logs/
├── download.log
├── preprocess.log
├── train.log
├── evaluate.log
└── .gitkeep

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

.gitkeep files are placed in every empty directory (including `metrics/` and `logs/`).  
`.flake8` is located at the repository root as required by the linting task.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Hierarchical Bootstrap (FR‑010) | Needed to respect species‑level dependence; simple t‑test would inflate Type I error. | Ignoring hierarchy would breach FR‑010. |
| Spatial Block CV (FR‑007) | Prevents spatial leakage; random CV would produce over‑optimistic AUC. | Random split rejected for same reason. |
| Checksum Verification (T010) | Guarantees data integrity; without it the pipeline could silently use corrupted rasters. | Skipping checksum would violate FR‑001 and Constitution III. |
| Logging Configuration (T003) | Required for reproducible audit trails; empty logs fail verification. | No‑log approach omitted required provenance. |
| .gitkeep in `metrics/` & `logs/` (T001) | Required directory placeholders for CI; missing files cause verification failure. | Omitted placeholders not acceptable. |
| GPU Abort (FR‑004) | Enforces CPU‑only constraint on free‑tier runner. | Allowing CUDA would breach FR‑004. |

## Implementation Phases

| Phase | FR / SC addressed | Tasks (script → output) |
|-------|-------------------|--------------------------|
| **0 – Setup** | I‑VII, T001 | Create `.gitkeep` files, place `.flake8` at repo root, add `code/requirements.txt` (includes `pygbif`). |
| **1 – Data Acquisition** | FR‑001, FR‑002, T004, T010 | `download.py` → `data/raw/occurrence_*.csv`, `data/raw/climate/` GeoTIFFs, `data/manifest.json` (includes SHA‑256). |
| **2 – Preprocessing** | FR‑003, FR‑014, T003 | `preprocess.py` → `data/processed/features.csv`, `logs/preprocess.log`, `metrics/data_sufficiency.json` (schema `data_sufficiency.schema.yaml`). |
| **3 – Power‑Analysis Gate** | FR‑011, FR‑006 | Within `preprocess.py` → flag species with `<100` records or power < 0.8; update `metrics/data_sufficiency.json`. |
| **4 – GPU Check** | FR‑004 | `utils/gpu_check.py` runs at start of `train.py`; aborts with clear log if CUDA present. |
| **5 – Model Training** | FR‑004, FR‑007, FR‑008 | `train.py` → `models/*.pkl`, `logs/train.log`. Adds disclaimer string to all report artifacts (FR‑008). |
| **6 – Evaluation & Projection** | FR‑005, FR‑009, FR‑010, SC‑001, SC‑003 | `evaluate.py` → `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`. Performs hierarchical bootstrap, Benjamini‑Hochberg correction, computes `delta_Suitability`. |
| **7 – Report Generation** | SC‑001, SC‑003, FR‑008 | `report.py` → `reports/findings.md` (includes associational disclaimer). |
| **8 – Versioning & Hash Update** | V (Constitution V) | `versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact creation. |
| **9 – Testing** | All FR/SC | `pytest` suite validates schema compliance (`contracts/*.schema.yaml`), reproducibility (seeded runs), and that no GPU is used. |

### Detailed Task List (≈12 tasks)

1. **Create repository scaffolding** – add missing `.gitkeep` in `metrics/` & `logs/`, place `.flake8` at root.  
2. **Write `requirements.txt`** – pin exact versions (e.g., `scikit-learn==1.5.0`, `pygbif==0.13.0`).  
3. **Implement `code/utils/gpu_check.py`** – simple `torch.cuda.is_available()` guard; log outcome.  
4. **Develop `code/download.py`** –  
   - GBIF occurrence fetch via `pygbif.occurrences.search` with pagination, rate‑limit back‑off.  
   - WorldClim raster download via `wget` using verified URLs (`https://worldclim.org/data/worldclim21.html`, `https://worldclim.org/data/cmip6.html`).  
   - Compute SHA‑256 for each file, compare against known values (if available) or record for future verification.  
   - Write entries to `data/manifest.json`.  
5. **Add checksum verification logic** – abort with error if mismatch (fulfills T010).  
6. **Implement `code/preprocess.py`** –  
   - Filter by breeding months (species‑specific month ranges stored in `config.py`).  
   - Remove exact duplicate coordinates.  
   - Spatial thinning using `spatial.thin_points` (dynamic 95th‑percentile distance, fallback 10 km).  
   - Extract climate variables with `rasterio.sample`.  
   - Impute missing climate values via nearest‑neighbor (or drop).  
   - Log counts before/after each step to `logs/preprocess.log`.  
   - Output `data/processed/features.csv` and `metrics/data_sufficiency.json`.  
7. **Power analysis** – within `preprocess.py`, compute power for Cohen’s h = 0.50 using `statsmodels.stats.power.NormalIndPower`; flag insufficient species.  
8. **Write `code/train.py`** –  
   - Generate spatial blocks (`utils.spatial.create_blocks`).  
   - For each species with sufficient data, fit RF (`RandomForestClassifier`), Bioclim (range envelope), MaxEnt‑style (logistic regression with L2 penalty).  
   - Store models as pickle files under `models/`.  
   - Log training duration; ensure no CUDA usage.  
9. **Write `code/evaluate.py`** –  
   - Load models, compute predictions on recent occurrences with 2005‑2020 climate.  
   - Compute AUC/TSS (`sklearn.metrics`).  
   - Project same models onto 2050 climate at identical locations; compute mean suitability per species.  
   - Calculate `delta_Suitability`.  
   - Perform hierarchical bootstrap (species → spatial block) on `delta_Suitability` (10 000 iterations).  
   - Apply Benjamini‑Hochberg correction across threshold sweep {0.01, 0.05, 0.10}.  
   - Write `metrics/model_performance.json` and `results/summary_table.csv`.  
10. **Add associational disclaimer** – `utils.logging_config.py` appends the string `"Findings are associational and assume niche stability"` to every generated report file.  
11. **Create `code/report.py`** – generate Markdown tables & figures (using `matplotlib`/`seaborn`) summarizing metrics, bootstrap confidence intervals, and the disclaimer.  
12. **Run `code/versioning.py`** after each phase to update hashes in the project state file.  

All tasks are deterministic, logged, and produce artifacts that can be validated against the JSON/YAML schemas in `contracts/`.

---
