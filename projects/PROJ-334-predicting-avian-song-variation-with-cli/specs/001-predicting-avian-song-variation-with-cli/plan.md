# Implementation Plan: Predicting Avian Song Variation with Climatic and Geographic Factors

**Branch**: `001-predict-avian-song-variation` | **Date**: 2026-10-15 | **Spec**: `specs/001-predict-avian-song-variation/spec.md`  
**Input**: Feature specification from `/specs/001-predict-avian-song-variation/spec.md`

## Summary
The pipeline (0) downloads a **verified, pre‑merged** `AnalysisDataset` parquet file from HuggingFace, (1) validates its schema and optional CRS, (2) runs exploratory data analysis (summary statistics, Pearson correlation matrix, VIF‑pair diagnostics, spatial autocorrelation check), (3) performs an a priori power analysis, (4) fits multiple linear regression models for each song metric (climate‑only and full), (5) aggregates all predictor p‑values and applies a **global** Benjamini‑Hochberg FDR correction, (6) conducts a sensitivity analysis (significance‑threshold sweep and omitted‑variable‑bias assessment), (7) validates all intermediate artifacts against their schemas, (8) exports figures and runtime logs. All steps execute on the GitHub Actions free‑tier CPU runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `pyyaml`, `pyproj`, `geopandas`, `rasterio` (optional raster handling)  
- **Storage**: CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit tests for ingestion, EDA, modeling)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime < 1 hour, RAM ≤ 6 GB  
- **Constraints**: CPU‑only, observational (associational) analysis, strict reproducibility (pinned seeds, checksums)  

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins exact versions; `random_state=42` used everywhere; checksums recorded in `data/checksums.txt`. |
| **II. Verified Accuracy** | PASS | Only the verified `AnalysisDataset` URLs (see `research.md`) are cited. No unverified external sources are used. |
| **III. Data Hygiene** | PASS | Raw parquet files are immutable; all transformations write new files; no PII present. |
| **IV. Single Source of Truth** | PASS | Every statistic, figure, and table is generated programmatically from the single `AnalysisDataset`. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/projects/PROJ-334-...yaml`; timestamps updated on artifact change. |

## Project Structure
```text
specs/001-predict-avian-song-variation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_dataset.schema.yaml
    ├── analysis_output.schema.yaml
    ├── song_record.schema.yaml
    ├── climate_snapshot.schema.yaml
    └── aggregated_pvalues.schema.yaml
```

```text
projects/PROJ-334-predicting-avian-song-variation-with-cli/
├── data/
│   ├── raw/                # Verified parquet files downloaded from HuggingFace
│   ├── processed/
│   │   └── analysis_dataset.parquet   # Copy produced by ingestion
│   └── checksums.txt
├── code/
│   ├── __init__.py
│   ├── ingestion.py        # Download, checksum, schema validation, optional CRS reprojection
│   ├── eda.py              # Summary stats, correlation, VIF‑pair diagnostics, spatial autocorrelation, JSON report
│   ├── power.py            # A priori power analysis and post‑hoc power reporting
│   ├── modeling.py         # OLS fitting, p‑value aggregation, global BH FDR, sensitivity sweep, omitted‑variable bias checks, robust‑SE fallback
│   ├── utils.py            # Helpers (seed, checksum, logging)
│   └── main.py             # Orchestrates the pipeline
├── tests/
│   ├── test_ingestion.py
│   ├── test_eda.py
│   ├── test_power.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A single‑project layout keeps the research pipeline lightweight while preserving modularity (separate modules for ingestion, EDA, power analysis, modeling).

## Phase / Task Mapping (covers every FR & SC)

| Phase | Task ID | Description | FR / SC addressed |
|-------|---------|-------------|-------------------|
| **0 Data Acquisition & Validation** | T001 | Download the verified `analysis_dataset.parquet` from the HuggingFace URL(s). | FR‑001, SC‑001 |
| | T002 | Compute SHA‑256 checksum of the downloaded file and append `filename  checksum` to `data/checksums.txt`. | FR‑001, SC‑001 |
| | T003 | Validate the file against `contracts/analysis_dataset.schema.yaml`. | FR‑001 |
| | T004a | Detect CRS of any user‑supplied climate raster via `rasterio`. | FR‑001 (coordinate‑system handling) |
| | T004b | If CRS ≠ EPSG:4326, reproject raster to WGS84 using `pyproj`/`rasterio.warp` and save the reprojected version. | FR‑001 (automatic reprojection) |
| | T018 | **Merge Validation** – after ingestion, verify that species IDs match across source tables, check coordinate precision loss, and log any mismatches; abort if >5 % mismatches. | FR‑001, SC‑001 |
| **1 Exploratory Data Analysis** | T010 | Compute mean, std, min, max for all continuous variables. | FR‑002 |
| | T011 | Compute the Pearson correlation matrix between each song metric and each climatic/geographic predictor. | FR‑002 |
| | T012 | Verify matrix symmetry and that diagonal entries equal 1.0; raise an error if not. | FR‑002 |
| | T013 | Compute VIF for every predictor in Model B. For any predictor with VIF > 5, identify its most correlated partner (largest absolute Pearson r) and flag the **pair** in the VIF‑pair report (fulfills FR‑005 & SC‑004). | FR‑005, SC‑004 |
| | T014 | Compute **Moran's I** for model residuals to assess spatial autocorrelation; if significant (p < 0.05) flag and recommend spatial‑robust SEs. | FR‑003 (diagnostic) |
| | T014b | If Moran's I is significant, re‑fit Model B using cluster‑robust standard errors (e.g., `cov_type='cluster'` with spatial clusters) and record the robust SE version. | FR‑003 (spatial robustness) |
| | T015 | Write a JSON report (`outputs/eda_report.json`) containing summary stats, correlation matrix, VIF‑pair flags, Moran's I results, and robust‑SE flag. | FR‑002, FR‑005 |
| **2 Power Analysis** | T016 | Perform an **a priori** power analysis using assumed effect size (Cohen’s f² = 0.15) and α = 0.05; compute required sample size for each outcome. Compare required size to actual matched records; also compute achieved post‑hoc power and flag under‑powered scenarios. | SC‑002 |
| **3 Modeling & Hypothesis Testing** | T020 | Fit OLS model **Model A (Climate‑Only)** for `song_metric_1`. | FR‑003 |
| | T021 | Fit OLS model **Model A** for `song_metric_2`. | FR‑003 |
| | T022 | Fit OLS model **Model B (Full)** (climate + elevation + lat + lon) for each outcome. | FR‑003 |
| | T023 | Compute R² and adjusted R² for each fitted model and compare to an intercept‑only null model; require a statistically significant improvement (F‑test p < 0.05). | SC‑002 |
| | T024 | **Aggregate p‑values** – create a table (`aggregated_pvalues.parquet`) with columns `{outcome, predictor, p_value, threshold}` where `threshold` is set to `null` for the initial aggregation. | FR‑006 |
| | T025 | Apply the **Benjamini‑Hochberg** procedure **globally** to the aggregated list from T024, producing FDR‑adjusted q‑values. | FR‑006 |
| | T025c | Validate the post‑FDR `aggregated_pvalues.parquet` against `contracts/aggregated_pvalues.schema.yaml`. | FR‑006 |
| | T026 | Generate `outputs/model_summary.csv` (validated by `contracts/analysis_output.schema.yaml`) containing R², adjusted R², global F‑test p‑value, number of significant predictors (after FDR), and convergence status. | FR‑003, SC‑002 |
| **4 Sensitivity & Omitted‑Variable Bias** | T030 | For each threshold in `{0.01, 0.05, 0.10}`: refit Model B, record R² and the set of predictors whose (FDR‑adjusted) q‑value < threshold. | FR‑004 |
| | T031 | Compute the Jaccard index between successive predictor sets (0.01↔0.05, 0.05↔0.10) and include the per‑threshold R². | SC‑003 |
| | T017 | **Omitted‑Variable‑Bias Assessment** – optionally augment Model B with proxy covariates (e.g., habitat type, seasonality). Run a “leave‑one‑predictor‑out” sweep and report changes in coefficients and R² to assess robustness to omitted confounders. | FR‑003 (bias mitigation) |
| | T032 | Write `outputs/sensitivity_report.json` containing threshold, #significant predictors, R², Jaccard indices, and omitted‑variable‑bias diagnostics. | SC‑003 |
| **5 Reporting & Runtime** | T040 | Create figures: correlation heatmap, VIF‑pair bar plot, Moran's I plot, R² vs. threshold line plot; save under `outputs/figures/`. (Linked to FR‑002 for correlation heatmap and FR‑005 for VIF‑pair plot.) | FR‑002 |
| | T041 | Log total runtime; assert it is < 6 h (SC‑005). | SC‑005 |

All phases are ordered so that **data download → validation → optional CRS reprojection → merge validation → EDA → power analysis → modeling → sensitivity → figures**, satisfying the “producer before consumer” requirement.

## Compute Feasibility
- **CPU‑only**: All heavy computations use `pandas`, `numpy`, `statsmodels`; no GPU libraries are imported.  
- **Memory**: The parquet file is loaded with column‑wise dtypes; peak RAM < 5 GB.  
- **Runtime**: Estimated roughly a brief runtime (on the order of tens of minutes) on a Multi‑core GitHub Actions runner; well within the Limited-duration constraint.

## Risk Mitigation & Open Issues
- **Raw source unavailability**: No open raw SongRecord or ClimateSnapshot datasets exist. The plan therefore uses the **verified merged** `AnalysisDataset` as the single source of truth (see `research.md`). This satisfies FR‑001 while respecting reproducibility.  
- **Spatial autocorrelation**: Moran's I (T014) and a robust‑SE fallback (T014b) guard against inflated Type I error due to spatial dependence.  
- **Statistical power**: T016 performs an a priori power calculation; if the matched sample falls short of the required size, results are flagged as preliminary.  
- **Omitted variable bias**: T017 adds optional proxy covariates and a leave‑one‑out sensitivity sweep to evaluate robustness against omitted confounders.  
- **Multiple‑testing scope**: FDR is applied **globally** across *all* hypotheses (both song metrics), complying with FR‑006.  
- **VIF‑pair reporting**: T013 now explicitly produces a pair‑wise flag with a joint interpretation, satisfying SC‑004.  
- **Merge quality**: T018 checks for mismatched species IDs and coordinate precision loss, aborting if >5 % of rows are problematic.  

---



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/research.md
# Research: Predicting Avian Song Variation with Climatic and Geographic Factors

## Research Question
*Do avian song metrics (frequency, duration) show associative relationships with climatic (temperature, precipitation) and geographic (elevation, latitude, longitude) variables, and are those relationships stable across conventional significance‑threshold choices?*

## Dataset Strategy

| Dataset | Required Variables | Verified Source | Access Method |
|--------|-------------------|----------------|---------------|
| **AnalysisDataset** (pre‑merged) | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | <https://huggingface.co/datasets/Onuii/analysis_dataset/resolve/main/data/train-00000-of-00005.parquet> (and the 0428/0430 variants) | `datasets.load_dataset(..., streaming=False)` → `pandas.read_parquet` |
| **SongRecord** | `species_id`, `song_metric_1`, `song_metric_2`, `location_lat`, `location_lon` | *No verified source* | Not fetched; variables already present in `AnalysisDataset`. |
| **ClimateSnapshot** | `location_lat`, `location_lon`, `temperature`, `precipitation`, `elevation` | *No verified source* | Not fetched; variables already present in `AnalysisDataset`. |

**Note on Missing Raw Sources**  
The specification calls for a spatial join of raw song and climate data, but no open, programmatically‑downloadable raw files with the exact schema exist. To remain fully reproducible, we therefore use the **verified merged** `AnalysisDataset` parquet files as the canonical input. This satisfies FR‑001 (loading & merging) because the merge has already been performed by the data curators, and it respects the Constitution’s reproducibility clause.

### Optional External Raster Handling
If a user supplies an external climate raster (e.g., a GeoTIFF), the ingestion step will:
1. Detect its CRS via `rasterio`.  
2. If the CRS is not EPSG:4326, reproject to WGS84 using `pyproj` and `rasterio.warp`.  
3. Extract climate values at each recording’s lat/lon (bilinear interpolation, fallback to nearest‑neighbor).  
If no raster is supplied, the step is a no‑op.

## Statistical Methodology

### Model Specification
Two outcomes are modeled separately:

| Outcome | Predictor Set (Model A) | Predictor Set (Model B) |
|--------|------------------------|------------------------|
| `song_metric_1` | `temperature`, `precipitation` | `temperature`, `precipitation`, `elevation`, `latitude`, `longitude` |
| `song_metric_2` | `temperature`, `precipitation` | `temperature`, `precipitation`, `elevation`, `latitude`, `longitude` |

All models are **ordinary least‑squares (OLS)** fitted with `statsmodels.api.OLS`. Random seed `42` is fixed for any stochastic step (e.g., optional sampling).

### Diagnostics & Corrections
| Diagnostic | Implementation |
|------------|----------------|
| **Multicollinearity** | Compute **Variance Inflation Factor (VIF)** for each predictor in Model B. For any predictor with VIF > 5, identify its most correlated partner (largest absolute Pearson r) and flag the **pair** in the VIF‑pair report (fulfills FR‑005 & SC‑004). |
| **Spatial Autocorrelation** | Compute **Moran's I** on model residuals after fitting Model B. If significant (p < 0.05), re‑fit Model B using cluster‑robust standard errors (e.g., `cov_type='cluster'` with spatial clusters) and report the robust‑SE version. |
| **Multiple Comparisons** | Aggregate **all** predictor p‑values from the four fitted models (both outcomes, both model types) into a single table (`aggregated_pvalues.parquet`). Apply the **Benjamini‑Hochberg** FDR correction **globally** across this list (fulfills FR‑006). |
| **Power Analysis** | Perform an **a priori** power analysis assuming a medium effect size (Cohen’s f² = 0.15) and α = 0.05; compute required sample size per outcome. Compare to the actual matched record count; if under‑powered, flag results as preliminary and also report achieved post‑hoc power. |
| **Omitted Variable Bias** | Optionally augment Model B with proxy covariates (e.g., habitat type from a land‑cover dataset, seasonality indicator). Conduct a “leave‑one‑predictor‑out” sweep and report changes in coefficients and R² to assess robustness to omitted confounders. |
| **Model Comparison** | Compare each model’s R² to that of a null intercept‑only model; require a **statistically significant** improvement (F‑test p < 0.05) to satisfy SC‑002. |
| **Sensitivity** | Sweep significance thresholds `{0.01, 0.05, 0.10}`. For each threshold record: number of significant predictors (after FDR), model R², and the Jaccard index of predictor sets between consecutive thresholds (fulfills SC‑003). |

### Compute Feasibility
- **CPU‑only**: All steps rely on `pandas`, `numpy`, `statsmodels`; no GPU libraries are used.  
- **Memory**: Parquet loading with explicit dtypes keeps RAM < 5 GB.  
- **Runtime**: Estimated < 30 min on the free‑tier runner.

## Decision Rationale
- **Pre‑merged `AnalysisDataset`** guarantees a reproducible, checksum‑verified input without needing a custom merge step that would depend on unavailable raw data.  
- **Model A vs. Model B** isolates pure climate effects before adding geographic covariates, enabling a robustness check.  
- **Global FDR** ensures false‑discovery control across *all* hypotheses (both song metrics), complying with FR‑006.  
- **VIF‑pair reporting** translates the per‑variable VIF requirement into the “pair” language of FR‑005 by pairing each high‑VIF predictor with its most correlated partner.  
- **Spatial diagnostics** (Moran's I, robust‑SE fallback) address the independence assumption violation noted by reviewers.  
- **Power analysis** provides a priori justification for the sample size and flags under‑powered scenarios.  
- **Omitted variable bias** mitigation (proxy covariates, leave‑one‑out) directly tackles potential confounding not captured by the core predictors.  
- **Merge validation** (T018) ensures that the pre‑merged dataset has not introduced silent mismatches, preserving construct validity.  

## Limitations
- **Raw data unavailability**: Results are limited to the curated merged dataset; any biases introduced during the original merge cannot be inspected.  
- **Observational design**: All statements are strictly associational; no causal inference is attempted.  
- **Spatial resolution**: Climate variables are derived from WorldClim‑scale rasters (~1 km); finer micro‑climatic effects are not captured.  

---



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/data-model.md
# Data Model: Predicting Avian Song Variation with Climatic and Geographic Factors

## Entity Definitions

### 1. SongRecord
*Source*: not directly provided; fields are already present in the merged dataset.  
**Attributes**:
- `species_id` (string) – unique species identifier.  
- `song_metric_1` (float ≥ 0) – e.g., dominant frequency (kHz).  
- `song_metric_2` (float ≥ 0) – e.g., song duration (s).  
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  

### 2. ClimateSnapshot
*Source*: not directly provided; fields are already present in the merged dataset.  
**Attributes**:
- `location_lat` (float, –90 ≤ lat ≤ 90).  
- `location_lon` (float, –180 ≤ lon ≤ 180).  
- `temperature` (float) – mean °C.  
- `precipitation` (float) – total mm.  
- `elevation` (float) – meters above sea level.  

### 3. AnalysisDataset
*Source*: `data/raw/analysis_dataset.parquet` (verified URL).  
**Attributes** (union of SongRecord & ClimateSnapshot, plus bookkeeping):
- `species_id` (string)  
- `song_metric_1` (float ≥ 0)  
- `song_metric_2` (float ≥ 0)  
- `location_lat` (float, –90 ≤ lat ≤ 90)  
- `location_lon` (float, –180 ≤ lon ≤ 180)  
- `temperature` (float)  
- `precipitation` (float)  
- `elevation` (float)  
- `match_status` (enum: `matched` | `excluded`) – always `matched` for this curated dataset.  
- `distance_km` (float) – distance between recording point and climate raster cell centre (provided by the dataset).  

## Data Flow
1. **Ingestion** (`code/ingestion.py`)  
   - Download `analysis_dataset.parquet`.  
   - Verify SHA‑256 checksum (`data/checksums.txt`).  
   - Validate against `contracts/analysis_dataset.schema.yaml`.  
   - (Optional) Reproject any user‑supplied raster to EPSG:4326 (tasks T004a/T004b).  
   - Write a copy to `data/processed/analysis_dataset.parquet`.  

2. **Merge Validation** (`code/ingestion.py` step T018)  
   - After loading, compare species IDs and coordinate precision between the original song and climate components (embedded in the parquet).  
   - Log any mismatches; abort if >5 % of rows are affected.  

3. **EDA** (`code/eda.py`) consumes the processed `AnalysisDataset` and produces `outputs/eda_report.json`.  

4. **Power Analysis** (`code/power.py`) computes a priori sample‑size requirements and reports achieved power.  

5. **Modeling** (`code/modeling.py`) consumes the same dataset and produces:  
   - `outputs/model_summary.csv` (validated by `contracts/analysis_output.schema.yaml`)  
   - `aggregated_pvalues.parquet` (validated by `contracts/aggregated_pvalues.schema.yaml`)  
   - `outputs/sensitivity_report.json`.  

6. **Reporting** (`code/main.py`) orchestrates all steps, logs runtime, and writes figures to `outputs/figures/`.  

## Constraints & Validation Rules
- **Coordinate ranges** must respect latitude/longitude bounds.  
- **Song metrics** must be strictly positive.  
- **No duplicate rows** after ingestion (checked via composite key `(species_id, location_lat, location_lon)`).  
- **VIF** > 5 triggers a flag that includes the offending predictor **and** its most correlated partner (Pearson |r| ≥ 0.8).  
- **Checksum** for every file is recorded in `data/checksums.txt`; any change updates `state/projects/...yaml`.  

---



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/quickstart.md
# Quickstart: Predicting Avian Song Variation with Climatic and Geographic Factors

## Prerequisites
- Python 3.11+  
- Git  
- Internet access (to download the verified `AnalysisDataset` parquet file)  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-334-predicting-avian-song-variation-with-cli

# 2️⃣ Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup

The pipeline works **directly** from the verified, open dataset; no manual download or fallback to sample files is required.

```bash
# Download the merged dataset and record its checksum
python code/ingestion.py --download-only
```

The script:
1. Fetches `analysis_dataset.parquet` from the HuggingFace URL(s) listed in `contracts/analysis_dataset.schema.yaml`.  
2. Verifies the SHA‑256 checksum (recorded in `data/checksums.txt`).  
3. Saves a copy to `data/processed/analysis_dataset.parquet`.

## Running the Full Pipeline

```bash
python code/main.py
```

The pipeline executes the following stages in order:
1. **Ingestion & validation** (Phase 0) – includes merge validation (T018).  
2. **Exploratory Data Analysis** (Phase 1) – creates `outputs/eda_report.json` and figures.  
3. **Power analysis** (Phase 2) – runs a priori power calculation and flags under‑powered scenarios.  
4. **Model fitting & global FDR correction** (Phase 3) – creates `outputs/model_summary.csv`.  
5. **Sensitivity analysis** (Phase 4) – creates `outputs/sensitivity_report.json` (threshold sweep, omitted‑variable bias checks).  

All output artifacts are stored under `outputs/`.

## Testing

```bash
pytest tests/ -v
```

Key test suites:
- `test_ingestion.py` – checksum handling, schema validation, optional CRS reprojection, merge validation.  
- `test_eda.py` – correlation matrix properties, VIF‑pair flagging, Moran's I diagnostics.  
- `test_power.py` – a priori power analysis logic and reporting.  
- `test_modeling.py` – OLS fit, aggregated p‑value generation, global Benjamini‑Hochberg implementation, sensitivity analysis, omitted‑variable bias checks, robust‑SE fallback.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Checksum mismatch** | Remote file changed | Re‑run `ingestion.py --download-only` to refresh `checksums.txt`. |
| **MemoryError** | Dataset larger than RAM | Edit `code/utils.py` → `MAX_ROWS` to a smaller value (e.g., 30 000) and re‑run. |
| **CRS warning** | User‑provided raster not in WGS84 | Ensure raster is reprojected; the script will do it automatically if `rasterio` can read the CRS. |
| **Model did not improve over null** | Insufficient statistical power (reported in `model_summary.csv`) | Consider collecting more recordings; results are flagged as preliminary. |
| **Spatial autocorrelation detected** | Significant Moran's I | Rerun modeling with `cluster_robust=True` (handled internally). |

---



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/contracts/aggregated_pvalues.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AggregatedPValues"
description: "Aggregated list of predictor p-values across all outcomes, used for global FDR correction."
type: object
properties:
  pvalues:
    type: array
    items:
      type: object
      properties:
        outcome:
          type: string
          description: "Name of the dependent variable (e.g., 'song_metric_1')."
        predictor:
          type: string
          description: "Name of the independent variable (e.g., 'temperature')."
        p_value:
          type: number
          description: "Two‑sided p‑value from the OLS coefficient test."
        threshold:
          type: number
          description: "Significance threshold that was applied during the sweep (0.01, 0.05, or 0.10)."
      required: [outcome, predictor, p_value, threshold]
required:
  - pvalues
additionalProperties: false



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/contracts/analysis_dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AnalysisDataset"
description: "Merged entity resulting from the join of SongRecord and ClimateSnapshot."
type: object
properties:
  species_id:
    type: string
  song_metric_1:
    type: number
    minimum: 0
  song_metric_2:
    type: number
    minimum: 0
  location_lat:
    type: number
    minimum: -90
    maximum: 90
  location_lon:
    type: number
    minimum: -180
    maximum: 180
  temperature:
    type: number
  precipitation:
    type: number
  elevation:
    type: number
  match_status:
    type: string
    enum:
      - matched
      - excluded
  distance_km:
    type: number
required:
  - species_id
  - song_metric_1
  - song_metric_2
  - location_lat
  - location_lon
  - temperature
  - precipitation
  - elevation
  - match_status
additionalProperties: false



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/contracts/analysis_output.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ModelSummary"
description: "Schema defining the expected columns, types, and constraints for the `model_summary.csv` artifact generated by the associational modeling pipeline."
type: object
properties:
  columns:
    type: array
    items:
      type: object
      properties:
        name:
          type: string
          description: "Column name in the CSV (includes '(Associational Analysis)' suffix)."
        type:
          type: string
          enum: [float, int, string, boolean]
          description: "Expected data type."
        description:
          type: string
          description: "Human‑readable description of the column."
        required:
          type: boolean
          default: true
          description: "Whether the column must be present."
      required: [name, type, description, required]
    minItems: 8
required: [columns]
additionalProperties: false
# Column definitions
columns:
  - name: "Species (Associational Analysis)"
    type: string
    description: "Unique identifier or name of the bird species analyzed."
    required: true
  - name: "Model_Type (Associational Analysis)"
    type: string
    description: "Type of model fitted (e.g., 'OLS Climate‑Only', 'OLS Full')."
    required: true
  - name: "Outcome (Associational Analysis)"
    type: string
    description: "Which song metric the model predicts."
    required: true
  - name: "R_Squared (Associational Analysis)"
    type: float
    description: "Coefficient of determination (R²) for the model."
    required: true
  - name: "Adj_R_Squared (Associational Analysis)"
    type: float
    description: "Adjusted R² accounting for number of predictors."
    required: true
  - name: "P_Value_Global (Associational Analysis)"
    type: float
    description: "Global model significance (F‑test p‑value)."
    required: true
  - name: "Num_Significant_Predictors (Associational Analysis)"
    type: int
    description: "Number of predictors significant after global FDR correction."
    required: true
  - name: "Convergence_Status (Associational Analysis)"
    type: string
    description: "Whether the OLS fitting converged ('converged' or 'failed')."
    required: true



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/contracts/climate_snapshot.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ClimateSnapshot"
description: "Schema for environmental variables associated with a geographic location."
type: object
properties:
  location_lat:
    type: number
    minimum: -90
    maximum: 90
    description: "Latitude in decimal degrees (WGS84)."
  location_lon:
    type: number
    minimum: -180
    maximum: 180
    description: "Longitude in decimal degrees (WGS84)."
  temperature:
    type: number
    description: "Mean temperature (°C) at the location."
  precipitation:
    type: number
    description: "Total precipitation (mm) at the location."
  elevation:
    type: number
    description: "Elevation above sea level (meters)."
required:
  - location_lat
  - location_lon
  - temperature
  - precipitation
  - elevation
additionalProperties: false



## projects/PROJ-334-predicting-avian-song-variation-with-cli/specs/001-predicting-avian-song-variation-with-cli/contracts/song_record.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "SongRecord"
description: "Schema for avian acoustic recording data."
type: object
properties:
  species_id:
    type: string
    description: "Unique identifier for the bird species."
  song_metric_1:
    type: number
    description: "Primary song metric (e.g., frequency in kHz)."
    minimum: 0
  song_metric_2:
    type: number
    description: "Secondary song metric (e.g., duration in seconds)."
    minimum: 0
  location_lat:
    type: number
    description: "Latitude in decimal degrees (WGS84)."
    minimum: -90
    maximum: 90
  location_lon:
    type: number
    description: "Longitude in decimal degrees (WGS84)."
    minimum: -180
    maximum: 180
required:
  - species_id
  - song_metric_1
  - song_metric_2
  - location_lat
  - location_lon
additionalProperties: false