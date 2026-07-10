# Implementation Plan: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

**Branch**: `001-predicting-oxidation-resistance` | **Date**: 2026-06-26 | **Spec**: [spec.md]

## Summary

This feature implements a composition-only predictive screening pipeline for nickel-based superalloys to estimate high-temperature oxidation weight gain (mg/cm²). The system utilizes thermodynamic and periodic table descriptors derived from elemental composition, trained via CPU-efficient machine learning models (Random Forest, Gradient Boosting, Gaussian Process). 

**Critical Scope Note**: Due to the absence of a verified real-world alloy dataset in the input block, the pipeline includes a **Synthetic Data Fallback** mode. This mode is strictly for **Pipeline Validation** (testing code robustness, statistical logic, and error handling) and **NOT** for validating the scientific hypothesis regarding real-world oxidation resistance. If no real dataset is found, the project will output a "Data Gap Report" rather than claiming scientific validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `pyyaml`, `requests`, `numpy`, `matplotlib`, `statsmodels` (for power analysis)  
**Storage**: Local filesystem (`data/raw`, `data/processed`), Parquet/CSV formats.  
**Testing**: `pytest` (unit tests for feature engineering, integration tests for pipeline execution).  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM, no GPU).  
**Project Type**: Data Science CLI / Analysis Pipeline.  
**Performance Goals**: End-to-end execution ≤ 6 hours on CI; memory usage < 7 GB; dataset capped at a reasonable size for CI.  
**Constraints**: No GPU usage; no external quantum chemistry calls at runtime; strict associational framing; dataset capping logic for CI vs. Local modes.  
**Scale/Scope**: Processing up to 500 samples for CI; up to 1000 for local sensitivity analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **I. Reproducibility**: The plan mandates pinned `random_state` in all model training and fixed dataset fetch URLs. **Note**: If real data is unavailable, reproducibility applies to the *pipeline logic* via the synthetic generator. Scientific result reproducibility is contingent on the availability of the real dataset.
2.  **II. Verified Accuracy**: All dataset citations in `research.md` will strictly reference the URLs provided in the `# Verified datasets` block. If those URLs are invalid for the domain, the plan explicitly logs a deviation and uses synthetic data *only* for code testing, ensuring no false claims of accuracy are made.
3.  **III. Data Hygiene**: Raw data will be downloaded to `data/raw` with checksums recorded. Derived features will be saved to `data/processed` as new files.
4.  **IV. Single Source of Truth**: All metrics (R², RMSE) in reports will be generated programmatically from the `data/processed` artifacts, not manually typed.
5.  **V. Versioning Discipline**: The `requirements.txt` will pin versions. Artifact hashes will be tracked in the project state file.
6.  **VI. Thermodynamic Feature Integrity**: The pipeline will explicitly separate raw composition inputs from calculated thermodynamic descriptors (e.g., oxide formation enthalpy) in the feature vector construction.
7.  **VII. Microstructural Limitation Quantification**: The plan includes a specific "Gap Analysis" phase (US-2) to compute the RMSE delta (SC-002) between composition-only and microstructural-augmented models, fulfilling the core hypothesis verification *if* real data is available.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-oxidation-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── prediction.schema.yaml
    └── gap_analysis.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-277-predicting-oxidation-resistance/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                 # CLI entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py          # Dataset download logic (includes fallback)
│   │   └── processor.py        # Feature engineering (thermo descriptors)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── trainer.py          # Model training & CV logic (Nested CV)
│   │   └── evaluator.py        # Gap analysis & metrics
│   └── viz/
│       ├── __init__.py
│       └── shap_plots.py       # Interpretability generation
├── data/
│   ├── raw/                    # Downloaded raw files (checksummed)
│   └── processed/              # Derived feature tables
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: Selected a modular CLI structure (`code/` subdirectories) to separate data fetching, feature engineering, and modeling. This ensures the "Thermodynamic Feature Integrity" principle is maintained by isolating the descriptor calculation logic. The `data/` directory is strictly for artifacts, with `raw` being immutable.

## Complexity Tracking

No violations detected. The modular structure is necessary to enforce the separation of composition and thermodynamic features (Constitution Principle VI) and to support the distinct "Gap Analysis" workflow (Principle VII) without conflating code paths.

## Implementation Phases

### Phase 0: Data Sourcing & Gap Handling
**Goal**: Attempt to fetch real data; if unavailable, initialize synthetic fallback.
1.  **Fetch Real Data**: Execute fetcher logic against NIST/Zenodo URLs.
2.  **Validate Availability**: Check if dataset contains required columns (Ni, Cr, Al, weight gain).
3.  **Fallback Trigger**: If fetch fails or data is invalid (as per input block), trigger `SyntheticDataGenerator`.
4.  **Log Deviation**: Record a formal deviation from FR-001 in `logs/data_gap_report.txt`, stating that real data is unavailable and the project is proceeding in "Pipeline Validation Mode".

### Phase 1: Data Processing & Validation
**Goal**: Prepare data and enforce strict validation rules.
1.  **Data Cleaning**: Handle missing values, filter out rows with missing key elements.
2.  **Feature Engineering**: Calculate thermodynamic descriptors (enthalpy, atomic radius) and periodic table features. **Strictly separate** raw composition from derived features.
3.  **Validation (SC-005)**: 
    - Check for missing required predictors.
    - If any required predictor is missing in >0% of rows, halt execution with `EXIT_CODE_DATA_VALIDATION_FAILURE`.
    - Count and log excluded rows.
4.  **Zero Variance Detection**: Exclude features with zero variance to prevent division-by-zero errors.

### Phase 2: Model Training & Selection
**Goal**: Train models using robust statistical methods.
1.  **Nested Cross-Validation**: Implement kx2 Nested CV

The specific value to remove/generalize: 'k'

Rewritten passage:
Implement kx2 Nested CV. This study addresses the research question of how to robustly evaluate model performance under varying data splits. The method employed is kx2 Nested Cross-Validation to assess generalization error without data leakage. References: [Citation] to prevent overfitting during model selection.
2.  **Model Training**: Train RF, GB, and GP models.
3.  **Model Comparison**: Compare models using pre-registered metric (RMSE). Use Friedman test if sample size permits.
4.  **Power Analysis**: Calculate statistical power for the Gap Analysis (see research.md).

### Phase 3: Gap Analysis & Interpretability
**Goal**: Quantify the microstructural effect and explain model decisions.
1.  **Gap Analysis**: Compare RMSE of composition-only vs. composition+microstructure models.
    - If microstructural subset n < 30, report "INCONCLUSIVE" and the calculated power (e.g., < 0.2).
2.  **SHAP Analysis**: Generate SHAP summary plots and local explanations.
3.  **Collinearity Check**: Explicitly report the correlation between Al content and Al2O3 enthalpy; do not claim independent effects for definitionally linked features.

### Phase 4: Reporting & Output
**Goal**: Generate final reports and artifacts.
1.  **Generate Reports**: `gap_analysis_report.json`, `predictions.csv`, `shap_summary_plot.png`.
2.  **Scientific Validity Warning**: If synthetic data was used, append a prominent warning to all reports stating that results are for pipeline validation only and do not validate the scientific hypothesis.
3.  **Final Artifacts**: Commit all artifacts to `data/processed`.
