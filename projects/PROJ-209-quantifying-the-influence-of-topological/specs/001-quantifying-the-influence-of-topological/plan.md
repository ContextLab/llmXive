# Implementation Plan: Quantifying the Influence of Topological Defects on 2D Material Properties

**Branch**: `001-quantify-defect-influence` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-quantify-defect-influence/spec.md`

## Summary

This plan implements a computational workflow to quantify how topological defects (dislocations, grain boundaries) in 2D materials (graphene, MoS₂) alter electronic conductivity, Young's modulus, and fracture strength. The approach combines data acquisition from the Materials Project API (with a synthetic data fallback), statistical modeling via Random Forest regressors, and rigorous inference using permutation testing with Benjamini-Hochberg FDR control. The workflow is designed to run entirely on a CPU-only GitHub Actions free-tier runner, utilizing streaming where possible and sampling to fit within 7GB RAM / 6h limits.

**Critical Scope Clarification**: This study does **not** claim to discover new physical laws. Instead, it focuses on **validating the robustness of the ML pipeline** in recovering *known* defect-property trends from a **Physics-Informed Parametric Surrogate**. The surrogate uses established analytical formulas (e.g., continuum elasticity) to generate the signal component of the data, calibrated with noise derived from verified DFT datasets. This ensures the study can proceed without real-world defect data while maintaining physical plausibility.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `jupyter`, `matplotlib`, `seaborn`, `joblib`, `scipy`
**Storage**: Local file system (`data/raw`, `data/processed`, `data/validation`)
**Testing**: `pytest` (for unit tests of data loaders and model wrappers), manual integration testing via notebook execution.
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk).
**Project Type**: Computational research pipeline / data analysis.
**Performance Goals**: Complete full workflow (download/generate -> process -> model -> validate) within 6 hours.
**Constraints**: No GPU; no external API credentials beyond public endpoints; strict memory limits requiring streaming or sampling; no fabrication of data (must use verified sources or explicit synthetic generation).
**Scale/Scope**: **N=1000+** synthetic data points (generated to ensure statistical stability for permutation testing). 3 target properties; 5-fold CV.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, `seed=42` for all stochastic steps, and deterministic data loading. |
| **II. Verified Accuracy** | **CONDITIONALLY MET** | The study's data provenance is verified: the synthetic data generator uses analytical laws and DFT-calibrated noise. The "Verified Accuracy" applies to the *methodology* and *data provenance*. |
| **III. Data Hygiene** | **PASS** | Plan requires checksums for all `data/` artifacts and immutable raw data. Derivations go to `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in the final report will trace to `data/processed/features.csv` and `data/processed/model_outputs.json`. |
| **V. Versioning Discipline** | **PASS** | Plan includes `model_config.yaml` and content hashing for `data/` artifacts. |
| **VI. Defect Dataset Integrity** | **CONDITIONALLY MET** | The plan explicitly documents the failure of all verified real-world defect datasets. The synthetic fallback is a documented, last-resort mechanism mandated by the spec (FR-010). |
| **VII. Modeling Reproducibility** | **PASS** | Plan mandates `RandomForestRegressor` with fixed seeds, explicit hyperparameters, and saved `feature_selection_log.json`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-defect-influence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── 01_data_acquisition.py       # Fetches pristine structures, attempts defect data, generates synthetic fallback
├── 02_data_processing.py        # Normalization, one-hot encoding, missing value handling, feature engineering
├── 03_modeling.py               # RF training, CV, permutation testing, FDR control, hold-out evaluation, stratification
├── 04_sensitivity_analysis.py   # Threshold sweeping, FPR/FNR reporting
├── 05_validation.py             # External validation check, Validation_Report.json generation
├── utils/
│   ├── synthetic_generator.py   # Physics-informed parametric synthetic data generator
│   └── config.py                # Path and seed management
├── requirements.txt
└── run_workflow.sh              # Orchestration script

data/
├── raw/
│   ├── pristine_structures.csv  # Downloaded from Materials Project (or cached)
│   ├── defect_dataset_2022.csv  # Attempted download (may be empty/missing)
│   ├── synthetic_train.csv      # Generated if real data missing (data_source='synthetic')
│   ├── synthetic_holdout.csv    # Generated for independent test (data_source='synthetic')
│   ├── synthetic_defect_fallback.csv # Generated if primary download fails (data_source='synthetic')
│   └── surrogate_noise_params.json # Parameters for noise calibration from DFT
├── processed/
│   ├── features.csv             # Normalized, encoded feature matrix
│   ├── targets.csv              # Normalized target vectors
│   ├── model_outputs.json       # R², MAPE, CV stats
│   └── feature_selection_log.json # Collinearity exclusion log
└── validation/
    └── Validation_Report.json   # Final validation status

tests/
├── unit/
│   ├── test_synthetic_generator.py
│   └── test_data_processing.py
└── integration/
    └── test_full_workflow.py
```

**Structure Decision**: Single `code/` directory for linear pipeline scripts. This minimizes overhead and aligns with the 6-hour runtime constraint, avoiding complex service orchestration. The separation of `raw` and `processed` ensures data hygiene (Constitution III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Fallback Logic** | The spec requires a valid dataset even if the primary source fails (FR-010). | A simple "fail" would halt the entire research pipeline, preventing any analysis or model training. |
| **Permutation Testing + FDR** | Required for valid statistical inference on feature importance (FR-05, FR-11). | Standard `feature_importances_` from RF are biased; without permutation + FDR, the study cannot claim statistical significance for defect descriptors. |
| **Hold-out Set Generation** | Required to validate predictive power (FR-12). | Using only cross-validation risks overfitting to the specific dataset split; an independent synthetic hold-out provides a stricter test. |
| **Physics-Informed Parametric Surrogate** | Required to break the circular validation loop while ensuring physical plausibility. | Using deterministic analytical formulas alone would result in a tautology. Adding DFT-calibrated noise introduces realistic variability without requiring a complex, unverified generative model. |

## Statistical Power & Limitations

*   **Sample Size**: The plan generates **N=1000+** synthetic samples to ensure statistical stability for permutation testing and 5-fold CV. This mitigates the underpowering concern (methodology-df682d81) for the *trend recovery* task.
*   **Limitation**: The study **cannot** claim to discover new physics or model the full complexity of real-world defect interactions. The goal is to validate the ML pipeline's ability to recover *known* trends from noisy, physics-informed data.
*   **Interpretation**: Results are framed as "The model successfully recovered the known defect-property trends from the surrogate data with X% accuracy" rather than "Defects cause Y% change in properties".

## Task Breakdown & Phase Order

### Phase 0: Data Acquisition (US-1)
*   **T010**: Download pristine structures from Materials Project API. **Output**: `data/raw/pristine_structures.csv` (>= 50 entries). If API fails, generate synthetic pristine structures and log.
*   **T011**: Attempt to download `defect_dataset_2022.csv`. Validate columns. **Output**: `data/raw/defect_dataset_2022.csv` (even if empty). Log failure if download fails.
*   **T012**: **Fallback Logic**: If T011 fails or data is invalid, invoke synthetic generator with seed=42, generate >= 100 entries, save to `data/raw/synthetic_defect_fallback.csv`, set `data_source='synthetic'`.
*   **T013**: Generate `synthetic_train.csv` (N=1000+) using the Physics-Informed Parametric Surrogate (analytical signal + DFT-calibrated noise). **Output**: `data/raw/synthetic_train.csv`.
*   **T014**: Generate `synthetic_holdout.csv` using the hold-out mode of the generator. **Output**: `data/raw/synthetic_holdout.csv`.

### Phase 1: Data Processing (US-1, US-2)
*   **T018**: Process data: normalize by pristine references, one-hot encode defect type, handle missing values (exclude if missing reference), log excluded entries. **Output**: `data/processed/features.csv`, `data/processed/targets.csv`.

### Phase 2: Modeling & Inference (US-2)
*   **T020**: **Collinearity Check & Re-training**: Compute VIF. **While** VIF > 5 for any pair: exclude lower-importance feature (based on permutation stability), re-train model, re-calculate VIF. Log all iterations in `data/processed/feature_selection_log.json`.
*   **T021**: Train Random Forest models (3 targets) with 5-fold CV. Report R², MAPE, CV std.
*   **T022**: **Stratification Logic**: If 'synthesis_method' or 'grain_size' is present and has >= 3 distinct values with sufficient sample size: train separate models per stratum and report metrics per stratum. Else: include as covariates.
*   **T023**: Permutation Testing: Generate p-values for feature importance.
*   **T024**: **FDR Correction**: Input: p-values from T023. Process: Apply Benjamini-Hochberg procedure to control FDR at q <= 0.05. Output: 'fdr_adjusted_p' and 'is_significant' in `data/processed/model_outputs.json`.
*   **T025**: **Hold-out Evaluation**: Evaluate final models on `data/raw/synthetic_holdout.csv`. Report R², MAPE.

### Phase 3: Validation & Sensitivity (US-3)
*   **T027**: Sensitivity Analysis: Sweep thresholds, report FPR/FNR.
*   **T031**: **External Validation**: Check for external dataset. If none, generate `data/validation/Validation_Report.json` with `status: NO_EXTERNAL_DATA`, `method: internal_only`, and `data_source` flag.

## Compute Feasibility & Resource Management
*   **CPU-First**: All modeling uses `scikit-learn` Random Forests, which are CPU-tractable. The synthetic data generation is CPU-tractable.
*   **Memory**: The dataset size (synthetic or real) is expected to be small (<1000 rows). If larger, the plan uses `pandas` chunking or sampling to stay under 7GB RAM.
*   **Runtime**: The workflow (download -> process -> 5x CV RF -> permutation test) is estimated to complete in < 2 hours on a 2-core CPU, well within the 6-hour limit.
*   **Streaming**: Streaming is used for the Materials Project API (paginated requests) and synthetic data generation (streaming rows to disk). The DFT parquet files are small enough to be loaded fully.