# Implementation Plan: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Branch**: `001-predict-poissons-ratio` | **Date**: 2024-01-15 | **Spec**: `specs/001-predict-poissons-ratio/spec.md`
**Input**: Feature specification from `/specs/001-predict-poissons-ratio/spec.md`

## Summary

This project implements a predictive pipeline to determine how the concentration of specific alloying elements (Cu, Mg, Si, Zn, Mn) influences the Poisson's ratio of monolithic aluminum alloys. The approach involves extracting compositional and property data from public materials repositories, filtering for monolithic alloys with complete and *independent* data, applying Isometric Log-Ratio (ILR) transformations to handle compositional constraints, and training a Random Forest regressor. The implementation strictly adheres to the constraint of running on CPU-only CI (2 cores, 7 GB RAM) and frames all findings as associational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `compositions` (for ILR), `statsmodels` (for VIF)  
**Storage**: Local CSV/Parquet files under `data/`  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete data extraction, cleaning, training, and evaluation within 6 hours on 2 CPU cores.  
**Constraints**: No GPU/CUDA; no external API authentication (public endpoints only); strict unit normalization (GPa); compositional data handling (ILR).  
**Scale/Scope**: Expected dataset size < 1000 entries; model training time < 30 minutes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence/Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`. External datasets fetched from verified URLs in `research.md`. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Pass** | Pass if valid independent measurement data (Poisson's ratio from ultrasonic/Shear modulus) is found after filtering. Derived-only entries are excluded, not fatal, provided N >= 50 remains. |
| **III. Data Hygiene** | **Pass** | Raw data will be checksummed upon download. Transformations produce new files (e.g., `raw.csv` -> `filtered.csv` -> `processed.parquet`). |
| **IV. Single Source of Truth** | **Pass** | Feature importance and MAE metrics will be derived directly from `code/` outputs, not hand-typed. |
| **V. Versioning Discipline** | **Pass** | Task T020 implements automated SHA-256 hashing and state file updates for every artifact. |
| **VI. Unit Consistency** | **Pass** | Pipeline includes explicit normalization step to GPa and atomic fractions summing to 1.0. |
| **VII. Compositional Attribution** | **Pass** | Plan includes ILR transformation, Compositional Perturbation for importance, and Basis Sensitivity checks. |

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
│   ├── dataset.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-420-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── 00_run_pipeline.py
│   ├── 01_data_extraction.py
│   ├── 02_data_cleaning.py
│   ├── 03_feature_engineering.py
│   ├── 04_model_training.py
│   ├── 05_analysis.py
│   ├── 06_null_model_validation.py
│   └── requirements.txt
├── data/
│   ├── raw/
│   ├── processed/
│   └── checksums.txt
└── tests/
    ├── test_data_extraction.py
    ├── test_model_metrics.py
    └── test_contracts.py
```

**Structure Decision**: Single-project structure selected to minimize overhead for a linear research pipeline. Data is separated into `raw` (immutable) and `processed` (derived) to satisfy Data Hygiene principles. The master orchestrator `00_run_pipeline.py` coordinates the sequential execution of scripts 01-06.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **ILR Transformation** | Required by compositional data constraints (atomic fractions sum to 1.0). | Standard regression on raw fractions violates the simplex constraint, leading to spurious correlations and invalid coefficients. |
| **VIF Diagnostic** | Required to detect collinearity in raw space (FR-007). | Skipping VIF would ignore the spec's requirement to flag high collinearity, risking misinterpretation of feature importance. VIF scores are persisted in the final output. |
| **Separate Test Split** | Required for unbiased MAE estimation (FR-005). | Using only cross-validation MAE would overestimate performance on unseen data; a held-out set is mandated. |
| **Compositional Perturbation** | Required to rank elements in the original space without closure artifacts. | Simple back-transformation of gain importance is methodologically unsound for compositional data. |
| **Null Model Validation** | Required to establish statistical significance of feature importance in small N datasets. | Without a null distribution, importance scores may be artifacts of noise. |

## Implementation Phases & Tasks

### Phase 0: Data Extraction & Validation
- **Task T014 (Data Availability Gate)**: Query Materials Project and NIST APIs. Verify the presence of `shear_modulus_gpa` and `measurement_method` fields.
  - **Verification Logic**: For each entry, check if `measurement_method` contains "Ultrasonic", "Shear", or "Resonant" OR if `shear_modulus_gpa` is present and non-null (implying independent measurement).
  - **Filtering Action**: If an entry lacks independent measurement evidence (e.g., only has Young's modulus and no Shear modulus), mark it as `is_independent_measurement = False` and **exclude** it from the training dataset.
  - **Halt Condition**: If the number of *remaining* valid entries (after excluding derived-only data) is < 50, halt with error "Insufficient Data: <50 independent measurements found after filtering".
  - **Halt Condition**: If APIs are unreachable or require authentication, halt with error "Data Source Unavailable".

- **Task T015 (Power & Sensitivity Analysis)**: Calculate Minimum Detectable Effect Size (MDES) for the expected sample size (N=50).
  - *Halt Condition*: If MDES > 0.1 MAE improvement, halt with warning "Insufficient Power: Effect sizes <0.1 cannot be detected".

### Phase 1: Feature Engineering & Modeling
- **Task T016 (Compositional Perturbation)**: Implement feature importance ranking via perturbation.
  - *Method*: Perturb target element (e.g., Cu) by a small magnitude., proportionally reduce Al to maintain unit sum, measure prediction change.
  - *Output*: Ranked list of elements by perturbation impact.
- **Task T017 (Basis Sensitivity)**: Re-run importance ranking with an alternative ILR basis (e.g., balance Cu/Mg vs. rest).
  - *Output*: Flag if rankings change significantly (>10% rank shift).
- **Task T018 (Null Model Validation)**: Run Random Forest on multiple shuffled target permutations.
  - *Output*: th percentile threshold for feature importance. Only scores above this are reported as significant.

### Phase 2: Versioning & Reporting
- **Task T020 (Versioning Script)**: Generate SHA-256 hashes for all `data/` artifacts and update `state/...yaml`.
  - *Mechanism*: Python script using `hashlib` and `yaml` to update the state file automatically.
- **Task T021 (VIF Persistence)**: Ensure VIF scores and the `high_vif_flag` are written to the final `model_results.json` output file (see `model_output.schema.yaml`).

## Data Handling Notes

- **Composition Calculation**: `composition_al` is calculated as `1.0 - sum(Cu, Mg, Si, Zn, Mn)` using standard arithmetic.
- **ILR Library**: The `compositions` library is used *only* for the ILR transformation of the resulting vector, not for the balance calculation itself.
- **Data Integrity**: Raw data is never modified. All transformations produce new files with new checksums.
- **Independence Verification**: Entries are excluded if they lack explicit evidence of independent Poisson's ratio measurement (e.g., Shear modulus presence). This is a data filtering step, not a project failure condition, unless the filtered set is too small.