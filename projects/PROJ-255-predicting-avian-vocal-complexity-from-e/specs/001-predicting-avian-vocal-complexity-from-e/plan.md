# Implementation Plan: Predicting Avian Vocal Complexity from Environmental Noise Levels

**Branch**: `001-predict-avian-vocal-complexity` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predict-avian-vocal-complexity/spec.md`

## Summary

This project implements a computational pipeline to test the hypothesis that ambient environmental noise levels (dB(A)) are negatively associated with avian vocal complexity (syllable count, duration, bandwidth, spectral entropy). The system acquires audio metadata and files from Xeno-canto, assigns ambient noise levels via the verified `noise-map/global-soundscapes` dataset (with nearest-neighbor interpolation fallback), extracts acoustic features using `librosa`, and fits linear mixed-effects models (LMM) with species and location as random effects. The pipeline includes rigorous data hygiene, sensitivity analysis on SNR thresholds, and multiple-comparison correction for hypothesis testing, all designed to run on CPU-first infrastructure.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `librosa` (audio feature extraction), `statsmodels` (LMM), `pandas`, `scikit-learn` (LOSO CV), `requests`, `datasets` (HuggingFace), `pyyaml`, `pytest`
**Storage**: Local file system (`data/raw`, `data/interim`, `data/processed`), CSV/Parquet formats
**Testing**: `pytest` (unit, contract, integration)
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7GB RAM)
**Project Type**: Data Science / Computational Biology Pipeline
**Performance Goals**: Process 100s of recordings in < 6 hours; fit LMM on < 5GB dataset
**Constraints**: No local GPU; memory < 7GB; disk < 14GB; no unverified external data sources; strict reproducibility (random seeds).
**Scale/Scope**: Target a diverse set of species, a substantial number of recordings total.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Mitigation |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_seed` in `config.yaml`; `requirements.txt` pins versions; data fetched from canonical URLs (Xeno-canto, NoiseMap, OpenLandMap). |
| **II. Verified Accuracy** | **PASS** | Citations restricted to verified sources. Primary noise source is `noise-map/global-soundscapes` (verified). Interpolation is a gap-filler, not a primary source. |
| **III. Data Hygiene** | **PASS** | Pipeline writes to new files (`data/interim/*`, `data/processed/*`); raw data preserved; checksums recorded in state YAML. |
| **IV. Single Source of Truth** | **PASS** | `data/processed/final_dataset.csv` is the sole source for modeling; `model_results.csv` traces back to this. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes updated in state YAML upon write; `plan.md` versioned with spec. |
| **VI. Acoustic Signal Integrity** | **PASS** | SNR > 10 dB filter implemented; resampling to a standard audio frequency enforced; logging of excluded records. |
| **VII. Statistical Modeling Rigor** | **PASS** | LMM with species/location random intercepts; LOSO Fixed-Effect Stability Check; FDR correction; effect size (Cohen's d) reporting; collinearity diagnostics. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-avian-vocal-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_results.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
src/
├── config/
│   ├── config.yaml      # Global config (seeds, paths, thresholds)
│   └── logging_config.py
├── data/
│   ├── acquisition.py   # Xeno-canto & NoiseMap fetchers
│   ├── extraction.py    # librosa feature extraction
│   ├── preprocessing.py # Filtering, interpolation, merging
│   └── validation.py    # Schema validation logic
├── models/
│   ├── lmm.py           # Linear Mixed Effects fitting & LOSO
│   └── diagnostics.py   # Residual plots, QQ plots
├── viz/
│   ├── plots.py         # Scatter, heatmap generation
│   └── report.py        # Summary report generation
├── utils/
│   ├── io.py            # CSV/Parquet I/O helpers
│   └── math.py          # SNR calc, interpolation logic
└── main.py              # Orchestrator script

tests/
├── unit/
│   ├── test_config_logging.py  # Addresses T009
│   ├── test_acquisition.py
│   └── test_extraction.py
├── contract/
│   ├── test_dataset_schema.py  # Addresses T006/T007/T020
│   └── test_output_schema.py   # Addresses T022 (numeric validation)
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single-project structure selected for data science workflow. `src/` contains modular scripts for acquisition, extraction, modeling, and viz. `tests/` mirrors `src/` to ensure contract testing and unit tests cover all logic, specifically addressing the missing test artifacts (T009, T022) by including `test_config_logging.py` and completing `test_output_schema.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Phase Execution Strategy

### Phase 0: Research & Data Strategy
*Goal: Verify data availability and define the statistical approach.*
1.  **Data Verification**: Confirm Xeno-canto API access, `noise-map/global-soundscapes` availability, and OpenLandMap availability.
2.  **Statistical Design**: Define the LMM formula: `Complexity ~ Noise + Habitat + (1|Species) + (1|Location)`.
3.  **Power & Attenuation Analysis (Task 0.4)**: Calculate the attenuation factor due to noise measurement error (interpolation). Determine required sample size N = N_ideal / (1 - λ²) where λ is reliability. Ensure N meets the study's power requirements given the expected effect size attenuation.
4.  **Compute Check**: Verify `librosa` and `statsmodels` run within 7GB RAM on CPU.

### Phase 1: Data Model & Contracts
*Goal: Define schemas and ensure data hygiene.*
1.  **Schema Definition**: Create `dataset.schema.yaml` (Input), `model_results.schema.yaml` (Output), and `output.schema.yaml` (General).
2.  **Data Model**: Define `Recording`, `NoiseProfile`, `VocalMetric`, `Habitat` entities and log schemas (`noise_interpolation_log.csv`, `species_filtered.csv`, `validation_log.csv`).
3.  **Quickstart**: Document how to run the pipeline end-to-end.

### Phase 2: Implementation & Tasks
*Goal: Execute the pipeline and generate results.*
1.  **Task 2.0: Unit Tests for Config/Logging**: Implement `tests/unit/test_config_logging.py` to verify `config.yaml` loading and logging initialization. (Addresses T009).
2.  **Task 2.1: Audio Feature Extraction**: Implement `src/data/extraction.py` to extract syllable count, duration, bandwidth, entropy. Handle corrupted files by skipping and logging. (Addresses T019).
3.  **Task 2.2: Noise Mapping & Interpolation**: Implement `src/data/acquisition.py` to fetch noise levels from `noise-map/global-soundscapes`. Generate `data/interim/noise_mapped.csv` and `data/interim/noise_interpolation_log.csv` (logging recording_id, source_distance_km, interpolated_value_db, neighbor_count). (Addresses T015, FR-009).
4.  **Task 2.3: Preprocessing & Validation**: Implement `src/data/preprocessing.py` to merge data, filter SNR, validate against schema, and generate:
    *   `data/interim/filtered_records.csv` (columns: `recording_id`, `filter_reason`, `species_id`, `location_id`).
    *   `data/interim/species_filtered.csv` (columns: `species_id`, `location_id`, `recording_count`, `reason`).
    *   `data/interim/validation_log.csv` (columns: `record_id`, `validation_error`, `schema_name`).
    *   `data/processed/final_dataset.csv` (Addresses T015c, T018b, T020).
5.  **Task 2.4: Species Filtering**: Implement logic to filter species with <5 recordings per location and generate `data/interim/species_filtered.csv`.
6.  **Task 2.5: Modeling & Stability Check**: Fit LMM. Perform Leave-One-Species-Out Fixed-Effect Stability Check (fit on train, predict on holdout with random effect=0). Run collinearity diagnostics (VIF).
7.  **Task 2.6: Sensitivity Analysis & Constraint Check**: Sweep SNR thresholds (low, medium, high). Calculate variation in correlation rates. Generate `sensitivity_report.json` with pass/fail status for ≤15% variation constraint.
8.  **Task 2.7: Contract Testing**: Implement `tests/contract/test_output_schema.py` with full `test_numeric_columns_are_valid` logic. Run against `data/processed/model_results.csv`. (Addresses T022, T007).

### Phase 3: Validation & Reporting
*Goal: Verify against acceptance criteria.*
1.  **Contract Tests**: Run `pytest` against schemas.
2.  **Reproducibility Check**: Re-run pipeline with new seed to ensure stability.
3.  **Final Report**: Compile findings into `paper/` draft.

### Phase 4: Cleanup
*Goal: Ensure repository hygiene.*
1.  Remove intermediate files not required for reproducibility.
2.  Update state YAML with artifact hashes.