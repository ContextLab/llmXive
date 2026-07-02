# Implementation Plan: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Branch**: `001-evaluating-llm-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-evaluating-llm-cognitive-load/spec.md`

## Summary

This feature implements an observational study to evaluate the **association** between LLM-based code completion **adoption culture** (proxied by config presence) and developer cognitive load, proxied by code review metrics (comment length, iteration count, revert frequency). The technical approach involves:
1.  **Data Ingestion**: Fetching PR metadata from a curated list of GitHub repositories via the public API, distinguishing LLM-adopting projects based on configuration files (`.cursorrules`, `copilot`) and commit keywords.
2.  **Preprocessing**: Calculating derived metrics, filtering by PR count, and applying **Stratified Sampling** by `llm_adopted` status if necessary to fit RAM while preserving group balance.
3.  **Statistical Analysis**: Executing a **Linear Mixed-Effects Model (LMM)** with `repo_id` as a random effect to account for nested data structure (PRs within Repos) and prevent pseudoreplication. Controls include `lines_of_code`, `contributor_count`, `repo_stars`, and `repo_fork_count`. **Note**: `domain_complexity` is **excluded** from the regression to avoid mathematical collinearity (see Task 3.2).
4.  **Sensitivity Analysis**: Stress-testing results against threshold variations and stratification by language/age.
5.  **Construct Validity**: Verifying the link between proxies (FR-007) and enforcing a data coverage threshold (SC-004).

All analysis is constrained to run on a CPU-only GitHub Actions runner (2 cores, 7GB RAM) within 6 hours.

**Methodological Limitations**:
-   **Adoption Culture vs. Usage**: The binary flag `llm_adopted` proxies for "tool presence" or "adoption culture," not "usage intensity." This may introduce attenuation bias (biasing coefficients toward zero).
-   **Unobserved Confounders**: Factors like "Developer Expertise" are unobserved. PSM cannot balance these. Results are strictly **associational**, not causal.
-   **Proxy Validity**: `revert_frequency` is a quality/stability proxy, not a direct cognitive load proxy. It is only included if it correlates significantly with `iteration_count` (FR-007).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `statsmodels`, `requests`, `pyyaml`, `numpy`, `linearmodels` (for Mixed-Effects)
**Storage**: Local filesystem (`data/` for raw/processed CSVs/Parquet, `results/` for JSON outputs).
**Testing**: `pytest` (contract tests on schemas, unit tests on metric calculation).
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: Data analysis pipeline / Research script.
**Performance Goals**: Complete full pipeline (ingestion + analysis) within 6 hours on 2 CPU cores.
**Constraints**: No GPU usage; no external database; memory footprint < 7GB; strict adherence to GitHub API rate limits (exponential backoff).
**Scale/Scope**: ~50 repositories, thousands of PRs (sampled if necessary to fit RAM).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin exact versions. Random seeds will be set in `code/`. For live API data, reproducibility is defined as: same code, same parameters, same timestamp recorded in `manifest.json`. Exact data values may vary due to live repo state; the manifest records the collection timestamp to allow manual comparison of repo states if needed. |
| **II. Verified Accuracy** | **PASS** | For the GitHub API source, the plan verifies that the API endpoints and request parameters match the official GitHub API documentation (primary source). Data integrity is verified via checksums of raw JSON dumps (Principle III). Acknowledged that 'Verified Accuracy' of live data values is not possible against a static ground truth, so the gate is satisfied by process verification and checksumming. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` with checksums. Derived data in `data/processed/` with derivation scripts. PII scan on commit. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final report will be generated directly from `data/processed/` via `code/` scripts. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. State file updated on change. |
| **VI. Empirical Data Collection Transparency** | **PASS** | `data/manifest.json` will record API endpoints, request parameters, and timestamps as a mandatory step in **Task 1.2**. |
| **VII. Statistical Rigor** | **PASS** | Regression uses Mixed-Effects Model (LMM) to handle nested data. `domain_complexity` excluded to avoid collinearity. VIF checks and Ridge fallback implemented for remaining predictors. PSM standard mean difference < 0.1 enforced for covariate balance. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-cognitive-load/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/
├── code/
│   ├── __init__.py
│   ├── ingest.py            # GitHub API fetching, LLM flagging, Maturity proxies
│   ├── preprocess.py        # Metric calculation, filtering, Stratified Sampling
│   ├── analysis.py          # LMM, Construct Validity, Sensitivity
│   ├── utils.py             # Helpers (backoff, VIF calc)
│   └── main.py              # Entry point
├── data/
│   ├── raw/                 # Raw API JSON/CSV dumps
│   ├── processed/           # Cleaned CSVs for analysis
│   └── manifest.json        # Collection metadata
├── results/
│   ├── regression.json      # Coefficients, CIs, Hypothesis Test
│   ├── validity.json        # Construct validity correlations, Coverage Rate
│   └── sensitivity.json     # Sensitivity metrics
├── tests/
│   ├── test_ingest.py
│   ├── test_analysis.py
│   └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected. The `code/` directory contains modular scripts for the linear pipeline (Ingest -> Preprocess -> Analyze). This minimizes overhead and fits the CPU-only constraint. `data/` is strictly for artifacts, not code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Model (LMM)** | Required to handle nested data (PRs within Repos) and prevent pseudoreplication (Scientific Soundness concern). | Simple OLS would underestimate standard errors and inflate Type I error rates. |
| **Exclusion of `domain_complexity`** | Required to avoid mathematical collinearity (Scientific Soundness concern). | Including it would make the regression matrix rank-deficient. **Spec Kickback**: FR-003 must be updated to remove this requirement. |
| **Construct Validity Gate** | Required to validate the theoretical link between proxies (FR-007) and ensure `revert_frequency` is a valid proxy. | Blindly using `revert_frequency` risks measuring quality instead of cognitive load. |
| **Hard Fail on Coverage** | Required to meet SC-004 (≥80% success rate). | Proceeding with <80% data would invalidate the study's representativeness. |
| **Stratified Sampling** | Required to ensure both treatment and control groups remain balanced and powered if sampling is necessary. | Simple random sampling could result in an imbalanced dataset with insufficient power for the treatment group. |

## Implementation Phases

### Phase 1: Data Ingestion & Preprocessing

**Task 1.1: API Fetching & LLM Flagging**
- Fetch PR metadata for repositories in `target_repos.json`.
- Scan for `.cursorrules`, `copilot` config, and LLM keywords in commit messages to set `llm_adopted`.
- Fetch `repo_stars`, `repo_fork_count`, `lines_of_code`, `contributor_count`, `language`, `age`.
- **Rate Limit Handling**: Exponential backoff (max a limited number of retries).

**Task 1.2: Data Hygiene & Manifest**
- Store raw JSON in `data/raw/`.
- Generate `data/manifest.json` recording: API endpoints, request params, collection timestamp, and checksums (Constitution Principle VI).
- Calculate derived metrics: `domain_complexity` (for storage only, not regression), `exclude_from_analysis` (if PR count < 10).

**Task 1.3: Coverage Check (SC-004)**
- Calculate success rate: (Number of repos fetched successfully) / (Total repos in `target_repos.json`).
- **Condition**: If success rate < 80%, **ABORT** pipeline and log failure. Do not proceed with analysis.
- **Output**: Record `coverage_rate` in `results/validity.json`.

**Task 1.4: Stratified Sampling (if needed)**
- If dataset > 6GB, perform **Stratified Sampling** by `llm_adopted` status (preserving ratio) to fit RAM.
- **Constraint**: Ensure both groups remain sufficiently powered (e.g., a minimum number of repositories per group). Abort if this condition cannot be met.

### Phase 2: Construct Validity & Analysis

**Task 2.1: Construct Validity Check (FR-007)**
- Calculate correlation between `iteration_count` and `lines_of_code`.
- Calculate correlation between `revert_frequency` and `iteration_count`.
- **Gate**: If `revert_frequency` correlation with `iteration_count` is weak (p > 0.05), flag `revert_frequency` as invalid for cognitive load proxy in the final report and exclude it from the primary regression model.
- **Output**: `results/validity.json` (includes `corr_iteration_loc`, `revert_valid_proxy`, `coverage_rate`).

**Task 2.2: Propensity Score Matching (PSM)**
- Match `llm_adopted=1` and `llm_adopted=0` groups on covariates (`lines_of_code`, `contributor_count`, `repo_stars`, `repo_fork_count`).
- Verify Standardized Mean Difference (SMD) < 0.1.

**Task 2.3: Linear Mixed-Effects Model (LMM)**
- **Model**: `outcome ~ llm_adopted + lines_of_code + contributor_count + repo_stars + repo_fork_count + (1|repo_id)`
- **Note**: `domain_complexity` is **excluded** to avoid collinearity.
- **Hypothesis Test**: Perform a t-test on the `llm_adopted` coefficient against the null hypothesis value of 0.0.
- **Output**: `results/regression.json` (includes `coefficient_llm`, `p_value`, `significant_at_0.05`).

**Task 2.4: Sensitivity Analysis**
- Vary `min_pr_lines` thresholds.
- Stratify by language and age.
- Report effect size variation and flag instability.

### Phase 3: Reporting

**Task 3.1: Generate Results**
- Compile `results/regression.json`, `results/validity.json`, `results/sensitivity.json`.
- Ensure all fields match `contracts/` schemas.

**Task 3.2: Final Review**
- Verify all success criteria (SC-001 to SC-005) are met.
- Ensure `manifest.json` is complete.

## Spec Kickback Required

- **FR-003**: The spec mandates controlling for `domain_complexity` in the regression. However, `domain_complexity` is defined as `log10(LOC) + log10(Contributors) + 1`, making it mathematically collinear with `lines_of_code` and `contributor_count`. Including it renders the regression coefficients undefined. **Action**: The implementation plan excludes `domain_complexity` from the regression. The spec must be updated to remove this requirement or redefine `domain_complexity` as an independent metric.
