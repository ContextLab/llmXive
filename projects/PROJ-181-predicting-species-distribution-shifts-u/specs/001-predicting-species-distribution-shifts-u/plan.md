# Implementation Plan: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Branch**: `001-predicting-species-distribution-shifts` | **Date**: 2024-05-22 | **Spec**: `specs/001-predicting-species-distribution-shifts/spec.md`
**Input**: Feature specification from `/specs/001-predicting-species-distribution-shifts/spec.md`

## Summary

This project implements a computational pipeline to predict species distribution shifts by training Species Distribution Models (SDMs) on historical North American bird occurrence records from a multi-decadal period and WorldClim v2 climate data. The core technical approach involves CPU-optimized machine learning (Random Forest, Bioclim, and a MaxEnt-style implementation via `scikit-learn` surrogate) validated via spatial block cross-validation.

**Critical Methodological Correction**: The evaluation of "niche stability" is redefined to avoid temporal mismatch. We do not evaluate future projections against future occurrences (which do not exist). Instead, we:
1. Validate the historical model (1970-2000) against 2005-2020 occurrences using **2005-2020 climate** data to calculate AUC/TSS.
2. Project the same historical model to the **2050 climate** data *at the same 2005-2020 occurrence locations*.
3. Calculate `delta_Suitability` (Mean Suitability Shift) as the difference between the mean predicted suitability under 2050 climate vs. 2005-2020 climate. This measures the model's sensitivity to future climate change, isolating the "niche shift" signal without requiring future occurrence data.
   - **Statistical Test**: The hierarchical bootstrap (FR-010) is applied to the distribution of `delta_Suitability` values, not AUC/TSS, to test for niche stability.

The system explicitly handles data scarcity (flagging species with <100 records), performs rigorous statistical testing (hierarchical bootstrap, multiple-comparison correction), and outputs associational findings with strict provenance tracking as mandated by the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `geopandas`, `rasterio`, `pandas`, `requests`, `pyyaml`, `numpy`, `matplotlib`, `seaborn`, `statsmodels`  
**Storage**: Local file system (`data/raw`, `data/processed`, `models`, `metrics`); no external database.  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Full workflow (download, preprocess, train, evaluate) must complete within 360 minutes (6 hours). Memory usage must stay <7 GB.  
**Constraints**: CPU-only execution (no CUDA); no access to gated datasets (ADNI, HCP, etc.); strict adherence to open data sources (GBIF, WorldClim v2.1, WorldClim CMIP6).  
**Scale/Scope**: Representative subset of North American bird species to fit within compute limits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin all versions. Random seeds (`np.random.seed`, `random.seed`, `sklearn` `random_state`) will be set in `code/config.py`. Data download scripts will fetch from canonical GBIF/WorldClim URLs. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `data-model.md` will be verified against the "# Verified datasets" block provided in the prompt. No fabricated URLs will be used. |
| **III. Data Hygiene** | **PASS** | `code/download.py` will write raw data to `data/raw/`. `code/preprocess.py` will write derived data to `data/processed/`. Checksums (SHA-256) will be generated and stored in `state/projects/...yaml`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics (AUC, TSS, Suitability Shift) will be written to `metrics/` JSON files. The paper generation script will read *only* from these files. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **PASS** | **Mechanism**: After every artifact write (data, model, metric), the `code/utils/versioning.py` script will compute the content hash and update `state/projects/PROJ-181-...yaml` with the new hash and timestamp. This script is invoked at the end of each pipeline phase. |
| **VI. Ecological Data Provenance** | **PASS** | `data/raw/*.csv` will include columns: `source_id`, `download_timestamp`, `original_dataset_name`. The `code/download.py` script will explicitly populate `original_dataset_name` from the GBIF API response. `data/climate/` will include a `provenance.yaml` with WorldClim/CMIP6 version tags. |
| **VII. Model Evaluation Transparency** | **PASS** | `metrics/` will contain `model_performance.json` with AUC/TSS, effect sizes, p-values, and seeds for every species/model combination. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-species-distribution-shifts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── occurrence_record.schema.yaml
│   ├── climate_raster.schema.yaml
│   ├── climate_variable.schema.yaml
│   ├── data_sufficiency.schema.yaml
│   ├── model_artifact.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── occurrence.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── config.py            # Configuration (species list, paths, seeds, thresholds)
├── download.py          # Data acquisition (GBIF, WorldClim, CMIP6)
├── preprocess.py        # Cleaning, thinning, feature extraction
├── train.py             # Model training (RF, Bioclim, MaxEnt-style)
├── evaluate.py          # Projection, AUC/TSS calculation, statistical tests
├── utils/
│   ├── spatial.py       # Spatial thinning, block generation
│   ├── gpu_check.py     # CPU/GPU verification (FR-004)
│   └── stats.py         # Bootstrap, multiple-comparison correction
├── versioning.py        # Hash update for Constitution Principle V
└── main.py              # Orchestration script

data/
├── raw/
│   ├── occurrence_1970_2000.csv
│   ├── occurrence_2005_2020.csv
│   └── climate/         # Raster files (GeoTIFF)
├── processed/
│   └── features.csv     # Merged occurrence + climate data
└── metrics/             # Moved from data/metrics/ to align with Principle IV
    └── data_sufficiency.json

metrics/
└── model_performance.json

logs/
└── gpu_check.log
```

**Structure Decision**: Single-project structure selected. The pipeline is linear (Download -> Preprocess -> Train -> Evaluate), making a monolithic `code/` directory with modular scripts the most efficient approach for CI execution. No separate backend/frontend is required as the output is a research artifact (reports/tables), not a user-facing service.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Hierarchical Bootstrap** | FR-010 requires accounting for dependence structure in `delta_Suitability` across species. | Standard t-tests assume independence between species, which is violated by shared environmental variables and phylogenetic relationships. |
| **Spatial Block CV** | FR-007 requires spatial independence to avoid overfitting to spatial autocorrelation. | Random K-fold CV leaks spatial information, inflating AUC estimates artificially high. |
| **CPU-Only Constraint** | Compute budget is limited to GitHub Actions free tier (no GPU). | GPU-accelerated libraries (e.g., `xgboost` with CUDA) are not permitted; `scikit-learn` CPU backends are the only viable option for reproducibility on the target runner. |
| **Data Sufficiency Flag** | FR-006/FR-011 require statistical power validation (n >= 100). | Blindly training on sparse data leads to unstable models and meaningless AUC scores; the flag prevents reporting unreliable results. |
| **Temporal Mismatch Resolution** | The original spec's "2050 projection vs 2005-2020 reality" comparison was invalid. | We now compare model outputs at the *same locations* under different climate scenarios (2005-2020 vs 2050), calculating the difference in mean suitability (delta_Suitability) rather than AUC against future ground truth. |
| **Data Sufficiency Schema** | FR-006 requires logging specific counts for flagged species. | Referenced `contracts/data_sufficiency.schema.yaml` to ensure the flag includes the exact `recordCount` for `INSUFFICIENT_DATA` species. |

## Implementation Phases

### Phase 0: Data Acquisition (FR-001, FR-002, FR-014)
1.  **Download Historical Occurrences**: Fetch 1970-2000 records via GBIF API. Filter for breeding season. Save to `data/raw/occurrence_1970_2000.csv`.
2.  **Download Recent Occurrences**: Fetch 2005-2020 records via GBIF API. Save to `data/raw/occurrence_2005_2020.csv`.
3.  **Download Climate Rasters**:
    -   **Historical**: Download WorldClim (Bio1-Bio19) for 1970-2000.
    -   **Future**: Download WorldClim CMIP (SSP2-4.5) for 2050 (2041-2060) using specific `wget` patterns.
    -   **Validation**: Ensure all 19 variables are present for every record.
4.  **Metadata**: Populate `original_dataset_name` and `download_timestamp` columns in CSVs. The CSVs will conform to the Darwin Core (DwC-A) standard or explicitly map to the GBIF API schema version used.

### Phase 1: Preprocessing (FR-003, FR-014)
1.  **Spatial Thinning**: Apply spatial thinning using the **dynamic 95th percentile of nearest-neighbor distances** as the default threshold. If calculation fails (< 3 points), fall back to a fixed 10km threshold.
2.  **Climate Extraction**: Sample WorldClim rasters at occurrence coordinates. Impute missing values via nearest neighbor or exclude.
3.  **Data Sufficiency Check**: Count records per species. If `count < 100`, flag as `INSUFFICIENT_DATA`. Log the **specific count** for *every* species (including flagged ones) in `metrics/data_sufficiency.json` (Schema: `contracts/data_sufficiency.schema.yaml`).

### Phase 2: Power Analysis Gate (FR-011)
1.  **Calculate Power**: Perform a one-sample proportion test (alpha=0.05) to detect effect size `Cohen's h = 0.50` (source: Wikipedia). This compares the proportion of 'suitable' predictions (suitability > 0.5) against a null expectation of 0.5.
2.  **Gate**: If calculated power < 0.80 for a species, flag it as `INSUFFICIENT_DATA` and exclude from aggregation. Log the **power value** and the **record count** in `metrics/data_sufficiency.json`.

### Phase 3: Model Training (FR-004, FR-007)
1.  **GPU Check**: Run `code/utils/gpu_check.py`. If `torch.cuda.is_available()` is True, exit with code 1 and log to `logs/gpu_check.log`.
2.  **Spatial Block Generation**: Divide the study area bounding box into an equidistant grid, forming K=5 contiguous blocks. Rotate the held-out block index for each fold to ensure spatial independence.
3.  **Null Model**: Train a null model (predicting mean prevalence) to establish a baseline AUC (SC-001).
4.  **Train Models**: Train RF, Bioclim, and MaxEnt-style models using spatial block CV.

### Phase 4: Evaluation & Projection (FR-005, FR-009, FR-010)
1.  **Historical Validation**: Evaluate models on 2005-2020 occurrences using **2005-2020 climate**. Calculate AUC/TSS.
2.  **Future Projection**: Project models to **2050 climate** at the **same 2005-2020 occurrence locations**. Calculate suitability scores.
3.  **Niche Stability Metric**: Calculate `delta_Suitability` = (Mean Suitability @ 2050 Climate) - (Mean Suitability @ 2005-2020 Climate). This measures the change in predicted suitability driven solely by the climate variable shift.
4.  **Threshold Sweep**: Iterate through the exact threshold set defined by absolute differences including small increments from baseline 0.50, resulting in thresholds near 0.50. The summary table will explicitly report the **delta values** {0.01, 0.05, 0.10} and the corresponding rates.
5.  **Statistical Testing**:
    -   **Hierarchical Bootstrap**: Resample Species (Level 1) -> Resample Spatial Blocks (Level 2) within species. **Target Metric**: `delta_Suitability`.
    -   **Multiple-Comparison Correction**: Apply Benjamini-Hochberg correction for threshold sweeps (FR-005).
6.  **Report Generation**: Programmatically append the exact string "Findings are associational and assume niche stability" to the footer of all generated reports and JSON metadata files.

## Success Criteria

- **SC-001**: Predictive performance (AUC) measured against null model baseline.
- **SC-002**: Total compute time < 360 minutes.
- **SC-003**: Sensitivity analysis results reported in a summary table across the swept threshold set {0.01, 0.05, 0.10} (absolute differences from 0.50), explicitly listing the delta values and corresponding rates.
