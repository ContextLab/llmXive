# Implementation Plan: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

**Branch**: `001-pupil-dilation-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-pupil-dilation-cognitive-load/spec.md`
**Input**: Feature specification from `/specs/001-pupil-dilation-cognitive-load/spec.md`

## Summary

This project investigates the quantitative relationship between task-evoked pupil dilation and cognitive load during visual search tasks. The technical approach involves ingesting raw eye-tracking data from a **verified** eye-tracking dataset, preprocessing signals (Butterworth filtering, blink interpolation), computing trial-wise load proxies (search time, fixation count, target salience), and performing statistical analysis (Pearson/Spearman correlations with FDR correction, Linear Mixed-Effects models). Finally, a sliding-window logistic regression classifier will be trained to simulate real-time search-time estimation.

**Critical Scope Note**: The pipeline **MUST** halt with a clear error (Exit Code 1) if no verified eye-tracking dataset is found in the `# Verified datasets` block. No synthetic data is used for empirical analysis. Synthetic data is restricted to unit testing only, with hashes recorded in `state/test_artifacts.yaml`.

**Spec Contradiction Flag**: The source spec (`spec.md`) cites OpenNeuro ds001734 and ds002642 as eye-tracking datasets. **These are fMRI datasets.** The pipeline explicitly rejects these IDs. If these are the only sources available, the pipeline halts, and a note is generated to flag the spec for correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `mne` (for signal processing), `pyyaml`, `requests`, `datasets` (HuggingFace), `opencv-python-headless` (for image processing if needed), `matplotlib`, `seaborn`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`, `state`). No external database.  
**Testing**: `pytest` (unit and integration tests for pipeline steps and contract validation).  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline (preprocessing → modeling → classification) within 6 hours on 2 CPU cores, ≤ 6 GB RAM peak usage.  
**Constraints**: No GPU. No deep learning training from scratch. Data must be subsampled if necessary to fit memory.  
**Scale/Scope**: Single dataset processing (Verified Eye-Tracking Source), trial-level analysis (thousands of trials), statistical inference.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `config.yaml`. `requirements.txt` pins versions. Data fetched from canonical verified sources. Scripts runnable end-to-end. |
| **II. Verified Accuracy** | **PASS (Hard Gate)** | **Hard Gate**: The pipeline checks the `# Verified datasets` block for a valid eye-tracking source. If none exists, or if the only sources are invalid (e.g., ds001734/2642), the pipeline **HALTS** with Exit Code 1. No unverified URLs or synthetic data are used for empirical results. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` unaltered. Checksums recorded in `state/project_state.yaml`. Derivatives in `data/processed/`. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All statistics derived from generated CSVs (`results/*.csv`). No hand-typed numbers in reports. MNE objects converted to flat CSVs immediately. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes recorded in `state/project_state.yaml` for empirical data. Test-only synthetic data hashes recorded in `state/test_artifacts.yaml`. |
| **VI. Eye‑Tracking Data Integrity** | **PASS** | Raw files preserved. Preprocessing (filtering, interpolation) creates new files in `data/processed/` with provenance metadata. |
| **VII. Real‑Time Load Classification Validation** | **PASS** | Classifier evaluated on held-out set (stratified by subject). Thresholds defined in `config.yaml`. Metrics logged with seeds. Explicit labeling of ground truth source. |

## Project Structure

### Documentation (this feature)

```text
specs/001-pupil-dilation-cognitive-load/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-174-investigating-the-relationship-between-p/code/
├── config.yaml          # Configuration: seeds, thresholds, filter params
├── requirements.txt     # Pinned dependencies
├── main.py              # Orchestration script
├── preprocessing/
│   ├── __init__.py
│   ├── load_data.py     # Ingest raw eye-tracking files (Verified Source)
│   ├── filter.py        # Butterworth filter, blink interpolation
│   ├── temporal_align.py # Time-lagging and event-related averaging
│   ├── feature_extract.py # Compute load proxies (search time, salience, fixations)
│   └── mne_to_csv.py    # Convert MNE objects to flat CSV schema
├── analysis/
│   ├── __init__.py
│   ├── correlations.py  # Pearson/Spearman correlations + FDR correction
│   ├── lme_model.py     # Linear Mixed-Effects model fitting + VIF check
│   └── sensitivity.py   # Threshold sensitivity analysis
├── classification/
│   ├── __init__.py
│   ├── sliding_window.py # Sliding window feature extraction
│   ├── classifier.py     # Logistic regression training & evaluation
│   └── metrics.py        # Accuracy, AUC, confusion matrix
├── utils/
│   ├── __init__.py
│   ├── logging.py        # Centralized logging for exclusions
│   └── checksums.py      # Artifact hashing (Empirical & Test)
├── tests/
│   ├── test_preprocessing.py
│   ├── test_analysis.py
│   └── test_classification.py
│
├── generate_synthetic_test_data.py # ONLY for unit tests
└── verify_data_availability.py     # Hard gate script

data/
├── raw/                   # Raw eye-tracking files (Verified Source)
├── processed/             # Cleaned CSVs, feature tables
└── external/              # Stimulus images (if downloaded)

results/
├── correlations.csv
├── model_summary.csv
├── classification_metrics.csv
├── quality_report.csv
└── sensitivity_analysis.csv

state/
├── project_state.yaml     # Artifact hashes for empirical data
└── test_artifacts.yaml    # Artifact hashes for synthetic test data
```

**Structure Decision**: Single project structure (Option 1) chosen to align with the CLI/data-pipeline nature of the spec. Modular separation of `preprocessing`, `analysis`, and `classification` ensures testability and adherence to the Single Source of Truth principle.

## Complexity Tracking

No complexity violations identified. The plan adheres to CPU constraints by:
1.  Using lightweight statistical models (LME, Logistic Regression) instead of deep nets.
2.  Implementing efficient data streaming/subsampling strategies to fit 7GB RAM.
3.  Using `opencv-python-headless` for on-the-fly image processing only if necessary, otherwise relying on metadata.

## Phase Plan & Task Ordering

### Phase 0: Data Verification & Acquisition
1.  **Task**: Run `verify_data_availability.py`.
    *   **Logic**: Check `# Verified datasets` block for an eye-tracking dataset.
    *   **Condition**: If no verified eye-tracking dataset is found, **HALT** with Exit Code 1 and message: "ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed."
    *   **Condition**: If the only available sources are ds001734 or ds002642, **HALT** with Exit Code 1 and message: "ERROR: Spec cites invalid fMRI datasets (ds001734/2642). Pipeline cannot proceed. Spec requires correction."
    *   **Condition**: If found, download to `data/raw/`.
2.  **Task**: Generate synthetic data **ONLY** for unit tests.
    *   **Logic**: Run `generate_synthetic_test_data.py` if `--test-mode` flag is present.
    *   **Output**: Hash recorded in `state/test_artifacts.yaml`.

### Phase 1: Preprocessing & Feature Extraction
1.  **Task**: Ingest and Clean.
    *   **Logic**: Convert raw files to uniform CSV (`timestamp`, `x`, `y`, `pupil_diameter`).
    *   **Constraint**: Use `mne` for filtering, but **immediately convert** to flat CSV to maintain Single Source of Truth.
    *   **Filter**: Butterworth th order, low-pass filter.
    *   **Blink**: Interpolate gaps < 200ms; exclude trials with > 30% loss.
    *   **Timestamp**: Validate monotonicity; exclude non-monotonic trials.
2.  **Task**: Temporal Alignment.
    *   **Logic**: Apply time-lag shifts (s, and other relevant intervals) to pupil signal relative to search events to account for physiological latency.
    *   **Output**: Time-lagged pupil signals for each trial.
3.  **Task**: MNE-to-Feature Conversion.
    *   **Logic**: Convert MNE time-series objects to the 'Processed Trial Data' schema (aggregated features like `pupil_peak`, `pupil_mean`). This bridges the gap between raw time-series and analysis-ready features.
4.  **Task**: Compute Load Proxies.
    *   **Search Time**: Extract from metadata.
    *   **Fixation Count**: Extract from metadata.
    *   **Target Salience**: Check metadata. If missing, compute via Gabor filters on stimulus images (downsampled to a lower resolution). If images missing, **MARK AS UNFULFILLABLE** and log exclusion reason. Do not treat as 'SKIPPED' success.

### Phase 2: Statistical Analysis
1.  **Task**: Correlation Analysis.
    *   **Logic**: Compute Pearson r (and Spearman rho if linearity fails) between pupil metrics and load proxies.
    *   **Handling Missing Proxy**: If 'target salience' is uncomputable (no images), log row with `pearson_r: null`, `status: UNFULFILLABLE`, and specific error code.
    *   **Correction**: Apply Benjamini-Hochberg FDR to the set of valid tests.
2.  **Task**: LME Modeling.
    *   **Logic**: Fit `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`.
    *   **VIF Check**: Calculate VIF. If > 5, drop highest VIF predictor and refit.
    *   **Missing Salience**: If salience is uncomputable, fit reduced model and log the reduction.
    *   **Output**: Coefficients, SE, p-values, Likelihood Ratio Test.

### Phase 3: Classification & Validation
1.  **Task**: Sliding Window Classification.
    *   **Logic**: Short lookback, small step. Logistic Regression (L2).
    *   **Ground Truth**: Use independent behavioral proxy if available. If not, use median split of search time.
    *   **Critical Logic**: If independent truth is missing, **DISCARD** results from empirical claims. Report as "Pipeline Feasibility Check" only. Do not present as validation of cognitive load.
    *   **Validation**: Stratified hold-out by subject.
2.  **Task**: Sensitivity Analysis.
    *   **Logic**: Sweep thresholds across a range of moderate values.
    *   **Output**: Accuracy, AUC, relative decrease.

### Phase 4: Reporting
1.  **Task**: Generate `results/*.csv` and `state/project_state.yaml`.
    *   **Logic**: Record hashes of all empirical artifacts.
    *   **Constraint**: Ensure `ground_truth_limitation` string is present if independent truth is missing.
    *   **Constraint**: Ensure `status: UNFULFILLABLE` is present if target salience is missing.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **No Verified Eye-Tracking Data** | Pipeline halts with Exit 1. No empirical results generated. |
| **Invalid Spec Datasets (ds001734/2642)** | Pipeline halts with Exit 1. Spec flagged for correction. |
| **Missing Target Salience** | Proxy marked 'UNFULFILLABLE'; model refitted reduced; correlation logged as 'UNFULFILLABLE'. |
| **High Collinearity (VIF > 5)** | Drop predictor, log reduction, refit model. |
| **Insufficient Trials (< 20/subject)** | Aggregate or abort with warning. |
| **Memory Overflow** | Stream data; subsample if necessary; use `dtype` optimization. |

## Compute Feasibility & Constraints

- **Memory**: Data loaded in chunks. `pandas` operations on subsets.
- **CPU**: No GPU. `scipy.signal` for filtering. `statsmodels` for LME (CPU only). `scikit-learn` for logistic regression.
- **Runtime**: Pipeline designed to complete in < 6 hours.
- **Libraries**: `mne`, `statsmodels`, `scikit-learn`, `pandas`, `numpy`. All have CPU wheels.