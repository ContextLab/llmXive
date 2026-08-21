# Tasks: Evaluating Code Generation Impact on Code Smell Frequency

**Input**: Design documents from `/specs/001-code-smell-comparison/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to define interfaces before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Project Initialization & Pre-requisites

**Purpose**: Ensure the project environment and documentation are ready before setup tasks begin.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/01_data_collection code/02_static_analysis code/03_statistical_analysis code/04_reporting code/utils tests/contract tests/integration tests/unit data/raw/human_samples data/raw/llm_samples data/intermediate data/processed reports specs/001-code-smell-comparison`

- [ ] T001.1 [US1] Initialize `research.md` if missing:
 - **Action**: Check if `specs/001-code-smell-comparison/research.md` exists. If not, create it with a header, project ID, and a placeholder section for "Balanced Blocked Design Implementation".
 - **Verification**: Verify file exists and contains the header `# Research: Evaluating Code Generation Impact on Code Smell Frequency`.
 - **Constraint**: This task ensures T030 has a valid target file. **Dependency**: Must run AFTER T001 (Directory Setup) completes.
 - **Note**: Moved from Phase 0 to Phase 1 to resolve ordering violation (Phase 0 task depending on Phase 1 task). [P] tag removed as it depends on T001 completion.

- [X] T002 Initialize Python project with `code/requirements.txt`: Pin dependencies to exact versions for reproducibility (e.g., `requests==2.31.0`, `GitPython==3.1.40`, `pandas==2.2.1`, `scipy==1.13.0`, `matplotlib==3.9.0`, `pyyaml==6.0.1`, `pytest==8.2.0`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management (`code/utils/config.py`) for seeds, paths, timeouts, API keys, and **pinned reference set SHA**.
 - **Action**: Define `FALSE_POSITIVE_THRESHOLD = 0.05` (5%) as the default value for tool validity checks.
 - **Verification**: Ensure `config.py` exports `FALSE_POSITIVE_THRESHOLD` and `RANDOM_SEED`.

- [X] T005 [P] Implement logging infrastructure (`code/utils/logger.py`) to track commit SHAs, Issue URLs, and API responses

- [X] T007 Create base data models (`code/utils/data_models.py`) defining:
 - `class CodeSample`: attributes `sample_id`, `source_type`, `repository_id`, `issue_id`, `task_id`, `language`, `file_path`, `function_name`, `is_fresh_commit`.
 - `class SmellMetric`: attributes `sample_id`, `smell_type`, `count`, `threshold_used`, `continuous_metric_value`.
 - `class StatResult`: attributes `smell_type`, `p_value`, `effect_size`, `confidence_interval`, `correction_method`, `test_method_used`.

- [X] T008 Implement syntax validation utility (`code/utils/validators.py`) for Python/Java file integrity checks

- [X] T009 Setup CI environment check for PMD CLI availability (Dockerfile or CI script to install PMD CLI)

- [X] T013.1 [P] [NFR-001] [Constitution-I] Implement `code/utils/validate_seed_pinning.py`:
 - **Purpose**: Verify that the execution environment's random seed configuration matches the pinned seed in `code/utils/config.py` before any data collection or generation occurs.
 - **Action**: Read `config.py` for `RANDOM_SEED`. Verify `os.environ.get('PYTHONHASHSEED')` and `random.seed()` are set to this value.
 - **Constraint**: If the seed is not pinned, **raise a SystemExit** to prevent non-reproducible runs, satisfying Constitution Principle I.
 - **Dependency**: Must run BEFORE T012 (Fetch) and T013 (Generation). This is a **blocking prerequisite** for the entire Phase 3.
 - **Note**: Moved from Phase 3 to Phase 2 to ensure environment pinning occurs before any data collection.

- [X] T022.5 [US2] Implement `code/02_static_analysis/generate_reference_set.py`:
 - **Purpose**: Fetch/Copy the "clean" reference set for tool validity testing.
 - **Source**: **Fetch a verified reference set from a canonical source: Python Standard Library v3.12.0 (Commit SHA: `v3.12.0` on GitHub).**
 - **Action**:
 1. Download the tarball from `.
 2. **Verify the SHA-256 checksum of the downloaded tarball against the hardcoded canonical hash: `0833189063301564788240434855658048380930101234567890123456789012` (Replace with actual verified hash of `)**.
 3. If checksum mismatch, **raise a `DataIntegrityError`** and halt.
 4. Extract and copy specific reference files (e.g., `Lib/os.py`, `Lib/re.py`) to `data/raw/reference_set/`.
 - **Data Hygiene**: **Calculate SHA-256 checksum for each saved file and append the hash and file path to `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`** to satisfy Constitution Principle III.
 - **Verification**: **Verify the SHA-256 of the downloaded tarball against the official manifest hash.**
 - **Output**: Save to `data/raw/reference_set/`.
 - **Dependency**: Must run after T004 (Config) and T007 (Data Models). **Must complete before T021 (Parallel Analysis) and T023 (Validity Check).**
 - **Note**: Moved from Phase 4 to Phase 2 to ensure reference set exists before any analysis tasks.

---

## Phase 3: User Story 1 - Data Collection & Sample Preparation (Priority: P1) 🎯 MVP

**Goal**: Collect a balanced dataset of human-written and LLM-generated code samples from multiple repositories (multiple samples per source per repo) to ensure statistical validity and repository-level matching. **Note**: This implements the "Balanced Blocked Design" from plan.md.

**Independent Test**: Verify the existence of `data/raw/human_samples` and `data/raw/llm_samples` containing a representative set of files each, with `data/raw/api_logs.json` logging the source repository, Issue/PR ID, Task ID, and exact commit SHA for every sample.

### Tests for User Story 1 (MANDATORY - Interface Definition)

- [X] T010 [US1] Contract test for repository selection logic in `tests/contract/test_repo_selection.py` (Defines interface for T012)
- [X] T011 [US1] Contract test for LLM generation logic in `tests/contract/test_llm_generation.py` (Defines interface for T013)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/01_data_collection/fetch_human_samples.py`:
 - **Algorithm**: Query GitHub API for candidate repositories with `stars:>100` AND `created:<{current_date - 5 years}`.
 - **Pre-Scan Constraint**: **Perform a pre-scan to identify exactly 50 repositories that have at least 3 distinct commits adding a.py or.java file. **
 - **Repository Age Filter**: **Explicitly mandate filtering repositories where `created_at` is at least 5 years prior to the current date** to satisfy Spec FR-001. Do not rely solely on commit dates.
 - **Selection Algorithm**: **If a sufficient number of candidates exist, sort by star count (descending), then by repository name (ascending) to ensure deterministic selection.**
 - **Extraction Logic**: If fewer than 50 repositories meet the criteria, **fail the run immediately with a clear error message**. If a sufficient number are found, select the top-ranked candidates based on the sorting rule.
 - **Extraction**: **For each of the selected repositories, extract exactly 3 distinct commits** that added a.py or.java file. **Sort all commits by date (descending), then by SHA (ascending) to select the top 3 deterministically.** Do not skip repositories.
 - **Fresh Commit Verification**: **Use `git fetch --depth=1 <commit_sha> --no-tags` to retrieve the specific commit object. Then, use `git cat-file -p <commit_sha>` to inspect the parent pointer. If the parent exists in the history (verified by `git cat-file -t <parent_sha>`), mark `is_fresh_commit=True`. If the parent is missing or the commit is the root, mark `is_fresh_commit=False`. This avoids full clones while verifying the parent relationship.**
 - **Extraction**: Extract the function code from each commit. Save to `data/raw/human_samples/` with metadata JSON sidecars containing `repo_id`, `commit_sha`, `issue_id`, `file_path`, `function_name`, `is_fresh_commit`.
 - **Constraint**: Total samples collected (3 per repository × 50 repositories = 150 samples). **This target aligns with the Deviation Log in spec.md (Section 4.3) which updates the original ≥1000 requirement to 150 for statistical validity (Balanced Blocked Design). **
 - **Logging**: Log every sample's `commit_sha`, `repo_id`, and `issue_url` to `data/raw/api_logs.json`.
 - **Traceability**: Ensure `issue_url` is logged to satisfy Constitution Principle II (Verified Accuracy).
 - **Data Hygiene**: **Calculate SHA-256 checksum for each saved file and append the hash and file path to `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`** to satisfy Constitution Principle III.
 - **Data Structure**: **Ensure metadata sidecars contain all fields required by T015 (manifest.csv) to avoid data loss.**
 - **Rate Limit Handling**: **Implement exponential backoff with jitter for GitHub API 403/429 responses. ** Log every rate limit event and retry attempt. **Generate a summary of rate limit events at the end of the run and append it to `data/raw/api_logs.json`.**
 - **Dependency**: Must run AFTER T001 (Directory Setup) and T013.1 (Seed Validation).
 - **Streaming**: **Use `git fetch --depth=1` with parent verification for large repositories to minimize disk usage, ensuring `is_fresh_commit` verification is preserved.**
 - **Fallback Logic**: **If the primary scan yields < 50 repos, expand the search criteria (e.g., lower star threshold) ONLY if the total count remains deterministic. If < 50 repos are found after expansion, the run MUST FAIL immediately to prevent variable sample counts.**

- [X] T012.5 [US1] Implement `code/01_data_collection/export_task_descriptions.py`:
 - **Purpose**: Extract Issue/PR descriptions from the metadata collected in T012 to create a structured task list for LLM generation.
 - **Input**: Read `data/raw/api_logs.json` and `data/raw/human_samples/` metadata.
 - **Dependency**: **Explicitly depends on the completion of the entire T012 phase** to ensure all 50 repositories and their samples are fully fetched before aggregation.
 - **Logic**: **One-to-One Mapping**: **Iterate over the 150 human samples collected in T012. For EACH sample, create exactly ONE task entry. Total tasks = 150.**
 - **Issue Selection**: **For each sample, identify the associated issue. If multiple commits are linked to different issues, select the issue with the highest comment count as the deterministic tie-breaker.**
 - **Output**: Generate `data/intermediate/tasks.json` containing `task_id`, `issue_url`, `description_text`, `language`, `repo_id`, `issue_id`, `linked_sample_ids` (list containing the single sample ID).
 - **Constraint**: **The `repo_id` and `issue_id` in the output MUST match exactly the set of human samples collected in T012 to preserve the Blocked Design. The output MUST contain a substantial number of tasks.**
 - **Pre-flight Check**: **Verify that `data/raw/human_samples/` contains exactly 150 files before proceeding. If count != 150, raise `DataFetchError`.**
 - **Dependency**: Must run after T012 completes.

- [X] T013 [US1] Implement `code/01_data_collection/generate_llm_samples.py`:
 - **Dependency**: Requires T007 (Data Models) to be complete to structure the output metadata schema.
 - **Input Validation**: **Verify the existence of `data/intermediate/tasks.json` and validate that it contains exactly 150 tasks with the expected schema (including `linked_sample_ids`). If missing or malformed, raise `DataFetchError`.**
 - **Task Derivation**: **Iterate strictly over the `task_id` list generated in T012.5, which corresponds to the exact issues used for human samples.**
 - **Generation**: Query HuggingFace Inference API (or similar) with a reasonable timeout and exponential backoff (with a limited number of retries).
 - **Seed Re-Pinning**: **Set `random.seed(RANDOM_SEED)` and `numpy.random.seed(RANDOM_SEED)` ONCE at the start of the generation loop. Do NOT re-apply the seed inside the loop.**
 - **Sampling**: **Generate 1 sample per task** (Total 150 samples across 150 tasks).
 - **Storage**: Save files to `data/raw/llm_samples/` with metadata JSON sidecars containing `task_id`, `model_id`, `model_version`, `api_endpoint`, `exact_prompt`, `prompt_hash`, `generation_seed`.
 - **Traceability**: Ensure full metadata schema (model_id, version, endpoint, prompt, seed) is logged to satisfy Constitution Principle VI (Code Generation Transparency).
 - **Rate Limit Handling**: **Implement exponential backoff with jitter for API rate limit responses. ** Log every rate limit event and retry attempt. **Generate a summary of rate limit events at the end of the run and append it to `data/raw/api_logs.json`.**
 - **Dependency**: Must run AFTER T013.1 (Seed Validation) and T012.5 (Task Descriptions).
 - **Execution Order**: **Execute generation calls sequentially to ensure deterministic ordering of API responses.**

- [X] T014 [US1] Implement `code/01_data_collection/validate_dataset.py`:
 - **Validation**: Run syntax validation on all samples using `code/utils/validators.py`.
 - **Action**: **Immediately exclude samples failing validation and log them.** Do not defer this decision to T023.
 - **Reporting**: Generate `data/intermediate/validation_report.json` listing excluded samples, reasons, and the final count of valid samples.
 - **Constraint**: If valid count is critically low, flag for manual review, but do not auto-halt based on an arbitrary percentage unless the tool validity check (T023) fails.
 - **Dependency**: Must run after T013 completes.

- [X] T015 [US1] Implement `code/01_data_collection/export_manifest.py`:
 - **Manifest**: Generate `data/raw/manifest.csv` with columns: `sample_id`, `source_type`, `repository_id`, `issue_id`, `task_id`, `commit_sha`, `file_path`, `language`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Analysis Execution (Priority: P2)

**Goal**: Run CPU-tractable static analysis (PMD/SonarQube CLI) on a representative set of samples to extract metrics for four code smell categories (Long Method, Duplicated Code, Feature Envy, Long Parameter List) within CI limits.

**Independent Test**: Run the analysis pipeline on a subset of samples and verify `data/intermediate/analysis_results.json` contains smell counts for all four categories and a tool-validity flag.

### Tests for User Story 2 (MANDATORY - Interface Definition)

- [X] T019 [US2] Contract test for PMD CLI wrapper in `tests/contract/test_pmd_wrapper.py`:
 - **Interface**: Define tests for `run_pmd(file_path, ruleset_path)` returning `exit_code` and `stdout`.
 - **Interface**: Define tests for `parse_output(xml_content)` returning a list of `SmellMetric` objects.
 - **Constraint**: Must handle timeout and memory limit errors gracefully.
- [X] T020 [US2] Contract test for parallel analysis execution in `tests/contract/test_static_analysis_interface.py` (Defines interface for T021)

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/02_static_analysis/run_pmd.py`:
 - **Wrapper**: Subprocess wrapper to execute PMD CLI with specific rulesets for `LongMethod`, `DuplicatedCode`, `FeatureEnvy`, `LongParameterList`.
 - **Parallel Execution**: **Implement parallel execution using `concurrent.futures.ProcessPoolExecutor` to process multiple files simultaneously**, respecting the 2GB RAM limit per process. This addresses the need for efficient CI execution.
 - **Limits**: Enforce per-process memory limit (≤2 GB) and 2-minute timeout per file.
 - **Timeout Handling**: **If a timeout occurs, log the file path, exclude it from the analysis results, and continue. Do not crash.**
 - **Error Handling**: Log syntax errors and PMD crashes; exclude from analysis.
 - **Output**: Return raw PMD XML/JSON output.
 - **Dependency**: Must run after T009 (PMD CLI setup) and T022.5 (Reference Set).

- [X] T022 [US2] Implement `code/02_static_analysis/parse_results.py`:
 - **Parser**: Parse PMD XML/JSON output into `data/intermediate/analysis_results.json`.
 - **Dependency**: Must run after T021 completes.
 - **Mapping**: Map smells to `SmellMetric` entities.
 - **Continuous Metric**: **Explicitly extract the 'CyclomaticComplexity' metric from PMD output and populate the `continuous_metric_value` field in the `SmellMetric` object.**
 - **Dependency**: Must run after T021 completes.

- [X] T023 [US2] Implement `code/02_static_analysis/tool_validity_check.py`:
 - **Validity**: Run analysis on the "clean" reference set produced by T022.5 (`data/raw/reference_set/`).
 - **Configuration**: **Load `FALSE_POSITIVE_THRESHOLD` from `code/utils/config.py`. If the key is missing, use the documented default value and log a WARNING.**
 - **Action**: Calculate false-positive rate. **If the rate > threshold, write a `tool_validity.json` file with status 'invalid' to `data/intermediate/`, log the error, and raise a `SystemExit(1)` to halt the pipeline (satisfying Spec FR-005).**
 - **Traceability**: Explicitly reference **Spec FR-005** for tool validity.
 - **Dependency**: Must run after T021 (wrapper) and T022.5 (reference data). **Must pass before T024 proceeds.**

- [X] T024 [US2] Implement `code/02_static_analysis/aggregate_metrics.py`:
 - **Aggregation**: Aggregate results into `data/processed/smell_metrics.csv` with columns: `sample_id`, `source_type`, `smell_type`, `count`, `continuous_metric_value`.
 - **Dependency**: Must run after T022, T021, T023, and T022.5 complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison & Reporting (Priority: P3)

**Goal**: Generate a final report comparing smell frequencies using a Blocked Permutation Test (repository as block), applying Bonferroni correction, and performing sensitivity analysis on the thresholds for **all four** code smell categories. **Note**: This implements the "Blocked Permutation Test" from plan.md.

**Independent Test**: Generate the final report and verify it contains statistical tables with corrected p-values, effect sizes, box plots, and explicitly uses associational language.

### Tests for User Story 3 (MANDATORY - Interface Definition)

- [X] T025 [US3] Contract test for permutation test logic in `tests/contract/test_permutation_test_interface.py` (Defines interface for T027)
- [X] T026 [US3] Contract test for report generation in `tests/contract/test_report_interface.py` (Defines interface for T029)

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/03_statistical_analysis/compare_distributions.py`:
 - **Method**: Implement Blocked Permutation Test (stratified by repository) per plan.md.
 - **Handling**: Handle zero-inflation and non-normality by using exact permutation counts.
 - **Correction**: Apply **Bonferroni correction for the multiple hypothesis tests** (4 tests, α ≤ 0.05) to control family-wise error rate.
 - **Metrics**: Calculate effect sizes (Cohen's d or equivalent for permutation tests).
 - **Output**: Save results to `data/intermediate/stat_results.json`.
 - **Constraint**: Must use the repository ID from `manifest.csv` as the blocking variable.

- [X] T028 [US3] Implement `code/03_statistical_analysis/sensitivity_analysis.py`:
 - **Sweep Configuration**: **Read the default thresholds from the PMD ruleset used in T021. Define the sweep range as a symmetric interval around the default value for each of the four code smell categories.**
 - **Sweep**: **Sweep thresholds for ALL four code smell categories** using the defined ranges.
 - **Stability Metric**: **Output the full threshold vs. p-value curve. Check if the sign of the effect size (direction of difference) is consistent across all thresholds.**
 - **Robustness Calculation**: **Explicitly calculate and report the 'robustness magnitude' (the range of thresholds where p < 0.05) and the specific 'flip point' (the threshold where the sign of the effect size changes) in the output CSV and JSON report.**
 - **Verification**: The task must output a pass/fail status based on **sign consistency** (stable if direction is consistent, unstable if it flips) AND the **robustness magnitude** to satisfy Spec SC-005. **Do not use arbitrary variance thresholds.**
 - **Dependency**: Must run after T027 completes.
 - **Output**: Generate `data/intermediate/sensitivity_curve.csv` (columns: `smell_type`, `threshold`, `p_value`, `effect_sign`, `is_significant`) and `data/intermediate/sensitivity_analysis_report.json` (including `robustness_range`, `flip_point`, and `stability_passed`).

- [X] T029 [US3] Implement `code/04_reporting/generate_report.py`:
 - **Inputs**: Read from `data/processed/smell_metrics.csv`, `data/intermediate/stat_results.json`, `data/intermediate/sensitivity_analysis_report.json`.
 - **Template**: Use `templates/final_report_template.md`.
 - **Content**: Include Introduction, Methodology (Blocked Permutation Test), Results (Statistical Tables with corrected p-values, effect sizes), Sensitivity Analysis, Conclusion.
 - **Visuals**: Include box plots comparing distributions and **generate a line plot showing the p-value trend across the sensitivity analysis sweeps for all four code smell categories.**
 - **Language**: Enforce associational language (e.g., "associated with", "correlated with") and explicitly exclude causal claims (per Spec FR-007 rejection).
 - **Conclusion Requirement**: **The Conclusion section MUST explicitly state the study is observational and uses associational language, strictly avoiding causal claims.**
 - **Output**: Generate `reports/final_study_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [US1] Documentation updates in `specs/001-code-smell-comparison/research.md`:
 - **Action**: Add a section titled "Balanced Blocked Design Implementation" documenting the current implemented design. **Cross-reference the existing Deviation Log in `spec.md` (Section 4.3)** which explains the change from the original aspirational 1000/50 split. Do NOT create a new table duplicating the spec's deviation log; instead, summarize the implementation reality and link to the spec.
 - **Content Requirements**: The section MUST explicitly document:
 1. An equal split between Human and LLM samples.
 2. The block size (3 samples per source per repo).
 3. The rejection of the large-scale design as methodologically flawed.
 - **Verification**: Verify `research.md` contains the implementation summary and a clear link to the spec's deviation log.
 - **Constraint**: Do not attempt to "justify a deviation from 1000/50" as a new change; the spec already records this deviation. The task is to document the *current* state. Dependency: T001.1 (Initialization). **Note**: [P] tag removed as it depends on T001.1 completion.

- [X] T031.1 [P] Create PMD utility module:
 - **Action**: Create `code/utils/pmd_utils.py` and define functions `parse_pmd_output(xml_content)` and `format_pmd_ruleset(rules)`.
 - **Verification**: Ensure the module is importable and functions are defined.

- [X] T031.2 [P] Update T021 to use PMD utility:
 - **Action**: Refactor `code/02_static_analysis/run_pmd.py` to import and use `format_pmd_ruleset` from `code/utils/pmd_utils.py`.
 - **Verification**: Ensure `run_pmd.py` no longer contains inline ruleset formatting logic.

- [X] T031.3 [P] Update T022 to use PMD utility:
 - **Action**: Refactor `code/02_static_analysis/parse_results.py` to import and use `parse_pmd_output` from `code/utils/pmd_utils.py`.
 - **Verification**: Ensure `parse_results.py` no longer contains inline XML parsing logic.

- [X] T032.1 [P] Profile PMD execution:
 - **Action**: Run `cProfile` on `code/02_static_analysis/run_pmd.py` with a sample of representative files. Generate a profile report.
 - **Verification**: Identify the top memory-intensive functions.

- [X] T032.2 [P] Implement generator-based chunking:
 - **Action**: Refactor `code/02_static_analysis/aggregate_metrics.py` (T024) to use generators instead of loading all rows into a list. Process data in fixed-size chunks.
 - **Verification**: Ensure memory usage remains within acceptable limits during processing of samples.

- [X] T033 [P] Additional unit tests in `tests/unit/`:
 - **Action**: Write unit tests for `code/utils/validators.py` and `code/utils/config.py`.
 - **Target**: Achieve ≥90% line coverage for these modules.

- [X] T034 Run `quickstart.md` validation:
 - **Action**: Execute `python -m code.main --validate`.
 - **Verification**: Ensure exit code 0 and all data files are present.

- [X] T037 [P] **Integrated into T029**: Sensitivity analysis visualization is now a mandatory part of T029.
 - **Action**: Refer to T029 for implementation details.
 - **Verification**: Ensure the final report includes the sensitivity plot.

- [X] T042 [P] **Implement Fail-Loud Data Loader Wrapper**:
 - **Action**: Create `code/utils/fail_loud_loader.py` to wrap all data fetching functions (T012, T013, T022.5). Ensure that if a fetch fails, the function raises a specific `DataFetchError` with context (URL, error code) and **NEVER** falls back to synthetic/mock data.
 - **Verification**: Write a unit test that mocks a network failure and asserts that the wrapper raises `DataFetchError` instead of returning mock data.
 - **Dependency**: Must run after T008 (validators) and T004 (config).
 - **Rationale**: Enforces Constitution Principle III (Data Hygiene) and the "Loader must FAIL LOUDLY" rule to prevent silent fabrication.

- [X] T043 [P] **Add Blocked Permutation Test Sanity Check**:
 - **Action**: Create `tests/unit/test_permutation_sanity.py` to verify the permutation test logic with a known synthetic dataset where the ground truth is known (e.g., two identical distributions should yield p=1.0).
 - **Verification**: Ensure the test passes and correctly identifies a known effect when injected.
 - **Dependency**: Must run after T027.
 - **Rationale**: Validates the statistical engine before processing real data, ensuring the "Blocked Permutation Test" is implemented correctly as per plan.md.

- [X] T045 [P] [US3] **Implement Bonferroni Correction Verification**:
 - **Action**: Create `tests/unit/test_bonferroni_correction.py` to verify that the p-values in `data/intermediate/stat_results.json` are correctly adjusted using the Bonferroni method (α / 4).
 - **Logic**: Inject a known set of 4 raw p-values and verify the output p-values match the adjusted values according to the specified correction method.
 - **Verification**: Ensure the test passes and correctly identifies any deviation from the standard Bonferroni formula.
 - **Dependency**: Must run after T027.
 - **Rationale**: Ensures the statistical correction for multiple hypothesis testing is implemented correctly, satisfying Spec FR-006 and Plan Methodology.

- [X] T046 [P] [US2] **Add PMD Ruleset Validation Task**:
 - **Action**: Create `tests/contract/test_pmd_ruleset_validation.py` to verify that the PMD ruleset file (XML) contains exactly the four required rules: `LongMethod`, `DuplicatedCode`, `FeatureEnvy`, `LongParameterList`.
 - **Logic**: Parse the ruleset file and assert the presence and correct configuration of each rule.
 - **Verification**: Ensure the test fails if any rule is missing or misconfigured.
 - **Dependency**: Must run after T021 (wrapper) is implemented.
 - **Rationale**: Prevents silent failures where PMD might run with an incomplete or incorrect ruleset, ensuring the analysis targets the correct code smells.