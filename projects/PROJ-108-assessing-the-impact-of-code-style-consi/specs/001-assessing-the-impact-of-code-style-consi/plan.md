# Implementation Plan: Assessing the Impact of Code Style Consistency on LLM Code Understanding

**Branch**: `001-assess-code-style-impact` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-assess-code-style-impact/spec.md`

## Summary

This project assesses whether code style consistency (quantified via `pylint` and `radon` metrics) impacts Large Language Model (LLM) performance on code understanding tasks (summarization and bug localization). The approach involves: (1) calculating normalized style scores for code samples from CodeSearchNet and Defects4J; (2) stratifying samples into High/Medium/Low consistency groups for descriptive analysis; (3) running StarCoder small-scale (CPU-only) inference to generate summaries and bug predictions; and (4) performing statistical analysis (ANCOVA for group differences, Linear Regression for continuous correlation) to measure the effect of style, controlling for code complexity (using file size as a proxy to avoid multicollinearity with style metrics).

**Statistical Clarification**: The plan distinguishes between two analyses:
1.  **ANCOVA**: Tests for mean differences in performance between stratified groups (High/Med/Low) while controlling for covariates.
2.  **Linear Regression**: Measures the continuous correlation between the style score and performance (satisfying SC-001).

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `pylint`, `radon`, `transformers` (CPU-optimized), `datasets`, `scikit-learn`, `scipy`, `pandas`, `statsmodels`  
**Storage**: Local files (Parquet/CSV) within `data/` directory  
**Testing**: `pytest` (unit tests for scoring logic, integration tests for inference pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: Limited CPU resources and GB RAM., no GPU)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete full pipeline within 6 hours; memory usage < 7 GB  
**Constraints**: No GPU/CUDA; no heavy quantization libraries requiring CUDA; strict 6-hour timeout; CPU-only inference for StarCoder 1B  
**Scale/Scope**: Subset of CodeSearchNet (Python) and Defects4J (Python subset if available, else fallback) sufficient for statistical power analysis within compute limits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt` and random seeds in `code/`. External datasets are fetched from canonical HuggingFace/parquet sources listed in `research.md`.
- **II. Verified Accuracy**: **Mandatory Step**: The `00_validate_urls.py` script (Reference-Validator) MUST run before data loading. All dataset URLs in `research.md` are sourced strictly from the "Verified datasets" block. No invented URLs.
- **III. Data Hygiene**: Plan includes checksumming raw data and storing derived metrics in `data/metadata/` without modifying raw sources.
- **IV. Single Source of Truth**: Statistical reports will be generated programmatically from `data/` artifacts; no hand-typed numbers in the final report.
- **V. Versioning**: **Mechanism Defined**: The `00_hash_artifacts.py` script generates content hashes for all artifacts and updates `state/*.yaml` files automatically after each phase.
- **VI. Style‑Consistency Scoring**: Plan explicitly defines the scoring pipeline using `pylint` (indentation/naming) and `radon` (line-length) as per the constitution.
- **VII. Statistical Evaluation Rigor**: Plan mandates ANCOVA, t-tests, effect sizes (Cohen's d), and 95% CIs, with scripts stored in `code/`.

## Test Traceability

Every Functional Requirement (FR) and User Story (US) maps to a specific test script and contract schema to ensure full coverage.

| Requirement | User Story | Test Script | Contract Schema | Test Type |
| :--- | :--- | :--- | :--- | :--- |
| **FR-001** (Style Score) | US-1 | `tests/unit/test_style_scoring.py` | `schema_code_sample.yaml` | Unit (Score range negative values) |
| **FR-002** (Stratification) | US-1 | `tests/unit/test_stratification.py` | `schema_code_sample.yaml` | Unit (Group assignment) |
| **FR-003** (Inference) | US-2 | `tests/integration/test_inference.py` | `schema_inference_result.yaml` | Integration (Output format) |
| **FR-004** (Metrics) | US-2 | `tests/unit/test_metrics.py` | `schema_performance_metric.yaml` | Unit (BLEU/F1 calc) |
| **FR-005** (ANCOVA/T-Test) | US-3 | `tests/integration/test_analysis.py` | `schema_statistical_report.yaml` | Integration (Stat output) |
| **FR-006** (Correction) | US-3 | `tests/unit/test_corrections.py` | `schema_statistical_report.yaml` | Unit (P-value adjustment) |
| **FR-007** (Timeout) | US-2 | `tests/integration/test_timeout.py` | N/A | Integration (Exit code indicating resource exhaustion) |
| **FR-008** (Ablation) | US-3 | `tests/integration/test_ablation.py` | `schema_statistical_report.yaml` | Integration (R² check) |
| **FR-009** (Pre-Check) | US-3 | `tests/unit/test_precheck.py` | N/A | Unit (Effect size gate) |
| **SC-005** (Robustness) | US-3 | `tests/integration/test_robustness.py` | `schema_statistical_report.yaml` | Integration (Spearman) |
| **SC-004** (Validity) | US-3 | `tests/unit/test_validity.py` | `schema_statistical_report.yaml` | Unit (R² extraction) |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-code-style-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── schema_code_sample.yaml
│   ├── schema_inference_result.yaml
│   ├── schema_performance_metric.yaml
│   └── schema_statistical_report.yaml
└── tasks.md             # Phase 2 output (Generated by Implementer Agent, NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-108-assessing-the-impact-of-code-style-consi/
├── code/
│   ├── requirements.txt
│   ├── 00_validate_urls.py       # Reference-Validator (Constitution II)
│   ├── 00_hash_artifacts.py      # Versioning Mechanism (Constitution V)
│   ├── 01_style_scoring.py       # FR-001, FR-002
│   ├── 02_stratification.py      # FR-002
│   ├── 03_inference.py           # FR-003, FR-007
│   ├── 04_evaluation.py          # FR-004
│   ├── 05_statistical_analysis.py # FR-005, FR-006, FR-008, FR-009
│   ├── 06_robustness_check.py    # SC-005
│   └── utils/
│       └── metrics.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) is selected to minimize overhead for a research pipeline. The `code/` directory contains sequential scripts corresponding to the user stories (US-1 to US-3).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| ANCOVA vs. Simple ANOVA | Required by FR-005 to control for code complexity and file age, isolating the style effect. | Simple ANOVA would conflate style effects with complexity, violating the study's internal validity. |
| CPU-only StarCoder 1B | Required by FR-007 to run on free-tier CI (no GPU). | GPU-based models (e.g., StarCoder 15B) or quantization requiring CUDA would fail the runtime constraint. |
| Multiple Statistical Tests | Required by FR-006 to handle multiple comparisons (Tukey HSD, Bonferroni). | Single test would inflate Type I error rates, violating statistical rigor (Constitution Principle VII). |
| Linear Regression | Required by SC-001 to measure continuous correlation. | ANCOVA only measures group differences; regression is needed for the continuous relationship. |