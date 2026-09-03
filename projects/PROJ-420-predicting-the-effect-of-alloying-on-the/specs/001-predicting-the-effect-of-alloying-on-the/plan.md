# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2026-07-05 | **Spec**: `specs/001-predict-poissons-ratio/spec.md`
**Input**: Feature specification from `specs/001-predict-poissons-ratio/spec.md`

## Summary

This project implements a data-driven pipeline to predict the Poisson's ratio of monolithic aluminum alloys based on the atomic fractions of key alloying elements (Cu, Mg, Si, Zn, Mn). The technical approach involves extracting validated data from public materials repositories (Materials Project/NIST), applying Isometric Log-Ratio (ILR) transformation using a defined Sequential Binary Partition to handle compositional constraints, training a Random Forest regressor with rigorous cross-validation and a held-out test set, and extracting feature importance via grouped ILR coordinates. All findings are framed as associational due to the observational nature of the data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `datasets` (Hugging Face), `pyyaml`, `numpy`, `statsmodels` (for VIF), `compositions` (for ILR)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `models`, `results`); no external database.  
**Testing**: `pytest` (unit tests for data filtering, ILR transformation, schema validation, and independence checks).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM).  
**Project Type**: Data Science Pipeline / Research Tool.  
**Performance Goals**: Complete data extraction, cleaning, modeling, and reporting within 6 hours on CPU.  
**Constraints**: CPU-only execution; no GPU acceleration; strict adherence to compositional data analysis (ILR) to avoid spurious correlations; no causal claims.  
**Scale/Scope**: Dynamic dataset size (verified at runtime). Pipeline halts if N < 50. Expected range: entries spanning from a lower bound to an upper bound.

> Dataset sizes and empirical performance metrics are deferred to the research phase. The pipeline will verify data availability at runtime and halt if the minimum sample size (N=50) is not met.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Reproducibility (Principle I) (NON-NEGOTIABLE)**:
    *   **Plan**: All random seeds will be pinned in `code/modeling.py` and `code/data_extraction.py`.
    *   **Plan**: A `requirements.txt` will be generated at `code/requirements.txt` with exact version pins.
    *   **Plan**: Data checksums will be recorded in `state/projects/...yaml` after download.
2.  **Verified Accuracy (Principle II)**:
    *   **Plan**: Citations in `research.md` will be restricted to the "Verified datasets" block provided in the prompt or explicit API sources (Materials Project).
    *   **Plan**: The Reference-Validator Agent will be invoked before any review points are awarded.
3.  **Data Hygiene (Principle III)**:
    *   **Plan**: Raw data downloaded in `data/raw/` will be immutable.
    *   **Plan**: Derived data (filtered, normalized) will be written to `data/processed/` with new filenames.
    *   **Plan**: A PII scan will be run (though unlikely to contain PII, the process is mandated).
4.  **Single Source of Truth (Principle IV)**:
    *   **Plan**: All figures and statistics in the final report will be generated programmatically from `data/processed/` and `results/`.
    *   **Plan**: No hand-typed numbers in the final documentation.
5.  **Versioning Discipline (Principle V)**:
    *   **Plan**: Content hashes for all artifacts in `data/` and `models/` will be updated in the project state file upon change.
6.  **Unit Consistency and Dimensional Integrity (Principle VI)**:
    *   **Plan**: A dedicated validation step in `code/data_cleaning.py` will enforce GPa for elastic constants and atomic fractions summing to 1.0.
    *   **Plan**: Weight percent to atomic percent conversion will use standard atomic weights.
7.  **Compositional Attribution and Interpretability (Principle VII)**:
    *   **Plan**: Feature importance will be calculated via 'Grouped ILR Importance' (aggregating log-ratio contributions) to rank alloying elements, ensuring interpretability without invalid back-transformation.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-poissons-ratio/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── alloy_record.schema.yaml
│   ├── collinearity_diagnostic.schema.yaml
│   ├── feature_importance.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── data_extraction.py      # Downloads from Materials Project/NIST
│   ├── data_cleaning.py        # Filtering, unit normalization, ILR, wt%->at%
│   ├── modeling.py             # RF training, CV, VIF (on ILR), grouped importance
│   ├── logging_config.py       # JSON logging setup
│   └── requirements.txt
├── data/
│   ├── raw/                    # Unmodified downloads
│   └── processed/              # Cleaned, filtered, transformed data
├── models/
│   └── rf_model.pkl            # Trained Random Forest
├── results/
│   ├── cv_metrics.json         # Cross-validation results
│   ├── test_metrics.json       # Test set results
│   ├── feature_importance.json # Grouped ILR importance
│   └── vif_diagnostic.json     # Collinearity diagnostics
└── tests/
    ├── test_data_cleaning.py
    └── test_modeling.py
```

**Structure Decision**: A single-project structure was chosen to minimize overhead. The separation of `data_extraction`, `data_cleaning`, and `modeling` ensures modularity and testability, aligning with the "Reproducibility" and "Data Hygiene" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ILR Transformation (SBP Basis) | Essential for compositional data (atomic fractions sum to 1) to avoid spurious correlations. | Standard normalization fails to handle the constant-sum constraint, leading to invalid statistical inference. |
| Grouped ILR Importance | Required to rank elements without invalid back-transformation of non-linear splits. | Simple back-transformation is mathematically invalid for Random Forests on ILR coordinates. |
| VIF on ILR Features | Required by FR-007 to diagnose collinearity in the transformed space. | VIF on raw compositions yields infinite values due to the closure problem (sum=1). |
| 80/20 Split + CV | Required by FR-005 (held-out test) and FR-004 (5-fold CV). | Using only CV would not provide an independent estimate of generalization error. |
| Data Independence Check | Required by FR-009 to prevent learning mathematical identities (E vs G). | Assuming all data is independent risks training on derived values, creating circular validation. |

## Phases & Tasks

### Phase 1: Data Extraction & Availability Check
*Goal: Secure raw data and verify minimum sample size.*
1.  **T1.1**: Attempt to fetch data from Materials Project API (requires `MP_API_KEY` env var). If keyless access fails, halt with "Configuration Error".
2.  **T1.2**: Attempt to fetch data from NIST MDR (public endpoint).
3.  **T1.3**: If both sources fail or return 0 records, halt with "Data Availability Failure" (Error Code: 101).
4.  **T1.4**: Aggregate raw data and record checksums.
5.  **T1.5**: Verify dataset size. If N < 50, halt with "Insufficient Data for Power" (Error Code: 102).

### Phase 2: Data Cleaning & Unit Consistency
*Goal: Filter, normalize, and convert units.*
1.  **T2.1**: Filter for monolithic aluminum alloys (exclude composites).
2.  **T2.2**: Convert wt% to atomic% using standard atomic weights.
3.  **T2.3**: Enforce mass balance: Sum of (Cu, Mg, Si, Zn, Mn, Al) must be 1.0. Exclude rows where sum of major elements < 0.95.
4.  **T2.4**: Normalize elastic constants to GPa.
5.  **T2.5**: Verify Poisson's ratio independence. Exclude records where measurement method is unknown or derived (unless metadata confirms independent measurement).

### Phase 2.5: Data Independence & Quality Gate
*Goal: Explicit verification of FR-009.*
1.  **T2.6**: Log the count of excluded records due to independence failure.
2.  **T2.7**: If N < 50 after exclusions, halt with "Insufficient Independent Data" (Error Code: 103).

### Phase 3: Feature Engineering & Modeling
*Goal: Transform features and train the model.*
1.  **T3.1**: Apply ILR transformation using a defined Sequential Binary Partition (SBP) basis.
2.  **T3.2**: Split data: majority Train, minority Test (stratified if possible).
3.  **T3.3**: Train Random Forest with k-fold Cross-Validation on the training set.
4.  **T3.4**: Evaluate on the held-out test set.
5.  **T3.5**: Compare Test MAE against a Null Baseline (predicting the mean).

### Phase 4: Collinearity & Diagnostic Reporting
*Goal: Address FR-007 and SC-004.*
1.  **T4.1**: Compute Variance Inflation Factors (VIF) on the ILR-transformed features.
2.  **T4.2**: Flag any ILR coordinate with VIF > 5.
3.  **T4.3**: Generate `results/vif_diagnostic.json` with interpretation.

### Phase 5: Associational Framing & Reporting
*Goal: Address FR-008 and SC-005.*
1.  **T5.1**: Extract Feature Importance via Grouped ILR Importance (aggregating log-ratio contributions).
2.  **T5.2**: Rank elements by importance.
3.  **T5.3**: Generate `results/feature_importance.json` and `results/model_output.json` with explicit "Associational, Not Causal" framing.
4.  **T5.4**: Verify all output files contain the associational disclaimer.

## Risk Mitigation

- **Data Scarcity**: If <50 entries are found (or <50 after independence filtering), the project halts with a clear error.
- **Missing Variables**: If a required element (e.g., Mn) is missing in a row, the row is excluded.
- **API Failure**: If Materials Project/NIST APIs are down or require auth not provided, the pipeline halts.
- **Model Performance**: If Test MAE > 0.05 AND > Null Baseline, the result is flagged as "No Signal Detected" or "High Noise".

## Compute Feasibility

- **CPU-First**: Random Forest on <2000 samples is trivial for CPU.
- **Memory**: <2000 rows × ~10 columns fits easily in 7 GB RAM.
- **Time**: Training and inference will take <30 minutes.
- **GPU**: Not required. The plan does not use deep learning or CUDA.