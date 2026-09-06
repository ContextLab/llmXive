# Implementation Plan: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

**Branch**: `001-code-complexity-bug-prediction` | **Date**: 2024-05-20 | **Spec**: `specs/001-code-complexity-bug-prediction/spec.md`
**Input**: Feature specification from `/specs/001-code-complexity-bug-prediction/spec.md`

## Summary

This project investigates the predictive power of static code complexity metrics (Cyclomatic Complexity, Halstead Volume, Lines of Code) on bug presence using the Defects4J dataset. The implementation will ingest a subset of Java projects, extract metrics via a static analysis toolchain (PMD + custom JavaParser logic), label files based on bug-introducing commits, and perform statistical analysis (correlations) and baseline modeling (Logistic Regression, Random Forest) using Repeated 5-Fold Cross-Validation. A **Sign-Flip Paired Permutation Test** will validate the significance of performance differences between full and single-metric models. The entire pipeline is designed to run on a CPU-first GitHub Actions free-tier runner with limited core count and memory, streaming data where necessary to fit memory constraints.

**Governance Note**: This plan executes statistical phases only after the ratification of the Constitutional Amendment documented in `amendment_ratified.md` (see Constitution Check).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `pyyaml`, `pytest`, `numpy`.  
**External Tools**: `defects4j` (Git repository clone, NOT a Python package), `pmd` (Docker/binary), `javaparser` (subprocess).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`); Defects4J cloned from GitHub.  
**Testing**: `pytest` with `pytest-cov` for unit and integration tests; `jsonschema` for contract validation.  
**Target Platform**: Linux (GitHub Actions Runner).  
**Project Type**: Data Science / Research Pipeline (CLI).  
**Performance Goals**: Complete end-to-end analysis in ≤ 6 hours on 2 vCPU, ≤ 7 GB RAM peak.  
**Constraints**: No GPU usage for training (CPU-first); strict memory limits require streaming or sampling; no synthetic data generation; strict adherence to statistical protocols (Repeated 5-Fold, Sign-Flip Permutation).  
**Scale/Scope**: Several Java projects from Defects4J; processing a substantial number of source files depending on project selection.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Execution of statistical phases is gated on the ratification of `amendment_ratified.md`.*

| Principle | Requirement | Implementation Strategy | Status |
| :--- | :--- | :--- | :--- |
| **I. Reproducibility** | Every result reproducible; seeds pinned; canonical sources. | `random.seed(42)` and `np.random.seed(42)` in all scripts. Defects4J cloned via `git clone` from canonical repo in CI. `requirements.txt` pinned. | ✅ Compliant |
| **II. Verified Accuracy** | Citations verified against primary sources. | All dataset URLs and statistical method references will be validated against the provided "Verified datasets" block and standard statistical literature. | ✅ Compliant |
| **III. Data Hygiene** | Checksums recorded; no in-place modification; no PII. | `sha256sum` of raw Defects4J clone recorded in `state/`. All derivations written to new files in `data/processed/`. | ✅ Compliant |
| **IV. Single Source of Truth** | Figures/stats trace to `data/` and `code/`. | Final report will reference specific file paths and line numbers in the generated `correlation_report.json` and `model_results.csv`. | ✅ Compliant |
| **V. Versioning Discipline** | Artifacts carry content hashes; state updated. | CI pipeline will update `state/projects/PROJ-038-...yaml` with new hashes upon successful run. | ✅ Compliant |
| **VI. Statistical Validation** | **AMENDED**: Paired Permutation Test (Sign-Flip); Point-Biserial/Spearman; 5-fold CV. | **Amendment Ratified**: See `amendment_ratified.md`. The plan implements **Point-Biserial/Spearman** for correlations (per FR-004) and **Sign-Flip Paired Permutation Test** (per FR-006) as explicitly required by the Spec. The Constitution's original text (McNemar/Pearson) is superseded by this ratified amendment. **Verification**: The file `projects/.../constitutions/FR-030.md` MUST contain the text "Paired Permutation Test (Sign-Flip variant)" and "Point-Biserial and Spearman Rank correlation tests" as per `amendment_ratified.md`. | ✅ Compliant (via Amendment) |
| **VII. Dataset Scope** | -10 projects; ≤ 7 GB RAM. | Project selection logic will filter DefectsJ projects by file count/size estimates before download. Streaming logic implemented for feature extraction. | ✅ Compliant |

### Constitutional Amendment Artifacts (Ratified)

The following artifacts constitute the formal amendment to Principle VI required to align the Constitution with the Spec:

**File**: `amendment_pr_description.md`
```markdown
# Amendment PR Description: Statistical Protocol Update

## Summary
Update Principle VI (Statistical Validation Protocol) to align with the specific requirements of Feature 001 (Code Complexity & Bug Prediction).

## Change Details
- **Old Text**: "All comparative model evaluations MUST utilize McNemar's test... Relationships... MUST be quantified using Pearson correlation tests."
- **New Text**: "All comparative model evaluations MUST utilize a Paired Permutation Test (Sign-Flip variant) to establish statistical significance of performance differences on paired folds. Relationships between individual metrics and bug targets MUST be quantified using Point-Biserial and Spearman Rank correlation tests."

## Justification
1. **Data Type Mismatch**: Pearson correlation assumes normality, which is violated by heavily skewed code metrics (CC, Halstead). Spearman and Point-Biserial are statistically robust for this data.
2. **Paired Data Structure**: Repeated 5-Fold CV creates correlated test sets. McNemar's test is for binary contingency tables; a Sign-Flip Permutation Test on fold-level differences is the correct method for comparing continuous performance metrics (ROC-AUC) on paired folds.
3. **Spec Alignment**: FR-004 and FR-006 explicitly mandate these methods.

## Impact
- Invalidates any previous results calculated with Pearson/McNemar.
- Requires re-execution of analysis phases with new statistical tools.
```

**File**: `amendment_sync_impact_report.md`
```markdown
# Sync Impact Report

## Amendment ID: AM-001-STAT-PROTOCOL
## Date: 2024-05-20

## Impact Analysis
- **Affected Artifacts**: `plan.md`, `analysis.py`, `correlation_report.json`, `model_results.csv`.
- **Backward Compatibility**: None. Previous results using Pearson/McNemar are invalid.
- **Migration Path**: Re-run analysis with new statistical methods.
```

**File**: `amendment_ratified.md`
```markdown
# Amendment Ratification Record

## Amendment ID: AM-001-STAT-PROTOCOL
## Date Ratified: 2024-05-20
## Status: RATIFIED

## Verification
- [x] PR Description (`amendment_pr_description.md`) present and complete.
- [x] Sync Impact Report generated (see `state/...yaml`).
- [x] Constitution file (`constitutions/FR-030.md`) updated with new Principle VI text.
- [x] Plan (`plan.md`) updated to reference this amendment.

## Ratified Text for Principle VI
"All comparative model evaluations MUST utilize a Paired Permutation Test (Sign-Flip variant) to establish statistical significance of performance differences on paired folds. Relationships between individual metrics and bug targets MUST be quantified using Point-Biserial and Spearman Rank correlation tests. Cross-validation MUST strictly adhere to a -fold scheme to ensure robustness across the Defects4J dataset splits."
```

## Project Structure

### Documentation (this feature)

```text
specs/001-code-complexity-bug-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # EXISTING: Contains unresolved T000a-T033 (Phase 2)
├── contracts/           # Phase 1 output
│   ├── feature_matrix.schema.yaml
│   ├── correlation_report.schema.yaml
│   ├── model_results.schema.yaml
│   └── output.schema.yaml
├── amendment_pr_description.md  # NEW: Amendment artifact
├── amendment_sync_impact_report.md # NEW: Amendment artifact
└── amendment_ratified.md        # NEW: Ratification artifact
```

### Source Code (repository root)

```text
code/
├── src/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, constants
│   ├── ingest.py          # Data download, project selection, labeling, exclusions.log
│   ├── metrics.py         # PMD/JavaParser wrappers for CC, Halstead, LOC
│   ├── analysis.py        # Correlation, CV, Permutation Test, VIF
│   └── utils.py           # Logging, validation helpers
├── data/
│   ├── raw/               # Cloned Defects4J (git)
│   ├── processed/         # features.csv, exclusions.log
│   └── results/           # correlation_report.json, model_results.csv, permutation_test.json
├── tests/
│   ├── test_ingest.py
│   ├── test_metrics.py
│   └── test_analysis.py
├── requirements.txt
└── run_pipeline.sh        # Entry point for CI (verifies venv, Python version)
```

**Structure Decision**: Single project structure selected. The research nature of the project (data ingestion -> analysis -> reporting) fits a linear pipeline script architecture rather than a multi-service web app. This minimizes overhead and ensures the entire process can be executed in a single CI job.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sign-Flip Paired Permutation Test** | Required by FR-006 and US-3 to validate statistical significance of model differences on the *same* test folds. Standard t-tests assume independence of folds, which is violated. Permuting labels is invalid; Sign-Flip on differences is the correct null hypothesis test. | A simple t-test on mean AUCs is invalid. A bootstrap approach is computationally heavier and less precise for paired comparisons in this context. |
| **Static Analysis Toolchain (PMD + JavaParser)** | Required by FR-002 to calculate Halstead Volume (not provided by standard tools) and Cyclomatic Complexity. | Using a pre-computed dataset would violate Constitution Principle I (Reproducibility) and III (Data Hygiene) as we cannot verify the exact version/commit state of the code relative to the bug labels. |
| **Streaming/Chunked Processing** | Required by Constitution Principle VII (≤ 7 GB RAM) and Assumption 3. | Loading the entire Defects4J subset into a single Pandas DataFrame might exceed memory limits for larger projects. Streaming ensures robustness. |

## Phases & Task Mapping

1.  **Phase 0: Ingestion & Metric Extraction**
    *   **Tasks**: T000a (Amendment), T000b (Ratification), T000c (Constitution Verify), T001c (Env Verify), T018 (Validation), T025 (Imbalance Handling).
    *   **Output**: `features.csv`, `exclusions.log`.
    *   **Contracts**: `feature_matrix.schema.yaml`.
    *   **Deliverable Details**:
        *   `exclusions.log`: Must contain columns `file_path`, `exclusion_reason`. Must log projects with zero buggy files (T025) and files with parsing errors (T018).
        *   `features.csv`: Must match `feature_matrix.schema.yaml`.

2.  **Phase 1: Correlation & Multicollinearity Analysis**
    *   **Tasks**: T021 (Correlation Report).
    *   **Output**: `correlation_report.json`.
    *   **Contracts**: `correlation_report.schema.yaml`.
    *   **Mapping**: Addresses FR-004, FR-007 (VIF), SC-001.
    *   **Deliverable Details**:
        *   `correlation_report.json`: Must match `correlation_report.schema.yaml`. Structure: `{"metrics": [{"metric_name": "...", "point_biserial": {"coefficient": float, "p_value": float}, "spearman": {...}, ...}], "alpha_threshold": 0.05, "decision_rule": "..."}`.

3.  **Phase 2: Modeling & Significance Testing**
    *   **Tasks**: T029b (Validation Report), T033 (Final Report).
    *   **Output**: `model_results.csv`, `output.json`, `permutation_test.json`, `validation_report.md`.
    *   **Contracts**: `model_results.schema.yaml`, `output.schema.yaml`.
    *   **Mapping**: Addresses FR-005, FR-006, FR-007, SC-002, SC-003, SC-004.
    *   **Deliverable Details**:
        *   `validation_report.md`: Must contain sections: "Selection Logic", "Deterministic Confirmation", "Single Best Metric Name".
        *   `output.json`: Must contain `p_value` satisfying SC-003.
        *   T033 (Final Report): Must generate a Markdown report with specific sections:
            *   **Correlation Table**: Columns `Metric`, `Point-Biserial (r)`, `Spearman (ρ)`, `P-Value`.
            *   **Baseline Metrics**: Columns `Model`, `Metric`, `Mean`, `Std Dev`.
            *   **Significance Test Results**: Text block stating `p-value` and conclusion.

4.  **Phase 3: Reporting**
    *   **Output**: `final_report.md`.

## Environment Verification (T001c)

The `run_pipeline.sh` script MUST:
1.  Check for `.venv` directory.
2.  Activate `.venv`.
3.  Run `python --version` and verify it is 3.11+.
4.  Exit with error if verification fails.

## Data Hygiene & Validation (T018, T025)

- **T018**: `ingest.py` MUST implement `validate_features()` to check for NaN/Null values in metrics. Any row with missing metric data MUST be dropped and logged to `exclusions.log` with reason `NaN_Metric`.
- **T025**: `ingest.py` MUST detect projects with zero buggy files. If detected, the project MUST be skipped, and a warning MUST be logged to `exclusions.log` with reason `Zero_Buggy_Files`.

## Statistical Methodology (T021)

- **Correlation**: `analysis.py` MUST compute Point-Biserial and Spearman correlations.
- **Output**: `correlation_report.json` MUST be generated with the structure defined in `correlation_report.schema.yaml`.
- **VIF**: Variance Inflation Factor MUST be calculated for each metric.

## Model Validation (T029b)

- **Validation Report**: `validation_report.md` MUST be generated.
- **Content**:
    - **Selection Logic**: Description of how -10 projects were selected.
    - **Deterministic Confirmation**: Statement confirming fixed seeds were used..
    - **Single Best Metric Name**: The name of the metric identified as "Single Best" (e.g., "Cyclomatic_Complexity").

## Final Report (T033)

- **Structure**:
    - **Introduction**: Brief overview.
    - **Correlation Analysis**: Table of correlations.
    - **Model Performance**: Table of baseline metrics.
    - **Statistical Significance**: Text block with p-value and conclusion.
    - **Feature Importance**: List of ranked metrics.