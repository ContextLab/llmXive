# Implementation Plan: Predicting Plant Disease Severity from Publicly Available Image Data and Meteorological Records

**Branch**: `001-predict-plant-disease-severity` | **Date**: 2026-09-08 | **Spec**: `specs/001-predict-plant-disease-severity/spec.md`
**Input**: Feature specification from `/specs/001-predict-plant-disease-severity/spec.md`

## Summary

This feature implements a computational pipeline to predict plant disease severity by integrating visual features from the PlantVillage dataset with historical meteorological data. The core methodology involves extracting continuous visual severity metrics (lesion area, color index, texture entropy) via OpenCV, linking them to 7-day weather windows via the Open-Meteo API (with a lightweight NOAA GHCN-Daily fallback), and training a two-stage Random Forest model. The first stage predicts raw severity from images using K-Fold Cross-Validation to ensure unbiased residuals; the second predicts these **calibrated residuals** using weather variables to test the hypothesis that environmental context modulates the consistency of visual symptom progression. The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints (limited RAM, 6 hours).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `opencv-python`, `scikit-learn`, `pandas`, `numpy`, `requests`, `datasets` (for HuggingFace loading), `matplotlib`, `seaborn`, `pyyaml`
**Storage**: Local file system (temporary processing), Parquet/CSV for intermediate artifacts, JSON for logs.
**Testing**: `pytest` for unit tests on feature extraction and data linking; integration tests for the full pipeline on a subset.
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)
**Project Type**: Data Science / Computational Research Pipeline
**Performance Goals**: Process full PlantVillage dataset within 6 hours; Peak RAM < 7 GB.
**Constraints**: CPU-only execution; No GPU acceleration; Open-Meteo API rate limits must be respected (batching/backoff); OpenCV segmentation must handle edge cases (missing lesions) gracefully.
**Scale/Scope**: A comprehensive dataset of images (full PlantVillage); Multiple weather variables per image (aggregated 7-day); ~2-stage ML modeling.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-405/.../constitution.md`*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds (`np.random.seed`, `sklearn` `random_state`) will be pinned. `requirements.txt` will be strict. |
| **II. Verified Accuracy** | PASS | All dataset URLs will be taken from the verified list. Open-Meteo/NOAA usage will be logged with timestamps. |
| **III. Data Hygiene** | PASS | Raw PlantVillage zip will be checksummed. Derived weather CSVs will be checksummed. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics (R², MAE, p-values) will be written to a single `results.json` artifact. |
| **V. Versioning Discipline** | PASS | **Explicit Mechanism**: Upon completion of Phase 5, Step 5.2, the `state/*.yaml` file will be updated with SHA-256 hashes for `results.json`, `unified_analysis.csv`, and `model_artifacts.pkl`. This satisfies the requirement that every artifact change updates the state timestamp and hash map. |
| **VI. Environmental Context** | PASS | The plan explicitly includes the 7-day weather window and interaction terms in the augmented model. |
| **VII. Computational Resource Adherence** | PASS | Pipeline uses batched OpenCV and `scikit-learn` (CPU) with memory-mapped data handling where possible. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-severity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── weather.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-405/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, API keys
│   ├── data_ingestion.py      # PlantVillage download, OpenCV feature extraction
│   ├── weather_linker.py      # Open-Meteo API calls, 7-day aggregation, NOAA fallback
│   ├── modeling.py            # Baseline RF (K-Fold), Residual Calibration, Residual RF, Permutation test
│   ├── visualization.py       # Partial dependence plots, sensitivity analysis
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded PlantVillage zip
│   ├── interim/               # Extracted features CSV, Weather CSV
│   └── processed/             # Unified analysis-ready table
├── tests/
│   ├── unit/
│   │   ├── test_feature_extraction.py
│   │   └── test_weather_linker.py
│   └── integration/
│       └── test_full_pipeline.py
└── artifacts/
    └── results.json
```

**Structure Decision**: Single project structure chosen to minimize overhead. Data is processed in a linear pipeline (Ingest -> Link -> Model -> Visualize) stored in `data/` subfolders. `code/` contains modular scripts for each stage.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Two-Stage Modeling** | Required by Spec (US-2) to isolate weather effects on *unexplained* variance. | A single model predicting severity from (Image + Weather) would confound the primary visual signal with the environmental modulation effect, failing to answer the specific research question. |
| **Permutation Test (Feature Shuffle)** | Required by Spec (FR-005) for rigorous significance testing of residuals. | Standard p-values from Random Forest do not test the *difference* in R² against a null distribution generated by breaking the specific link between weather and residuals. |
| **K-Fold Baseline** | Required to ensure residuals are unbiased (methodological rigor). | Training a single baseline model on the full set would introduce systematic bias into the residuals, confounding the second stage. |
| **Residual Calibration** | Required to remove systematic bias from the baseline model (Methodology Panel Concern). | Without calibration, the residuals contain model error, not just biological modulation, confounding the second stage. |
| **7-Day Window** | Required by Spec (US-1) to capture lagged environmental stress. | Using current-day weather ignores the biological latency of lesion development, which is the core of the "modulation" hypothesis. |

## Phases & Steps

### Phase 0: Data Acquisition & Verification
- **Step 0.1**: Download PlantVillage dataset from verified URL (Standard PlantVillage, not VQA). Verify checksum.
- **Step 0.2**: Parse image metadata (filename conventions for location/date).
- **Step 0.3**: Verify Open-Meteo API availability and rate limits.
- **Step 0.4**: **Construct Validity Check**: On a random subset (n=50), compare OpenCV metrics (lesion area) against a small set of expert-labeled severity scores (or simulated ground truth). If correlation < 0.5, flag the study as "Associational Only" and note the limitation in `results.json`.
- **FR-001, FR-002, SC-003** addressed here.

### Phase 1: Feature Extraction & Weather Linking
- **Step 1.1**: Implement OpenCV pipeline to extract lesion area ratio, necrosis color index, texture entropy.
- **Step 1.2**: Handle missing lesions (filter/log) and missing metadata (exclude).
- **Step 1.3**: Fetch 7-day weather history for valid records.
    - **Primary**: Open-Meteo API.
    - **Fallback**: If Open-Meteo fails (timeout/rate-limit), query a **pre-processed NOAA GHCN-Daily station CSV** (subset of a representative global station network, filtered to a manageable data volume) to find the nearest station and interpolate. **If both fail, exclude the record with a specific log flag.** This satisfies FR-002's "or NOAA" requirement without exceeding RAM limits.
- **Step 1.4**: Merge image features and weather data into a unified CSV.
- **FR-001, FR-002, SC-003** addressed here.

### Phase 2: Baseline Modeling & Residual Calculation
- **Step 2.1**: Split data (Train/Test) for final evaluation.
- **Step 2.2**: Train Baseline Random Forest using **K-Fold Cross-Validation** on the Training set to generate **Out-of-Fold (OOF)** predictions for the entire dataset.
- **Step 2.3**: Calculate Raw Residuals = Actual Severity - OOF Prediction.
- **Step 2.4**: **Residual Calibration**: Apply isotonic regression or mean-centering to the Raw Residuals to remove systematic bias (e.g., if the baseline consistently under-predicts high severity). Store the **Calibrated Residuals** as the target for the second stage.
- **FR-003, SC-001** addressed here.

### Phase 3: Augmented Modeling & Hypothesis Testing
- **Step 3.1**: Train Augmented Random Forest (Weather + Interactions -> **Calibrated Residuals**) on the Training set.
- **Step 3.2**: Perform **Feature Permutation Test (1,000 iterations)**:
    - **Null Hypothesis**: Weather features have no predictive power for calibrated residuals.
    - **Method**: Shuffle (permute) the Weather feature columns in the Training set while keeping the Calibrated Residual target fixed. Retrain the Augmented model on shuffled data. Repeat [deferred] times to generate a null distribution of R² scores.
    - **Comparison**: Compare the observed R² (unshuffled) against this null distribution to calculate the p-value.
    - **Output**: Record `p_value`, `iterations`, `null_distribution_mean` matching `model_output.schema.yaml` (specifically the `hypothesis_test` block).
- **FR-004, FR-005, SC-001, SC-004** addressed here.

### Phase 4: Visualization & Sensitivity Analysis
- **Step 4.1**: Generate Partial Dependence Plots (Weather vs. Residuals).
- **Step 4.2**: Perform Sensitivity Analysis (sweep threshold deviations {0.01, 0.05, 0.1}).
- **Step 4.3**: Report `f1_scores` and `fpr_scores` arrays as defined in `model_output.schema.yaml` under `sensitivity_analysis`.
- **FR-006, FR-007, SC-002** addressed here.

### Phase 5: Validation & Reporting
- **Step 5.1**: Verify all metrics against acceptance criteria.
- **Step 5.2**: Generate final `results.json`. Compute SHA-256 hashes for `results.json` and `unified_analysis.csv`. Update `state/*.yaml` with these hashes to satisfy Constitution Principle V.
- **FR-008, SC-003** addressed here.
