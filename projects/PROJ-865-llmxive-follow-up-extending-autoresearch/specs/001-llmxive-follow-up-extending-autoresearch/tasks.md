# Tasks: llmXive follow-up: extending "AutoResearchClaw"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Constitutional Gates

**Purpose**: Mandatory validation steps required by the Project Constitution before any development begins.

- [X] T002c [Setup] **Implement Reference-Validator Script**: Create `code/utils/validate_citations.py` to fetch primary sources and verify citation metadata. **Action**: Implement script to query HuggingFace API and DOI resolver (e.g., `doi.org` or `crossref.org`) with rate-limit handling (retry with exponential backoff). **Output Schema**: `data/artifacts/citation_validation_report.json` must contain `{"status": "PASS"|"FAIL", "citations": [{"id": string, "status": "PASS"|"FAIL", "mismatch_reason": string|null, "source_metadata": {"title": string, "authors": list[str], "year": int}}]}`. **Dependency**: None. **Citation**: Per Constitution Principle II (Verified Accuracy).

- [X] T002 [Gate] **Reference-Validator Execution**: Implement and execute the `Reference-Validator Agent` as a blocking gate against `plan.md` and `spec.md`. **Action**:
 1. Fetch the primary source URLs/DOIs for all citations listed in `plan.md` and `spec.md` (e.g., the HuggingFace dataset `claw-ai-lab/arc-bench` or the associated paper DOI).
 2. Run `code/utils/validate_citations.py` with arguments `--input specs/001-llmxive-followup/plan.md --input specs/001-llmxive-followup/spec.md --output data/artifacts/citation_validation_report.json`.
 3. The validator MUST verify that each citation matches the metadata (title, authors, year) retrieved from the **primary source** (not just internal markdown).
 **Gate**: If any citation is `unreachable` or `mismatch` against the primary source, the pipeline MUST fail and block all subsequent tasks. **Output**: `data/artifacts/citation_validation_report.json` with status `PASS` or `FAIL`. **Dependency**: T002c. **Citation**: Per Constitution Principle II (Verified Accuracy). **Orchestration Enforcement**: The main orchestration script (T060) MUST explicitly check the exit code of T002 before invoking T002b. If T002 returns non-zero, T002b is skipped and the pipeline exits with an error.

- [X] T002b [Setup] **Record Validation State**: Record the results of T002 into the project state file. **Action**: Execute `code/utils/update_state.py` with arguments `--artifact data/artifacts/citation_validation_report.json --state-file state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` to update the hash and timestamp. **Constraint**: This task runs ONLY if T002 passes. **Dependency**: T002. **Citation**: Per Constitution Principle V (Versioning Discipline). **Orchestration Enforcement**: The main orchestration script (T060) MUST explicitly check the exit code of T002 before invoking T002b. If T002 returns non-zero, T002b is skipped and the pipeline exits with an error.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [Setup] **Initialize Project Structure**: Create the following directories and files:
 - `code/`, `code/data/`, `code/annotation/`, `code/engine/`, `code/analysis/`, `code/utils/`
 - `data/raw/`, `data/derived/`, `data/processed/`
 - `tests/unit/`, `tests/integration/`, `tests/contract/`
 - `docs/`, `ci/`, `specs/001-llmxive-followup/contracts/`
 - `requirements.txt`, `README.md`, `.gitignore`
 **Action**: Use `mkdir -p` and `touch` commands or a Python script to create the full directory tree and empty files. **Output**: Complete project directory structure. **Dependency**: None.

- [X] T003 [P] **Configure linting and formatting tools**: Create `.ruff.toml` and `pyproject.toml` configurations. **Action**:
 1. Create `.ruff.toml` with `select = ["E", "F", "W", "I"]`, `ignore = ["E501"]`, `target-version = "py311"`.
 2. Create `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']).
 3. Add `pre-commit` config in `.pre-commit-config.yaml` to run `ruff check` and `black` on push.
 **Output**: `.ruff.toml`, `pyproject.toml`, `.pre-commit-config.yaml`. **Dependency**: T001.

- [X] T004 [P] **Create `.gitignore` file**: Create `.gitignore` with specific exclusions. **Action**: Add patterns: `data/raw/*`, `!data/raw/.gitkeep`, `.env`, `__pycache__/`, `*.pyc`, `*.log`, `data/derived/*.parquet`, `data/derived/*.json`, `data/processed/*.csv`, `.ipynb_checkpoints/`, `.DS_Store`. **Output**: `.gitignore`. **Dependency**: T001.

- [X] T005 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy, lifelines)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006a [Setup] Create `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured").
- [X] T006d [Setup] **Create Distilled Rule Schema**: Re-implement `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` ensuring it matches FR-002 requirements. **Action**: Create schema with keys `rule_id` (string), `condition_pattern` (string), `pivot_action` (string), `confidence` (float). **Dependency**: T006a. **Output**: `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`.
- [X] T006c [Setup] Create `specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `method` (string), `time_to_pivot` (float), `success` (boolean), `failure_type` (string).
- [X] T007 [Setup] **Implement `code/utils/config.py` (Base Constraints)**: Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits for the Rule Engine: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `MAX_STREAMING_ROWS=500`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["LlamaB-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`. **Note**: Baseline resource configs are managed via T007b. **Action**: Write the file to `code/utils/config.py`. **Dependency**: T001.
- [X] T007b [Setup] **Implement Baseline Resource Overrides**: Create `code/utils/config_baseline.py` or extend `config.py` to define `BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`. **Action**: Implement logic to load these overrides when the `--profile=baseline` flag is passed. **Dependency**: T007. **Output**: `code/utils/config_baseline.py`.
- [X] T007c [Setup] **Implement Resource Watchdog**: Implement `code/utils/watchdog.py` with functions `check_memory_limit()` (monitor RAM, trigger shutdown if >7GB) and `enforce_cpu_quota()` (limit CPU usage). **Dependency**: T007. **Output**: `code/utils/watchdog.py`.
- [X] T007d [Setup] **Implement Adaptive Sampling Fallback**: Implement `code/utils/adaptive_sampler.py` to handle dataset truncation when RAM limits are exceeded. **Action**: Implement logic to reduce `MAX_STREAMING_ROWS` or sample from the dataset dynamically if `check_memory_limit()` is triggered. **Dependency**: T007, T007c. **Output**: `code/utils/adaptive_sampler.py`.
- [X] T008 [Setup] Implement `code/utils/logging.py` for structured logging of pipeline stages

---

## Phase 3: User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest ARC‑Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU‑tractable small model.

**Independent Test**: Run the pipeline on a small held‑out subset of cases and verify `rules_library.json` contains valid "If‑Condition‑Then‑Action" structures.

### Implementation for User Story 1

- [X] T009 [US1] **Implement `code/01_data_ingestion/download_arc_bench.py`**: Fetch the ARC‑Bench **topic subset** via HuggingFace `datasets`. **Action**: Implement logic to filter by `topic_id` (e.g., `dataset.filter(lambda x: x['topic'] in TOPIC_IDS)`) to ensure only the specified subset is ingested, not the full dataset. **Action**: Generate `data/raw/.checksums` file with SHA256 hashes of downloaded files. **Output**: `data/raw/arc_bench_topic_subset.parquet`, `data/raw/.checksums`. **Dependency**: T001, T007.

- [X] T050 [US1] Implement Real Data Source Verification. **Action**: Create `code/utils/verify_data_source.py` to read `data/raw/.checksums` and verify integrity against expected hashes. **Output**: `data/artifacts/data_source_report.json`. **Dependency**: T009.

- [X] T036 [US1] **Implement Streaming Data Loader**: Implement `code/data/loader.py` with streaming capability. **Action**: Use `datasets.load_dataset(..., streaming=True)` and `itertools.islice` to process data in chunks. **Dependency**: T009, T007c, T007d.

- [X] T005a [US1] **Implement Gold Standard Loader**: Create `code/annotation/gold_standard_loader.py` to load pre-verified ground truth data. **Action**: Implement loader that reads from `data/raw/gold_standard.json`. **Constraint**: If `data/raw/gold_standard.json` is missing, the script MUST raise `FileNotFoundError` with message "Real ground truth missing. Human-in-the-loop annotation required." **NO** synthetic generation is allowed for the gold standard. **Output**: `code/annotation/gold_standard_loader.py`. **Dependency**: T005e.

- [X] T005d [US1] **Provision Human Annotator Interface**: Create the workflow/interface for human-in-the-loop annotation. **Action**: Implement a Streamlit interface in `code/annotation/interface.py` that displays error logs, provides a dropdown with a limited number of enum values ("Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"), and submits to `data/derived/human_annotations.csv`. Define `docs/human_review_protocol.md` with exact review steps. **Dependency**: T036. **Output**: `code/annotation/interface.py`, `docs/human_review_protocol.md`.

- [X] T005e [US1] **Generate Gold Standard File**: Convert human annotations to `data/raw/gold_standard.json`. **Action**: Implement script `code/annotation/generate_gold_standard.py` that reads `data/derived/human_annotations.csv`, aggregates by `task_id` (majority vote), and writes to `data/raw/gold_standard.json` with schema `{task_id: {raw_error_log, ground_truth_resolution, annotated_structural_feature}}`. **Dependency**: T005d. **Output**: `data/raw/gold_standard.json`.

- [X] T009a [US1] **Implement Structural Feature Annotation Logic (FR-001)**: Implement the core logic in `code/annotation/annotator.py` to map raw error logs to the specific enum values. **Action**: Implement mapping using specific regex patterns: `r'SyntaxError.*'`, `r'IndentationError.*'` for Syntactic; `r'ambiguous|unclear|multiple meanings'` (case-insensitive) for Semantic; `r'loop|recursion|infinite'` for Logical Loop; `r'missing|context|undefined'` for Missing Context. **Default**: If no pattern matches, assign "Unstructured". **Dependency**: T036, T005a. **Output**: `code/annotation/annotator.py`.

- [X] T054 [US1] Implement Annotation Inter‑Rater Reliability Check. **Action**: Implement `code/annotation/kappa_calculator.py` to calculate Cohen's Kappa between human annotations and automated annotations. **Dependency**: T009a, T005d. **Output**: `data/derived/kappa_report.json`.

- [X] T005b [US1] **Implement Consensus Generation**: Create `code/annotation/consensus.py` to aggregate annotations from multiple raters (human and automated) into a single ground truth label. **Action**: Implement majority voting or weighted consensus logic. **Dependency**: T009a, T054. **Output**: `data/derived/consensus_annotations.csv`.

- [X] T005c [US1] **Resolve Disagreements**: Create `code/annotation/disagreement_resolver.py` to flag cases where consensus is not reached for manual review. **Dependency**: T005b. **Output**: `data/derived/disagreements.csv`.

- [X] T005f [US1] **Enforce Fail-Loudly on Data Fetch**: Ensure `code/01_data_ingestion/download_arc_bench.py` raises an exception if ARC-Bench fetch fails, with NO synthetic fallback. **Dependency**: T009. **Constraint**: Per Constitution Principle I & III.

- [X] T011a [US1] **Create Stratified Held-Out Split**: Split the labeled dataset into training ([deferred]) and held-out ([deferred]) sets **before** distillation. **Action**: Implement `code/annotation/create_split.py` to stratify by `annotated_structural_feature` and write `data/derived/train_split.json` and `data/derived/holdout_split.json`. **Dependency**: T005e, T005b. **Output**: `data/derived/train_split.json`, `data/derived/holdout_split.json`.

- [X] T011c [US1] **Implement CPU-Tractable Model Distillation Logic (Pilot)**: Implement the core logic in `code/annotation/distill_rules.py` to load a CPU-tractable model (e.g., Llama-3-8B-INT4) and generate rules. **Action**: Implement model loading with `load_in_8bit=True` or INT4 quantization, ensuring it runs on CPU. **Dependency**: T009a, T005b. **Output**: `code/annotation/distill_rules.py`.

- [X] T011b [US1] **Generate Distilled Rule Library Artifact (data/derived/rules_library.json)**: Generate the final rule library file. **Action**: Execute distillation using `train_split.json` and write output to `data/derived/rules_library.json`. **Dependency**: T011c, T009a, T005b, T011a. **Output**: `data/derived/rules_library.json`.

- [X] T011d [US1] **Implement Rule Coverage Validation & Gate (FR-002)**: Calculate the percentage of held-out patterns covered by the generated rules. **Action**: Implement script to calculate coverage. **Constraint**: If the validation split size or threshold is marked '[deferred]', skip the hard gate or use a configurable threshold. **Output**: `data/derived/coverage_report.json` with schema `{"coverage_percentage": float, "threshold": float, "status": "PASS"|"FAIL"|"DEFERRED"}`. **Dependency**: T011b, T011a.

- [X] T015b [US1] **Schema Validation**: Validate `rules_library.json` against `distilled_rule.schema.yaml`. **Action**: Implement `code/annotation/validate_rules_schema.py` to load `rules_library.json` and validate against `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`. Output `data/derived/schema_validation_report.json`. **Dependency**: T011b. **Output**: `data/derived/schema_validation_report.json`.

- [X] T016 [US1] **Log Annotation & Distillation Metrics**: Record metrics to `data/derived/metrics_log.json`. **Action**: Log `kappa_score` (from T054), `coverage_percentage` (from T011d), and rule counts. Output: `data/derived/metrics_log.json`. **Dependency**: T011d, T054.

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held‑out test set and compare performance against the full baseline agent.

**Independent Test**: Run on unseen tasks, log "Time‑to‑Pivot" and "Success", and verify metrics format.

### Implementation for User Story 2

- [X] T017 [US2] **Implement `code/03_execution/rule_engine.py`**: Implement the rule matching engine. **Action**:
 1. Input: `error_log` (string), `rules_library.json` (list of rules).
 2. Logic: Iterate rules, match `condition_pattern` (regex or JSON path) against `error_log`.
 3. Output: `{pivot_action: string, matched_rule_id: string}` or `{pivot_action: "UNMATCHED", matched_rule_id: null}`.
 4. Behavior for unmatched: Return "Manual Review" action.
 **Dependency**: T011b. **Output**: `code/03_execution/rule_engine.py`.

- [X] T041a [US2] **Implement GPU Policy CI Check**: Create `ci/check_gpu_policy.sh` to assert no GPU imports in `code/` and verify runner environment. **Output**: `data/artifacts/gpu_policy_check.json`. **Dependency**: T001.
- [X] T041b [US2] **Implement Code Import Guard**: Create `code/utils/gpu_guard.py` to check for `torch.cuda` imports at runtime in source files and raise errors if found. **Dependency**: T041a. **Output**: `code/utils/gpu_guard.py`.
- [X] T044 [US2] Power Analysis.
- [X] T019a [US2] **Generate experiment manifest**: Create `data/derived/experiment_manifest.json`. **Action**: Define JSON schema: `{"task_id": string, "method": string, "resource_profile": string, "expected_runtime": int}`. Populate for all test tasks. **Output**: `data/derived/experiment_manifest.json`. **Dependency**: T011a.

- [X] T058c [US2] **Configure CI Job Matrix for Dual Resource Profiles (FR-004)**: Implement the mechanism to isolate resource profiles. **Action**: Generate `ci/baseline_job.yml` (CPU, 4 cores, 16 GB RAM) and `ci/rule_engine_job.yml` (CPU, 2 cores, 7 GB RAM). Define artifact hand-off mechanism. **Action**: Ensure `ci/baseline_job.yml` uses `runs-on: ubuntu-latest` with `resources: { cpu: 4, memory: 16GB }`. **Dependency**: T007, T007b. **Output**: `ci/baseline_job.yml`, `ci/rule_engine_job.yml`.

- [X] T058b [US2] **Provision Baseline Runner**: Prepare the environment for the external baseline execution. **Dependency**: T058c.

- [X] T021 [US2] **Implement Baseline Execution (External Dispatch)**: Implement `code/03_execution/run_baseline.py`. **Action**: Implement dispatch mechanism using `subprocess.run` or GitHub Actions API (`gh run`) to invoke the baseline agent on a separate runner with 4 CPU/16GB RAM. Define input schema (task_id, error_log) and output schema (time_to_pivot, success). **Dependency**: T058c, T007b.

- [X] T021b [US2] **Implement Time-to-Pivot Censoring Logic**: Implement logic in `code/03_execution/run_baseline.py` to intercept and cap `time_to_pivot` values. **Action**: If a task exceeds `TIMEOUT_SECONDS`, set `time_to_pivot = TIMEOUT_SECONDS` and flag as censored. **Dependency**: T021.

- [X] T021c [US2] Instrument Baseline Resource Metrics (External).
- [X] T019 [US2] **Run Rule Engine Experiments**: Execute the rule engine on the test set. **Dependency**: T081.

- [X] T020 [US2] Record Metrics for Rule Engine.
- [X] T022 [US2] **Merge Rule‑Engine and Baseline Results**: Combine results into `data/derived/results.csv`. **Action**:
 1. Load `rule_engine_results.json` and `baseline_results.json`.
 2. Merge on `task_id` (inner join).
 3. Handle missing pairs: Log warning and exclude from paired tests.
 4. Output schema: `task_id, method_rule, time_rule, success_rule, method_baseline, time_baseline, success_baseline`.
 **Dependency**: T021, T019. **Output**: `data/derived/results.csv`.

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

### Implementation for User Story 3

- [X] T025 [US3] **Implement Mixed-Effects Logistic Regression**: Implement `code/04_analysis/logistic_regression.py`. **Action**:
 1. Use `statsmodels` library.
 2. Formula: `success ~ failure_type * method + (1|task_id)`.
 3. Output: Regression coefficients, p-values, and model summary to `data/derived/logistic_regression_results.json`.
 **Dependency**: T022. **Output**: `data/derived/logistic_regression_results.json`.

- [X] T025b [US3] **Implement Tobit Regression for Censored Time**: Implement `code/04_analysis/tobit_regression.py`. **Action**:
 1. Use `lifelines` library.
 2. Model: `time_to_pivot ~ failure_type * method` with censoring at `TIMEOUT_SECONDS`.
 3. Output: Coefficients, p-values to `data/derived/tobit_regression_results.json`.
 **Dependency**: T022. **Output**: `data/derived/tobit_regression_results.json`.

- [X] T027 [US3] **Implement Failure Categorization Logic: Coverage Gap vs Distillation Error (FR-007)**: Categorize every failed pivot from the rule engine into "Coverage Gap" or "Distillation Error". **Action**: Implement logic:
 1. Load `data/derived/results.csv` and `data/derived/rules_library.json`.
 2. For each failed pivot (success == False):
 a. Check if any rule in `rules_library.json` matches the `raw_error_log` (using `condition_pattern`).
 b. **IF** NO rule matches: Category = "Coverage Gap".
 c. **IF** a rule matches BUT the `pivot_action` executed differs from `ground_truth_resolution`: Category = "Distillation Error".
 d. **IF** a rule matches AND the action matches: Category = "Success" (should not be in failed set).
 3. Output `data/derived/error_taxonomy.json` with counts and sample cases for each category.
 **Dependency**: T022. **Output**: `data/derived/error_taxonomy.json`.

- [X] T026a [US3] **Model Fitting: Mixed-Effects Logistic Regression**: Fit the model with "Task ID" as random effect and "Failure Type * Method" as interaction term. **Action**: Use `statsmodels` library. Formula: `success ~ failure_type * method + (1|task_id)`. **Dependency**: T022, T027. **Output**: Regression coefficients, p-values.

- [X] T026b [US3] **Implement Pairwise Comparison Test (SC-001)**: Perform paired t-test or Wilcoxon signed-rank test for "Time-to-Pivot" differences. **Action**:
 1. Verify data integrity via T076.
 2. Use `scipy.stats.ttest_rel` or `scipy.stats.wilcoxon` on paired data from rule engine and baseline.
 3. Handle censored values consistently with T025b.
 4. Output `data/derived/pairwise_comparison.json`.
 **Dependency**: T022, T076.

- [X] T026c [US3] **Verify Interaction Term Significance (SC-003)**: Explicitly check if the interaction term (Failure Type * Method) has p-value < 0.05. **Dependency**: T026a. **Output**: Significance report.

- [X] T028 [US3] **Ground Truth Arbitration**: Implement arbitration logic for conflicting annotations. **Action**:
 1. Inputs: `human_annotations.csv`, `automated_annotations.csv`.
 2. Logic: Majority vote; if tie, flag for expert review.
 3. Output: `data/derived/arbitrated_ground_truth.json`.
 **Dependency**: T005b.

- [X] T029b [US3] **Stratified Success Rates**: Calculate success rates by failure type. **Action**:
 1. Stratify by `failure_type`.
 2. Calculate `success_rate = count(success=True) / total`.
 3. Output: `data/derived/stratified_success_rates.csv`.
 **Dependency**: T022.

---

## Phase 6: Revision & Analysis Resolution (Pending Review)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` phase regarding data flow, resource constraints, and rule distillation logic.

- [X] T072 [US1] **Refine Distillation Logic for Syntactic vs. Semantic**: Update `code/02_annotation_distillation/distill_rules.py` to explicitly differentiate rule generation strategies based on the `annotated_structural_feature`. **Logic**:
 1. For "Syntactic Error": Generate rules using strict regex patterns and exact string matching.
 2. For "Semantic Ambiguity": Generate rules that flag the case for probabilistic retrieval or "Unstructured" fallback, explicitly avoiding deterministic pattern matching for semantic issues.
 3. Add a validation step to ensure no semantic ambiguity cases are forced into deterministic regex rules.
 **Dependency**: T011b, T013. **Rationale**: Addresses the concern that the current distillation pipeline may incorrectly apply deterministic rules to ambiguous semantic failures, violating the core hypothesis of the study.

- [X] T073 [US2] **Enforce Resource Limits via Standard Runner**: Update `ci/baseline_job.yml` to use `runs-on: ubuntu-latest` with explicit resource constraints (4 CPU, 16 GB RAM) instead of undefined `self-hosted` labels. **Action**:
 1. Use `runs-on: ubuntu-latest`.
 2. Add `resources` block to limit CPU to 4 cores and memory to 16GB.
 3. Add pre-flight check in `code/03_execution/run_baseline.py` to verify runner's actual resource allocation.
 **Rationale**: Ensures the "Standard Resources" constraint for the baseline is strictly enforced and reproducible on standard GitHub Actions runners. **Dependency**: T058c.

- [X] T074 [US3] **Implement Robust Censored Data Handling in Tobit**: Refactor `code/04_analysis/tobit_regression.py` to explicitly handle cases where the `time_to_pivot` is exactly equal to `TIMEOUT_SECONDS` (censored) vs. `> TIMEOUT_SECONDS` (failed). Ensure the model correctly interprets these as censored observations and does not treat them as exact values. **Rationale**: Addresses the risk of survivorship bias and incorrect statistical inference if censored data is mishandled. **Dependency**: T025b.

- [X] T075 [US1] **Add Rule Coverage Validation for "Unstructured" Category**: Update `code/02_annotation_distillation/validate_rules.py` to explicitly check for the presence of an "Unstructured" or "Manual Review" fallback rule in the `rules_library.json`. **Logic**: If no such rule exists, the validation MUST fail, as all failure cases must have a prescribed action (even if it's "Manual Review"). **Rationale**: Ensures the rule engine never encounters an error log without a defined action, preventing silent failures during execution.

- [X] T076 [US3] **Verify Paired Data Integrity**: Implement `code/04_analysis/verify_paired_data.py`. **Action**:
 1. Load `data/derived/results.csv`.
 2. Check that every `task_id` has both `method_rule` and `method_baseline` entries.
 3. If any pair is incomplete, abort with error: "Data integrity failed: missing pairs for task_id [list]".
 4. Output: `data/derived/paired_data_validation.json` with status `PASS` or `FAIL`.
 **Rationale**: Prevents invalid statistical comparisons due to missing data points in the paired design. **Dependency**: T022.

- [X] T077 [US1] **Implement Explicit Logging for Distillation Thresholds**: Update `code/02_annotation_distillation/distill_rules.py` to log the specific confidence thresholds and coverage metrics used during rule generation, including any rules that were pruned due to low confidence. **Rationale**: Provides traceability for the rule distillation process and ensures reproducibility of the rule set.

- [X] T078 [US3] **Add Sensitivity Analysis for Interaction Term Significance**: Implement `code/04_analysis/sensitivity_interaction.py`. **Action**:
 1. Re-run mixed-effects model with A series of bootstrap iterations.
 2. Use fixed random seeds for reproducibility.
 3. Output: `data/derived/sensitivity_report.json` with stability metrics (std dev of coefficients).
 **Rationale**: Ensures the conclusion regarding "failure structure dictates method viability" is robust and not an artifact of random sampling.

- [X] T079 [US2] **Enforce Time-to-Pivot Censoring in Baseline Results**: Update `code/03_execution/run_baseline.py` to explicitly set `time_to_pivot = TIMEOUT_SECONDS` for any task that fails to pivot within the time limit, and ensure this value is correctly propagated to `baseline_results.json`. **Rationale**: Ensures the censored data handling in the statistical analysis is based on accurate and consistent data from the baseline execution. **Dependency**: T021b.

- [X] T080 [US1] **Validate Rule Library Schema Compliance**: Add a strict schema validation step in `code/02_annotation_distillation/distill_rules.py` to ensure that every generated rule conforms to the `distilled_rule.schema.yaml` (T006b) before writing to `rules_library.json`. **Rationale**: Prevents malformed rules from entering the rule library and causing errors during execution. **Dependency**: T006b, T013.

---

## Phase 7: Execution Orchestration & Final Validation

**Purpose**: Ensure the full pipeline executes correctly with all constraints, data flow, and revision fixes applied.

- [X] T081 [US1/US2/US3] **Implement End-to-End Orchestration with Revision Gates**: Create `code/main.py` to orchestrate the full pipeline (Ingestion → Annotation → Distillation → Execution → Analysis) with explicit checks for T072, T074, T076, and T079. **Action**: The script must verify that:
 1. Distillation logic correctly separates syntactic vs. semantic rules (T072).
 2. Censored data is handled correctly in both baseline and rule-engine results (T074, T079).
 3. Paired data integrity is validated before statistical analysis (T076).
 4. All resource constraints are enforced via watchdogs (T007c).
 **Output**: `data/derived/pipeline_execution_log.json` with status `PASS` or `FAIL` and detailed error logs if any gate fails. **Dependency**: T001, T007, T011b, T072, T074, T076, T079.

- [X] T082 [US1] **Run Pilot Distillation on Small Subset**: Execute the distillation pipeline on a small subset (N=10) of the ARC-Bench dataset to verify the rule generation logic (T072) and schema compliance (T080) before full-scale execution. **Action**: Run `code/annotation/distill_rules.py` with `--subset-size 10` and `--validate-schema`. **Output**: `data/derived/pilot_rules.json` and `data/derived/pilot_coverage_report.json`. **Dependency**: T009a, T011c, T011a. **Note**: T082 runs independently of T081 to validate logic early.

- [ ] T083 [US2] **Run Pilot Execution on Small Subset**: Execute the rule engine and baseline agent on the same small subset (N=10) used in T082 to verify data flow, metric logging, and censored data handling (T079). **Action**:
 1. Run `code/execution/run_rule_engine.py` with `--subset-size 10`.
 2. Dispatch baseline agent to a **separate CI job** via `gh run` or API call with 4 CPU/16GB RAM constraints.
 3. Collect and merge results.
 **Output**: `data/derived/pilot_results.csv` and `data/derived/pilot_baseline_results.json`. **Dependency**: T017, T021, T019a.

- [ ] T084 [US3] **Run Pilot Statistical Analysis**: Execute the statistical analysis pipeline on the pilot results (T083) to verify the mixed-effects model fitting (T026a), censored data handling (T074), and interaction term significance (T026c). **Action**: Run `code/analysis/statistical_model.py` with `--input data/derived/pilot_results.csv`. **Output**: `data/derived/pilot_regression_results.json` and `data/derived/pilot_interaction_significance_report.json`. **Dependency**: T025, T025b, T076.

- [ ] T085 [US1/US2/US3] **Full-Scale Execution with All Revision Fixes**: Execute the full pipeline (Ingestion → Annotation → Distillation → Execution → Analysis) on the full dataset (N=dynamic) with all revision fixes (T072, T074, T076, T079) applied. **Action**: Run `code/main.py` with `--full-scale`. **Output**: `data/derived/full_rules_library.json`, `data/derived/full_results.csv`, `data/derived/full_regression_results.json`. **Dependency**: T081, T082, T083, T084. <!-- FAILED: unspecified -->

- [ ] T086 [US3] **Generate Final Research Report**: Compile the final results from T085 into a research report that addresses the core hypothesis (failure structure dictates method viability) and includes the interaction term significance (T026c), error taxonomy (T027), and sensitivity analysis (T078). **Action**: <!-- ATOMIZE: requested -->
 1. Use `docs/research_report_template.md`.
 2. Extract data from `data/derived/full_regression_results.json`, `data/derived/error_taxonomy.json`.
 3. Include sections: Methodology, Results (Interaction Significance, Error Taxonomy), Discussion, Limitations.
 **Output**: `docs/research_report.md`. **Dependency**: T085, T026c, T027, T078.

- [X] T087 [US1/US2/US3] **Final Validation & Constitution Check**: Perform a final validation of the entire project against the Constitution Principles (I-VII) to ensure reproducibility, verified accuracy, data hygiene, and resource constraints were met. **Action**: Run `code/utils/validate_constitution.py` with `--input docs/research_report.md --input data/derived/full_results.csv`. **Output**: `data/artifacts/final_constitution_check.json` with status `PASS` or `FAIL`. **Dependency**: T086, T002. <!-- FAILED: unspecified -->

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048 [P] Update State.
- [X] T060 [Setup] Implement Final Orchestration Script.