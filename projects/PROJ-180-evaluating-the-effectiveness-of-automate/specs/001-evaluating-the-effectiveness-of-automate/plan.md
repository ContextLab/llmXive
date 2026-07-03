# Implementation Plan: Evaluating Automated Code Review Tools Effectiveness

**Branch**: `001-evaluating-code-review-tools` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-code-review-tools/spec.md`

## Summary

This project implements a computational pipeline to evaluate the effectiveness of three automated code review tools (SonarQube, DeepSource, CodeClimate) against a human-review baseline derived from GitHub pull requests. The technical approach involves: (1) stratified repository acquisition and tool execution, (2) dual-source ground truth construction (heuristic-extracted + random manual review), (3) AST/diff-based alignment of tool issues to human findings, and (4) statistical analysis (precision/recall, Wilcoxon tests, mixed-effects regression) to quantify tool performance and project characteristic influences. All components are designed to run on CPU-only GitHub Actions runners (multi-core, sufficient RAM) within a standard time window.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pandas`, `scikit-learn`, `statsmodels`, `pygithub`, `docker` (via subprocess), `networkx` (for graph analysis if needed), `pytest`  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`); no database required.  
**Testing**: `pytest` with contract tests for data schemas and integration tests for pipeline stages.  
**Target Platform**: Linux (GitHub Actions Runner), CPU-only.  
**Project Type**: Data analysis pipeline / Research tooling.  
**Performance Goals**: Pipeline runtime ≤ 5.5 hours; Peak memory ≤ 6 GB.  
**Constraints**: No GPU; strict adherence to CPU-tractable methods; all external tools must be version-pinned and run via Docker/binary to ensure reproducibility.  
**Scale/Scope**: A sample of multiple repositories; A substantial corpus of extracted annotations, with a representative subset expert-validated for ground truth, will be assembled to address the research question using the specified method (DOI:10.1234/example).; A substantial number of total issues across tools.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; `requirements.txt` pins versions; external datasets fetched from verified canonical sources (GitHub API) on every run. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `data-model.md` will be validated against primary sources (GitHub API, tool docs) before review points are awarded. |
| **III. Data Hygiene** | **PASS** | All files in `data/` will be checksummed (SHA-256) and recorded in `state/`. Raw data is immutable; derivations create new files. PII scan enforced via `Repository-Hygiene Agent`. |
| **IV. Single Source of Truth** | **PASS** | All figures/statistics in the final paper will trace to exactly one row in `data/processed` and one block in `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes generated for all artifacts; `updated_at` timestamps updated on any change to research artifacts. |
| **VI. Tool Version Pinning** | **PASS** | SonarQube Scanner, DeepSource CLI, and CodeClimate Engine versions pinned in `code/versions.yaml` and executed via specific Docker images/binaries. |
| **VII. Metric Reporting & Statistical Rigor** | **PASS** | Precision, recall, F1, Wilcoxon tests, and mixed-effects regression models will be computed and saved as CSV/PNG in `results/`, referenced unambiguously in the paper. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-code-review-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-180-evaluating-the-effectiveness-of-automate/
├── data/
│   ├── raw/                 # Cloned repos, raw tool JSON reports, raw PR comments
│   ├── processed/           # Aligned pairs, validated annotations, aggregated metrics
│   └── external/            # Verified datasets (if any, e.g., curated repo lists)
├── code/
│   ├── 01_data_acquisition.py   # Repo cloning, tool execution
│   ├── 02_human_annotation.py   # PR comment parsing, heuristic extraction
│   ├── 03_alignment.py          # AST/diff-based alignment logic
│   ├── 04_metrics.py            # Precision, recall, F1, statistical tests
│   ├── 05_regression.py         # Mixed-effects models, sensitivity analysis
│   ├── utils/
│   │   ├── aligner.py           # Alignment helper functions
│   │   ├── github_client.py     # GitHub API wrapper
│   │   └── stats_utils.py       # Statistical test helpers
│   ├── versions.yaml            # Tool version pins
│   └── requirements.txt         # Python dependencies
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # Pipeline stage tests
│   └── unit/                    # Utility function tests
├── results/                     # CSV/PNG artifacts (metrics, plots)
├── specs/
├── state/
└── docs/
```

**Structure Decision**: Single-project structure with clear separation of `data/`, `code/`, and `results/` to enforce the "Single Source of Truth" and "Data Hygiene" principles. The `code/` directory is organized by pipeline stage (01–05) to reflect the computational ordering: Data Acquisition → Human Annotation → Alignment → Metrics → Regression.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three separate tool executors** | Required to compare SonarQube, DeepSource, and CodeClimate per spec (FR-003). | A single generic executor would not capture tool-specific nuances or output formats. |
| **AST-based alignment** | Required for accurate line/file matching (FR-005) where diff-based methods fail. | Simple string matching is insufficient for semantic alignment; AST provides robustness. |
| **Mixed-effects regression** | Required to control for project-specific characteristics (FR-008) with small cluster size. | Standard OLS or fixed-effects models would suffer from overfitting with a limited number of clusters. |
| **Max-t Permutation Tests** | Required for non-parametric significance testing (FR-008) with FWER control. | Standard Bonferroni is too conservative; max-t permutation controls FWER while preserving power. |

## Unresolved Panel Concerns Resolution

The following concerns from the previous iteration are resolved in this plan:

1.  **Task T027 (Alignment) Dependency Clarity**: The plan explicitly defines `code/03_alignment.py` as consuming `data/raw/tool_reports.json` (from T019) and `data/processed/human_annotations.json` (from T022-T026). The output `data/processed/aligned_pairs.json` is the direct input for `code/04_metrics.py`. The "Independent Test" for US2 is clarified to require **mocked aligned pairs** for unit testing, while integration testing relies on the full US1/US2 pipeline. This resolves the semantic gap.
2.  **Task T032 (Metrics) Input Clarity**: The plan specifies that `code/04_metrics.py` consumes `data/processed/aligned_pairs.json` (from T029) and `data/raw/tool_reports.json` (from T019) to calculate precision/recall. The "sample dataset" for US3 testing is explicitly defined as **mocked aligned pairs** generated by the pipeline or a small subset of real data, ensuring independence from the full US1/US2 execution for unit tests.
3.  **Task T008 (Aligner Skeleton)**: The plan clarifies that `code/utils/aligner.py` is a utility module providing core alignment logic (AST parsing, diff matching) used by `code/03_alignment.py`. The "skeleton" nature is inherent in the TDD approach: tests for `aligner.py` are written first (Phase 2), followed by implementation.
4.  **Task T011/T012 (Contract Tests)**: The plan clarifies that `tests/contract/test_repository_filter.py` (T011) tests the **expected interface** of `code/01_data_acquisition.py` (T013) before implementation. The test expects specific input/output signatures, failing initially as intended, then passing once the implementation matches the contract.

## Computational Feasibility & Statistical Rigor

- **CPU-Only Execution**: All tools (SonarQube, DeepSource, CodeClimate) are executed via Docker containers or binaries on CPU. No GPU dependencies.
- **Memory Constraints**: Data is processed in chunks; repositories exceeding substantial RAM requirements are excluded and logged.
- **Statistical Rigor**:
  - **Multiple Comparisons & FWER**: The plan employs a **max-t permutation procedure** to control the Family-Wise Error Rate (FWER). For each permutation iteration, the test statistic is computed for all pairwise comparisons, and the **maximum** statistic across all comparisons is recorded. The adjusted p-value for each comparison is the proportion of permutations where the max statistic exceeds the observed statistic. This ensures the permutation distribution itself accounts for the joint null hypothesis, avoiding the logical gap of post-hoc correction.
  - **Power Justification**: Sample size of a limited number of repositories is acknowledged as a limitation.; **Mixed-Effects Models (LMM)** are used to mitigate overfitting and handle small cluster sizes.
  - **Causal Inference**: Observational study; all claims framed as associational. Mixed-effects models control for project-level confounders.
  - **Measurement Validity**: Ground truth is a **union** of (A) expert-validated heuristic candidates and (B) expert-validated random code changes. This ensures tools are not penalized for detecting bugs missed by the heuristic (resolving circular validation).
  - **Collinearity**: **Project characteristics (language, size, activity) are NOT assumed independent.** VIF diagnostics are mandatory. If VIF > 5, Ridge Regression or PCA is applied. Predictors are treated as potentially correlated.
  - **Ground Truth Stratification**: A subset of expert-validated annotations is drawn from a population of extracted annotations. Stratification includes **tool, language, and alignment difficulty** (easy, medium, hard) based on file complexity and comment ambiguity, ensuring the sample represents the full spectrum of alignment challenges.

## Ground Truth Construction

To avoid circular validation and heuristic bias while satisfying FR-004:
1.  **Candidate Generation (FR-004)**: Parse merged PR comments using keyword heuristics to generate a candidate pool of potential defects.
2.  **Random Stream (Independent)**: Select a stratified random sample of code changes/comments of sufficient size to ensure statistical power and representativeness. **regardless of keywords**.
3.  **Expert Validation**: Both streams undergo expert manual review.
4.  **Union Ground Truth**: The final ground truth is the union of (1) validated heuristic candidates and (2) validated random samples. This ensures the ground truth is independent of the heuristic's detection logic (tools are not penalized for heuristic misses) while fulfilling the spec's requirement to use heuristics for candidate generation.

## Phase Ordering

1.  **Phase 0 (Research)**: Verify datasets, define statistical methods, confirm tool availability.
2.  **Phase 1 (Data Model)**: Define schemas for raw/processed data, contracts for tool outputs.
3.  **Phase 2 (Foundational)**: Implement utilities (`aligner.py`, `github_client.py`), write contract tests.
4.  **Phase 3 (US1 - Data Acquisition)**: Clone repos, execute tools, generate raw JSON reports.
5.  **Phase 4 (US2 - Human Baseline)**: Extract annotations (heuristic + random), validate with experts, align with tool issues.
6.  **Phase 5 (US3 - Metrics & Analysis)**: Compute metrics, run **max-t permutation tests**, fit mixed-effects models (with VIF/Ridge handling), generate artifacts.
7.  **Phase 6 (Validation)**: Verify reproducibility, checksum data, update state.

This ordering ensures data is downloaded before analysis, models are fitted before evaluation, and figures are generated before paper inclusion.

## Assumptions

- GitHub REST API rate limits will not prevent retrieval of PR comments for a representative sample of repositories within a feasible time budget.
- Static analysis tools (SonarQube Scanner, DeepSource CLI, CodeClimate Engine) can be executed via Docker containers or binary releases on CPU-only GitHub Actions runners without GPU dependencies.
- Keyword heuristics for defect annotation extraction will capture relevant human-review findings, subject to expert validation of a stratified random sample; the heuristic threshold sensitivity is analyzed via FR-012.
- Repository codebases will fit within 7 GB RAM during concurrent analysis; if a repository exceeds this, it will be excluded and logged as a resource constraint failure.
- The observational nature of this study (no randomization of tool usage) means all findings will be framed as associational rather than causal relationships.
- **Project characteristics (language, size, activity) are NOT definitionally independent.** They are expected to be correlated (e.g., Java projects tend to be larger). The analysis plan explicitly includes VIF diagnostics and regularization (Ridge/PCA) to handle this multicollinearity.
- No post-task psychological variables (e.g., anxiety, rumination) are required since this study focuses on code quality metrics rather than human factors.
- A sample size of repositories provides adequate statistical power for permutation-based tests and mixed-effects regression, provided the max-t procedure is used for FWER control.