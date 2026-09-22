# Implementation Plan: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Branch**: `001-doomscrolling-anxiety` | **Date**: 2026-06-25 | **Spec**: `specs/001-doomscrolling-anxiety/spec.md`
**Input**: Feature specification from `/specs/001-doomscrolling-anxiety/spec.md`

## Summary

This project implements a statistical analysis pipeline to test the hypothesis that frequency of negative news consumption on social media **associates with** elevated anxiety scores, independent of demographic factors. The approach involves downloading the verified **NHANES 2017-2018** dataset, performing strict data hygiene (listwise deletion, VIF checks), fitting a multiple linear regression model with diagnostic validation, and generating visualizations and robustness checks. The implementation adheres to the project constitution's requirements for reproducibility, data hygiene, and psychometric validity, while operating within the constraints of a CPU-only GitHub Actions runner (limited cores, 7GB RAM).

**Note on Data & Constructs**: The primary dataset (NHANES) contains 'general anxiety' (GAD-7) but not 'anticipatory anxiety'. Per FR-008, the system will use 'general anxiety' as a proxy and explicitly flag this limitation. The 'news exposure' variable will be proxied by available 'media consumption' variables. If the schema does not match, the pipeline halts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `datasets>=2.14.0`  
**Storage**: Local file system (`data/`, `output/`)  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for data cleaning logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: Full pipeline execution ≤ 60 seconds for ≤ 100k records; memory usage < 6GB.  
**Constraints**: No GPU; no external credentials; strict listwise deletion (no imputation); N ≥ 30 required to proceed.  
**Scale/Scope**: Single dataset analysis; one primary regression model; one robustness subset analysis (Education Level).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Justification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds will be pinned in `code/ingest.py` and `code/model.py`. External datasets will be fetched via verified NHANES URL. |
| **II. Verified Accuracy** | **PASS** | All dataset citations in `research.md` are limited to verified NHANES URLs. A pre-flight schema check validates the dataset against required variables before execution. |
| **III. Data Hygiene** | **PASS** | Raw data will be stored in `data/raw/` with SHA-256 checksums. Derived data in `data/processed/` will be immutable. PII scan will be run via `git-secrets` or equivalent in CI. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final output will be generated programmatically from `data/processed/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | Artifacts will include content hashes in `state/`. `requirements.txt` will be pinned. |
| **VI. Ethical Human‑Subjects** | **PASS** | The selected dataset (NHANES) is public, anonymized, and IRB-approved by the original collectors. No PII will be stored. |
| **VII. Psychometric Validity** | **PASS (with limitation)** | The anxiety instrument used is the GAD-7 (Generalized Anxiety Disorder 7-item scale) from NHANES. The plan documents this instrument and explicitly flags the use of 'general anxiety' as a proxy for 'anticipatory anxiety' in `research.md` and the output `flags` array. |

## Project Structure

### Documentation (this feature)

```text
specs/001-doomscrolling-anxiety/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-540-the-influence-of-social-media-doomscroll/
├── code/
│   ├── __init__.py
│   ├── ingest.py          # Data download, streaming, and cleaning
│   ├── model.py           # Regression fitting, diagnostics, robustness
│   ├── viz.py             # Plot generation
│   └── main.py            # Orchestration script
├── data/
│   ├── raw/               # Raw downloaded files (checksummed)
│   └── processed/         # Cleaned CSVs for analysis
├── output/
│   ├── plots/             # Generated PNG/SVG files
│   └── results/           # JSON/CSV regression results
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   └── test_model.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and alignment with the "CLI tool" nature of the analysis. The `code/` directory isolates logic, `data/` separates raw and processed states, and `tests/` ensures contract compliance.

## Complexity Tracking

*No violations found. The scope is strictly limited to a single regression analysis with standard diagnostics.*

## Methodological Rigor & Coverage

This plan explicitly addresses every Functional Requirement (FR) and Success Criterion (SC) from the spec:

- **FR-001 (Ingestion)**: Addressed in `code/ingest.py` (Phase 1). Includes pre-flight schema check against `contracts/dataset.schema.yaml`.
- **FR-002 (Listwise Deletion/N≥30)**: Addressed in `code/ingest.py`. Hard stop if N < 30. Low power warning if 30 ≤ N < 100. (Note: Removed non-existent 'N < 130' override; strictly follows spec).
- **FR-003 (Regression & Distinct Constructs)**: Addressed in `code/model.py`. If 'baseline_anxiety' and 'anxiety_score' are from the same timepoint/instrument, 'baseline_anxiety' is dropped to avoid coupling, and a warning is emitted. The logic references `data-model.md` and `dataset.schema.yaml` for field definitions.
- **FR-004 (Correlation)**: Addressed in `code/model.py`.
- **FR-005 (Visualization)**: Addressed in `code/viz.py`.
- **FR-006 (Robustness)**: Addressed in `code/model.py`. Replaced 'social_media_engagement' check with 'Education Level' subgroup analysis (High vs. Low) due to data availability. The correlation condition (r > 0.3) is replaced by a sample size check for the subgroup. This deviation is documented in the 'Task Dependencies & Amendments' section.
- **FR-007 (Assumption Checks)**: Addressed in `code/model.py` (Residuals, Q-Q, Shapiro-Wilk).
- **FR-008 (Proxy Flagging)**: Addressed in `code/model.py` and `output.schema.yaml`. If 'general_anxiety' is used, the string 'Proxy Used: General Anxiety' is added to the `flags` array.
- **SC-001 to SC-005**: All metrics (p-values, R², consistency, assumption p-values, runtime) are captured in the output schema, including the `runtime` field for SC-005.

## Compute Feasibility

- **CPU-First**: The entire pipeline (download, cleaning, OLS regression on a large dataset, plotting) is computationally lightweight and will run comfortably on the GitHub Actions runner.
- **No GPU Required**: No transformer models or deep learning are involved.
- **Streaming Strategy**: `datasets.load_dataset(..., streaming=True)` will be used for initial inspection. If the dataset is large, a **random sample** (seeded) of up to 100,000 rows will be drawn to ensure CPU feasibility and avoid selection bias. The data is then materialized into a pandas DataFrame for regression.

## Data Availability

- **Primary Source**: NHANES 2017-2018 (via verified CDC/FTP or HuggingFace mirror).
- **Constraint**: The spec requires `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, and demographics.
- **Fallback**: 
  - If `news_exposure_freq` is missing: HALT (Edge Case 1).
  - If `anticipatory_anxiety` is missing but `general_anxiety` exists: USE PROXY, FLAG (FR-008).
  - If `baseline_anxiety` is not distinct from `anxiety_score`: DROP `baseline_anxiety` from model, FLAG.
- **Verification**: Only the verified NHANES URLs will be cited. If the schema does not match, the pipeline halts.

## Task Dependencies & Amendments

- **Amendment T036**: **REMOVED**. The plan strictly follows the spec's N=30 threshold.
- **Task T025b (Robustness)**: Implements the 'Education Level' subgroup check, not the 'engagement' check. The correlation condition (r > 0.3) is replaced by a sample size check for the subgroup. This deviation is documented here.
- **Task T037 (Data Source Verification)**: Performs schema validation. If the schema is invalid, the pipeline halts.
- **Task T001b (Source Structure)**: Will be executed to create the directory tree and `__init__.py` files.
- **Task T004 (Reproducibility)**: Will pin random seeds in code and log them.
- **Task T019a (Construct Validity)**: Will verify distinctness of anxiety measures via metadata or variable names. If ambiguous, it will drop the baseline covariate and flag.
- **Task T033 (Benchmark)**: Will produce a `benchmark.log` to verify SC-005 (≤ 60s runtime).
