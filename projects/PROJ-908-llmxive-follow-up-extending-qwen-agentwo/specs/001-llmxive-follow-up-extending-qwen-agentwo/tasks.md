# Tasks: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` in `projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo/`: Execute `mkdir -p code/oracle code/rules code/analysis code/inference code/utils data/raw data/processed tests/unit tests/integration tests/contract specs/contracts`.
- [X] T002 Setup Python 3.11 virtualenv and install requirements.txt: Create `venv/` and run `pip install -r requirements.txt` to ensure all dependencies are available.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` with `[lint]` rules and `pyproject.toml` with `[tool.black]` configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/loaders.py` with strict real-data fetching (no synthetic fallbacks) using `datasets.load_dataset` or verified HF URLs
- [X] T005 Implement `code/utils/checksums.py` for data hygiene and source verification
- [X] T006 [P] Setup `data/raw/` and `data/processed/` directory structure: Create `data/.gitignore` ignoring `*.parquet`, `*.jsonl`, `__pycache__`, and `*.pth`.
- [X] T007 Create base schema definitions in `specs/001-llmxive-followup/contracts/`: Create `oracle.schema.yaml` (fields: `interaction_type: string`, `state_transition: object`), `rules.schema.yaml` (fields: `rule_id: string`, `predicate: string`, `confidence: float`), and `divergence.schema.yaml` (fields: `task_id: string`, `classification: string`, `confidence: float`) with definitions from plan.md.
- [X] T008 Configure `pytest` with fixed random seed (42) and integration test scaffolding: Create `pytest.ini` with `addopts = --random-seed=42` and `tests/integration/conftest.py`.
- [X] T009 Implement `code/__init__.py` and `code/main.py` entry point structure

---

## Phase 2.5: Data Setup (Shared Prerequisite)

**Purpose**: Fetch and verify the canonical Qwen-AgentWorld benchmark and traces required by all user stories.

- [X] T016a [P] [Data] Fetch Canonical Benchmark: Download `qwen-agentworld/benchmark` from HuggingFace using `datasets.load_dataset` (streaming=True) to `data/raw/benchmark.json`. Verify checksum against the canonical source. If fetch fails, raise `DataFetchError` (Constitution Principle III).
- [ ] T016b [Data] Verify Benchmark Schema: Validate `data/raw/benchmark.json` against `specs/001-llmxive-followup/contracts/oracle.schema.yaml` using `jsonschema`. Output `data/processed/benchmark_validation.json` with pass/fail status. **Requires**: T016a completion.
- [ ] T016c [Data] Checksum Verification: Generate and store checksum for `data/raw/benchmark.json` in `state/projects/PROJ-908-llmxive-follow-up-extending-qwen-agentwo.yaml` under the `artifact_hashes` map. **Requires**: T016a completion.
- [X] T041 [Data] Implement explicit URL verification and checksum validation for `AgentWorldBench` in `code/utils/loaders.py`: Replace generic `load_dataset` calls with explicit `hf_hub_download` or verified raw URL fetch for the environment source code and benchmark tasks, ensuring the script fails with a clear error if the specific commit hash or checksum does not match the expected value (Constitution Principle III - Data Hygiene). **Requires**: T016a completion.

**Checkpoint**: Foundation and Data Setup ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Oracle Construction (Priority: P1) 🎯 MVP

**Goal**: Parse Qwen-AgentWorld source code to generate a deterministic state-transition oracle for independent ground truth verification.

**Independent Test**: Verify generated oracle matches original environment simulator trajectories for N=1,000 random inputs (seed=42) with ≥99.9% accuracy. [UNRESOLVED-CLAIM: c_9a90d514 — status=not_enough_info]

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Contract test for `oracle/parser.py` in `tests/unit/test_oracle_parser.py` (verifies schema alignment)
- [X] T011 [US1] Integration test for Oracle vs. Environment Simulator in `tests/integration/test_oracle_validation.py` (N=1,000 random seeds, seed=42)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/oracle/parser.py` to parse Qwen-AgentWorld source and extract interaction logic (spatial, temporal, causal)
- [X] T013 [US1] Implement `code/oracle/simulator.py` to execute deterministic state transitions based on parsed logic
- [ ] T014 [US1] Generate `data/processed/oracle_graph.json` (Deterministic State-Transition Oracle) and invoke checksum verification: Run `python code/main.py --stage=oracle --output=data/processed/oracle_graph.json`. **CRITICAL**: Must also execute a semantic verification step comparing the generated oracle against the simulator on N=1,000 samples (seed=42) and assert ≥99.9% accuracy. Verify exit code 0, file size > 0, and checksum matches expected value.
- [X] T015 [US1] Implement orchestration step in `code/main.py` or `oracle/parser.py` to invoke `code/utils/checksums.py` during Oracle generation and fail on mismatch (Code Drift check)
- [X] T016 [US1] Add logging for Oracle generation and validation steps: Add `logging.basicConfig` to `code/oracle/parser.py` and `code/oracle/simulator.py` with level=INFO and format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'.

**Checkpoint**: Ground Truth Oracle is fully functional, validated against simulator, and ready for rule extraction.

---

## Phase 3.5: Trace Generation (Prerequisite for US2 & US3)

**Goal**: Fetch real LLM CoT traces. **FAIL LOUDLY** if real traces are missing.

- [ ] T017 [US2] Fetch Real CoT Traces: Attempt to fetch `qwen-agentworld/cot_traces` from HuggingFace to `data/raw/cot_traces.json`. **CRITICAL**: If fetch fails (network or missing), the script MUST raise `DataFetchError` and STOP. **DO NOT** generate synthetic traces or fallback to a local model. Verify output: file size > 0, valid JSON schema, and log metadata (task_id, interaction_type). Requires T016a completion.
- [X] T019a [US2] Generate Synthetic Control Traces (Unit Test Only): Create `code/rules/synthetic_generator.py` to generate `data/raw/synthetic_control_traces.json` containing N=500 traces with pre-determined logical patterns (simple conjunctions of state predicates). **Scope**: This data is for unit testing and validation only; it must NOT be used as input for the primary research analysis in US2/US3.

**Checkpoint**: Real CoT traces are available for rule extraction.

---

## Phase 4: User Story 2 - Rule Extraction from Reasoning Traces (Priority: P2)

**Goal**: Apply ILP/Decision Tree to LLM CoT traces to extract explicit logical rules and validate against the Oracle.

**Independent Test**: Feed synthetic traces with known patterns; Verify extracted rules reproduce patterns with ≥95% precision. [UNRESOLVED-CLAIM: c_0d9d948c — status=not_enough_info]

### Implementation for User Story 2

- [X] T020 [US2] Load LLM CoT traces: Load `data/raw/cot_traces.json` (produced by T017). If missing, FAIL LOUDLY (do not generate synthetic data). Requires T017 completion.
- [X] T021 [US2] Implement `code/rules/extractor.py` using FOL/ILP (library: `ilpy`, params: `max_depth=3`, `min_support=5`) to derive rules from CoT traces
- [X] T042 [US2] Implement streaming logic for large CoT trace datasets in `code/rules/extractor.py`: Refactor the trace loading logic to use `datasets.load_dataset(..., streaming=True)` and iterate via `itertools.islice` with `chunk_size=1000`. Explicitly log `INFO: Streaming chunk {i}/{total}, sample_size={n}`. If streaming is truncated or interrupted, the task MUST raise a `DataTruncationError` and NOT proceed, ensuring 'fail loud' behavior. (Constitution Principle: Large real datasets).
- [ ] T023 [US2] Implement and Execute Rule Extraction: Implement the core logic in `code/rules/extractor.py` to parse CoT traces and induce First-Order Logic rules. **Ambiguity Criteria**: Flag traces with conflicting predicates or missing state transitions as "Extraction Uncertainty". **Validation**: Execute the script to produce `data/processed/extracted_rules.json` AND run the validation against `data/raw/synthetic_control_traces.json` (T019a) to assert ≥95% precision. Requires T021 and T042 completion.
- [X] T022 [US2] Implement `code/rules/validator.py` to cross-check extracted rules against the Ground Truth Oracle (FR-002)
- [ ] T027 [US2] Implement `code/rules/metrics.py` to calculate **Rule Precision** by comparing `data/processed/extracted_rules.json` against `data/processed/oracle_graph.json` (Ground Truth) and output `data/processed/rule_precision.json` (scalar metric) to satisfy SC-005: Implement `calculate_precision(extracted_rules, oracle_graph)` where Precision = (Count of extracted rules matching Oracle) / (Total extracted rules). **Output Schema**: `{"precision": float, "total_rules": int, "matching_rules": int}`. Requires T023 completion.
- [ ] T026 [US2] Implement `code/analysis/metrics.py` to calculate **CoT Quality Score**: Calculate a logical consistency metric for the REAL traces in `data/raw/cot_traces.json` (produced by T017) and output `data/processed/cot_quality_scores.json` for SC-005 correlation analysis. Requires T017 completion.
- [X] T024 [US2] Implement logic to flag "Extraction Uncertainty" for ambiguous/contradictory traces: Ensure that when calculating Hallucination and Rule Gap rates in downstream tasks, the denominators strictly exclude counts marked as "Extraction Uncertainty" or "Coverage Gap (Cold Start)". Output a separate `excluded_metrics` field in the intermediate data structure (not the final report).
- [X] T025 [US2] Add logging for rule extraction confidence: In `code/rules/extractor.py`, add `logger.info(f"Rule confidence: {confidence}")` for each extracted rule.
- [ ] T019b [US2] Validate Extraction on Synthetic Data: Run the extraction algorithm (T023) on `data/raw/synthetic_control_traces.json` and assert that the extracted rules reproduce the known patterns with ≥95% precision (US-02 Independent Test). Output `data/processed/synthetic_validation_report.json` containing the precision metric and pass/fail status. **Note**: This task is now logically part of T023's completion criteria.

**Checkpoint**: Hypothesized Rule Set is extracted, validated against Oracle, uncertainty is properly flagged and reported separately, CoT quality metrics are generated, and Rule Precision is calculated.

---

## Phase 5: User Story 3 - Divergence Quantification and Classification (Priority: P3)

**Goal**: Compare LLM, Extracted Rules, and Oracle on long-horizon tasks; classify errors into "Hallucination" and "Rule Gap"; perform statistical significance testing.

**Independent Test**: Run on small manually verified dataset; Confirm error classification (Hallucination vs Rule Gap) matches human annotation (Cohen's Kappa ≥ 0.8).

### Tests for User Story 3 ⚠️

- [ ] T028 [P] [US3] Contract test for `analysis/diverge.py` in `tests/unit/test_divergence_classifier.py`
- [X] T029 [US3] Integration test for Statistical Significance (Permutation Test) in `tests/integration/test_stats_significance.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis/diverge.py` to execute standardized tasks and classify transitions: Implement `classify_transition(llm_state, oracle_state, rules)` returning one of: Match, Hallucination, Rule Gap, Uncertainty, Cold Start. **Priority Logic**: 1. Match, 2. Hallucination (if Oracle valid), 3. Rule Gap (if Rule valid), 4. Uncertainty, 5. Cold Start. **CRITICAL**: Implement logic to strictly exclude Uncertainty and Cold Start from the primary Hallucination/Rule Gap counts. Requires T014 (Oracle) and T023 (Rules) completion.
- [ ] T030a [US3] Calculate Hallucination/Rule Gap Rates: Aggregate counts from T030's output, calculate the rates (excluding Uncertainty/Cold Start) as required by SC-001 and SC-002, and output `data/processed/rate_metrics.json`. **Output Schema**: `{"hallucination_rate": float, "rule_gap_rate": float, "total_transitions": int, "excluded_count": int}`. Requires T030 completion.
- [ ] T043 [US3] Add a "Cold Start" verification task to `code/analysis/diverge.py`: Explicitly compare the set of `interaction_type` values found in `data/processed/oracle_graph.json` nodes against those found in `data/raw/cot_traces.json` metadata. Identify types present in Oracle but absent in Traces and categorize them as "Coverage Gap (Cold Start)" in the intermediate classification results. Requires T014 completion.
- [ ] T032 [US3] Implement logic in `code/analysis/stats.py` to identify the specific step count or state complexity boundary where measured adherence drops below the adherence threshold (read from `config.yaml`, default high confidence) (per FR-006/SC-004): Implement `find_adherence_boundary(trajectories, threshold=0.95)` using binary search and output a structured `boundary_conditions` object to `data/processed/boundary_conditions.json`. **SC-004 Compliance**: This metric MUST be recorded in the final report. Requires T031 (Draft) completion (see ordering fix below).
- [ ] T033 [US3] Perform Bootstrapped Permutation Test: Implement `run_permutation_test(trajectories, interaction_classes, N=1000)` to calculate p-values for divergence differences between classes (FR-005/SC-003), accounting for Markovian dependencies. Output `data/processed/permutation_results.json`. Requires T030a completion.
- [ ] T033a [US3] Verify Statistical Significance (SC-003): Read `data/processed/permutation_results.json` and assert that the p-value for the primary interaction class comparison is ≤ 0.05. If p > 0.05, log a warning but do not fail (as this is a research result, not a bug); however, the result MUST be included in the final report. Requires T033 completion.
- [ ] T034 [US3] Calculate Pearson's correlation (r) between extracted rule precision (from T027 `data/processed/rule_precision.json`) and CoT quality metrics (from T026 `data/processed/cot_quality_scores.json`) to satisfy SC-005: Read files, compute `scipy.stats.pearsonr`, output result to `data/processed/correlation_result.json` (scalar `r` value), and verify against SC-005 threshold (r ≥ 0.7) with a pass/fail status. **CRITICAL**: If r < 0.7, the pipeline MUST fail with an error to enforce the success criterion. Requires T020, T021, T023, T026, T027 completion.
- [ ] T034a [US3] Assert SC-005 Threshold: Explicitly assert that the correlation value from T034 is ≥ 0.7. If not, raise `AssertionError` to fail the pipeline. (This is a verification step for T034). Requires T034 completion.
- [ ] T031 [US3] Generate `data/processed/divergence_report.json` with classified counts, `excluded_metrics` (uncertainty/cold start), and metadata: Run `python code/analysis/diverge.py --input=... --output=data/processed/divergence_report.json`. **CRITICAL**: Merge `correlation_result.json` (T034), `boundary_conditions` (T032), and `permutation_results` (T033) into a single atomic write (write to temp file, then `os.rename()`). The final report MUST include fields: `p_values`, `boundaries`, `correlation`, `excluded_metrics`. **Requires**: T030a, T033, T033a, T034, T034a, T032 completion.
- [X] T031a [US3] Verify Exclusion Logic: Add assertions in `tests/integration/test_stats_significance.py` to verify that `excluded_metrics` are NOT included in p-value or correlation calculations. Generate `data/processed/exclusion_audit.json` confirming the exclusion logic was applied. Requires T029 completion.

**Checkpoint**: Divergence Report is generated with statistically significant error classification, boundary analysis, and correlation metrics.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036a [P] Documentation updates: Update `README.md` with new CLI usage examples and `docs/api.md` with new function signatures.
- [X] T036b [P] Generate API documentation: Run `pdoc3` or `sphinx-apidoc` to generate `docs/api.md` from docstrings in `code/`.
- [X] T037 [P] Run linter: Execute `ruff check code/ --fix` to ensure code cleanliness.
- [X] T038 [P] Performance optimization for ILP induction on CPU: Refactor `code/rules/extractor.py` to use optimized algorithms (pruning and parallelization) to ensure execution completes within standard CI limits (target <6h on GitHub Actions 2-core CPU).
- [X] T039 [P] Additional unit tests coverage: Achieve ≥80% line coverage on `code/oracle`, `code/rules`, `code/analysis` using `pytest-cov`.
- [X] T040 [P] Run `quickstart.md` validation and end-to-end smoke test: Execute `bash scripts/quickstart.sh` and verify exit code 0.

---

## Phase N+1: Data Pipeline Robustness & Verification (Revision)

**Purpose**: Address critical data hygiene and execution reliability concerns identified in prior research reviews regarding real data sourcing, streaming, and strict "fail loud" data loading policies.

- [X] T044 [P] [US2] Create a "Fail Loudly" integration test in `tests/integration/test_loader_failures.py`: Simulate a network failure or checksum mismatch for the real data source and assert that the pipeline raises an exception and does NOT fall back to any synthetic or mock data generation (Constitution Principle: Loader must fail loudly).

---

## Phase N+2: Execution & Reporting Revision

**Purpose**: Ensure the final analysis pipeline correctly aggregates all metrics, handles edge cases in data streaming, and produces a single, atomic, reproducible report.

- [ ] T045 [US3] Implement `code/analysis/reporter.py` to aggregate all intermediate JSON artifacts (`divergence_report.json`, `rule_precision.json`, `cot_quality_scores.json`, `correlation_result.json`, `boundary_conditions.json`, `rate_metrics.json`) into a single `data/processed/final_report.json`: **Required Fields**: `divergence_report`, `excluded_metrics`. **Optional Fields**: `correlation`, `boundaries`. **Logic**: Handle missing optional fields gracefully (log `WARNING [Field Missing]` but do not fail). The final report must include a `metadata` section with `git_commit_hash`, `dataset_checksums`, and `execution_timestamp`. **Note**: Must explicitly read `boundary_conditions.json` from T032.
- [ ] T046 [US3] Add a "Streaming Integrity Check" task in `tests/integration/test_streaming_integrity.py`: Verify that the streaming logic in `code/rules/extractor.py` (T042) correctly processes a dataset larger than available RAM by simulating a memory-constrained environment (using `pytest-mock` to limit `sys.getrecursionlimit` or memory usage) and confirming that the `itertools.islice` chunking mechanism prevents OOM errors while maintaining data integrity.
- [ ] T047 [US3] Implement `code/utils/audit.py` to generate a `data/processed/audit_trail.json` documenting the exact sequence of data transformations: This script must use `git rev-list` and `sha256sum` to read the `git` history, `requirements.txt` hashes, and input dataset checksums to create a provenance record that links every output metric back to its specific input data version and code commit, satisfying the "Single Source of Truth" and "Versioning Discipline" principles.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Setup (Phase 2.5)**: Depends on Foundational - BLOCKS Trace Gen and US2/US3
 - **T016a** is the entry point.
 - **T016b, T016c, T041** depend on T016a (sequential after fetch).
- **User Stories (Phase 3+)**: All depend on Foundational and Data Setup phases completion
 - **US1 (P1)**: Must complete first to provide the Ground Truth Oracle required by US2 and US3.
 - **Trace Gen (Phase 3.5)**: Depends on Data Setup (T016a) and T017 (Inference). **T017 is a hard sequential gate**; it must complete before US2 logic begins.
 - **US2 (P2)**: Depends on US1 (Oracle) for rule validation and Trace Gen (T017) for input data.
 - **US3 (P3)**: Depends on US1 (Oracle), US2 (Rules), and Trace Gen (T017) for comparison.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation. No dependencies on other stories.
- **Trace Generation**: Produces inputs for US2 and US3. **T017 is sequential**.
- **User Story 2 (P2)**: Depends on US1 (Oracle) for rule validation and Trace Generation for input.
 - **Chain**: T017 -> T020 -> T021 -> T023 -> T027.
 - **Parallel**: T026 (depends on T017).
- **User Story 3 (P3)**: Depends on US1 (Oracle), US2 (Rules), and Trace Generation for comparison.
 - **Chain**: T030 -> T030a -> T033 -> T033a.
 - **Parallel**: T034 (depends on T027, T026) -> T034a.
 - **Final**: T032 (Boundary) and T031 (Report) depend on T030a, T033, T034.
 - **Report**: T031 requires T033 (Permutation Test) to be complete first.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loaders (`utils/loaders.py`) must be implemented before any data fetching tasks
- Models/Logic before services/executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1 must run first; Trace Gen (T017) is a **sequential gate** (not parallel); US2 and US3 can be prepared in parallel (but US3 execution waits for US2 completion)
- All tests for a user story marked [P] can run in parallel
- **T017 is NOT parallel** with T020 (Loading) as it produces the input.
- **T023, T027 are NOT parallel** with T017; they form a sequential chain.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Data Setup (T016a)
4. Complete Phase 3: User Story 1 (Oracle Construction)
5. **STOP and VALIDATE**: Verify Oracle matches simulator on N=1,000 samples.
6. Deploy/Demo Oracle generation pipeline.

### Incremental Delivery

1. Complete Setup + Foundational + Data Setup → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Trace Generation (T017) → Fetch real data (FAIL LOUDLY if missing)
4. Add User Story 2 → Test independently → Deploy/Demo (Rule Extraction)
5. Add User Story 3 → Test independently → Deploy/Demo (Divergence Analysis)
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Data Setup together
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: Trace Generation (T017) - **Sequential Gate**
 - Developer C: User Story 2 Logic (waits for Oracle & Data)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Hygiene**: Strictly no synthetic data fallbacks in `code/utils/loaders.py`. Fail loudly on fetch errors.
- **Compute**: Ensure ILP tasks are CPU-tractable; if GPU is required for a specific step, mark it explicitly for offloading, but prefer CPU for the main pipeline.
- **ID Conflict Resolution**: All task IDs (T001-T047) are now unique and sequential.
- **Revision Note**: T016a moved to Phase 2.5; T019 split into T019a/T019b; T023/T023b merged; T026/T027 activated; T031/T034 reordered; T042/T043 moved to Phase 4/5; T036 split; T037 replaced with linter; T045-T047 added for final reporting and streaming integrity; **T017 is now sequential**; **T033 moved before T031**; **T034a added for SC-005 assertion**; **T030a added for rate calculation**.
- **Trace Generation**: T017 now fetches REAL traces first, failing loudly if not found, ensuring FR-002 and SC-005 are met.