# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-10-18 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary
Build a fully reproducible, CPU‑only pipeline that (1) downloads open North American bird occurrence records (historical 1970‑2000, recent 2005‑2020) via the GBIF/eBird APIs, (2) streams WorldClim v2.1 climate rasters, (3) preprocesses the data (breeding‑season filter, duplicate removal, bias‑corrected spatial thinning, VIF‑based collinearity mitigation, climate extraction), (4) trains three SDM algorithms (Random Forest, Bioclim, MaxEnt‑style surrogate) on a reduced set of **10 representative species** using spatial block cross‑validation, (5) evaluates on recent records **with calibration checks**, (6) projects to a 2050 CMIP6 SSP2‑4.5 scenario **and assesses environmental similarity (MOP/MESS)**, (7) computes niche‑stability metrics that combine calibration performance and extrapolation risk, (8) generates a fully documented markdown report. All artifacts are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `pygbif==0.13.0`, `tqdm==4.66.2`, `statsmodels==0.14.2`, `matplotlib==3.8.4`, `seaborn==0.13.2`, `requests==2.32.3`, `pyyaml==6.0.1`  
- **Storage**: Local filesystem under `data/`, `models/`, `metrics/`, `logs/`  
- **Testing**: `pytest` with schema‑validation fixtures  
- **Target Platform**: GitHub Actions free‑tier Linux runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only, open‑source data only, strict reproducibility (Constitution I‑VII)  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Pin exact versions, set global seeds, deterministic scripts. |
| II. Verified Accuracy | **FAIL** – GBIF/eBird APIs lack a pre‑verified static URL; they are open APIs and therefore not “verified” per the constitution. This is explicitly noted. | No change; the pipeline will still use these open sources but the principle is marked FAIL. |
| III. Data Hygiene | PASS | Raw files immutable; SHA‑256 checksums recorded in `data/manifest.json`. |
| IV. Single Source of Truth | PASS | All numbers read from JSON/YAML files in `metrics/` and `results/`. |
| V. Versioning Discipline | PASS | `code/versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact. |
| VI. Ecological Data Provenance | PASS | Occurrence CSVs include `source_id`, `download_timestamp`, `dataset_name`. |
| VII. Model Evaluation Transparency | PASS | Metrics saved with effect size, p‑value, seed, and script version. |

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
    ├── occurrence_record.schema.yaml
    └── log_counts.schema.yaml

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

.flake8                     ← placed at project root (required by T001)
requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Missing `.gitkeep` in `metrics/` & `logs/` | Required by T001 for CI directory placeholders. | Omit placeholders – verification fails. |
| `.flake8` not at repo root | Required by T001 & Constitution I. | Keep inside `code/` – violates spec. |
| No checksum verification (T010) | Guarantees data integrity; without it the pipeline could use corrupted rasters. | Trust download – violates Constitution III. |
| No logging configuration (T003) | Structured logs needed for reproducibility and audit trails (Constitution VI). | Print to stdout only – fails T003. |
| Potential GPU usage (FR‑004) | Must enforce CPU‑only execution on free CI. | Implicitly rely on torch – may invoke CUDA. |
| Long download time (T004) | Previous timeout; need robust streaming & retry logic. | Single large download – exceeds CI time budget. |
| Computational overload (data_resources‑9944fde3) | Training three algorithms for 30 species with 10 000 bootstraps exceeds CI limits. | Reduce species, iterations, thresholds – still meets scientific goals. |
| Power analysis mismatch (methodology‑f2b48fb8) | Original plan used Cohen’s h which does not match the AUC outcome. | Switch to power for detecting ΔAUC = 0.05. |
| Sample‑size for hierarchical bootstrap (methodology‑14aa9a8a) | 30 species may be insufficient for stable across‑species variance estimates. | Limit to 10 species, reduce bootstrap to 2 000, note limitation. |
| Sampling bias not addressed (methodology‑42d9dfc4) | Autocorrelation thinning alone does not correct heterogeneous detection effort. | Add bias‑layer creation and bias‑corrected background sampling. |
| Calibration missing before projection (methodology‑f2c537f6) | Projection quality cannot be judged without checking calibration on known data. | Compute calibration curves & Brier scores; only well‑calibrated models are projected. |
| Collinearity unmitigated (methodology‑9c0ea701) | High VIF among Bioclim variables inflates variance. | Perform VIF screening, drop >10, optionally PCA for MaxEnt surrogate. |
| FR‑014 reference (spec_coverage‑4ae03827) | Non‑existent requirement. | Removed reference. |
| Lack of schema validation references (plan_consistency‑b03f230f,‑2e90e09e,‑fe9b7bd6) | Contracts not mentioned in plan phases. | Added explicit validation steps for occurrence CSVs, processed features, climate raster metadata, and model artifacts. |
| Circular niche‑stability validation (scientific_soundness‑1556b93d) | Delta suitability uses only model predictions. | Introduced calibration check and environmental similarity (MOP/MESS) analysis; niche‑stability reported as proportion of future area within analogous climate space. |

## Implementation Phases & FR/SC Coverage

| Phase | FR / SC addressed | Tasks (script → output) |
|-------|-------------------|--------------------------|
| **0 – Scaffold** | T001, Constitution I‑VII | `main.py scaffold` → creates missing `.gitkeep` files in `metrics/` and `logs/`, places a `.flake8` file at the repository root, generates empty `requirements.txt`. |
| **1 – Data Acquisition** | FR‑001, FR‑002, T004, T010, T02 | `download.py` → `data/raw/occurrence_historical.csv`, `data/raw/occurrence_recent.csv`, `data/raw/climate/*.tif`; `data/manifest.json` (SHA‑256, size, timestamp). Implements exponential back‑off, 3‑retry policy, streams rasters tile‑by‑tile, and **verifies each file against its `climate_raster.schema.yaml` checksum**. |
| **2 – Preprocessing** | FR‑003, FR‑042 (bias correction), FR‑009 (collinearity), T003 | `preprocess.py` → `data/processed/features.csv`, `logs/preprocess.log`, `metrics/data_sufficiency.json`. Steps: <br>1. **Breeding‑season filter** (configurable months). <br>2. **Duplicate removal**. <br>3. **Bias‑layer creation** from observation density; background points sampled proportionally to bias raster. <br>4. **Spatial thinning** with dynamic `min_distance` (95th‑percentile NN distance, fallback 10 km). <br>5. **VIF screening** (drop variables with VIF > 10). Optional **PCA** for MaxEnt surrogate (first 5 components). <br>6. **Climate extraction** (19 Bioclim variables) using `rasterio.sample`; nearest‑neighbor imputation for missing raster cells. <br>All steps log before/after counts to `logs/preprocess_counts.yaml` (validated against `log_counts.schema.yaml`). |
| **3 – Power‑Analysis Gate** | FR‑011, FR‑006 | Inside `preprocess.py` → computes statistical power to detect a **minimum AUC difference of 0.05** between historical and future models using `statsmodels.stats.power.NormalIndPower`. Flags species with `<100` records **or** power < 0.8 as `INSUFFICIENT_DATA`. Results stored in `metrics/data_sufficiency.json` (schema `data_sufficiency.schema.yaml`). |
| **4 – GPU Check** | FR‑004 | `utils/gpu_check.py` runs at start of `train.py`; aborts with clear log if `torch.cuda.is_available()`. |
| **5 – Model Training** | FR‑004, FR‑007, FR‑008, FR‑009 | `train.py` → `models/*.pkl`, `logs/train.log`. Performs 5‑fold spatial block CV (5 × 5 grid), trains Random Forest (`n_estimators=500`), Bioclim (range‑envelope), MaxEnt‑style surrogate (logistic regression on PCA‑reduced predictors). **Model artifacts are validated against `model_artifact.schema.yaml`.** |
| **6 – Evaluation & Projection** | FR‑005, FR‑009, FR‑010, SC‑001, SC‑003 | `evaluate.py` → `metrics/model_performance.json`, `results/summary_table.csv`, `logs/evaluate.log`. <br>1. **Calibration check** on recent test set (Brier score, calibration curve); only models with Brier < 0.2 are projected. <br>2. **Historical validation**: compute AUC/TSS on recent records. <br>3. **Future projection** onto 2050 climate; compute **Environmental Similarity (MOP/MESS)** to flag extrapolation zones. <br>4. **Niche‑stability metric**: proportion of future suitable area that lies within analogous climate space (from MOP) **plus** calibrated AUC change. <br>5. **Threshold sweep** (0.49, 0.55, 0.60) with Benjamini‑Hochberg FDR = 0.05 correction. <br>6. **Hierarchical bootstrap** (species‑level resampling → spatial‑block resampling) with **2 000 iterations** (reduced to fit CI). |
| **7 – Report Generation** | SC‑001, SC‑003, FR‑008 | `report.py` → `reports/findings.md` (tables, ROC curves, calibration plots, MOP maps, bootstrap CI plots, disclaimer). |
| **8 – Versioning & State Update** | Constitution V | `versioning.py` updates `state/projects/PROJ-181-...yaml` after each artifact. |
| **9 – Testing** | All FR/SC | `pytest` validates schema compliance, reproducibility, and that no GPU is invoked. |

### Detailed Task List (≈12 tasks)
1. Scaffold directories & placeholder files (including `.gitkeep` in `metrics/` & `logs/`, `.flake8` at repo root).  
2. Write `requirements.txt` with pinned versions.  
3. Implement `utils/gpu_check.py`.  
4. Implement robust `download.py` (streaming, retries, SHA‑256 verification, manifest update, raster‑metadata schema validation).  
5. Add checksum‑verification logic (step 4).  
6. Implement `utils/logging_config.py` (YAML config).  
7. Implement `preprocess.py` (filters, bias correction, thinning, VIF screening, climate extraction, power analysis).  
8. Write `contracts/log_counts.schema.yaml` for `logs/preprocess_counts.yaml`.  
9. Write `train.py` (spatial block CV, three algorithms, model‑artifact schema validation).  
10. Write `evaluate.py` (calibration, MOP analysis, bootstrap, multiple‑comparison correction).  
11. Write `report.py` (markdown report with disclaimer).  
12. Run `versioning.py` after each phase and execute full `pytest` suite.

All tasks produce real files that conform to the schemas in `contracts/` and can be verified deterministically on the CI runner.
