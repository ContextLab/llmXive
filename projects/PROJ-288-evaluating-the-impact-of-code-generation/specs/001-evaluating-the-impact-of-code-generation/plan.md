# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Time

**Branch**: `001-evaluating-llm-code-review-impact` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-llm-code-review-impact/spec.md`
**Input**: Feature specification from `specs/001-evaluating-llm-code-review-impact/spec.md`

## Summary

This project evaluates the impact of **explicit LLM disclosure** (vs. non-disclosure) on code review time. 

**Critical Methodological Clarification**: The study explicitly acknowledges that keyword filtering ("copilot", "llm", "generated") identifies PRs where the author *disclosed* LLM usage, not necessarily all LLM-generated code. The "Non-Disclosing" group serves as a negative control, which may contain both human-written code and undisclosed LLM-generated code. Therefore, the primary research question is reframed: **"Does explicitly disclosing LLM usage in a PR affect its review duration compared to PRs that do not disclose such usage?"**

The technical approach involves:
1.  **Data Acquisition**: Querying the GitHub REST API for PRs in high-star repositories, filtering for keywords to identify the "Disclosing" group, and fetching a stratified sample of "Non-Disclosing" PRs from the same repositories.
2.  **Classification & Validation**: Using keywords to define the primary "Disclosing" label. A separate, external code-specific dataset (e.g., CodeParrot/CodeXGLUE) is used to calibrate style heuristics (formatting, comment density) which are then used *only* as covariates and for validation, not to define the primary group label. A manual validation set of samples is used to estimate misclassification rates of the *disclosure signal* (e.g., false positives where humans use keywords).
3.  **Statistical Analysis**: Performing a Mann-Whitney U test (primary) and a Linear Mixed-Effects Regression with SIMEX correction for misclassification bias (secondary) to compare review durations. The model includes code size, reviewer count, and a proxy for reviewer experience as fixed effects, and repository as a random effect.
4.  **Visualization**: Generating diagnostic plots and a summary report.

The implementation strictly adheres to the GitHub Actions free-tier constraints (2 CPU, 7 GB RAM, 6h limit) by using CPU-optimized libraries (`statsmodels`, `scikit-learn`, `pandas`) and sampling data where necessary.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `requests`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `simex` (or custom implementation)  
**Storage**: Local CSV/Parquet files in `data/` (no external database required for runtime)  
**Testing**: `pytest` (unit tests for heuristics, integration tests for API rate limiting)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Data Analysis CLI / Research Pipeline  
**Performance Goals**: Complete data extraction, classification, and analysis within 6 hours on CPU-only runner.  
**Constraints**:
-   No GPU usage.
-   Memory usage < 7 GB (data must be streamed or chunked if large).
-   API rate limiting: A configurable threshold with a token bucket algorithm.
-   Strict adherence to `spec.md` FR-001 through FR-010.
**Scale/Scope**: Targeting a sample of high-star repositories (≥1000 stars) with PRs matching specific keywords. Exact counts deferred to `research.md`.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pinning, random seed fixing, and execution of scripts against `data/` on fresh runners. |
| **II. Verified Accuracy** | **PASS** | Plan requires citing only verified dataset URLs from the `# Verified datasets` block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan mandates checksumming raw data, immutable derivations, and PII scanning. |
| **IV. Single Source of Truth** | **PASS** | Plan ensures all statistics trace to specific rows in `data/` and code blocks. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashing for artifacts and updates to `state/` timestamps. |
| **VI. LLM Code Identification** | **PASS** | Plan explicitly implements the keyword-based labeling for the primary group ("Disclosing") and uses style heuristics *only* for validation/covariates, with a validation log (`data/validation_log.csv`). The plan acknowledges the limitation that keywords are a proxy for *disclosure*, not necessarily *code origin*. |
| **VII. Statistical Rigor** | **PASS** | Plan mandates Mann-Whitney U test (α=0.05) as primary, and mixed-effects regression with SIMEX correction and specified covariates (code size, reviewer count, reviewer experience proxy). |

## FR Traceability Matrix

| FR ID | Requirement Summary | Plan Phase / Step | Implementation File | Step Detail |
| :--- | :--- | :--- | :--- | :--- |
| **FR-001** | Query GitHub API for PRs with keywords. | Data Acquisition | `code/data/fetch_prs.py` | Fetch PRs from high-star repos, filter by keywords. |
| **FR-002** | Classify using heuristics, validate on a sample set. | Classification | `code/data/classify.py` | Apply style heuristics for validation/covariates; log validation results. **Note**: Primary label is keyword-based; heuristics are secondary. |
| **FR-003** | Calculate review times. | Data Processing | `code/data/process.py` | Compute `first_review_time`, `total_review_time`. |
| **FR-004** | Mixed-effects regression with covariates. | Statistical Analysis | `code/analysis/models.py` | Fit LMER with `origin`, `code_size`, `reviewer_count`, `reviewer_experience`. |
| **FR-005** | Generate plots. | Visualization | `code/analysis/viz.py` | Boxplot, scatter, residual plots. |
| **FR-006** | Exclude outliers (>30 days). | Data Processing | `code/data/process.py` | Filter PRs with `total_review_time` > 30 days. |
| **FR-007** | Rate limiting (token bucket). | Data Acquisition | `code/data/fetch_prs.py` | Implement token bucket with exponential backoff. |
| **FR-008** | Sensitivity analysis on thresholds. | Statistical Analysis | `code/analysis/models.py` | Sweep confidence thresholds and report error rates. |
| **FR-009** | Stratified sampling & >50% exclusion. | Data Acquisition | `code/data/fetch_prs.py` | **Step**: For each repo, calculate % of PRs with keywords. If >50%, exclude repo. **Step**: Stratify sampling by repo size/activity. |
| **FR-010** | False positive estimation & matrix correction. | Statistical Analysis | `code/analysis/models.py` | **Step**: Use external baseline corpus to estimate false positive rate. **Step**: Apply SIMEX correction to regression coefficients if rate > 5%. |
| **SC-001** | Measure median difference via p-value. | Statistical Analysis | `code/analysis/models.py` | Output Mann-Whitney U p-value. |
| **SC-002** | Measure heuristic accuracy (Kappa ≥ 0.6). | Classification | `code/data/classify.py` | Calculate Cohen's Kappa on validation set. |
| **SC-003** | Measure code size impact (slope coefficients). | Statistical Analysis | `code/analysis/models.py` | **Output**: Extract and report `code_size_slope` for both "Disclosing" and "Non-Disclosing" groups. |
| **SC-004** | Measure distribution shape (Shapiro-Wilk). | Statistical Analysis | `code/analysis/models.py` | Perform Shapiro-Wilk test on residuals. |
| **SC-005** | Measure feasibility (h, 7GB). | Execution | `code/main.py` | Monitor runtime and memory; fail if exceeded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-code-review-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-288-evaluating-the-impact-of-code-generation/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Configuration, API keys, constants
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetch_prs.py          # FR-001, FR-007, FR-009: API extraction & stratification
│   │   ├── classify.py           # FR-002: Heuristic classification & validation
│   │   └── process.py            # FR-003, FR-006: Cleaning & metrics
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── models.py             # FR-004, FR-008, FR-010, SC-001, SC-003: Regression, SIMEX, Sensitivity
│   │   └── viz.py                # FR-005: Visualization
│   └── main.py                   # Orchestration entry point
├── data/
│   ├── raw/                      # Raw API responses (checksummed)
│   ├── processed/                # Cleaned CSVs/Parquet
│   ├── validation_log.csv        # FR-002: Validation results
│   └── baseline_corpus/          # External code-specific baseline for heuristic calibration
├── tests/
│   ├── unit/
│   │   ├── test_classify.py
│   │   └── test_rate_limit.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── reports/                  # Generated plots and PDF reports
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure (`code/` with modular subpackages) selected for simplicity and alignment with the research nature of the project. No separate backend/frontend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **SIMEX Correction** | Required by FR-010 and to address measurement error in the 'origin_label' (methodology-47dd5e7b, scientific_soundness-1b43a05e). | Standard regression assumes no error in predictors; ignoring misclassification leads to biased (attenuated) effect sizes. |
| **Stratified Sampling & >50% Exclusion** | Required by FR-009 to prevent selection bias. | Simple random sampling could over-represent repos dominated by LLM keywords, skewing the 'Non-Disclosing' control group. |
| **External Baseline Corpus** | Required by FR-010 to estimate false positive contamination. | Using internal 'Non-Disclosing' group as baseline is circular (scientific_soundness-55c90b9c); external code-specific data is needed. |
| **Mann-Whitney U as Primary Test** | Required by Constitution Principle VII. | Linear mixed-effects models are sensitive to distribution assumptions; non-parametric test is more robust for the primary hypothesis. |
| **Disclosure vs. Origin Distinction** | Required to address methodology-24e1e421. | Assuming keywords = LLM code is scientifically unsound. The study measures the impact of the *signal* (disclosure), not the *code* directly. |

