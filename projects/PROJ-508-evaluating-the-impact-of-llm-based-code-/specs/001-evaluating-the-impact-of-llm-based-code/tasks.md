# Tasks: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Input**: Design documents from `/specs/001-evaluating-llm-cognitive-load/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory tree: `mkdir -p code data/raw data/processed results tests` (ensures all required folders exist).
- [ ] T002 Initialize Python 3.11 project and create `requirements.txt` containing pinned versions:
  ```
  pandas==2.2.2
  numpy==1.26.4
  scikit-learn==1.5.0
  statsmodels==0.14.2
  linearmodels==5.3
  requests==2.32.3
  aiohttp==3.9.5
  pyyaml==6.0.1
  ```
- [ ] T003 [P] Configure linting with `flake8` and formatting with `black` (add config files `.flake8` and `pyproject.toml`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Verify and initialize data directory structure (`data/raw/`, `data/processed/`, `results/`) by ensuring directories exist and creating `.gitkeep` files to preserve them in version control.
- [ ] T005 [P] Implement utility module `code/utils.py` with function:
  ```python
  def exponential_backoff(retries: int, base: float = 1.0, factor: float = 2.0, max_delay: float = 30.0) -> float:
      """Return delay in seconds for given retry count."""
      """Catch requests.exceptions.HTTPError, requests.exceptions.Timeout, and requests.exceptions.ConnectionError."""
  ```
- [ ] T006 Create base data schemas in `code/schemas.py` using Pydantic:
  ```python
  class Repository(BaseModel):
      repo_id: int
      name: str
      llm_adopted: bool
      lines_of_code: int
      contributor_count: int
      repo_stars: int
      repo_fork_count: int
      language: str
      age_days: int
      domain_complexity: float  # log10(LOC)+log10(contrib)+1

  class PullRequest(BaseModel):
      pr_id: int
      repo_id: int
      comment_length_chars: int
      iteration_count: int
      revert_frequency: int
      exclude_from_analysis: bool = False
  ```
- [ ] T007 Configure environment configuration management by creating `code/config.py` that loads `target_repos.json` (JSON list of repo URLs) and reads `GITHUB_TOKEN` from environment variables.
- [ ] T008 Setup logging infrastructure to record timestamps, API request/response metadata, and write a `data/manifest.json` (including endpoint URLs, request parameters, collection timestamp, and SHA256 checksums of raw JSON files).

**Spec Kickback Tasks (Spec Amendments)**  
These tasks update the specification before any conflicting implementation occurs.

- [ ] T050 [SpecKickback] Amend FR‑003 in `spec.md` to **remove** `domain_complexity` as a required control variable (replace with a note that it is stored for reporting only). Place this amendment before any analysis tasks.
- [ ] T051 [SpecKickback] Amend US‑2 in `spec.md` to permit a **Linear Mixed‑Effects Model (LMM)** with a random intercept for `repo_id` as the primary analysis technique, replacing the original plain linear regression requirement.

- [ ] T052 Compute a quantitative `proxy_validity_score` based on correlations from T019/T020:
  ```
  score = (abs(corr_iteration_loc) + (abs(corr_revert_iter) if revert_valid else 0)) / (1 if revert_valid else 0.5)
  ```
  Store the score in `results/validity.json` under key `proxy_validity_score`.

- [ ] T053 Build the regression model formula dynamically in `code/analysis.py`:
  * Always include `llm_adopted`, `lines_of_code`, `contributor_count`, `repo_stars`, `repo_fork_count`.
  * Include `revert_frequency` **only if** `revert_valid` (from T020) is `True`.
  * Exclude `domain_complexity` (per T050).
  * Return the formula string for downstream modeling tasks.

- [ ] T054 If any VIF ≥ 5, switch from the LMM to an **OLS Ridge Regression** (no random effect) using `sklearn.linear_model.Ridge(alpha=1.0)`. Log the switch in `results/regression.json` under `model_type`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public GitHub PR metadata, identify LLM adoption, and extract code review metrics.

**Independent Test**: Run ingestion script against a fixed subset of repositories (several LLM, 2 control) and verify output CSV structure, `llm_adopted` flags, and handling of edge cases (empty repos, <10 PRs).

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/ingest.py` to fetch PR metadata for repos listed in `target_repos.json` using the GitHub REST API (authenticated via token). Store raw JSON per repository in `data/raw/`.
- [ ] T010 [US1] Implement LLM adoption detection in `code/ingest.py`:
  * Scan repository root for `.cursorrules` or any file named `copilot` (case‑insensitive) containing the word `copilot`.
  * Scan **PR commit messages**, **PR review comments**, and **PR body descriptions** for case‑insensitive keywords: `copilot`, `cursor`, `codium`, `tabnine`.
  * Set `llm_adopted = True` if any of the above are found; otherwise `False`. Log ambiguous cases.
- [ ] T011 [US1] Extract metrics per PR:
  * `comment_length_chars`: total characters across all review comments.
  * `iteration_count`: count of distinct commit‑comment cycles (a commit followed by a non‑empty comment block counts as one iteration).
  * `revert_frequency`: count of merged PRs that have a subsequent merged revert PR within 7 days (detected via `merged_at` timestamps and `revert` label detection).
- [ ] T012 [US1] Implement rate‑limit handling with exponential backoff (using `code/utils.exponential_backoff`) – A limited number of retries per request will be permitted..
- [ ] T013 [US1] Store raw JSON dumps in `data/raw/` and generate `data/manifest.json` (per T008) recording API endpoint, parameters, timestamp, and SHA256 checksum.
- [ ] T014 [US1] Calculate derived metrics:
  * `domain_complexity = log10(lines_of_code) + log10(contributor_count) + 1` (stored for reporting only).
  * `exclude_from_analysis = True` if the repository has < 10 PRs; otherwise `False`.
- [ ] T015 [US1] Implement coverage check (SC‑004): compute `coverage_rate = successful_repos / total_repos` and abort pipeline with a clear error if `< 0.80`. Write `coverage_rate` to `results/validity.json`.
- [ ] T016 [US1] If total processed data size exceeds a large threshold, perform stratified sampling by `llm_adopted` (preserving the original ratio) to fit within RAM while ensuring at least 10 repositories per group; abort if this cannot be satisfied.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Execute Propensity Score Matching, construct validity checks, and run the primary regression analysis.

**Independent Test**: Run analysis on preprocessed data; verify PSM SMD < 0.1, regression output includes coefficients/CIs, and VIF check triggers Ridge fallback when needed.

### Implementation for User Story 2

- [ ] T017 [US2] Implement Propensity Score Matching (PSM) in `code/analysis.py`:
  * Fit a logistic regression (`sklearn.linear_model.LogisticRegression`) on covariates `lines_of_code`, `contributor_count`, `repo_stars`, `repo_fork_count`.
  * Perform nearest-neighbor matching with caliper 0.2.
  * Produce a matched dataset and store it as `data/processed/matched.csv`.
- [ ] T018 [US2] Verify PSM balance: compute Standardized Mean Difference (SMD) for each covariate; assert all SMD < 0.1. Log results in `results/validity.json`.
- [ ] T019 [US2] Implement Construct Validity Check (FR‑007):
  * Compute Pearson correlation between `iteration_count` and `lines_of_code` (store as `corr_iteration_loc` with p‑value).
  * Compute Pearson correlation between `revert_frequency` and `iteration_count` (store as `corr_revert_iter` with p‑value).
  * Write both correlations to `results/validity.json`.
- [ ] T020 [US2] Implement Construct Validity Gate:
  * If `corr_revert_iter` has p > 0.05, set `revert_valid = False`; otherwise `True`. Record `revert_valid` in `results/validity.json`.
- [ ] T021 [US2] Implement Linear Mixed‑Effects Model (LMM) in `code/analysis.py` using `linearmodels.PanelOLS` (REML) with random intercept for `repo_id`. Retrieve the formula string from T053 to ensure correct inclusion/exclusion of variables.
- [ ] T022 [US2] **(Spec Kickback Compliant)** Exclude `domain_complexity` from the regression formula as mandated by spec amendment T050. Reference T050 for justification.
- [ ] T023 [US2] Perform VIF check on all fixed‑effect predictors; if any VIF ≥ 5, invoke task T054 to switch to OLS Ridge Regression (no random effect) and log the change.
- [ ] T024 [US2] Conduct hypothesis test on the `llm_adopted` coefficient against the null hypothesis value 0.0 (two‑tailed t‑test). Record p‑value and significance.
- [ ] T025 [US2] Output `results/regression.json` containing:
  * `coefficient_llm`, `p_value`, `ci_lower`, `ci_upper`
  * `model_type` (`LMM` or `Ridge`)
  * `theoretical_limitations` (populated later in Phase 6)
  * any VIF warnings or fallback notes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds and stratification, generating robustness reports.

**Independent Test**: Run sensitivity module with 3 alternative parameter values; verify output includes plots/tables of effect size variation and instability flags.

### Implementation for User Story 3

- [ ] T026 [US3] Implement sensitivity analysis in `code/analysis.py`:
  * Baseline `min_pr_lines` is defined in `code/config.py` as a configurable threshold..
  * Sweep thresholds at, 100, and 110 lines (±10% of baseline).
- [ ] T027 [US3] Implement stratification logic:
  * Identify top programming languages by repo count.
  * Split repositories into “young” vs “old” using median `age_days`.
  * Run the regression (via T021/T054) for each language‑age stratum and each threshold.
- [ ] T028 [US3] Generate `results/sensitivity.json` summarizing the `llm_adopted` effect size (coefficient) for every scenario.
- [ ] T029 [US3] Instability detection: if the coefficient sign flips across any scenario, set `high_sensitivity = True` and record a warning in `results/sensitivity.json`.
- [ ] T030 [US3] Generate a line plot saved as `results/effect_size_plot.png`:
  * X‑axis: threshold variant (90, 100, 110).
  * Y‑axis: `llm_adopted` coefficient.
  * Separate lines for each language‑age stratum, with legend.
- [ ] T031 [US3] Compile final results by aggregating `results/regression.json`, `results/validity.json`, and `results/sensitivity.json` into a single `results/final_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Research Integrity (Addressing Prior Reviews)

**Goal**: Document theoretical limitations, proxy validity, and ensure output schemas reflect all required fields.

### Implementation for Revision Concerns

- [ ] T032 [US3] Update `results/regression.json` schema to include a string field `theoretical_limitations` describing the “Adoption Culture vs. Usage” attenuation bias.
- [ ] T033 [US3] In `code/analysis.py`, log the theoretical framework statement:
  * “Cognitive load is proxied by review friction (iteration count, revert frequency) per SE literature; self‑report measures are out of scope for a public‑API study.”
- [ ] T034 [US3] Add a note in `results/sensitivity.json` under `limitations` acknowledging that the study measures individual review friction rather than emergent team problem‑solving dynamics.
- [ ] T035 [US3] Ensure `results/validity.json` includes the `proxy_validity_score` computed in T052.
- [ ] T036 [P] Documentation updates in `README.md` (include theoretical limitations section referencing T032‑T034).
- [ ] T037 Code cleanup and refactoring (remove dead code, enforce type hints).
- [ ] T038 [P] Refactor `code/ingest.py` to use asynchronous HTTP requests with `aiohttp` and an async request pool to reduce total I/O time, helping meet the runtime budget.
- [ ] T039 [P] Add unit tests in `tests/test_analysis.py`:
  * `test_metric_iteration_count`
  * `test_metric_revert_frequency`
  * `test_correlation_computation`
  * `test_model_formula_construction` (verifies T053 behavior)
- [ ] T040 Run `quickstart.md` validation script to ensure end‑to‑end reproducibility.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Performance optimization: profile the pipeline and cache GitHub API responses locally to avoid redundant calls (cache stored in `data/cache/`).
- [ ] T042 Additional integration tests for the full pipeline (`tests/integration/test_pipeline.py`).
- [ ] T043 Ensure all scripts respect the 2‑core CPU limit (use `joblib` with `n_jobs=2` where applicable).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup – BLOCKS all user stories.
- **Spec Kickback (Phase 2)**: Must run before any analysis tasks (T021‑T025).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
  - User stories can proceed in parallel after Foundational.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational; no dependencies on other stories.
- **User Story 2 (P2)**: Requires completion of User Story 1 (data ingestion) and spec amendments (T050, T051) before analysis.
- **User Story 3 (P3)**: Requires analysis results from User Story 2 (regression output) before sensitivity runs.
- **Revision Concerns (Phase 6)**: Depends on final results (T031) to document limitations.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational is complete, all user stories can start in parallel (if staffed).
- All tests for a user story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2 (including spec kickback tasks T050‑T054).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Run User Story 1 independent test suite.
5. Deploy/demo if ready.

### Incremental Delivery

1. Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test → Deploy/Demo (MVP!).
3. Add User Story 2 → Test → Deploy/Demo.
4. Add User Story 3 → Test → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

- Team completes Setup + Foundational together.
- After Foundational:
  - Developer A: User Story 1 (Ingestion).
  - Developer B: User Story 2 (Analysis).
  - Developer C: User Story 3 (Sensitivity).

---

## Notes

- All analysis runs on CPU‑only GitHub Actions runner (2 cores, ≤ 7 GB RAM) within 6 hours.
- No GPU or 8‑bit model loading.
- Real GitHub API data only; no fabricated inputs.
- All proxy limitations (adoption culture vs. usage intensity) are explicitly documented in Phase 6 artifacts.