# Implementation Plan: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Branch**: `001-predict-cognitive-load-eeg` | **Date**: 2023-10-27 | **Spec**: `specs/001-predicting-cognitive-load-eeg/spec.md`

## Summary

This project implements a computational pipeline to predict cognitive load from EEG spectral power changes during naturalistic viewing using the OpenNeuro ds000246 dataset. The approach involves downloading raw EEG and behavioral data, preprocessing with MNE-Python (bandpass filtering, downsampling, ICA artifact removal), extracting theta and alpha band power features, generating a cognitive load proxy from gaze variance, and training a Ridge Regression model with Leave-One-Subject-Out (LOSO) cross-validation. A critical addition is the extraction of video-level stimulus features (luminance, cut rate) to control for confounds. All operations are constrained to run on GitHub Actions free-tier runners (CPU-only, ≤7GB RAM, ≤6h runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: mne, pandas, numpy, scikit-learn, pyyaml, requests, tqdm, opencv-python, jsonschema  
**Storage**: Local filesystem (temporary artifacts), GitHub Actions cache for intermediate data  
**Testing**: pytest (unit tests for data loading, feature extraction, model evaluation, contract validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: ≤7 GB RAM peak, ≤6 hours total runtime  
**Constraints**: CPU-only execution, no GPU, no deep learning training, memory-efficient chunked data loading  
**Scale/Scope**: Single dataset (OpenNeuro ds), ~10-20 subjects, ~1000 epochs total

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: ✅ Plan includes pinned dependencies, random seeds, and deterministic data fetching from canonical OpenNeuro source.
- **II. Verified Accuracy**: ✅ All dataset citations reference verified URLs from the "# Verified datasets" block; no fabricated URLs.
- **III. Data Hygiene**: ✅ Plan mandates checksumming of downloaded data in `data/manifest.json`, no in-place modifications, and derivation tracking via versioned artifacts.
- **IV. Single Source of Truth**: ✅ All metrics and figures will trace to `data/` artifacts and `code/` execution blocks.
- **V. Versioning Discipline**: ✅ Content hashes for all raw and processed artifacts recorded in `data/manifest.json`; `pipeline_config.yaml` versioned alongside code.
- **VI. Public Dataset Integrity**: ✅ OpenNeuro ds000246 identifier and version recorded in `data/manifest.json`; checksums verified.
- **VII. Signal-Processing Pipeline Transparency**: ✅ All preprocessing parameters (filter ranges, sampling rate, ICA components) codified in `pipeline_config.yaml`.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-cognitive-load-eeg/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── eeg-epoch.schema.yaml
    ├── cognitive-load-label.schema.yaml
    └── spectral-feature-vector.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-295-predicting-cognitive-load-eeg/
├── data/
│   ├── raw/              # Downloaded OpenNeuro ds000246
│   ├── processed/        # Cleaned epochs, feature matrices
│   └── manifest.json     # Dataset version, checksums for ALL artifacts
├── code/
│   ├── __init__.py
│   ├── pipeline_config.yaml
│   ├── validate_contracts.py  # Contract validation logic
│   ├── download_data.py
│   ├── preprocess_eeg.py
│   ├── compute_stimulus_features.py  # NEW: Video feature extraction
│   ├── extract_features.py
│   ├── train_model.py
│   └── evaluate_results.py
├── tests/
│   ├── test_preprocess.py
│   ├── test_features.py
│   ├── test_model.py
│   └── test_contracts.py  # Tests for contract validation
└── requirements.txt
```

**Structure Decision**: Single project structure selected for computational research pipeline; all code, data, and tests organized under `projects/PROJ-295-predicting-cognitive-load-eeg/` to ensure reproducibility and CI compatibility.

## Complexity Tracking

> **N/A** — No Constitution Check violations requiring justification.

## Contract Validation Flow

To ensure the contracts defined in `contracts/` are exercised, the following flow is implemented:

1. **Pipeline Integration**: Each data-producing script (`preprocess_eeg.py`, `extract_features.py`, `compute_stimulus_features.py`) imports the `validate_contracts.py` module.
2. **Validation Logic**: Before saving any artifact (e.g., epochs, features, labels), the script constructs the data structure and passes it to `validate_contracts.py`. This module uses the `jsonschema` library to validate the structure against the corresponding schema file (e.g., `eeg-epoch.schema.yaml`).
3. **Failure Handling**: If validation fails, the script raises a `ValidationError` and halts execution, logging the specific field that failed. This prevents invalid data from entering the pipeline.
4. **Testing**: The `tests/test_contracts.py` file contains unit tests that verify the `validate_contracts.py` module correctly accepts valid data and rejects invalid data according to the schemas.

This ensures that the contracts are not just documentation but active gates in the data pipeline.

## Computational Feasibility & Risk Mitigation

- **Memory**: Chunked loading strategy for datasets >7 GB; ICA and PSD computed on downsampled data to stay within 7 GB RAM.
- **Runtime**: Downsampled data (250 Hz) and CPU-tractable methods (Ridge, ICA, Welch) ensure ≤6 hours total runtime. Video feature extraction is optimized to run in chunks.
- **No GPU required**: All libraries (mne, scikit-learn, opencv-python) have CPU wheels; no CUDA/mixed-precision dependencies.
- **Risk**: Video processing may be slow. **Mitigation**: Downsample video frames for feature extraction (e.g., process every 5th frame) if necessary to meet time limits.
- **Risk**: Small sample size (N~-20). **Mitigation**: Use Leave-One-Subject-Out (LOSO) CV and bootstrapped confidence intervals to maximize power and assess stability.