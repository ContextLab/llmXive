# Implementation Plan: Gut Microbiome-Sleep Architecture Correlation

**Branch**: `001-gut-microbiome-sleep-architecture` | **Date**: 2026-06-27 | **Spec**: `specs/001-gut-microbiome-sleep-architecture/spec.md`
**Input**: Feature specification from `/specs/001-gut-microbiome-sleep-architecture/spec.md`

## Summary

This project implements a rigorous, reproducible analysis pipeline to investigate the **associational** correlation between gut microbiome composition (metagenomic counts) and sleep architecture (polysomnography/actigraphy metrics). The system ingests data, validates variable completeness (FR-001), and applies a **Centered Log-Ratio (CLR)** transformation to address the compositional nature of the data before any statistical testing.

The statistical method is selected dynamically based on distributional properties:
1.  **Zero-Inflated Negative Binomial (ZINB)**: Selected if proportion of zeros > 30% **OR** over-dispersion ratio > 1.5.
2.  **Spearman Rank Correlation**: Selected if non-normal (Shapiro-Wilk p < 0.05) but not zero-inflated.
3.  **Pearson Correlation**: Selected if normally distributed (Shapiro-Wilk p ≥ 0.05).

The pipeline applies Benjamini-Hochberg correction for multiple comparisons (FR-003) and performs robustness checks including:
-   **Collinearity Diagnostics**: Matrix rank check for perfect multicollinearity (FR-006) followed by VIF calculation on CLR-transformed data (VIF > 5 flagged).
-   **Sensitivity Analysis**: Re-running significance at p < 0.01, p < 0.05, p < 0.10 and reporting the percentage change in significant findings (FR-005).
-   **Power Analysis**: Calculating minimum N to detect r ≥ 0.3 with Power ≥ 0.80, adjusted for FDR and sparsity (US-3).

All findings are explicitly labeled as "associational" (FR-004). The pipeline is designed to execute entirely on a CPU-only GitHub Actions runner within 6 hours.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels` (for ZINB and VIF), `scikit-learn` (for CLR and robustness), `pyyaml`, `pytest`, `pwr` (for power analysis).  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/results`, `data/config`).  
**Testing**: `pytest` (unit, integration, contract).  
**Target Platform**: `ubuntu-latest` GitHub Actions runner (CPU-only, cores, 7GB RAM).  
**Project Type**: Data analysis library / CLI pipeline.  
**Performance Goals**: Complete full pipeline (ingestion -> analysis -> reporting) in < 6 hours for N < 1000 subjects.  
**Constraints**: No GPU available; no access to gated clinical datasets; must handle zero-inflated, compositional data; must explicitly avoid causal language.  
**Scale/Scope**: < 500 taxa, < 1000 subjects, < 7 GB RAM.  
**Data Reality**: No open dataset exists containing both metagenomic and sleep data. The project is a **Methodology Validation Study** using a **Dirichlet-Multinomial synthetic data generator** to mimic real statistical properties (zero-inflation, over-dispersion, sum constraint).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **PASS**. Plan mandates pinned `requirements.txt`, isolated virtualenv, deterministic random seeds, and a `validation_mode_flag.json` to toggle synthetic data generation.
- **II. Verified Accuracy**: **PASS**. Plan includes Reference-Validator integration in CI (see CI/CD Workflow); citations in `research.md` restricted to verified URLs/DOIs.
- **III. Data Hygiene**: **PASS**. Plan mandates checksumming of `data/raw` files; no in-place modification; derived files in `data/processed`.
- **IV. Single Source of Truth**: **PASS**. All statistics trace to `data/results/correlation_matrix.json` (generated from `data/results/correlation_results.csv`). No hand-typed numbers in reports.
- **V. Versioning Discipline**: **PASS**. Artifacts will carry content hashes; state file updated on change.
- **VI. Biological Sample Integrity**: **PASS**. Plan includes a metadata check for chain-of-custody logs if real data is used. If `validation_mode_flag.json` is present (synthetic mode), this check is bypassed as per the exception for synthetic validation.
- **VII. Sleep Metric Standardization**: **PASS**. Plan mandates validation of sleep stage definitions (REM, SWS) against standard scoring criteria before analysis.

## CI/CD Workflow

The `analysis.yml` workflow integrates the Reference-Validator:
1.  **Checkout & Setup**: Install Python 3.11 and dependencies.
2.  **Citation Validation**: Run `python -m scripts.validate_citations` against `contracts/citations.json`. Fails if any URL is unreachable or DOI mismatch > 0.3.
3.  **Pipeline Execution**: Run `python code/main.py`.
4.  **Contract Testing**: Run `pytest tests/contract/` against generated JSON outputs.
5.  **Artifact Upload**: Upload `data/results/` and `data/metadata/` as artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-sleep-architecture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── .gitkeep
│   ├── citations.json
│   ├── correlation_result.schema.yaml
│   ├── dataset.schema.yaml
│   ├── dataset_schema.schema.yaml
│   ├── output.schema.yaml
│   ├── sensitivity_analysis.schema.yaml
│   ├── synthetic_data_manifest_schema.yaml
│   └── vif_report.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── ingest.py            # Data loading, validation, checksumming
├── synthetic_data.py    # Deterministic Dirichlet-Multinomial data generator
├── analysis.py          # CLR transformation, correlation logic, ZINB
├── diagnostics.py       # Matrix rank check, VIF, power analysis
├── reporting.py         # Sensitivity analysis, report generation, causal language filter
├── main.py              # Orchestration, timing, gate logic
└── utils.py             # Helper functions

data/
├── raw/
│   ├── synthetic_data.csv
│   └── real_data.csv    # (Optional, if available)
├── processed/
│   ├── cleaned_data.csv
│   ├── clr_transformed_data.csv
│   └── metadata/
│       ├── required_variables.yaml
│       └── static_collinearity_map.json
└── results/
    ├── validation_failure_report.json
    ├── correlation_results.csv
    ├── correlation_matrix.json
    ├── vif_report.json
    ├── sensitivity_analysis.json
    └── timing_evidence.json

tests/
├── __init__.py
├── unit/
│   ├── test_ingest.py
│   ├── test_analysis.py
│   └── test_diagnostics.py
├── integration/
│   └── test_pipeline_synthetic.py
└── contract/
    └── test_contracts.py

.github/
└── workflows/
    └── analysis.yml
```

**Structure Decision**: Single project structure selected to minimize overhead for a data analysis pipeline. Directories strictly separated by stage (`raw`, `processed`, `results`) to enforce Data Hygiene (Constitution III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CLR Transformation | Microbiome data is compositional (sum constraint). Standard correlations yield spurious results. | Ignoring compositionality violates statistical validity. |
| ZINB Model | Data is expected to be zero-inflated (>30% zeros). | Simple Pearson/Spearman would yield biased estimates. |
| Matrix Rank Check | FR-006 requires detection of perfect multicollinearity via rank. | VIF alone cannot detect perfect linear dependence (division by zero). |
| Synthetic Data Gate | No verified real-world dataset with both modalities exists. | Running on real data only would make the project unexecutable; synthetic data allows pipeline validation. |
| Simulation Power Analysis | ZINB power analysis requires simulation, not t-test approximation. | `tt_solve_power` underestimates required N for zero-inflated data. |

## Phase Breakdown

### Phase 0: Data Ingestion & Validation
-   **T090**: Generate synthetic data (Dirichlet-Multinomial) if `validation_mode_flag.json` exists.
-   **T004d**: Populate `required_variables.yaml` with variable names from the generated/loaded data.
-   **T012**: Validate presence of all required variables.
-   **T013**: If validation fails, write `data/results/validation_failure_report.json` and halt.

### Phase 1: Preprocessing
-   **T022**: Apply CLR transformation if data is compositional (sum constraint detected).
-   **T014b**: Filter outliers (>1.5x IQR).

### Phase 2: Statistical Analysis
-   **T021**: Select method (ZINB/Spearman/Pearson) based on CLR-transformed data distribution.
-   **T021f_algo**: Perform Matrix Rank Check on CLR-transformed predictors.
-   **T021f_io**: Write `data/metadata/static_collinearity_map.json`.
-   **T079**: Calculate VIF for non-collinear predictors (threshold > 5).
-   **T020a**: Compute correlations (ZINB coefficients or Spearman/Pearson r).
-   **T003**: Apply Benjamini-Hochberg correction.

### Phase 3: Robustness & Reporting
-   **T005**: Perform sensitivity analysis (p < 0.01, 0.05, 0.10) and calculate stability score.
-   **T006d_init**: Initialize checksum state after data generation.
-   **T078**: Generate `sensitivity_analysis.json`.
-   **T079**: Generate `vif_report.json`.
-   **T016**: Measure execution time and write `timing_evidence.json`.
-   **T004**: Ensure all outputs include "Associational Finding:" prefix (FR-004).

## Task Dependencies (Resolved)

-   **T004d** depends on **T090** (Sequential): Schema must be populated before validation.
-   **T021f_algo** depends on **T022** (Sequential): Collinearity check runs on CLR-transformed data.
-   **T079** depends on **T021f_io** (Sequential): VIF calculation uses the collinearity map.
-   **T006d_init** depends on **T090** (Sequential): Checksums generated after data creation.
-   **T081/T082** depend on **validation_mode_flag.json**: If present, skip real-data fetch.

## Success Criteria Mapping

-   **SC-001**: Measured by `data/results/validation_failure_report.json` (if missing = success).
-   **SC-002**: Measured by `data/results/sensitivity_analysis.json` (stability_score).
-   **SC-003**: Measured by `data/results/vif_report.json` (presence of warnings, is_collinear flag).
-   **SC-004**: Measured by `data/results/timing_evidence.json` (duration < 6h).
-   **SC-005**: Measured by `data/results/power_analysis.json` (flag if N < required).