# Implementation Plan: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

**Branch**: `001-social-exclusion-prosociality` | **Date**: 2026-07-01 | **Spec**: `specs/001-social-exclusion-prosociality/spec.md`
**Input**: Feature specification from `specs/001-social-exclusion-prosociality/spec.md`

## Summary

This feature implements a reproducible research pipeline to quantify the causal effect of experimentally induced social exclusion on subsequent prosocial behavior (monetary donation/allocation). The approach involves ingesting open behavioral datasets from OSF (via verified HuggingFace mirrors), validating schemas, standardizing variables, and performing a Zero-Inflated Gamma (ZIG) or Hurdle meta-analysis. The analysis strictly separates Randomized Controlled Trials (Causal Pool) from observational studies (Associational Pool) to prevent causal overreach. The pipeline enforces strict data hygiene, handles zero-inflation natively without imputing structural zeros, and performs a scientifically valid sensitivity analysis on model assumptions (link functions and distributions).

**Critical Note on Data Availability**: The current "Verified datasets" block provided for this project contains **zero** datasets matching the required schema (social exclusion + prosocial outcome). Consequently, the pipeline will execute schema validation, find no valid datasets, and halt with an "Insufficient Data" error as per FR-008. This plan is designed to handle this failure mode gracefully and correctly.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `requests`, `pyyaml`, `pytest`, `metafor` (or `meta` equivalent for Python)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`) with checksums; no external DB.  
**Testing**: `pytest` (unit tests for ingestion logic, integration tests for model fitting on synthetic data).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM).  
**Project Type**: Data Science Pipeline / CLI Tool  
**Performance Goals**: Complete ingestion, cleaning, and analysis (if data existed) within 4 hours on CPU; memory usage < 6 GB.  
**Constraints**: No GPU; no heavy LLM inference; strict adherence to zero-inflated modeling for donation data; halt if <3 valid datasets found.  
**Scale/Scope**: **0 valid datasets currently available** in the verified list. The pipeline is designed to aggregate multiple public datasets *if* valid sources are added to the verified list in the future.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The following checks reflect the current state of data availability. Since the verified list contains no valid datasets for this study, principles requiring data implementation are marked as **FAIL** with a strategy to halt.

| Principle | Status | Verification Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/analysis.py`; `requirements.txt` pins versions; data fetched from canonical URLs (even if none exist). The *logic* is reproducible. |
| **II. Verified Accuracy** | **FAIL** | The provided "Verified datasets" block contains **zero** datasets matching the study's schema. The system correctly identifies this absence and halts, satisfying the requirement to not use invalid data, but the *input data block* itself fails the accuracy check for this specific research question. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums; no in-place modification; derived data in `data/processed/`. (Logic is ready, data is absent). |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated programmatically from `data/processed/` via `code/`. (Logic is ready, data is absent). |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed in `state/...yaml`; `updated_at` timestamps managed by agent. |
| **VI. Experimental Condition Fidelity** | **FAIL** | No valid datasets exist to implement the exclusion condition. The pipeline halts before this step can be attempted, preventing the violation of implementing a condition from invalid data. The principle cannot be satisfied because the required data is missing. |
| **VII. Behavioral Outcome Independence** | **PASS** | Data model treats `condition` and `prosocial_amount` as distinct columns; no circular derivation logic. (Logic is ready, data is absent). |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-exclusion-prosociality/
├── plan.md              # This file (revised)
├── research.md          # Phase 0 output (revised)
├── data-model.md        # Phase 1 output (revised)
├── quickstart.md        # Phase 1 output (revised)
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-382-the-impact-of-simulated-social-exclusion/
├── code/
│   ├── __init__.py
│   ├── ingestion.py       # OSF download, schema validation, standardization
│   ├── preprocessing.py   # Missing value handling, zero-inflation prep
│   ├── analysis.py        # ZIG/Hurdle models, Meta-analysis, Sensitivity
│   └── main.py            # CLI entry point
├── data/
│   ├── raw/               # Downloaded raw files (checksummed)
│   └── processed/         # Standardized CSVs, aggregated results
├── tests/
│   ├── test_ingestion.py
│   ├── test_analysis.py
│   └── fixtures/          # Synthetic test data
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The pipeline is a linear workflow (Ingest -> Clean -> Analyze) best suited for a modular script-based approach rather than a web service or mobile app. This minimizes overhead and fits the free-tier CPU constraints.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Zero-Inflated Models** | Donation data is inherently zero-inflated (many non-donors). | Standard OLS or Gamma GLM would produce biased estimates by treating zeros as continuous values or requiring arbitrary imputation, violating FR-002 and FR-003. |
| **Dual Pool Strategy** | Causal claims require RCTs; observational data cannot support them. | Merging all data would conflate correlation with causation, violating the "Causal Pool" requirement in FR-007 and the study's core hypothesis. |
| **Sensitivity Sweep (Link/Distribution)** | Model assumptions (link function, distribution) must be robust. | A single model run cannot verify stability; the sweep (FR-005) is required to ensure the effect is not an artifact of parameter choice. *Note: Threshold sweep was rejected as scientifically invalid.* |

## Requirements Mapping (Updated)

- **FR-001**: System MUST download raw data from OSF URLs specified in the configuration and merge them into a single standardized dataframe.
- **FR-001.5**: System MUST validate the schema of every downloaded dataset. If any are missing, the dataset MUST be rejected and logged.
- **FR-002**: System MUST impute missing values (NaN) in the `prosocial_amount` column using *median* imputation for datasets with <5% missingness. **Structural zeros (value=0) MUST NOT be imputed**.
- **FR-003**: System MUST execute a **Zero-Inflated Gamma (ZIG)** or **Hurdle** model for continuous outcomes. The model MUST use `prosocial_amount` as the dependent variable and `condition` (binary) as the independent variable.
- **FR-004**: System MUST calculate and report the confidence interval for the exclusion effect coefficient for both the Causal (RCT) and Associational pools.
- **FR-005 (Revised)**: System MUST perform a sensitivity analysis by re-running the regression with a sweep of **link functions** (logit vs. probit) for the zero-inflation component and **distributional assumptions** (Gamma vs. Log-Normal) for the positive component. The result is considered robust if the coefficient variance is < 10% across this range. *(Replaces invalid threshold sweep).*
- **FR-006**: System MUST detect and exclude datasets where the exclusion group sample size (rows where `condition` == 1) is < 5 participants from the primary meta-analysis pool.
- **FR-007**: System MUST filter datasets based on the `randomized` flag. The primary causal analysis MUST only include datasets where `randomized` == true.
- **FR-008**: System MUST halt execution and report an error if fewer than 3 valid datasets (passing FR-001.5) are found after ingestion.

## Success Criteria (Updated)

- **SC-001**: The proportion of downloaded OSF datasets successfully merged into the standard format is measured against the total number of valid URLs provided in the run configuration.
- **SC-002**: The effect size (regression coefficient) of exclusion on prosocial behavior is measured against the null hypothesis ($\beta = 0$) to determine statistical significance at $\alpha = 0.05$ for the **Causal Pool**.
- **SC-003 (Revised)**: The stability of the effect size estimate is measured across the **link function/distribution sweep**; the result is considered robust if the coefficient variance is < 10% across this range. *(Replaces invalid threshold sweep).*
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier limits.
- **SC-005**: The count and percentage of datasets excluded due to insufficient sample size (n < 5) is measured and reported. Additionally, a **meta-analytic power analysis** will be performed to report the detectable effect size given the number of studies and heterogeneity.
- **SC-006**: The number of datasets included in the **Causal Pool** vs. the **Associational Pool** is reported.