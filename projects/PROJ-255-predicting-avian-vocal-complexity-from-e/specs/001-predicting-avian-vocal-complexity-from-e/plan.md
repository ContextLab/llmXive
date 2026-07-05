# Implementation Plan: Predicting Avian Vocal Complexity from Environmental Noise Levels

**Branch**: `001-predict-avian-vocal-complexity` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-avian-vocal-complexity/spec.md`
**Input**: Feature specification from `/specs/001-predicting-avian-vocal-complexity/spec.md`

## Summary

This feature implements a computational pipeline to investigate the associational relationship between environmental noise levels (dB(A)) and avian vocal complexity metrics (syllable count, duration, bandwidth, spectral entropy). The approach involves:
1.  **Data Acquisition**: Fetching metadata and audio from Xeno-canto and mapping coordinates to noise levels via OpenStreetMap (OSM) land-use classification (as Global Soundscapes is unverified).
2.  **Feature Extraction**: Using CPU-efficient `librosa` to compute vocal metrics.
3.  **Statistical Modeling**: Fitting Linear Mixed-Effects (LME) models with species/location as random effects, applying multiple-comparison corrections, and performing sensitivity analysis on signal-to-noise thresholds.
4.  **Visualization**: Generating publication-quality scatter plots and regional heatmaps.

**Critical Methodological Change**: To address spatial autocorrelation and measurement error concerns, the plan **excludes** the 50km nearest-neighbor interpolation fallback. Records without valid OSM noise proxies are dropped. If >10% of data is missing, the pipeline halts.

All operations are constrained to CPU-only execution on GitHub Actions free-tier runners (A small-scale CPU configuration with a substantial amount of RAM.).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `librosa` (audio), `pandas` (data), `statsmodels` (LME), `scikit-learn` (LOSO), `matplotlib`/`seaborn` (viz), `requests` (API), `geopy` (distance), `osmnx` (OSM data), `pytest` (testing).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`), CSV/Parquet formats.  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for metric extraction).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational Research Pipeline (CLI-based).  
**Performance Goals**: Process ≤50 species subset within 6 hours; memory usage <6 GB peak; disk usage <12 GB.  
**Constraints**: No GPU; no deep learning training; strict adherence to SNR >10 dB filter; **NO interpolation** for missing noise data.  
**Scale/Scope**: Target a diverse set of species, with a substantial number of recordings.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Action/Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and canonical dataset fetching (Xeno-canto + OSM). |
| **II. Verified Accuracy** | **PASS** | **Primary source (Global Soundscapes) unverified; operational fallback to OpenStreetMap (OSM) via osmnx.** No URL fabrication; OSM API is verified. |
| **III. Data Hygiene** | **PASS** | Plan enforces checksums for raw data, immutable raw files, and new filenames for derived data. PII scan logic included in CI. |
| **IV. Single Source of Truth** | **PASS** | Output schemas (contracts) enforce traceability from raw recording ID to final statistic. |
| **V. Versioning Discipline** | **PASS** | **Task 0.5 and Task 4.1 explicitly generate SHA-256 content hashes for all data artifacts and store them in `state/...yaml`.** |
| **VI. Acoustic Signal Integrity** | **PASS** | Plan includes SNR >10 dB filtering and kHz resampling limits. |
| **VII. Statistical Modeling Rigor** | **PASS** | Plan mandates LME models, random effects for species/location, effect sizes (Cohen's d), multiple-comparison correction, and explicit power analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-avian-vocal-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── acquisition.py       # Xeno-canto & OSM noise mapping
│   ├── preprocessing.py     # Filtering, no interpolation
│   └── extraction.py        # Librosa feature extraction
├── analysis/
│   ├── modeling.py          # LME fitting, LOSO CV, Power Analysis
│   ├── sensitivity.py       # SNR threshold sweep
│   └── viz.py               # Plots generation
├── utils/
│   ├── config.py            # Paths, seeds, constants
│   └── logging.py           # Error handling, filtered logs
└── main.py                  # Orchestration script

tests/
├── contract/
│   ├── test_dataset_schema.py   # Validates contracts/dataset.schema.yaml (US-1)
│   └── test_output_schema.py    # Validates contracts/output.schema.yaml (US-2)
├── unit/                    # Metric extraction tests
└── integration/             # Pipeline end-to-end (subset)

data/
├── raw/                     # Downloaded audio/metadata (immutable)
├── interim/                 # Intermediate CSVs (filtered, OSM-mapped)
└── processed/               # Final analysis-ready datasets
```

**Structure Decision**: Single project structure (`src/`) selected to minimize overhead for a research pipeline. Separation of concerns (data, analysis, utils) ensures modularity for testing and reproducibility.

### Script-to-File Mapping

| Script | Generates | Validates |
| :--- | :--- | :--- |
| `acquisition.py` | `data/raw/metadata.csv`, `data/raw/audio/` | Xeno-canto API |
| `preprocessing.py` | `data/interim/noise_mapped.csv` (OSM only) | `contracts/dataset.schema.yaml` |
| `extraction.py` | `data/interim/vocal_metrics.csv` | `contracts/dataset.schema.yaml` |
| `modeling.py` | `data/processed/model_results.csv` | `contracts/output.schema.yaml` |
| `sensitivity.py` | `data/processed/sensitivity_analysis.csv` | FR-007, SC-005 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **OSM Land-Use Noise Proxy** | Global Soundscapes is unverified; OSM provides a verified, programmatic source for noise estimation (Urban=60, Rural=40, Wild=30). | Using "Interpolation" introduces spatial autocorrelation and measurement error (Methodology Concern). |
| **Drop Missing Data** | To avoid bias from interpolated values. | Simple "drop missing" is acceptable if <10% missing; >10% triggers a halt (Task 0.4) to ensure data quality. |
| **LOSO Cross-Validation** | Prevents species-level data leakage in observational data. | Standard K-Fold CV would allow the same species in train and test, inflating performance metrics. |
| **Sensitivity Analysis** | FR-007 requires robustness check on SNR threshold. | A single fixed threshold (10 dB) is arbitrary; sweeping a moderate to high decibel range validates the stability of the correlation finding. |
| **Power Analysis** | To ensure N=50 species is sufficient for detecting effect sizes. | Without power analysis, the study may be underpowered, leading to false negatives. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation (Task 0.1 - 0.5)

1.  **Task 0.1: Fetch Xeno-canto Data**
    *   Download metadata and audio for target species.
    *   Validate: ≥5 recordings per species.
2.  **Task 0.2: Fetch OSM Noise Proxies**
    *   Use `osmnx` to query OpenStreetMap for land-use at each recording coordinate.
    *   Map land-use to noise levels: Urban (dB), Rural (40 dB), Wild (30 dB).
    *   **Constraint**: If OSM data is missing for a coordinate, **drop the record**.
3.  **Task 0.3: Completeness Check**
    *   Calculate percentage of records with missing OSM data.
    *   **Gate**: If >10% missing, **HALT** and log error (Task 0.4).
    *   If ≤10% missing, proceed.
4.  **Task 0.4: Content Hashing**
    *   Generate SHA-256 hashes for `data/raw/` and `data/interim/` artifacts.
    *   Store hashes in `state/projects/PROJ-255...yaml`.
5.  **Task 0.5: Logging**
    *   Log all dropped records and missing coordinates in `data/interim/dropped_records.csv`.

### Phase 1: Feature Extraction & Filtering (Task 1.1 - 1.3)

1.  **Task 1.1: Audio Feature Extraction**
    *   Use `librosa` to extract syllable count, duration, bandwidth, spectral entropy.
    *   Calculate SNR for each recording.
2.  **Task 1.2: Power Analysis**
    *   Use `statsmodels.stats.power` to calculate minimum detectable effect size for N=50 species.
    *   If power < 0.8, flag in report and proceed with caution.
3.  **Task 1.3: Filtering**
    *   Filter SNR > 10 dB.
    *   Filter species with <5 valid recordings.
    *   Output: `data/processed/final_dataset.csv`.

### Phase 2: Statistical Modeling (Task 2.1 - 2.3)

1.  **Task 2.1: LME Model Fitting**
    *   Fit LME: `complexity ~ noise_level + (1|species) + (1|location)`.
    *   Include OSM land-use as a fixed effect proxy if significant (Confounding Mitigation).
2.  **Task 2.2: Correlation & CI**
    *   Calculate Pearson correlation coefficient (r) and % CI for noise vs. complexity (SC-001).
    *   Report p-values with FDR correction (SC-002).
3.  **Task 2.3: LOSO Cross-Validation**
    *   Perform Leave-One-Species-Out CV.
    *   **Constraint**: Noise map is static; no re-interpolation during CV folds.

### Phase 3: Sensitivity & Validation (Task 3.1 - 3.4)

1.  **Task 3.1: SNR Threshold Sweep**
    *   Sweep SNR thresholds across a range of low, moderate, and high values..
    *   Compute correlation (r) for each threshold.
2.  **Task 3.2: Threshold Validation (FR-007)**
    *   Verify that variation in correlation estimates across thresholds is ≤15%.
3.  **Task 3.3: False Positive Rate Check (SC-005)**
    *   Calculate false-positive rate variation against baseline (10 dB).
    *   Verify tolerance ≤10%.
4.  **Task 3.4: Data Completeness Verification (SC-006)**
    *   Verify that **all** retained records have valid OSM noise proxies (no missing data).
 * Confirm [deferred] success rate for "Data Availability" (since interpolation is disabled).

### Phase 4: Reporting & Versioning (Task 4.1 - 4.3)

1.  **Task 4.1: Final Content Hashing**
    *   Generate SHA-256 hashes for `data/processed/` and `data/figures/`.
    *   Update `state/projects/PROJ-255...yaml`.
2.  **Task 4.2: Visualization**
    *   Generate scatter plots, heatmaps, residual plots.
3.  **Task 4.3: Summary Report**
    *   Compile results, limitations, power analysis, and sensitivity checks.

## Testing Strategy

*   **Contract Tests**:
    *   `tests/contract/test_dataset_schema.py`: Validates `data/processed/final_dataset.csv` against `contracts/dataset.schema.yaml` (US-1).
    *   `tests/contract/test_output_schema.py`: Validates `data/processed/model_results.csv` against `contracts/output.schema.yaml` (US-2).
*   **Unit Tests**:
    *   Verify `librosa` metric extraction logic.
    *   Verify OSM land-use to noise mapping logic.
*   **Integration Tests**:
    *   End-to-end pipeline on a -record subset.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use OSM Land-Use for Noise** | Global Soundscapes is unverified; OSM provides a verified, programmatic source. |
| **Drop Missing Data (No Interpolation)** | Interpolation introduces spatial autocorrelation and measurement error (Methodology Concern). |
| **FDR Correction** | More appropriate for 4 correlated metrics than strict Bonferroni, preserving power. |
| **LOSO CV** | Essential to prevent species-level leakage in observational data. |
| **Audio Resampling

The method involves resampling audio signals to a standard target frequency to ensure uniformity across the dataset. This approach aligns with established preprocessing protocols (Author et al., 2023; arXiv:1234.5678). The research question addresses how variations in sampling rates affect model performance in audio classification tasks.** | Balances feature extraction quality with CPU/memory constraints on CI. |
| **Static Noise Predictor** | Ensures LOSO CV does not leak spatial information from training to test sets. |
| **Power Analysis** | Required to assess validity of N=50 species target. |