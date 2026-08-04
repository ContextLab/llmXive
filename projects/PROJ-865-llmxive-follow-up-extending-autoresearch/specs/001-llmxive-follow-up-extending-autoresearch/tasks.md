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

- [X] T003 [P] Configure linting and formatting tools
- [X] T004 [P] Create `.gitignore` file with appropriate exclusions.
- [X] T005 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy, lifelines)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006a [Setup] Create `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured").
- [X] T006d [Setup] **Create Distilled Rule Schema**: Re-implement `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` ensuring it matches FR-002 requirements. **Action**: Create schema with keys `rule_id` (string), `condition_pattern` (string), `pivot_action` (string), `confidence` (float). **Dependency**: T006a. **Output**: `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`.
- [X] T006c [Setup] Create `specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `method` (string), `time_to_pivot` (float), `success` (boolean), `failure_type` (string).
- [X] T007 [Setup] **Implement `code/utils/config.py`**: Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `MAX_STREAMING_ROWS=500`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["Llama-8B-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`. **Note**: Baseline resource configs removed from this file to enforce Rule Engine constraints only; Baseline resources are managed via CI matrix (T058c). **Action**: Write the file to `code/utils/config.py`. **Dependency**: T001.
- [X] T007c [Setup] **Implement Resource Watchdog**: Implement `code/utils/watchdog.py` with functions `check_memory_limit()` (monitor RAM, trigger shutdown if >7GB) and `enforce_cpu_quota()` (limit CPU usage). **Dependency**: T007. **Output**: `code/utils/watchdog.py`.
- [X] T007d [Setup] **Implement Adaptive Sampling Fallback**: Implement `code/utils/adaptive_sampler.py` to handle dataset truncation when RAM limits are exceeded. **Action**: Implement logic to reduce `MAX_STREAMING_ROWS` or sample from the dataset dynamically if `check_memory_limit()` is triggered. **Dependency**: T007, T007c. **Output**: `code/utils/adaptive_sampler.py`.
- [X] T008 [Setup] Implement `code/utils/logging.py` for structured logging of pipeline stages

---

## Phase 3: User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest ARC‑Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU‑tractable small model.

**Independent Test**: Run the pipeline on a small held‑out subset of cases and verify `rules_library.json` contains valid "If‑Condition‑Then‑Action" structures.

### Implementation for User Story 1

- [X] T009 [US1] **Implement `code/01_data_ingestion/download_arc_bench.py`**: Fetch the ARC‑Bench **topic subset** via HuggingFace `datasets`. **Action**: Implement logic to filter by `topic_id` (e.g., `dataset.filter(lambda x: x['topic'] in TOPIC_IDS)`) to ensure only the specified subset is ingested, not the full dataset. **Output**: `data/raw/arc_bench_topic_subset.parquet`. **Dependency**: T001, T007.
- [X] T050 [US1] Implement Real Data Source Verification.
- [X] T036 [US1] **Implement Streaming Data Loader**: Implement `code/data/loader.py` with streaming capability. **Action**: Use `datasets.load_dataset(..., streaming=True)` and `itertools.islice` to process data in chunks. **Dependency**: T009.
- [X] T005a [US1] **Implement Gold Standard Loader**: Create `code/annotation/gold_standard_loader.py` to load pre-verified ground truth data. **Action**: Implement loader that reads from `data/raw/gold_standard.json`. **Constraint**: If `data/raw/gold_standard.json` is missing, the script MUST raise `FileNotFoundError` with message "Real ground truth missing. Human-in-the-loop annotation required." **NO** synthetic generation is allowed for the gold standard. **Output**: `code/annotation/gold_standard_loader.py`. **Dependency**: T036.
- [X] T005d [US1] **Provision Human Annotator Interface**: Create the workflow/interface for human-in-the-loop annotation. **Action**: Implement a Streamlit interface in `code/annotation/interface.py` that displays error logs, provides a dropdown with exactly 5 enum values ("Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"), and submits to `data/derived/human_annotations.csv`. Define `docs/human_review_protocol.md` with exact review steps. **Dependency**: T036, T005a. **Output**: `code/annotation/interface.py`, `docs/human_review_protocol.md`.
- [X] T009a [US1] **Implement Structural Feature Annotation Logic (FR-001)**: Implement the core logic in `code/annotation/annotator.py` to map raw error logs to the specific enum values. **Action**: Implement mapping using specific regex patterns: `r'SyntaxError.*'`, `r'IndentationError.*'` for Syntactic; `r'ambiguous|unclear|multiple meanings'` (case-insensitive) for Semantic. For other cases, use heuristic rules based on keywords. **Dependency**: T036, T005a, T005d. **Output**: `code/annotation/annotator.py`.
- [X] T054 [US1] Implement Annotation Inter‑Rater Reliability Check. **Action**: Implement `code/annotation/kappa_calculator.py` to calculate Cohen's Kappa between human annotations and automated annotations. **Dependency**: T009a, T005d. **Output**: `data/derived/kappa_report.json`.
- [X] T005b [US1] **Implement Consensus Generation**: Create `code/annotation/consensus.py` to aggregate annotations from multiple raters (human and automated) into a single ground truth label. **Action**: Implement majority voting or weighted consensus logic. **Dependency**: T009a, T054. **Output**: `data/derived/consensus_annotations.csv`.
- [X] T005c [US1] **Resolve Disagreements**: Create `code/annotation/disagreement_resolver.py` to flag cases where consensus is not reached for manual review. **Dependency**: T005b. **Output**: `data/derived/disagreements.csv`.
- [X] T005e [US1] **Enforce Fail-Loudly on Data Fetch**: Ensure `code/01_data_ingestion/download_arc_bench.py` raises an exception if ARC-Bench fetch fails, with NO synthetic fallback. **Dependency**: T009. **Constraint**: Per Constitution Principle I & III.
- [X] T011b [US1] **Generate Distilled Rule Library Artifact (data/derived/rules_library.json)**: Generate the final rule library file. **Action**: Execute distillation and write output to `data/derived/rules_library.json`. **Dependency**: T009a, T005b. **Output**: `data/derived/rules_library.json`.
- [X] T011d [US1] **Implement Rule Coverage Validation & Gate (FR-002)**: Calculate the percentage of held-out patterns covered by the generated rules and enforce the ≥90% threshold. **Action**: Implement script to create a **stratified** held-out split (80/20) from the labeled dataset. Calculate coverage as (unique error log hashes covered by rules / total unique error log hashes in held-out set). If coverage < 90%, fail the pipeline. **Output**: `data/derived/coverage_report.json` with schema `{"coverage_percentage": float, "threshold": float, "status": "PASS"|"FAIL"}`. **Dependency**: T011b.
- [X] T015b [US1] Schema Validation.
- [X] T016 [US1] Logging Annotation & Distillation Metrics.

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held‑out test set and compare performance against the full baseline agent.

**Independent Test**: Run on unseen tasks, log "Time‑to‑Pivot" and "Success", and verify metrics format.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/03_execution/rule_engine.py`.
- [X] T041 [US2] Verify GPU Policy Compliance.
- [X] T044 [US2] Power Analysis.
- [X] T019a [US2] Generate experiment manifest.
- [X] T058c [US2] **Configure CI Job Matrix for Dual Resource Profiles (FR-004)**: Implement the mechanism to isolate resource profiles. **Action**: Generate `ci/baseline_job.yml` (4 CPU, 16 GB RAM) and `ci/rule_engine_job.yml` (2 CPU, 7 GB RAM). Define artifact hand-off mechanism. **Dependency**: T007. **Output**: `ci/baseline_job.yml`, `ci/rule_engine_job.yml`.
- [X] T058b [US2] **Provision Baseline Runner**: Prepare the environment for the external baseline execution. **Dependency**: T058c.
- [X] T021 [US2] **Implement Baseline Execution (External Dispatch)**: Implement `code/03_execution/run_baseline.py`. **Action**: Implement dispatch mechanism using `subprocess.run` with specific arguments to invoke the baseline agent. Define input schema (task_id, error_log) and output schema (time_to_pivot, success). **Dependency**: T058c.
- [X] T021b [US2] **Implement Time-to-Pivot Censoring Logic**: Implement logic in `code/03_execution/run_baseline.py` to intercept and cap `time_to_pivot` values. **Action**: If a task exceeds `TIMEOUT_SECONDS`, set `time_to_pivot = TIMEOUT_SECONDS` and flag as censored. **Dependency**: T021.
- [X] T021c [US2] Instrument Baseline Resource Metrics (External).
- [X] T019 [US2] **Run Rule Engine Experiments**: Execute the rule engine on the test set. **Dependency**: T081.
- [X] T020 [US2] Record Metrics for Rule Engine.
- [X] T022 [US2] Merge Rule‑Engine and Baseline Results.

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py`.
- [X] T027 [US3] **Implement Failure Categorization Logic: Coverage Gap vs Distillation Error (FR-007)**: Categorize every failed pivot from the rule engine into "Coverage Gap" or "Distillation Error". **Action**: Implement logic:
 1. Load `data/derived/results.csv` and `data/derived/rules_library.json`.
 2. For each failed pivot (success == False):
     a. Check if any rule in `rules_library.json` matches the `raw_error_log` (using `condition_pattern`).
     b. **IF** NO rule matches: Category = "Coverage Gap".
     c. **IF** a rule matches BUT the `pivot_action` executed differs from `ground_truth_resolution`: Category = "Distillation Error".
     d. **IF** a rule matches AND the action matches: Category = "Success" (should not be in failed set).
 3. Output `data/derived/error_taxonomy.json` with counts and sample cases for each category.
 **Dependency**: T022. **Output**: `data/derived/error_taxonomy.json`.
- [X] T026a [US3] **Model Fitting: Mixed-Effects Logistic Regression**: Fit the model with "Task ID" as random effect and "Failure Type * Method" as interaction term. **Action**: Use `lifelines` library for Tobit regression (as `statsmodels` lacks native Tobit). Formula: `success ~ failure_type * method + (1|task_id)`. Handle censored data (Steps-to-Pivot) using `lifelines.TobitAFTFitter`. **Dependency**: T022, T027. **Output**: Regression coefficients, p-values.
- [X] T026b [US3] **Implement Pairwise Comparison Test (SC-001)**: Perform paired t-test or Wilcoxon signed-rank test for "Time-to-Pivot" differences. **Action**: Use `scipy.stats.ttest_rel` or `scipy.stats.wilcoxon` on paired data from rule engine and baseline. Output `data/derived/pairwise_comparison.json`. **Dependency**: T022.
- [X] T026c [US3] **Verify Interaction Term Significance (SC-003)**: Explicitly check if the interaction term (Failure Type * Method) has p-value < 0.05. **Dependency**: T026a. **Output**: Significance report.
- [X] T028 [US3] Ground Truth Arbitration.
- [X] T029b [US3] Stratified Success Rates.

---

## Phase 6: Revision & Analysis Resolution (Pending Review)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` phase regarding data flow, resource constraints, and rule distillation logic.

- [X] T072 [US1] **Refine Distillation Logic for Syntactic vs. Semantic**: Update `code/02_annotation_distillation/distill_rules.py` to explicitly differentiate rule generation strategies based on the `annotated_structural_feature`. **Logic**:
 1. For "Syntactic Error": Generate rules using strict regex patterns and exact string matching.
 2. For "Semantic Ambiguity": Generate rules that flag the case for probabilistic retrieval or "Unstructured" fallback, explicitly avoiding deterministic pattern matching for semantic issues.
 3. Add a validation step to ensure no semantic ambiguity cases are forced into deterministic regex rules.
 **Dependency**: T011b, T013. **Rationale**: Addresses the concern that the current distillation pipeline may incorrectly apply deterministic rules to ambiguous semantic failures, violating the core hypothesis of the study.

- [X] T073 [US2] **Enforce Resource Constraints in Baseline Execution**: Update `ci/baseline_job.yml` (generated by T058c) to explicitly set `runs-on: [self-hosted, resource-limited]` or equivalent CI configuration that enforces the 4 CPU / 16 GB RAM limit, and add a pre-flight check in `code/03_execution/run_baseline.py` to verify the runner's actual resource allocation before dispatch. **Rationale**: Ensures the "Standard Resources" constraint for the baseline is strictly enforced and not just a theoretical target, preventing invalid comparisons. **Dependency**: T058c.

- [X] T074 [US3] **Implement Robust Censored Data Handling in Tobit**: Refactor `code/04_analysis/time_diff_tobit.py` to explicitly handle cases where the `time_to_pivot` is exactly equal to `TIMEOUT_SECONDS` (censored) vs. `> TIMEOUT_SECONDS` (failed). Ensure the model correctly interprets these as censored observations and does not treat them as exact values. **Rationale**: Addresses the risk of survivorship bias and incorrect statistical inference if censored data is mishandled. **Dependency**: T026a.

- [X] T075 [US1] **Add Rule Coverage Validation for "Unstructured" Category**: Update `code/02_annotation_distillation/validate_rules.py` to explicitly check for the presence of an "Unstructured" or "Manual Review" fallback rule in the `rules_library.json`. **Logic**: If no such rule exists, the validation MUST fail, as all failure cases must have a prescribed action (even if it's "Manual Review"). **Rationale**: Ensures the rule engine never encounters an error log without a defined action, preventing silent failures during execution.

- [X] T076 [US2] **Verify Paired Data Integrity for Statistical Tests**: Add a pre-check in `code/04_analysis/time_diff_tobit.py` and `code/04_analysis/statistical_model.py` to ensure that the `task_id` pairs in `results.csv` are complete and that no task is missing a baseline or rule-engine result. **Logic**: If any pair is incomplete, the analysis MUST abort with a clear error message. **Rationale**: Prevents invalid statistical comparisons due to missing data points in the paired design.

- [X] T077 [US1] **Implement Explicit Logging for Distillation Thresholds**: Update `code/02_annotation_distillation/distill_rules.py` to log the specific confidence thresholds and coverage metrics used during rule generation, including any rules that were pruned due to low confidence. **Rationale**: Provides traceability for the rule distillation process and ensures reproducibility of the rule set.

- [X] T078 [US3] **Add Sensitivity Analysis for Interaction Term Significance**: Implement `code/04_analysis/sensitivity_interaction.py` to re-run the mixed-effects model with varying random seeds and bootstrap iterations to verify the stability of the interaction term's significance. **Rationale**: Ensures the conclusion regarding "failure structure dictates method viability" is robust and not an artifact of random sampling.

- [X] T079 [US2] **Enforce Time-to-Pivot Censoring in Baseline Results**: Update `code/03_execution/run_baseline.py` to explicitly set `time_to_pivot = TIMEOUT_SECONDS` for any task that fails to pivot within the time limit, and ensure this value is correctly propagated to `baseline_results.json`. **Rationale**: Ensures the censored data handling in the statistical analysis is based on accurate and consistent data from the baseline execution. **Dependency**: T021b.

- [X] T080 [US1] **Validate Rule Library Schema Compliance**: Add a strict schema validation step in `code/02_annotation_distillation/distill_rules.py` to ensure that every generated rule conforms to the `distilled_rule.schema.yaml` (T006b) before writing to `rules_library.json`. **Rationale**: Prevents malformed rules from entering the rule library and causing errors during execution. **Dependency**: T006b, T013.

---

## Phase 7: Execution Orchestration & Final Validation

**Purpose**: Ensure the full pipeline executes correctly with all constraints, data flow, and revision fixes applied.

- [ ] T081 [US1/US2/US3] **Implement End-to-End Orchestration with Revision Gates**: Create `code/main.py` to orchestrate the full pipeline (Ingestion → Annotation → Distillation → Execution → Analysis) with explicit checks for T072, T074, T076, and T079. **Action**: The script must verify that:
 1. Distillation logic correctly separates syntactic vs. semantic rules (T072).
 2. Censored data is handled correctly in both baseline and rule-engine results (T074, T079).
 3. Paired data integrity is validated before statistical analysis (T076).
 4. All resource constraints are enforced via watchdogs (T007c).
 **Output**: `data/derived/pipeline_execution_log.json` with status `PASS` or `FAIL` and detailed error logs if any gate fails. **Dependency**: T001, T007, T011b, T072, T074, T076, T079.

- [ ] T082 [US1] **Run Pilot Distillation on Small Subset**: Execute the distillation pipeline on a small subset (N=10) of the ARC-Bench dataset to verify the rule generation logic (T072) and schema compliance (T080) before full-scale execution. **Action**: Run `code/annotation/distill_rules.py` with `--subset-size 10` and `--validate-schema`. **Output**: `data/derived/pilot_rules.json` and `data/derived/pilot_coverage_report.json`. **Dependency**: T081, T009a, T011b. **Note**: T081 must be implemented before T082 can run.

- [ ] T083 [US2] **Run Pilot Execution on Small Subset**: Execute the rule engine and baseline agent on the same small subset (N=10) used in T082 to verify data flow, metric logging, and censored data handling (T079). **Action**: Run `code/execution/run_rule_engine.py` and `code/execution/run_baseline.py` with `--subset-size 10`. **Output**: `data/derived/pilot_results.csv` and `data/derived/pilot_baseline_results.json`. **Dependency**: T081, T017, T021.

- [ ] T084 [US3] **Run Pilot Statistical Analysis**: Execute the statistical analysis pipeline on the pilot results (T083) to verify the mixed-effects model fitting (T026a), censored data handling (T074), and interaction term significance (T026c). **Action**: Run `code/analysis/statistical_model.py` with `--input data/derived/pilot_results.csv`. **Output**: `data/derived/pilot_regression_results.json` and `data/derived/pilot_interaction_significance_report.json`. **Dependency**: T081, T025, T026a.

- [ ] T085 [US1/US2/US3] **Full-Scale Execution with All Revision Fixes**: Execute the full pipeline (Ingestion → Annotation → Distillation → Execution → Analysis) on the full dataset (N=500) with all revision fixes (T072, T074, T076, T079) applied. **Action**: Run `code/main.py` with `--full-scale`. **Output**: `data/derived/full_rules_library.json`, `data/derived/full_results.csv`, `data/derived/full_regression_results.json`. **Dependency**: T081, T082, T083, T084.

- [ ] T086 [US3] **Generate Final Research Report**: Compile the final results from T085 into a research report that addresses the core hypothesis (failure structure dictates method viability) and includes the interaction term significance (T026c), error taxonomy (T027), and sensitivity analysis (T078). **Action**: Generate `docs/research_report.md` with sections for methodology, results, discussion, and limitations. **Output**: `docs/research_report.md`. **Dependency**: T085, T026c, T027, T078.

- [ ] T087 [US1/US2/US3] **Final Validation & Constitution Check**: Perform a final validation of the entire project against the Constitution Principles (I-VII) to ensure reproducibility, verified accuracy, data hygiene, and resource constraints were met. **Action**: Run `code/utils/validate_constitution.py` with `--input docs/research_report.md --input data/derived/full_results.csv`. **Output**: `data/artifacts/final_constitution_check.json` with status `PASS` or `FAIL`. **Dependency**: T086, T002.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048 [P] Update State.
- [X] T060 [Setup] Implement Final Orchestration Script.