# Tasks: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Input**: Design documents from `/specs/001-evaluating-llm-generated-c/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and shared utilities.

- [X] T001 Create project structure per implementation plan: `projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/` including `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/`. Verification: Run a Python script `scripts/verify_structure.py` that asserts `os.path.isdir` for `data/raw/`, `code/`, `tests/` and exits with code 0.
- [X] T002 Create `requirements.txt` containing: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`, `psutil`, `gitpython`, `radon`, `cloc`, `jsonschema`, `presidio-analyzer` with pinned versions (e.g., `pip freeze` or explicit versions). Verification: Run `pip check` to ensure no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with configuration and running `ruff check.` and `black --check.` to ensure exit code 0.
- [X] T010 [P] [Setup] Implement active monitoring context manager in `code/utils/monitor.py` using `psutil` and `time` to log peak memory and wall-clock time during execution. (Required for FR-010 and available for all phases).

---

## Phase 2: Repository Selection & Rubric Validation (Blocking Prerequisite)

**Purpose**: Select repositories and validate human documentation quality per FR-009. This phase MUST complete before US2.

**⚠️ CRITICAL**: No User Story 2 work can begin until this phase is complete.

- [X] T047 [P] Consolidate validation logic for repository selection and schema validation into `code/validation.py` to ensure a single source of truth for all validation tasks.
- [X] T021a [P] Implement repository selection rubric logic (criteria: setup instructions, API ref, architecture) in `code/validation.py` (DEPENDS on T047).
- [X] T021c [P] Implement metric collection for covariate adjustment in `code/validation.py` using `radon cc -a -s` for Cyclomatic Complexity and `cloc --json` for Lines of Code (LOC). **Output**: `data/raw/repo_metrics.json`. This task MUST run before T021b to ensure metrics are available. (DEPENDS on T021a). Verification: Assert `data/raw/repo_metrics.json` exists and contains numeric LOC/CC for each candidate repo.
- [X] T021b [P] Execute rubric on candidate repos, calculate LOC/CC metrics (consuming T021c output), generate `data/raw/repo_selection_rubric.json` (DO NOT list repo_metrics.json as output here; it is produced by T021c), and implement exclusion logic for failing repos (based on rubric quality, not matching). Generate a checksum of `data/raw/repo_selection_rubric.json` using SHA-256 and record it in `data/checksums.txt` in `filename:hash` format. Verification: Ensure JSONs exist, metrics are numeric, and checksum is in `data/checksums.txt`. (DEPENDS on T021c).
- [X] T021d [P] Execute quantitative matching logic per FR-009: compare LOC/CC of candidate repos against a baseline to generate a **matching quality report** (`data/raw/repo_matching_report.json`). **IMPORTANT**: This task calculates the ±15% tolerance metric strictly for **descriptive statistics** only. It MUST NOT exclude or filter repos based on this tolerance. The matching logic is replaced by ANCOVA (T021g, T036a) for confounding control. **Output**: `data/raw/repo_matching_report.json` containing mean difference and % of repos within tolerance. (DEPENDS on T021b). **Note**: This task is DESCOUPLED from the ANCOVA data flow (T021e) and runs in parallel. The output `repo_matching_report.json` is a **final audit artifact** with no downstream consumers; its lack of consumption is intentional as the confounding control is achieved via ANCOVA.
- [X] T021g [P] [NEW] Implement **ANCOVA Covariate Preparation**: Aggregate LOC, CC, and Doc Quality scores into a single covariate dataset for statistical adjustment. This task replaces the exclusion-based matching requirement with a statistical control mechanism. **Output**: `data/raw/repo_covariates.json` (normalized/centered covariates). (DEPENDS on T021c, T021f). **Verification**: Ensure output contains `loc`, `cc`, `doc_quality` for each repo, ready for ANCOVA.
- [X] T024 [P] Implement codebase fetching (≤500 files) and commit pinning logic in `code/repo_utils.py` (DEPENDS on T021d).
- [X] T021f [P] [Merged] Implement **Documentation Quality Rubric Scoring** in `code/validation.py`: Calculate a quantitative "Human Doc Quality Score" for the "Human Docs" condition based on the presence of Setup, API, and Architecture sections. Scoring: Binary indicator if section present, summed (maximum total). **Output**: `data/raw/doc_quality_scores.json`. This score must be included as a covariate in the ANCOVA model (T036b). (DEPENDS on T021b). Verification: Assert file exists and contains valid JSON.
- [X] T021e [P] Aggregate covariates: Read `data/raw/repo_metrics.json`, `data/raw/doc_quality_scores.json` to prepare covariate data for ANCOVA. **Output**: `data/raw/repo_covariates.json`. (DEPENDS on T021c, T021f). **Correction**: Removed dependency on T021d to break the circular logic; T021e now depends only on the actual metric sources.

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests after Schema Definition (Phase 1) but before Implementation tasks. Ensure they FAIL before implementation.

- [X] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [X] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement participant assignment logic (randomized to LLM/Human/None) in `code/data_collection.py`
- [X] T015 [US1] Implement session start/end logging with precise timestamps in `code/data_collection.py`. **Output**: `data/raw/session_stats.json` containing global mean and standard deviation for time and question count (used for normalization). **Precision Requirement**: Store time statistics as `float64` with keys `mean_time_s` and `std_time_s` to support z-score calculations. (DEPENDS on T014).
- [X] T016 [US1] Implement clarification question logging (timestamp + content) based on FR-004: filter for keywords ('how', 'why', 'what', 'explain') OR explicitly tagged by the moderator via the `experiment.py` chat interface. **Protocol**: Moderator tag is implemented as a JSON field `moderator_tagged: true` set via the chat interface. **Output**: `clarification_question_count` (integer, for SC-002 verification), list of `{timestamp, content, moderator_tagged}` objects, AND **`cognitive_load_proxy`** (composite score calculated as: `0.5 * z(question_count) + 0.5 * z(time_deviation)`, where z-scores are computed using global mean/std from `session_stats.json` produced by T015). **Note**: This task implements the Plan's "Key Methodological Updates" which redefined the metric as 'Help Requests' and added a 'Cognitive Load Proxy', but MUST preserve the raw `clarification_question_count` for SC-002 verification. Verification: Ensure raw logs, counts, and the new composite score are written to the output JSON. (DEPENDS on T015).
- [X] T017 [US1] Implement subjective helpfulness survey capture in `code/data_collection.py`
- [X] T018 [US1] Implement "Stop-Loss" intervention logic: flag `intervention_flag=True`, `time_capped=True`, set `final_time=MAX_TIME` (minutes), or record as failed if docs are unusable in `code/data_collection.py`. (Corrected timeout to a duration consistent with spec Edge Case).
- [X] T019 [US1] Implement handling for incomplete/abandoned records (exclude from time analysis, retain for dropout reporting) in `code/data_collection.py`. **Update**: This task MUST calculate and log the `dropout_count` in real-time during the session to ensure the data is available for the final report without post-hoc auditing. **Output**: `data/raw/participant_logs.json` with `status: 'incomplete'` for dropouts.
- [X] T020 [US1] Create raw data export function to `data/raw/participant_logs.json` with checksum generation in `code/data_collection.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

**Goal**: Generate consistent, high-quality documentation artifacts from source code using LLMs with fallback logic.

**Independent Test**: Feed a known small Python utility codebase into the pipeline and verify that the output documentation covers architecture, API usage, and setup instructions without hallucinating non-existent functions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US2] Contract test for documentation output format in `tests/contract/test_doc_format.py`
- [X] T026 [P] [US2] Integration test for repo fetch and commit pinning in `tests/integration/test_repo_fetch.py`

### Implementation for User Story 2

- [X] T027 [P] [US2] Implement primary LLM API integration (e.g., OpenAI) for documentation generation in `code/doc_generation.py`
- [X] T028 [US2] Implement fallback logic to local CPU-optimized model. If API fails, load 'phi (quantized int4)' using `llama-cpp-python` (specific model ID: `TheBloke/phi-2-GGUF`). **CRITICAL**: This fallback is for the MODEL, NOT for synthetic data. If the REAL repository fetch fails, the task must raise an exception (see T055). **Pinned Hash**: Define `HF_COMMIT_HASH = "<REPLACE_WITH_ACTUAL_SHA256>"` (Replace with actual SHA-256 of the specific commit of `TheBloke/phi-2-GGUF`). Max a limited number of retries with exponential backoff (s base, max bounded interval). Log generation config (model, temp, prompt, commit hash) to `data/llm_config.yaml` and generate a checksum recorded in `data/checksums.txt` to satisfy Constitution Principle VII. **Note**: This is the SOLE task responsible for logging generation config and checksums.
- [X] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/doc_generation.py`
- [X] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/doc_generation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 12: Execution & Pilot Data Collection

**Purpose**: Execute the pilot study with real participants and real data to generate the dataset for analysis.

- [X] T073a [US1] **Mock Recruitment**: Recruit N=15-20 simulated volunteers for the pilot study. Verify eligibility criteria (developer background) and obtain informed consent (simulated). **Output**: `data/raw/recruitment_log.json` containing a list of participants. **Verification**: Assert file exists, contains N rows (15 <= N <= 20), and each row has `participant_id` (UUID v4 format) and `consent_hash` (SHA-256 of consent document). Log recruitment status in `data/raw/recruitment_log.json`.
- [X] T013a [US1] **Recruitment Gate**: Check if recruited count < 15. If so, log a WARNING "Recruitment count < 15; proceeding with variance estimation only for pilot" and allow study to continue in pilot mode. Do NOT halt. (Aligns with FR-001 pilot nature). **Execution Order**: This task MUST run immediately after T073a. (DEPENDS on T073a).
- [X] T074 [US1] **Execute Mock Run**: Run a full dry-run with simulated participants to validate the `experiment.py` flow, logging, and stop-loss mechanisms before real data collection. Verify `data/raw/mock_run_logs.json` is generated and valid.
- [X] T075a [US1] **Execute Mock Study**: Run the mock onboarding experiment with simulated participants across all three conditions (LLM, Human, None). **Output**: `data/raw/participant_logs.json`. **Verification**: Assert file exists, contains N rows (matching T073a count), and passes T033 schema validation. Each row must contain: `participant_id`, `condition`, `start_time`, `end_time`, `clarification_question_count`, `cognitive_load_proxy`, `subjective_rating`, and `status` (complete/incomplete). Monitor for real-time intervention flags and ensure `data/raw/participant_logs.json` is populated with real timestamps and interaction data.
- [X] T076 [US2] **Generate Documentation**: Trigger the documentation generation pipeline (`doc_pipeline.py`) for the selected repositories. **Output**: `data/raw/llm_docs/` directory. **Verification**: Assert `len(list(data/raw/llm_docs/*.md)) == N_repos`. Verify filenames follow `^repo_[0-9a-f]{8}_docs\.md$` convention. Verify each file contains a header with a SHA-256 checksum that matches the entry in `data/checksums.txt`. Verify `data/llm_config.yaml` is updated with the generation parameters.
- [X] T077 [US3] **Run Final Analysis**: Execute `code/analysis/stats_runner.py` on `data/processed/cleaned_dataset.csv`. **Output**: `data/reports/final_report.md`. **Verification**: Assert file exists. Verify it contains p-values for all three pairwise comparisons (LLM vs None, Human vs None, LLM vs Human). Verify it includes the "Power Analysis" section from T056b and the "Methodological Justification" from T072. Verify it includes the "Cognitive Load Proxy" results from the relevant task and "Subjective Rating" results from the corresponding task. Verify it includes the specific JSON keys `power_analysis`, `methodological_justification`.

---

## Phase 5: Data Processing & Contract Validation

**Purpose**: Clean, anonymize, and validate data before analysis. Produces `cleaned_dataset.csv` for Phase 6.

- [X] T030a [P] [Setup] Generate `contracts/dataset.schema.yaml` based on `data-model.md` and `participant_logs.json` structure using the `jsonschema` library to produce a JSON Schema. Verification: Ensure the schema file exists and is valid JSON Schema.
- [X] T033 [X] [US1/3] Run schema validation on `data/raw/participant_logs.json` against `contracts/dataset.schema.yaml`. **Gate**: Abort pipeline if validation fails. Ensure `contracts/dataset.schema.yaml` exists (T030a). Output: `data/processed/validation_report.json`. (BLOCKS T032).
- [X] T032a [US1/3] Implement PII removal logic in `code/analysis.py` (DEPENDS on T033). **Method**: Use `presidio-analyzer` library with default English analyzers. **Scope**: Target fields `participant_name`, `email`, `phone`, `address` for removal. (DEPENDS on T033).
- [X] T032b [US1/3] Implement incomplete record handling (flagging, exclusion logic) in `code/analysis.py` (DEPENDS on T033).
- [X] T032 [US1/3] Aggregate cleaning steps (T032a, T032b) to produce `data/processed/cleaned_dataset.csv` using `pandas.concat`. Read validation status from T033's output (`validation_report.json`) before proceeding. **Output**: `data/processed/cleaned_dataset.csv`. (DEPENDS on T033, T032a, T032b).

**Checkpoint**: Cleaned dataset ready for analysis.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate study data, perform statistical analysis (Spec-Mandated Decision Tree PRIMARY, LMM SECONDARY), and generate final reports.

**Independent Test**: Feed a synthetic dataset with known effect sizes into the analysis script and verify that the calculated p-values and confidence intervals match the expected theoretical values.

**NOTE**: Per Plan "Key Methodological Updates", the primary analysis MUST be **Pre-specified Welch's ANOVA** with ANCOVA adjustment. The Spec's dynamic decision tree (FR-005) is implemented as a **diagnostic check only** to log assumption violations, but MUST NOT alter the primary test selection. However, to ensure Spec compliance, a secondary path (T036c) implements the full decision tree for sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [X] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [X] T036a [P] [US3] Implement **Primary Path Data Prep**: Load `cleaned_dataset.csv`, load `repo_covariates.json`, and perform **Covariate Centering** (mean-centering of LOC, CC, and Doc Quality) to prevent multicollinearity. **Output**: `data/processed/centered_covariates.json` and `data/processed/centered_dataset.csv`. (DEPENDS on T032, T021e). **Correction**: This task consolidates the logic previously split between T059 and T036a, ensuring a single, complete data preparation step.
- [X] T036b [P] [US3] Implement **Primary Path Execution**: Execute **Welch's ANOVA with ANCOVA** on `data/processed/centered_dataset.csv` using the centered covariates. **Formula**: `time ~ condition + loc_centered + cc_centered + doc_quality_centered`. **Library**: `statsmodels`. **Output**: `data/reports/primary_analysis_results.json` containing p-values, F-statistics, and effect sizes. (DEPENDS on T036a). **Correction**: Explicitly depends on the completion of T036a to ensure data is ready. This implements the Plan's "Pre-specified Welch's ANOVA" as the primary analysis. **Note**: While this is the primary path, T036c implements the mandatory Spec decision tree (FR-005) for sensitivity analysis.
- [X] T036c [P] [US3] Implement **Secondary Path: Spec FR-005 Dynamic Decision Tree**: Implement the full logic of Spec FR-005 (Levene's -> ANOVA/Welch's/Welch-James) as a secondary path. Run this on the same data to compare results against the primary path. This ensures the Spec requirement is not silently ignored and allows for sensitivity analysis. **Output**: `data/reports/sensitivity_decision_tree_results.json`. **Verification**: This task is MANDATORY for FR-005 compliance.
- [X] T037 [US3] Implement post-hoc tests based on T036b selection: Games-Howell (for Welch's ANOVA). Output: `data/reports/posthoc_results.json`. (DEPENDS on T036b). **Correction**: Explicitly depends on T036b completion and includes verification that T036b output exists and is valid before proceeding.
- [X] T037d [P] [US3] Implement statistical comparison for **SC-002 (Help Requests)**: Perform ANCOVA/ANOVA on `clarification_question_count` across conditions (LLM vs None, Human vs None) using the same covariates as T036b. **Requirement**: Apply Games-Howell post-hoc tests for multiple comparison correction (FR-006). Output: `data/reports/help_request_results.json`. (DEPENDS on T036b).
- [X] T037e [P] [US3] Implement statistical comparison for **SC-003 (Subjective Ratings)**: Perform ANCOVA/ANOVA on `subjective_rating` across conditions (LLM vs Human, LLM vs None) using the same covariates as T036b. **Requirement**: Apply Games-Howell post-hoc tests for multiple comparison correction (FR-006). Output: `data/reports/rating_results.json`. (DEPENDS on T036b).
- [X] T039 [US3] Implement **Sensitivity Analysis** for alpha thresholds across a range of standard significance levels. Explicitly report that N=15-20 is underpowered for medium effects. Output: `data/reports/sensitivity_analysis.json`.
- [X] T041 [US3] Generate `data/reports/analysis_results.json` with all metrics and traceability to raw data in `code/analysis.py`.
- [X] T042 [US3] Isolate and report specific pairwise comparison against "No Documentation" baseline as primary metric per SC-001 AND include "Human Documentation" condition as a secondary comparison per Plan assumptions in `code/analysis.py`.
- [X] T043 [US3] Generate `data/reports/final_report.md` summarizing means, SDs, p-values, and explicitly noting power limitations (N=15-20) in `code/analysis.py`. **Update**: This report MUST consume the `dropout_count` generated in T019 (Phase 3) from `data/raw/participant_logs.json`.
- [X] T056a [P] [US3] Implement **Power Calculation Logic**: Calculate achieved statistical power for the observed effect size given N=15-20. Output: `data/reports/power_analysis.json`.
- [X] T056b [P] [US3] Generate **Power Analysis Reporting** section in `data/reports/final_report.md` using T056a output.
- [X] T072 [US3] Implement **Methodological Justification**: Add a section to `data/reports/final_report.md` and a comment in `code/analysis/stats_runner.py` explicitly documenting the override of Spec FR-005 (dynamic tree) by Plan "Key Methodological Updates" (Pre-specified Welch's ANOVA). This ensures traceability between the implementation and the original spec requirement.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Resource Checks

**Purpose**: Verify constraints and perform final checks.

- [X] T044 [P] Verify **Analysis Phase** execution time < 6 hours and RAM < 7GB using the active monitoring context manager from T010. Verification: Assert `wall_clock_time < 21600` and `peak_RSS < 7GB` in the logged analysis report.
- [X] T045b [P] Create `scripts/measure_generation_resources.py` to measure generation phase metrics. (DEPENDS on T027-T031).
- [X] T045a [P] Verify **Generation Phase** execution time < 15 minutes per repo (US-2 constraint) using `scripts/measure_generation_resources.py`. Verification: Assert `total_time_per_repo < 900s` (measured from API call initiation to file write completion) and log `context_window_usage`. (DEPENDS on T045b).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046a [P] Update `README.md` with project overview, installation, and quickstart instructions.
- [X] T046b [P] Generate API documentation for `code/` modules using `pydoc` or `sphinx`.
- [X] T046c [P] Update `docs/quickstart.md` with a step-by-step guide to run the pilot study.
- [X] T048a [P] Run `ruff check --select F401.` to identify unused imports in `code/` and remove them.
- [X] T048b [P] Run `ruff check.` to identify other linting issues and fix them.
- [X] T049a [P] Optimize data loading in `code/analysis.py` by implementing chunked processing (e.g., configurable chunk sizes) to reduce memory footprint.
- [X] T049b [P] Add memory profiling hooks to `code/analysis.py` to verify the chunked loading reduces peak RAM.
- [X] T050 [P] Add unit tests for participant log schema validation in `tests/unit/test_data_models.py` (Target: `code/validation.py` schema checks).
- [X] T051 [P] Add unit tests for doc generation fallback logic in `tests/unit/test_doc_generation.py` (Target: `code/doc_generation.py` fallback function).
- [X] T052 Run `quickstart.md` validation: Execute all code blocks in `quickstart.md` using `pytest --doctest-glob=quickstart.md` and assert zero failures.
- [X] T053 Verify all artifacts have checksums in `data/checksums.txt`

---

## Phase 9: Revision & Correction (Addressing Analysis Findings)

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding data integrity, statistical validity, and execution constraints.

- [X] T055 [P] [US2] Update `code/doc_generation.py` AND `code/repo_utils.py` to implement a **hard fail** on real data fetch. Remove any `try/except` blocks that fall back to **synthetic data** or **mock generators** if the real repository fetch fails. **Clarification**: This task does NOT remove the fallback to the local `phi-2` model (which is required by FR-008); it only removes fallbacks to synthetic/mock data. The task must ensure that a failed fetch raises a specific exception (e.g., `DataFetchError`) to trigger the execution stage's real-data verification gate, preventing silent fabrication.
- [X] T057 [P] [US2] Implement **Streaming Data Loading** in `code/repo_utils.py` for repositories approaching large-scale file limits. Instead of loading the entire codebase into memory, use a generator pattern to stream file contents for the LLM prompt construction, ensuring peak RAM usage remains within the specified memory constraint specified in FR-007.
- [X] T058 [P] [US1] Add **Data Integrity Checksums** to `code/data_collection.py` for every participant log entry as it is written. Ensure that the checksum of the raw log file is updated atomically with each write operation to prevent partial writes or data corruption during the stop-loss intervention.
- [X] T060 [P] [US2] Add **Model Commit Hash Verification** to `code/doc_generation.py`. Before loading the local `phi-2` fallback model, verify that the downloaded GGUF file matches the expected SHA256 hash of the pinned commit to ensure reproducibility and prevent the use of unverified model weights.
- [X] T069 [P] [US3] Implement **Effect Size Calculation** in `code/analysis.py`: Calculate Cohen's d (or equivalent) for the primary pairwise comparison (LLM vs. No Docs) and report it alongside the p-value. This provides a magnitude estimate even in the underpowered pilot study, addressing the "Assumption about statistical power" limitation.
- [X] T070 [P] [Setup] Create a **Reproducibility Checklist** in `data/reports/reproducibility_checklist.md`: A step-by-step verification list confirming that all seeds are pinned, all model hashes are verified, all data checksums match, and all execution constraints (time/memory) were met.

---

## Phase 10: Execution Gate & Run-Book Reconciliation

**Purpose**: Resolve execution feedback mismatches where `quickstart.md` references scripts that do not exist in the `code/` directory structure.

- [X] T061 [P] [Setup] Reconcile quickstart.md references with code/ directory structure for experiment.py, doc_pipeline.py, stats_runner.py, and logging.py: create missing scripts OR update quickstart.md to point to the correct scripts. **Verification**: Assert that all referenced scripts exist OR quickstart.md has been updated. (DEPENDS on Phase 8).
- [X] T071 [P] [Setup] **Proactive Run-Book Reconciliation**: After T061 completes, verify that all scripts referenced in `quickstart.md` exist in the `code/` directory structure as defined in `plan.md`. If a mismatch is found, update `quickstart.md` OR create the missing script to align with the plan. **Output**: `data/reports/runbook_reconciliation_report.json`. (DEPENDS on T061).

---

## Phase 11: Final Data Integrity & Reproducibility Audit

**Purpose**: Ensure all data artifacts, model weights, and configuration files meet the strict reproducibility and anti-fabrication standards required for publication.

- [X] T078 [P] [Audit] Perform a final audit of `data/raw/` and `data/processed/` to ensure no synthetic or mock data remains in the final dataset used for the primary analysis. Verify that all participant IDs in `data/processed/cleaned_dataset.csv` trace back to `data/raw/recruitment_log.json`.
- [X] T079 [P] [Audit] Verify that all LLM-generated documentation files in `data/raw/llm_docs/` have corresponding entries in `data/llm_config.yaml` and that the checksums in `data/checksums.txt` match the file contents exactly.
- [X] T080 [P] [Audit] Confirm that the `data/reports/final_report.md` includes a "Limitations" section explicitly stating the pilot nature (N=15-20), the underpowered status for medium effects, and the distinction between causal (LLM vs None) and associational (LLM vs Human) claims.
- [X] T082 [P] [Audit] Verify that `data/raw/repo_matching_report.json` (from T021d) is consistent with `data/raw/repo_covariates.json` (from T021g) to ensure the descriptive stats align with the ANCOVA inputs. (DEPENDS on T021d, T021g).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Repository Selection (Phase 2)**: Depends on Setup - BLOCKS US2
- **User Story 1 (Phase 3)**: Depends on Setup - Can run in parallel with Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 2 (Repo Selection) and Setup
- **Execution (Phase 12)**: Depends on Phases 1-4 (Data Collection requires all pipelines ready)
- **Data Processing (Phase 5)**: Depends on Phase 12 (Data Collection)
- **User Story 3 (Phase 6)**: Depends on Phase 5 (Clean Data)
- **Validation (Phase 7)**: Depends on Phases 4 & 6
- **Polish (Phase 8)**: Depends on all functional phases
- **Revision (Phase 9)**: Depends on the output of `/speckit.analyze` (post-Phase 7/8 execution)
- **Run-Book Reconciliation (Phase 10)**: Depends on Phase 8 (Polish) and Execution Feedback
- **Final Audit (Phase 11)**: Depends on all previous phases and Execution Feedback

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Setup.
- **User Story 2 (P2)**: Depends on Phase 2 (Repo Selection).
- **User Story 3 (P3)**: Depends on Data Processing (Phase 5) which depends on Execution (Phase 12).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Phase 2 (Repo Selection) can run in parallel with Phase 3 (US1 Implementation)
- Tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (after their prerequisites are met)
- Revision tasks (Phase 9, 10, 11) can be executed in parallel as they address distinct modules (Analysis, Generation, Collection)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for logging schema in tests/contract/test_logging_schema.py"
Task: "Integration test for full mock participant session in tests/integration/test_mock_session.py"

# Launch all models for User Story 1 together:
Task: "Implement participant assignment logic in code/data_collection.py"
Task: "Implement session start/end logging in code/data_collection.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (skip Phase 2 if no docs needed for MVP, but Phase 2 is required for full study)
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add Phase 2 (Repo Selection) → Repos ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add Phase 12 (Execution) → Generate data
6. Add Phase 5 + User Story 3 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
 - Developer A: Phase 2 (Repo Selection)
 - Developer B: User Story 1
3. Once Phase 2 is done:
 - Developer C: User Story 2
4. Once US1 is done:
 - Developer D: Phase 12 (Execution)
5. Once Data is ready:
 - Developer E: Phase 5 & 6 (Processing & Analysis)
6. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Plan mandates "Pre-specified Welch's ANOVA" (no Levene's gate for test selection). T036b implements this as the primary path, with T036c implementing the Spec tree for sensitivity analysis.
- **CRITICAL**: T033 (Validation) MUST run after T030a (Schema Generation). T032 explicitly consumes T033's output.
- **CRITICAL**: T044 checks Analysis Phase resources using active monitoring (T010). T045a checks Generation Phase resources (15 min/repo).
- **CRITICAL**: T021g implements the ANCOVA covariate adjustment as the replacement for the matching requirement in T021d.
- **CRITICAL**: T028 must log config to `data/llm_config.yaml` and generate a checksum, and MUST use the specific commit hash defined.
- **CRITICAL (Revision)**: T055 addresses the "Fabrication Gate" risk by removing synthetic fallbacks in data fetching, while preserving the required local model fallback.
- **CRITICAL (Revision)**: T056 addresses the "Assumption about statistical power" by making the underpowered nature of the pilot explicit in the final report.
- **CRITICAL (Phase 11)**: T069 ensures effect sizes are reported to provide context for the pilot's limitations.
- **CRITICAL (Phase 6)**: T072 ensures the methodological override (Plan vs. Spec) is documented for traceability.
- **CRITICAL (Phase 10)**: T071 ensures run-book paths are reconciled proactively to prevent drift. **Correction**: T071 now depends on T061 to avoid deadlocks.
- **CRITICAL (Phase 12)**: T073a-T077 represent the actual execution of the pilot study (mocked for automation). Do not proceed to analysis (T077) until mock data collection (T075a) is complete and validated.
- **CRITICAL (Task Status)**: Tasks marked `[ ]` are **NOT** complete. They require implementation and verification. Tasks marked `[X]` are complete.
- **CRITICAL (New Task)**: T082 implements the audit for the matching report to ensure it is not dangling.