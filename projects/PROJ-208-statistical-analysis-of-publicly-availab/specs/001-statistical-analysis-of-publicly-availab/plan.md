# Implementation Plan: Statistical Analysis of GitHub Issue Resolution Times

**Branch**: `001-github-issue-resolution` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-github-issue-resolution/spec.md`

## Summary

This project implements a statistical analysis pipeline to characterize GitHub issue resolution times. The system collects closed issues from diverse repositories, preprocesses temporal data, fits parametric distributions (log-normal, Weibull), and performs hypothesis testing (ANOVA/Kruskal-Wallis) and mixed-effects modeling. The implementation strictly adheres to CPU-only constraints for GitHub Actions feasibility, ensures all datasets are open and streamable, and enforces "associational" language in all reporting.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels`, `seaborn`, `matplotlib`, `datasets` (HuggingFace), `requests`, `resource` (for memory profiling)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/interim/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: CLI / Data Pipeline  
**Performance Goals**: Complete analysis of [deferred] issues (verified dataset size) within 6 hours on 2 CPU cores, 7GB RAM.
**Constraints**: No GPU usage; strict memory limits (streaming data); Holm-Bonferroni correction mandatory; VIF diagnostics mandatory (Marginal OLS method); **10-Fold CV** (not LOO-CV) for feasibility.  
**Scale/Scope**: A set of repositories and deferred issues (verified dataset).

> **Compute Feasibility Note**: All statistical methods (MLE fitting, mixed-effects models) are implemented using `scipy` and `statsmodels` which are CPU-tractable. The dataset is accessed via streaming to avoid OOM errors on the 7GB RAM limit. **10-Fold Cross-Validation** is used instead of LOO-CV to ensure the 6-hour runtime constraint is met and to avoid the computational explosion of fitting 100+ LMMs.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan uses `datasets.load_dataset(..., streaming=True)` with pinned seeds. All scripts in `code/` will be deterministic.
- **II. Verified Accuracy**: Plan includes a specific task (Phase 5, Task 5.2) to execute the Reference-Validator Agent on generated artifacts before the `research_accepted` transition.
- **III. Data Hygiene**: Raw data from HuggingFace is checksummed upon download. No in-place modifications; all transformations produce new files in `data/processed/`.
- **IV. Single Source of Truth**: All figures and stats trace to `data/processed/cleaned_issues.csv` and the specific script outputs.
- **V. Versioning**: `requirements.txt` pins versions. Content hashes will be recorded in `state/`.
- **VI. Temporal Data Integrity**: `created_at` and `closed_at` are stored as raw ISO strings from the API. Conversion to hours is done in a deterministic script.
- **VII. Reproducible Feature Engineering**: Label extraction and language mapping are implemented in `code/features/` with explicit API field declarations.

## Project Structure

### Documentation (this feature)

```text
specs/001-github-issue-resolution/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-208-statistical-analysis-of-publicly-availab/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── loader.py          # Fetches from HuggingFace (verified source)
│   │   ├── cleaner.py         # Handles time logic, outliers, missing values
│   │   └── stream_utils.py    # Streaming helpers
│   ├── analysis/
│   │   ├── distribution.py    # ECDF, Log-Normal, Weibull fitting (MLE + Bootstrap)
│   │   ├── hypothesis.py      # Kruskal-Wallis, ANOVA, Holm-Bonferroni
│   │   ├── mixed_effects.py   # LMM fitting, 10-Fold CV
│   │   └── diagnostics.py     # VIF (Marginal OLS), Sensitivity Analysis
│   ├── viz/
│   │   └── plots.py           # ECDF, histograms, figure captions (associational)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Parquet files (streamed/downloaded)
│   └── processed/
│       └── cleaned_issues.csv
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen to minimize overhead and ensure tight coupling between data processing and analysis, fitting the 7GB RAM constraint by keeping data flow in-memory or streaming.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-Effects Modeling | Required by FR-005 to account for repository-level variance. | Simple linear regression would violate the spec's requirement to handle hierarchical data (issues nested in repos). |
| Streaming Data Load | Required by compute constraints (7GB RAM) for large datasets. | Loading full dataset into memory would cause OOM on GitHub Actions free tier. |
| Holm-Bonferroni Correction | Required by FR-004 for multiple comparisons. | Standard Bonferroni is too conservative; Tukey's is for pairwise only. |
| **10-Fold CV** | Required for computational feasibility (6h limit) and statistical robustness. | **LOO-CV** (100 fits) is too slow for the runtime constraint and risks timeout. |
| Marginal OLS VIF | Required for methodological soundness. | Standard VIF on LMM is unsound; GVIF libraries are not standard in Python. |

## Implementation Phases (Addressing Unresolved Concerns)

### Phase 0: Dataset Verification & Feasibility Check
*Addresses: Data Resources Concerns, Early Failure Prevention.*
- **Task 0.0 (T000)**: **Verify Dataset Schema and Size**.
  - **Action**: Programmatically load the `akhousker/github-issues` dataset (streaming) and verify:
    1. It contains `created_at`, `closed_at`, `labels`, `assignee`, `comments_count`.
    2. It contains data from ≥100 distinct repositories.
    3. It contains ≥5000 closed issues (minimum for statistical power).
  - **Fail Fast**: If any check fails, the pipeline halts with a clear error message and does not proceed to Phase 1. This prevents wasting compute on an invalid source.

### Phase 1: Data Collection & Preprocessing
*Addresses: FR-001, FR-002, FR-003, US-1, US-1 Acceptance 1-3.*
- **Task 1.1 (T005)**: Implement `data/loader.py` using the verified HuggingFace dataset `akhousker/github-issues`.
  - **Constraint**: Primary data source is HuggingFace. API fallback is only for missing metadata.
  - **Rate Limit Handling**: Implement exponential backoff with a **≥60 seconds** wait if the rate limit is hit. **This logic applies to ANY rate limit event (primary stream or fallback).**
- **Task 1.2 (T012)**: Implement `data/cleaner.py` to:
  - Calculate `resolution_time_hours`.
  - Exclude issues where `closed_at < created_at` (log entry required).
  - **Explicitly implement** the `≥60 seconds` wait logic for rate limits in the API fallback wrapper.
  - Flag issues with `resolution_time > 30 days` as outliers (justified as a conservative cap for extreme tail data, aligned with 95th percentile).
  - **Calculate and log** the count/percentage of outliers.
- **Task 1.3 (T013)**: Output `data/processed/cleaned_issues.csv`. **Critical**: Ensure this file is non-empty and contains ≥1000 rows to satisfy US-1.
- **Task 1.4 (T014)**: **Validate Dataset Size**. Verify `cleaned_issues.csv` contains ≥1000 rows and matches `contracts/dataset.schema.yaml` before proceeding. **This is a blocking gate.**

### Phase 2: Distribution Analysis
*Addresses: FR-002, US-2, SC-002.*
- **Task 2.1 (T015)**: Implement `analysis/distribution.py` to generate ECDF plots.
- **Task 2.2 (T016)**: **Implement MLE Fitting**: Fit Log-Normal and Weibull distributions using `scipy.stats`.
  - **Robustness**: Use bounded optimization and method-of-moments fallback if MLE fails due to heavy skew.
  - **Validation**: If standard KS p-values are unreliable, perform a **Parametric Bootstrap** (n=1000) to generate the null distribution for the KS statistic (resolves circular validation concern).
  - Report KS statistic, p-value, and AIC for **BOTH** families.
- **Task 2.3 (T017)**: **Implement Outlier Detection**: Calculate and log the count/percentage of issues >30 days.
- **Task 2.4 (T018)**: Save figures with captions containing "associational" (FR-008). **Ensure all figure titles and captions include the phrase.**
- **Task 2.5 (T019)**: **Save Distribution Metrics**: Write KS, p-value, AIC for both families to `data/interim/distribution_metrics.json`.
- **Task 2.6 (T020)**: **Save Outlier Report**: Write count and percentage of outliers to `data/interim/outlier_report.json` (merged into `distribution_metrics.json` as per schema).
- **Task 2.7 (T021)**: **Validate Associational Language**: Check figure captions and JSON report text for "associational" or "correlational" phrasing.

### Phase 3: Hypothesis Testing & Modeling
*Addresses: FR-004, FR-005, FR-006, FR-007, US-3.*
- **Task 3.1 (T022)**: Implement `analysis/hypothesis.py` for Kruskal-Wallis/ANOVA.
  - Apply **Holm-Bonferroni** correction for ≥3 tests.
- **Task 3.2 (T023)**: Implement `analysis/diagnostics.py` for VIF calculation.
  - **Method**: Calculate VIF on the **Marginal OLS** model (fixed effects only) to ensure methodological soundness.
  - **Encoding**: Group rare labels into 'Other' to prevent high dimensionality and perfect multicollinearity.
  - Flag VIF ≥ 5.
  - Report joint relationships descriptively if collinearity exists.
- **Task 3.3 (T024)**: **Save Collinearity Report**: Write VIF scores and flags to `data/interim/collinearity_report.json`.
- **Task 3.4 (T025)**: Implement `analysis/mixed_effects.py` for LMM.
  - Fit model with random intercepts for repository.
  - **Validation**: Implement **k-Fold Cross-Validation** stratified by repository size (replaces LOO-CV for feasibility).
- **Task 3.5 (T026)**: **Save CV Results**: Write MAE and R² metrics from **10-Fold CV** to `data/interim/mixed_effects_results.json`.

### Phase 4: Sensitivity & Reporting
*Addresses: FR-007, FR-008.*
- **Task 4.1 (T027)**: Implement Sensitivity Analysis in `analysis/diagnostics.py`.
  - **Explicitly sweep** thresholds: `{0.01, 0.05, 0.1}`.
  - **Method**: Report **Stability Proportion** (proportion of bootstrap resamples significant) for each threshold. (Note: FP/FN rates are not calculable without ground truth; stability is the valid metric).
- **Task 4.2 (T028)**: **Save Sensitivity Results**: Write stability analysis results to `data/interim/sensitivity_results.json`.

### Phase 5: Validation & Constitution Gate
*Addresses: Constitution Principle II, FR-008.*
- **Task 5.1 (T039)**: Implement Reference-Validator Agent execution script.
- **Task 5.2 (T040)**: **Execute Reference-Validator**: Run the agent against all citations in `research.md`, `plan.md`, and generated JSON reports (`distribution_metrics.json`, `mixed_effects_results.json`, etc.) as a blocking gate before `research_accepted`.
- **Task 5.3 (T041)**: Verify all figures have "associational" disclaimers.

### Phase 6: Integration & CI
*Addresses: FR-009, FR-010.*
- **Task 6.1 (T042)**: Run full pipeline on GitHub Actions runner (standard CPU, sufficient RAM).
- **Task 6.2 (T043)**: Verify runtime ≤ 6 hours.
- **Task 6.3 (T044)**: **Measure and Record Compute Metrics**: Instrument pipeline to capture peak memory usage (via `resource` module) and total runtime, writing to `data/interim/compute_metrics.json`. Verify memory ≤ 7GB.

## Tasks (Detailed)

- [ ] **T000**: **Verify Dataset Schema and Size** (Phase 0). Fail fast if HuggingFace dataset is insufficient.
- [ ] **T005**: Implement API client with exponential backoff and **≥60 seconds** wait logic for rate limits (applies to all rate limit events).
- [ ] **T009**: Fetch data from HuggingFace `akhousker/github-issues` with streaming.
- [ ] **T011**: Save cleaned dataset to `data/processed/cleaned_issues.csv`. **Must contain ≥1000 rows**.
- [ ] **T012**: Implement logging for excluded issues and rate limit waits.
- [ ] **T013**: Output `data/processed/cleaned_issues.csv`.
- [ ] **T014**: **Validate Dataset Size** (Blocking Gate). Verify ≥1000 rows and schema compliance.
- [ ] **T015**: Generate ECDF plots.
- [ ] **T016**: Fit log-normal and Weibull models with MLE, robust initialization, and fallback. Report KS/AIC for **both** families.
- [ ] **T017**: Detect and report extreme outliers (>30 days) and their percentage.
- [ ] **T018**: Save figures with "associational" captions and results to `data/interim/distribution_metrics.json`.
- [ ] **T019**: Save Distribution Metrics to JSON.
- [ ] **T020**: Save Outlier Report to JSON.
- [ ] **T021**: Validate Associational Language in figures and JSON.
- [ ] **T022**: Implement Kruskal-Wallis/ANOVA with Holm-Bonferroni correction.
- [ ] **T023**: Fit mixed-effects model with random intercepts.
- [ ] **T024**: Calculate VIF on Marginal OLS model with label grouping.
- [ ] **T025**: Perform sensitivity analysis sweeping thresholds **{0.01, 0.05, 0.1}** and report **Stability Proportion**.
- [ ] **T026**: Enforce "associational" language in all result text and figure captions.
- [ ] **T027**: Implement Sensitivity Analysis (Stability Proportion).
- [ ] **T028**: Save Sensitivity Results to JSON.
- [ ] **T039**: Implement Reference-Validator Agent.
- [ ] **T040**: Execute Reference-Validator Agent on generated artifacts as a blocking gate.
- [ ] **T041**: Validate associational language in result text and figure captions.
- [ ] **T042**: Execute Reference-Validator Agent on generated artifacts as a blocking gate.
- [ ] **T043**: Verify runtime ≤ 6 hours.
- [ ] **T044**: Measure and Record Compute Metrics.