# Implementation Plan: Predicting the Impact of Composition on the Density of Metallic Glasses

**Branch**: `001-predict-metallic-glass-density` | **Date**: 2024-05-22 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-predict-metallic-glass-density/spec.md`

## Summary

This project implements a machine learning pipeline to predict the bulk density of metallic glasses based on their elemental composition. The core hypothesis is that non-linear atomic packing effects (captured by descriptors like radius mismatch and packing efficiency) explain density deviations from the simple Linear Mixing Rule. The system ingests data from public repositories (Zenodo/Materials Cloud), engineers atomic-level features using the `mendeleev` library, trains a Gradient Boosting model on the *residual* density, and generates a scientific report with SHAP interpretability. If real data is unavailable or insufficient (<50 rows), the system gracefully degrades to a 'Pipeline Validation Mode' using synthetic data generated from physical mixing rules.

**Critical Methodological Note**: The implementation adopts **Group K-Fold** (grouped by dominant element) instead of the Spec's requested Stratified K-Fold to prevent data leakage and ensure generalizability. The implementation also defines the **Mass-Only Model** as the true baseline for comparison, overriding the Spec's tautological 'Model vs Zero' definition. These deviations are necessary for scientific rigor and are flagged for Spec kickback.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `mendeleev`, `shap`, `matplotlib`, `seaborn`, `requests`  
**Storage**: Local CSV files (`data/raw_data.csv`, `data/clean_data.csv`), Model pickle (`models/model.pkl`), Metrics JSON (`reports/metrics.json`)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for feature engineering logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM)  
**Project Type**: Scientific Data Pipeline / Regression Modeling  
**Performance Goals**: Complete pipeline execution ≤ 2 hours; Model training ≤ 600 seconds on CPU.  
**Constraints**: No GPU usage (CPU-first); Must handle missing data; Must fall back to synthetic data if real data fails.  
**Scale/Scope**: Dataset size variable (target ≥50 real rows); Synthetic fallback ≥100 rows.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: The plan mandates pinned random seeds in `code/` and explicit downloading of datasets from canonical sources (Zenodo/Materials Cloud) with checksum validation. Synthetic data generation uses a fixed seed if real data is missing.
- **Principle II (Verified Accuracy)**: All elemental constants (atomic mass, radius, electronegativity) are sourced strictly from the `mendeleev` library, which is the verified primary source for periodic table data in this context. No external web scraping for constants is permitted.
- **Principle III (Data Hygiene)**: The plan enforces a "Raw -> Clean -> Derived" file workflow. `raw_data.csv` is never modified; `clean_data.csv` is a new artifact. Checksums are recorded in the state file.
- **Principle IV (Single Source of Truth)**: All metrics (MAE, R²) and visualizations in the report are generated programmatically from the model and data objects, not hand-typed. The `reports/metrics.json` is the SSoT for reported metrics; `models/model.pkl` is the SSoT for model state.
- **Principle V (Versioning Discipline)**: The implementation will use content hashes for data files and model artifacts to trigger invalidation of stale results.
- **Principle VI (Amorphous Packing Descriptor Validation)**: The plan explicitly requires the calculation of `radius_mismatch` and `packing_efficiency` descriptors. The report *must* use SHAP values to compare the contribution of these packing descriptors against the `mean_atomic_mass` baseline before claiming structural insights.
- **Principle VII (Computational Screening Fidelity)**: The success metric is explicitly tied to MAE ≤ 0.1 g/cm³. **If MAE > 0.1, the plan mandates the generation of Partial Dependence Plots and a specific analysis of variance explained by radius mismatch as a distinct finding.** The `code/analysis/report.py` module is explicitly responsible for generating these artifacts as a mandatory step, not optional.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-impact-of-composition-on/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-461-predicting-the-impact-of-composition-on-/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py          # FR-001, FR-007: Zenodo/Materials Cloud fetch + fallback
│   │   └── preprocess.py        # FR-001: Cleaning, IUPAC normalization, imputation
│   ├── features/
│   │   ├── __init__.py
│   │   └── engineering.py       # FR-002: Atomic descriptors, residual calculation
│   ├── models/
│   │   ├── __init__.py
│   │   └── train.py             # FR-003 (Modified): Group K-Fold, LightGBM on residuals
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── report.py            # FR-005, FR-006, VII: SHAP, Sensitivity, PDP, Distinct Findings
│   └── main.py                  # Orchestration entry point
├── data/
│   ├── raw_data.csv             # Downloaded artifact
│   ├── clean_data.csv           # Preprocessed artifact
│   └── synthetic_data.csv       # Validation mode artifact
├── models/
│   └── model.pkl                # Trained model artifact (SSoT for state)
├── reports/
│   ├── analysis_report.html     # Final output
│   └── metrics.json             # SSoT for reported metrics
├── tests/
│   ├── unit/
│   │   └── test_engineering.py
│   └── contract/
│       └── test_schema_validation.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: The project adopts a modular "pipeline" structure (`code/data`, `code/features`, `code/models`, `code/analysis`) to strictly separate concerns. This aligns with the Constitution's requirement for reproducibility and hygiene, ensuring that data ingestion, feature engineering, and modeling are distinct, testable steps. The fallback to synthetic data is handled within the `download.py` module, ensuring the rest of the pipeline remains agnostic to the data source.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Residual Target Modeling | The hypothesis specifically targets *non-linear* packing effects beyond the linear mixing rule. | Training on raw density would conflate the dominant mass effect with the subtle packing effects we aim to isolate. |
| Synthetic Fallback Mode | Real metallic glass datasets are sparse and often behind paywalls or with broken links. | A pipeline that fails on missing data yields no results; a synthetic fallback allows validation of the entire code path and feature logic. |
| Atomic Fraction Conversion | Mass fractions and atomic radii are collinear in a way that biases radius-based descriptors. | Using mass fractions for radius calculations would introduce a mathematical artifact, violating Principle II (Verified Accuracy) regarding physical constants. |
| Group K-Fold (vs Stratified) | Stratified K-Fold on 'Dominant Element' risks leakage if the element family correlates with the residual. | Group K-Fold ensures the model is tested on *unseen* element families, providing a rigorous test of generalizability. |
| Mass-Only Baseline | The Spec's 'Model vs Zero' baseline is tautological for a residual target. | Comparing against a 'Mass-Only Model' (Linear Regression on mean atomic mass) isolates the *added value* of packing descriptors. |