# Implementation Plan: Predicting Species Distribution Shifts

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-05-22 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`

## Summary

This project implements a Species Distribution Modeling (SDM) pipeline to predict distribution shifts of North American birds. It downloads historical (1970-2000) and recent (2005-2020) occurrence data via `pygbif`, processes climate rasters from WorldClim (historical) and CMIP6 (future), trains three CPU-only models (Random Forest, Bioclim, and Target-Group Background Logistic Regression), and evaluates them using spatial block cross-validation. The pipeline strictly adheres to CPU-only constraints for CI compatibility, handles data sufficiency checks dynamically using a power-based threshold (Cohen's h), and frames all results as associational. Crucially, it includes a **Recent-Data Baseline Control** to distinguish biological niche shifts from model transferability failures.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pygbif`, `scikit-learn`, `rasterio`, `geopandas`, `pandas`, `numpy`, `requests`, `xarray`, `shapely`, `statsmodels`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `models/`, `metrics/`)  
**Testing**: `pytest` (unit tests for data loaders, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Computational Data Analysis Pipeline  
**Performance Goals**: Complete full workflow within 6 hours; memory usage < 7GB.  
**Constraints**: No GPU/CUDA; no synthetic data; strict adherence to open data sources; dynamic pagination for GBIF; data subsetting for climate rasters.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates pinned `requirements.txt` and random seeds in `code/`. External datasets (GBIF, WorldClim) are fetched via deterministic API calls. *Status: Compliant.*
2.  **Verified Accuracy**: All citations in `research.md` will be restricted to the "Verified datasets" block or standard literature (e.g., Cohen's h). *Status: Compliant.*
3.  **Data Hygiene**: The plan includes `code/download.py` to checksum raw files and `code/preprocess.py` to log derivation steps (thinning, filtering). *Status: Compliant.*
4.  **Single Source of Truth**: All metrics (AUC, TSS) will be written to `metrics/` and referenced by ID in the final report. *Status: Compliant.*
5.  **Versioning Discipline**: Content hashes will be recorded in `state/projects/.../artifact_hashes` for every new data file. *Status: Compliant.*
6.  **Ecological Data Provenance**: The plan explicitly requires retaining `source`, `timestamp`, `dataset_name`, and `original_dataset_name` columns in the occurrence CSV. *Status: Compliant.*
7.  **Model Evaluation Transparency**: The plan mandates saving `metrics/` with test set versions and random seeds. *Status: Compliant.*

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-species-distribution-shifts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── data_sufficiency.schema.yaml
│   ├── model_metrics.schema.yaml
│   ├── niche_stability.schema.yaml
│   └── occurrence.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-181-predicting-species-distribution-shifts-u/
├── code/
│   ├── __init__.py
│   ├── config.py            # Species list, API keys, paths
│   ├── download.py          # GBIF pagination, WorldClim/CMIP download (with subsetting)
│   ├── preprocess.py        # Thinning, filtering, sufficiency check (dynamic threshold)
│   ├── train.py             # Model training, spatial CV, GPU check
│   ├── evaluate.py          # Future projection, niche stability, stats (permutation tests)
│   └── utils/
│       ├── gpu_check.py     # CUDA detection and exit logic
│       └── io_helpers.py    # CSV/JSON loaders
├── data/
│   ├── raw/                 # Downloaded CSVs and Rasters
│   │   ├── occurrence_1970_2000.csv
│   │   ├── occurrence_2005_2020.csv
│   │   └── climate/
│   ├── processed/           # Thinned, joined data
│   └── metrics/             # data_sufficiency.json, model_metrics.json, niche_stability.json
├── models/                  # Serialized model artifacts
├── logs/                    # Execution logs
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: The single-project structure is selected to maintain a tight coupling between data processing and modeling, ensuring the 6-hour CI limit is respected by minimizing overhead. The `utils/` directory isolates hardware checks and I/O logic to facilitate testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Spatial Block CV | Required to prevent spatial autocorrelation bias in AUC/TSS. | Standard K-fold splits data randomly, violating spatial independence assumptions. |
| Dynamic Pagination | GBIF API requires offset handling for >300 records. | Hardcoded `limit=300` fails to capture full historical baselines for common species. |
| CPU-Only Enforcement | CI runners lack GPUs; CUDA errors crash jobs. | Relying on GPU fallback is impossible on free-tier; must fail fast or run on CPU. |
| Data Subsetting | Downloading multiple full-continent rasters exceeds the 6h limit.. | Full download is infeasible; subsetting by species bounding box is required. |
| Dynamic Threshold | Fixed 100-record threshold lacks statistical power justification. | Arbitrary thresholds risk Type II errors; Cohen's h provides a rigorous power basis. |
| **Niche Stability Control** | Distinguishing model failure from biological niche shift. | Simple projection comparison conflates transferability limits with niche instability. |

## Implementation Phases

### Phase 0: Data Acquisition & Subsetting (Data Feasibility)

**Goal**: Download occurrence data and *subset* climate rasters to species-specific bounding boxes to ensure feasibility.

1.  **Download Occurrences**:
    *   `code/download.py` implements dynamic pagination (offset loop) for GBIF.
    *   Fetches records for 1970-2000 (historical) and 2005-2020 (recent) for species in `config.py`.
    *   **Output**: `data/raw/occurrence_1970_2000.csv`, `data/raw/occurrence_2005_2020.csv`.
    *   **Metadata**: Includes `source`, `download_timestamp`, `dataset_name` (per Constitution Principle VI).

2.  **Subset Climate Rasters**:
    *   Calculate bounding box for each species from historical occurrences.
    *   Download WorldClim v2 (historical) and CMIP6 (future) rasters *only* for the bounding box.
    *   **Output**: `data/raw/climate/{species}_historical.tif`, `data/raw/climate/{species}_future.tif`.
    *   **Validation**: Checksums recorded in `state/.../artifact_hashes`.

### Phase 1: Preprocessing & Data Sufficiency

**Goal**: Clean data, thin spatially, and determine statistical power.

1.  **Filter & Thin**:
    *   Filter by breeding season (month).
    *   Spatial thinning: Remove points within `min_distance` (computed dynamically, not hardcoded).
    *   **Metric**: Log the *actual* minimum distance achieved between remaining points.

2.  **Dynamic Sufficiency Check**:
    *   Calculate minimum sample size ($N_{min}$) required to detect effect size $h=0.50$ (Cohen's h) with 80% power (alpha=0.05).
    *   If `count < N_min`, flag species as `INSUFFICIENT_DATA`.
    *   **Output**: `metrics/data_sufficiency.json` (schema compliant).

### Phase 2: Model Training (CPU-Only)

**Goal**: Train models using spatial block cross-validation.

1.  **Model Selection**:
    *   **Random Forest**: `scikit-learn`.
    *   **Bioclim**: Rule-based (percentile envelope).
    *   **Target-Group Background Logistic Regression**: Uses co-occurring species as background points to mimic MaxEnt's sampling strategy (replacing "MaxEnt-style" for construct validity).

2.  **Training**:
    *   Spatial Block CV (K=5).
    *   **GPU Check**: `code/utils/gpu_check.py` runs before training; exits with code 1 if CUDA detected.
    *   **Output**: `models/{species}_{algorithm}_historical.pkl`.

### Phase 3: Evaluation, Projection & Niche Stability

**Goal**: Validate against observed data, project to future, and rigorously test niche stability.

1.  **Hindcasting (Validation)**:
    *   Project 1970-2000 models onto **2005-2020 observed climate** (WorldClim v2.1 or equivalent historical proxy for that period).
    *   Compare predictions against **2005-2020 observed occurrences**.
    *   **Metric**: $AUC_{hist\_to\_recent}$ (Performance of Historical Model on Recent Data).

2.  **Recent-Data Baseline Control (NEW - Addresses Methodology Concern)**:
    *   Train a **Recent Model** using the *same* algorithms on **2005-2020 data**.
    *   Project this Recent Model onto **2005-2020 observed climate** (self-validation).
    *   **Metric**: $AUC_{recent\_to\_recent}$ (Performance of Recent Model on Recent Data).
    *   **Logic**: This establishes the "ceiling" performance. If the Historical Model's drop in performance is comparable to the inherent noise of the Recent Model, the drop is due to **model transferability limits**, not niche shift.

3.  **Niche Stability Test (FR-009)**:
    *   Calculate **Niche Non-Stationarity Metric**:
        $$ NonStationarity = (AUC_{hist\_to\_recent} - AUC_{recent\_to\_recent}) $$
        *Note: Since $AUC_{recent\_to\_recent}$ is the optimal performance on recent data, a negative value indicates the Historical Model performed worse than the Recent Model, implying degradation. The magnitude of this difference is the metric.*
    *   **Interpretation**:
        *   If $NonStationarity \approx 0$: The Historical Model's performance on recent data is as good as a model trained on recent data. The niche is likely **stable**; any degradation in future projections is likely due to model limitations, not biological shift.
        *   If $NonStationarity \ll 0$ (significant drop): The Historical Model performs significantly worse than the Recent Model on recent data. This indicates **Niche Non-Stationarity** (biological shift).
    *   **Statistical Test**: Use paired permutation tests (FR-010) to determine if $NonStationarity$ is significantly different from zero.

4.  **Forecasting**:
    *   Project both Historical and Recent models onto **2050 CMIP6 SSP2-4.5** climate.
    *   **Output**: Suitability maps for 2050.

5.  **Sensitivity & Correction (FR-005)**:
    *   Sweep suitability thresholds (low, medium, high).
    *   Apply Bonferroni or Benjamini-Hochberg correction for multiple comparisons.

6.  **Cross-Species Comparison (FR-010)**:
    *   Perform non-parametric permutation tests to compare AUC/TSS across algorithms and species.

## Compute Feasibility

- **CPU-First**: All models run on CPU. `torch` is not used; `scikit-learn` is the primary engine.
- **Memory Management**: Climate rasters are downloaded *per species* (subset) to fit in RAM.
- **Time Budget**: The pipeline processes a subset of species (e.g., common birds) with subsetting to fit within the CI limit.
- **GPU Escape Hatch**: Not applicable. The plan explicitly avoids GPU dependencies. If a CUDA call is detected, the process exits with code 1.