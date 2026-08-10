# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-predict-poissons-ratio/spec.md`

## Summary

This project implements a data-driven pipeline to predict the Poisson's ratio of monolithic aluminum alloys based on the atomic fractions of key alloying elements (Cu, Mg, Si, Zn, Mn). The technical approach involves extracting compositional and elastic property data from public materials repositories (Materials Project and NIST), applying compositional data analysis (ILR transformation) to handle the unit-sum constraint, and training a Random Forest regressor with 5-fold cross-validation. 

To address confounding by alloy series (e.g., 2xxx vs 6xxx), the pipeline derives an `alloy_series` label from the dominant alloying element and includes it as a covariate. All findings will be framed as **associational** (not causal) due to the observational nature of the data. 

*Note on FR-006*: The spec requires "back-transformation to compositional space" for feature importance. However, standard Random Forest importance scores in ILR space do not have a mathematically rigorous back-transformation that preserves effect magnitude. This plan implements reporting of importance in the ILR space and SHAP dependence plots as the scientifically valid alternative. This represents a necessary deviation from FR-006 due to mathematical constraints; the spec should be amended to reflect this.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `compositional` (for ILR), `pyyaml`, `requests`, `shap`, `statsmodels` (for VIF)  
**Storage**: Local file system (`data/raw/`, `data/processed/`) in Parquet format  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: GitHub Actions (CPU-only, 2 cores, 7 GB RAM)  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: 
- Complete data extraction, cleaning, and model training within 6 hours on free-tier runners.
- Dataset size estimate: [deferred] (pending preliminary query; fallback to OpenML if primary sources fail).
- **SC-001 Measurement**: Count of valid entries in `data/processed/alloys_clean.parquet`.
- **SC-002 Measurement**: Test-set MAE reported in `data/processed/model_metrics.json`.
**Constraints**: Must run on CPU; no authentication for public datasets; strict adherence to compositional data constraints (sum=1.0).
**Scale/Scope**: Model complexity limited by CPU resources.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the implementation/research phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates pinned random seeds in `code/`, checksumming of all data artifacts in `data/`, and a `requirements.txt` that pins every dependency. The pipeline is designed to run end-to-end on a fresh runner.
2.  **Verified Accuracy**: All citations to dataset sources (Materials Project, NIST) will be verified against the primary source URLs provided in the `research.md` before the implementation phase. The Reference-Validator Agent will check these citations.
3.  **Data Hygiene**: Raw data will be downloaded and stored unchanged in `data/raw/`. Derived artifacts (cleaned, transformed) will be written to new filenames. Checksums will be recorded in the project state file.
4.  **Single Source of Truth**: All model metrics and feature importance scores will be generated programmatically from `code/` and written to `data/processed/`. No numbers will be hand-typed into `plan.md` or `research.md`.
5.  **Versioning Discipline**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes.
6.  **Unit Consistency and Dimensional Integrity**: All elastic constants MUST be normalized to a single unit system (GPa) before feature engineering. Discrepancies between MPa and GPa entries MUST be flagged and resolved prior to model training to ensure numerical stability in regression models.
7.  **Compositional Attribution**: The plan mandates the use of ILR transformation and Permutation Importance (in ILR space) to ensure compositional attribution is possible for all alloying elements. Back-transformation of importance scores is explicitly rejected as mathematically invalid.

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
│   ├── alloy_schema.schema.yaml
│   ├── dataset.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── data/
│   ├── raw/             # Downloaded raw datasets (parquet/csv)
│   └── processed/       # Cleaned, filtered, and transformed data
├── code/
│   ├── __init__.py
│   ├── _download_logic.py   # Core download and parse logic (MP & NIST)
│   ├── merge.py             # Dual-source merge and deduplication logic
│   ├── data_extraction.py   # CLI entry point for extraction
│   ├── preprocessing.py     # Filtering, normalization, ILR, Series derivation
│   ├── modeling.py          # RF training, CV, evaluation
│   ├── analysis.py          # Feature importance (Permutation/Shapley), VIF, diagnostics
│   └── cli/
│       └── download_cli.py  # CLI wrapper
├── tests/
│   ├── contract/          # Schema validation tests
│   ├── integration/       # Pipeline end-to-end tests
│   └── unit/              # Unit tests for transforms
├── docs/
│   └── quickstart.md
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: The structure follows a standard data science pipeline with a clear separation between raw data ingestion, processing, modeling, and analysis. The CLI is isolated in `code/cli/` to ensure the core logic remains testable and reusable. The use of `data/raw/` and `data/processed/` enforces the Data Hygiene principle by preventing in-place modification of raw data. The `merge.py` module explicitly handles the dual-source requirement of FR-001.

## Traceability Matrix

| Requirement | Code Module | Task ID | Notes |
| :--- | :--- | :--- | :--- |
| **FR-001** (Download MP & NIST) | `code/_download_logic.py`, `code/merge.py` | T1.1, T1.2, T1.3 | T1.3 handles the merge logic. |
| **FR-002** (Filter Monolithic) | `code/preprocessing.py` | T1.4 | Filters for non-composite, complete data. |
| **FR-003** (Normalize Units/Sum) | `code/preprocessing.py` | T1.4 | Normalizes to GPa and atomic fractions. |
| **FR-004** (ILR & CV) | `code/preprocessing.py`, `code/modeling.py` | T1.6, T2.1 | ILR in preprocessing; CV in modeling. |
| **FR-005** (Train/Test Split) | `code/modeling.py` | T2.2 | 80/20 split logic. |
| **FR-006** (Feature Importance) | `code/analysis.py` | T2.4 | Permutation importance in ILR space (see Note on FR-006). |
| **FR-007** (VIF Diagnostic) | `code/analysis.py` | T1.5 | Computes VIF on raw data; logs, does not fail. |
| **FR-008** (Associational Framing) | `code/analysis.py` | T2.5 | Ensures output text is associational. |
| **FR-009** (Independence Check) | `code/preprocessing.py` | T1.4b | Validates `measurement_method` field. |
| **SC-001** (Dataset Completeness) | `code/data_extraction.py` | T1.3 | Measured by count of valid entries. |
| **SC-002** (Model Accuracy) | `code/modeling.py` | T2.3 | Measured by test-set MAE vs SD. |
| **SC-004** (Collinearity Risk) | `code/analysis.py` | T1.5 | Measured by VIF values. |
| **SC-006** (Data Independence) | `code/preprocessing.py` | T1.4b | Measured by `is_independent_measurement` flag. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ILR Transformation | Required to handle the unit-sum constraint of compositional data (atomic fractions sum to 1.0). | Standard regression on raw fractions would produce spurious correlations and violate statistical assumptions due to collinearity. |
| Dual-Source Download (MP + NIST) | Necessary to maximize dataset size and coverage for aluminum alloys. Primary strategy per FR-001. | Using a single source (e.g., only Materials Project) risks insufficient sample size (<50 entries), leading to a failed pipeline or unreliable model. [Deferred] if single source suffices. |
| VIF Diagnostic | Required to detect and report collinearity between alloying elements (e.g., Cu and Mg often co-occur). | Ignoring collinearity would violate the spec's edge case requirement to flag VIF > 5 and would compromise the interpretability of the "associational" findings. High VIF is expected and confirms the need for ILR. |
| Permutation Importance (ILR Space) | Required for robust feature importance in non-linear models; back-transformation is mathematically invalid. | Simple back-transformation of RF importance scores is not mathematically rigorous and can distort the perceived effect of elements. (Note: This conflicts with FR-006 in the spec; see Summary). |
| Bootstrapping | Required to assess stability of feature importance in small samples (N < 100). | Without bootstrapping, feature importance rankings in small datasets may be spurious and unstable. |

## Implementation Phases

### Phase 1: Data Ingestion & Cleaning

1.  **T1.1: Download Materials Project Data** (`code/_download_logic.py`)
    *   Query MP API for aluminum alloys.
    *   Parse raw JSON/CSV.
    *   Output: `data/raw/mp_raw.parquet`.
2.  **T1.2: Download NIST Data** (`code/_download_logic.py`)
    *   Download NIST MDR dataset (direct link).
    *   Parse raw CSV/Parquet.
    *   Output: `data/raw/nist_raw.parquet`.
3.  **T1.3: Merge & Deduplicate** (`code/merge.py`)
    *   Concatenate MP and NIST data.
    *   Deduplicate based on composition (atomic fractions).
    *   Resolve source conflicts (prefer NIST if both exist).
    *   **Metric**: Count of valid entries (SC-001).
    *   Output: `data/processed/merged_raw.parquet`.
4.  **T1.4: Filter & Verify Independence** (`code/preprocessing.py`)
    *   Filter for monolithic alloys.
    *   **T1.4b: Independence Check**: Verify `measurement_method` field. If missing, attempt inference from source metadata; if impossible, exclude. Set `is_independent_measurement` flag.
    *   Filter for sum of major elements >= 0.95.
    *   Normalize units (GPa) and composition (atomic fractions).
    *   **Failure Condition**: If valid entries < 50, HALT with error (per Spec Edge Cases).
    *   Output: `data/processed/alloys_clean.parquet`.
5.  **T1.5: Collinearity Diagnostic** (`code/analysis.py`)
    *   Compute VIF on raw predictors.
    *   Log VIF scores. **Do not halt** if VIF > 5 (expected for compositional data).
    *   Output: `data/processed/collinearity_diagnostic.json`.
6.  **T1.6: ILR Transformation & Series Derivation** (`code/preprocessing.py`)
    *   Apply ILR transformation to atomic fractions.
    *   Derive `alloy_series` label from dominant element.
    *   Output: `data/processed/alloys_ilr.parquet`.

### Phase 2: Modeling & Evaluation

1.  **T2.1: Train Random Forest** (`code/modeling.py`)
    *   Train RF on ILR features + `alloy_series`.
    *   Perform k-fold cross-validation.
    *   **Power Check**: If N < 50, HALT (already handled in T1.4).
    *   **Bootstrap**: If N < 100, run 1000 bootstrap resamples for feature importance stability.
2.  **T2.2: Train/Test Split** (`code/modeling.py`)
    *   Split data into training and testing subsets using a standard proportion.
    *   Output: Train and Test sets.
3.  **T2.3: Evaluate Model** (`code/modeling.py`)
    *   Compute test-set MAE.
    *   **Metric**: Compare MAE to standard deviation of target (SC-002).
    *   **Note**: No arbitrary 0.05 threshold is used.
    *   Output: `data/processed/model_metrics.json`.
4.  **T2.4: Feature Importance** (`code/analysis.py`)
    *   Compute Permutation Importance in ILR space.
    *   Compute SHAP values for interpretability.
    *   Output: `data/processed/feature_importance.json`.
5.  **T2.5: Generate Report** (`code/analysis.py`)
    *   Draft results with explicit associational framing (SC-005).
    *   Include VIF diagnostic summary.
    *   Output: `data/processed/results_report.md`.

### Phase 3: Verification

1.  **T3.1: Contract Validation** (`tests/contract/`)
    *   Validate all output files against YAML schemas.
2.  **T3.2: Associational Framing Check** (`tests/unit/`)
    *   **Regex Check**: Verify `results_report.md` contains phrases: "associational", "correlation", "not causal".
    *   **Failure**: If phrases missing, flag as methodological error.
3.  **T3.3: Reproducibility Check**
    *   Re-run pipeline from scratch; verify checksums match.

## Contract Inventory

The following schema files are defined in `contracts/` and used for validation:

1.  `alloy_record.schema.yaml`: Schema for the cleaned `alloys_clean.parquet` (FR-002, FR-003, FR-009).
2.  `alloy_schema.schema.yaml`: Schema for raw/intermediate records (legacy/compatibility).
3.  `dataset.schema.yaml`: Schema for the final cleaned dataset (FR-001, FR-002).
4.  `model_metrics.schema.yaml`: Schema for model evaluation results (FR-005, SC-002).
5.  `model_output.schema.yaml`: Schema for the complete model output including diagnostics (FR-006, FR-007).
