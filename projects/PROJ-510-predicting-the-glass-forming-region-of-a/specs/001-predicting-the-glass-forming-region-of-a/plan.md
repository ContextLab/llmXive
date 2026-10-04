# Implementation Plan: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Branch**: `001-predict-glass-forming-region` | **Date**: 2026-07-25 | **Spec**: `specs/001-predict-glass-forming-region/spec.md`
**Input**: Feature specification from `/specs/001-predict-glass-forming-region/spec.md`

## Summary

This project implements a machine learning pipeline to predict the critical cooling rate (CCR) of ternary alloy systems using thermodynamic descriptors derived from verified experimental data. The approach involves ingesting experimental data, engineering features (mixing enthalpy, atomic size mismatch, electronegativity variance), training a Random Forest regressor with k-fold cross-validation, and performing sensitivity analysis on physically-grounded thresholds. **All findings are explicitly framed as ASSOCIATIONAL**, respecting the observational nature of the dataset. Causal claims are prohibited.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `mendeleev` (for periodic table data), `datasets` (Hugging Face), `pyyaml`, `pytest`, `scipy`
**Storage**: Local file system (`data/` directory for CSVs, logs, models)
**Testing**: `pytest` with strict exit codes and JSON-formatted reports
**Target Platform**: Linux (GitHub Actions CPU runner: A moderate number of vCPUs, 7GB RAM)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: Complete end-to-end pipeline in < 6 hours; model training < 1 hour on 500+ samples.
**Constraints**: No external GPU; strict memory limits (~GB); deterministic reproducibility via pinned seeds and checksums.
**Scale/Scope**: Target N ≥ 1000 raw entries, filtered to N ≥ 500 valid ternary alloys with CCR data.

> **Dataset Strategy**: The project relies on verified **experimental** datasets containing `critical_cooling_rate`.
> 1. **Primary Source**: `bulk-metallic-glasses/CCR-experimental` (Zenodo/figshare record, verified URL: `). This source contains experimental CCR values.
> 2. **Fallback Source**: A curated experimental CSV from the 'Bulk Metallic Glasses' literature compilation (verified URL: `).
> 3. **Failure Condition**: If *both* sources fail to provide N ≥ 500 valid entries, the pipeline halts with a specific `DataInsufficiencyError` (Code 2). **No synthetic data or unverified sources are used.**

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Reproducibility (Principle I)**: All random seeds (`random_state=42`) are pinned in code. Data sources are fixed URLs. Checksums recorded in `data/`.
2. **Verified Accuracy (Principle II)**: All citations (experimental datasets, thermodynamic formulas) will be validated against the provided URLs. No fabricated metrics.
3. **Data Hygiene (Principle III)**: Raw data downloaded to `data/raw/` (checksummed). Processed data to `data/processed/` (derived, new file). No in-place modification.
4. **Single Source of Truth (Principle IV)**: All metrics in `REPORT.md` trace to `data/models/cv_metrics.json` and `data/processed/processed_alloys.csv`.
5. **Versioning Discipline (Principle V)**: Content hashes updated on artifact change. Every artifact under this project carries a content hash.
6. **Thermodynamic Integrity (PrPrinciple VI)**: Descriptors calculated *strictly* using `mendeleev` (Periodic Table) and composition strings. No proxy values.
7. **CV Rigor (Principle VII)**: 5-fold CV and permutation importance implemented exactly as specified. No single-split reporting as primary metric.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-glass-forming-region/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── dataset.schema.yaml
│ ├── metrics.schema.yaml
│ ├── model_output.schema.yaml
│ └── sensitivity.schema.yaml
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-510-predicting-the-glass-forming-region-of-a/
├── code/
│ ├── ingestion.py # Data download, parsing, filtering (T001a, T008, T012a, T050, T051)
│ ├── features.py # Thermodynamic descriptor calculation (T014a, T016a)
│ ├── train.py # Model training, CV, metrics (T020, T021, T022)
│ ├── analyze.py # Importance, sensitivity, collinearity (T031, T037)
│ ├── validate_schemas.py # Schema validation script (validates ALL 4 schemas)
│ └── utils.py # Logging, hashing helpers
├── data/
│ ├── raw/ # Downloaded CSVs (checksummed)
│ ├── processed/ # Feature-engineered CSVs
│ ├── models/ # Pickled models, metrics JSON
│ └── logs/ # Error logs, exclusion logs, hashes
├── tests/
│ ├── unit/
│ │ ├── test_features.py # Unit tests for mixing enthalpy, size mismatch (T010a, T010b)
│ │ └── test_ingestion.py
│ └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for data science pipeline. Separation of `code/`, `data/`, and `tests/` ensures reproducibility and hygiene. `logs/` directory explicitly created to satisfy T008, T050, T051.

## Task Specifications

### T001a: Data Ingestion & Validation
- **Action**: Download Primary Source. If missing/empty, attempt Fallback Source.
- **Validation**: Check for `critical_cooling_rate` column. Filter for ternary alloys.
- **Output**: `data/processed/processed_alloys.csv`.
- **Error Handling**: If N < 500 after both sources, raise `DataInsufficiencyError` (Code 2) and write to `data/logs/fetch_error.log`.

### T008: Error Logging
- **Action**: On any fetch failure or empty dataset, write to `data/logs/fetch_error.log`.
- **Format**: JSON lines. `{"timestamp": "...", "error_code": "E001", "message": "..."}`.
- **Exit Code**: 1 on error, 0 on success.

### T012a: Composition Parsing
- **Action**: Parse composition strings (e.g., "Zr50Cu30Al20").
- **Regex**: `r'([A-Z][a-z]?)(\d*\.?\d*)'`.
- **Edge Cases**: If non-ternary or malformed, log to `data/logs/exclusion_log.txt` with `{"row_id":..., "reason": "Non-ternary"}`.

### T014a: Feature Engineering
- **Action**: Compute descriptors using `mendeleev`.
- **Properties**: Pauling electronegativity, Covalent radii.
- **Error**: If `mendeleev` lacks data, raise `ValueError("Missing data for pair: X-Y")`.

### T020: Train-Test Split
- **Action**: Split data into training and test sets..
- **Parameters**: `random_state=42`, `test_size=0.2`.
- **Output**: `data/processed/train.csv`, `data/processed/test.csv`.

### T021: Model Training & Metrics
- **Action**: Train Random Forest. Perform 5-fold CV.
- **Baseline**: Dummy Regressor (mean).
- **Test**: Two-sided paired t-test (`scipy.stats.ttest_rel`) comparing RF RMSE vs Dummy RMSE.
- **Output**: `data/models/cv_metrics.json`.
- **Metrics**: `mean_rmse`, `oob_score`, `learning_curve_slope`, `p_value` (t-test).

### T022: Model Persistence
- **Action**: Save model to `data/models/random_forest_model.pkl`.

### T031: Sensitivity & Importance
- **Action**: Permutation importance (n=1000). Threshold sweep (, varying rates including 150 K/s).
- **Thresholds**: Map 50=Low, 100=Medium, 150=High.
- **Stability**: "Negligible margin" = variance < 5% of mean RMSE.
- **Top-2 Check**: Verify top-2 features have p < 0.05.
- **Output**: `data/models/sensitivity_report.json`.

### T037: Schema Validation
- **Action**: Run `validate_schemas.py` against `dataset`, `metrics`, `model_output`, `sensitivity` schemas.
- **Output**: `data/logs/validation_report.json`.

### T047: Reproducibility Check
- **Action**: Compute SHA-256 of `processed_alloys.csv` (UTF-8, LF line endings). Compare to stored hash.
- **Output**: `data/logs/ingestion_hash.txt`.

### T050: Empty Dataset Handling
- **Action**: If N=0 after filtering, raise `ValueError("Dataset is empty after filtering.")` and log to `data/logs/empty_dataset_error.log`.

### T051: Label Filtering
- **Action**: Filter rows with missing `glass_forming_label` or `critical_cooling_rate`. Log exclusions.

### T074: Report Generation
- **Action**: Generate `REPORT.md` from template.
- **Constraint**: Template enforces "Associational" disclaimer. No causal language allowed.

## Complexity Tracking

*No complexity violations identified. The pipeline is linear: Ingest -> Feature -> Train -> Analyze. All steps are CPU-tractable for N=500.*