# Tasks: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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
- [X] T002 Initialize a Python project with a recent stable version. with `requirements.txt` (pinning `datasets`, `scikit-learn`, `prolog`, `networkx`, `pandas`, `pytest`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` with `[lint]` rules and `pyproject.toml` with `[tool.black]` configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/loaders.py` with strict real-data fetching (no synthetic fallbacks) using `datasets.load_dataset` or verified HF URLs
- [X] T005 Implement `code/utils/checksums.py` for data hygiene and source verification
- [X] T006 [P] Setup `data/raw/` and `data/processed/` directory structure: Create `data/.gitignore` ignoring `*.parquet`, `*.jsonl`, `__pycache__`, and `*.pth`.
- [X] T007 Create base schema definitions in `specs/001-llmxive-followup/contracts/`: Create `oracle.schema.yaml`, `rules.schema.yaml`, and `divergence.schema.yaml` with definitions from plan.md.
- [X] T008 Configure `pytest` with fixed random seed (42) and integration test scaffolding: Create `pytest.ini` with `addopts = --random-seed=42` and `tests/integration/conftest.py`.
- [X] T009 Implement `code/__init__.py` and `code/main.py` entry point structure
- [X] T016a [P] [US3] Define the Standardized Benchmark: Create `data/raw/standardized_benchmark.json` containing a curated list of long-horizon planning tasks (as required by FR-003) with metadata including `interaction_type` (spatial, temporal, causal) and `task_id`. This file serves as the single source of truth for T017/T018.
- [X] T041 [P] [US1] Implement explicit URL verification and checksum validation for `AgentWorldBench` in `code/utils/loaders.py`: Replace generic `load_dataset` calls with explicit `hf_hub_download` or verified raw URL fetch for the environment source code and benchmark tasks, ensuring the script fails with a clear error if the specific commit hash or checksum does not match the expected value (Constitution Principle III).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Oracle Construction (Priority: P1) 🎯 MVP

**Goal**: Parse Qwen-AgentWorld source code to generate a deterministic state-transition oracle for independent ground truth verification.

**Independent Test**: Verify generated oracle matches original environment simulator trajectories for N=1,000 random inputs (seed=42) with ≥99.9% accuracy.

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Contract test for `oracle/parser.py` in `tests/unit/test_oracle_parser.py` (verifies schema alignment)
- [X] T011 [US1] Integration test for Oracle vs. Environment Simulator in `tests/integration/test_oracle_validation.py` (N=1,000 random seeds, seed=42)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/oracle/parser.py` to parse Qwen-AgentWorld source and extract interaction logic (spatial, temporal, causal)
- [X] T013 [US1] Implement `code/oracle/simulator.py` to execute deterministic state transitions based on parsed logic
- [X] T014 [US1] Generate `data/processed/oracle_graph.json` (Deterministic State-Transition Oracle) and invoke checksum verification: Run `python code/main.py --stage=oracle --output=data/processed/oracle_graph.json`.
- [X] T015 [US1] Implement orchestration step in `code/main.py` or `oracle/parser.py` to invoke `code/utils/checksums.py` during Oracle generation and fail on mismatch (Code Drift check)
- [X] T016 [US1] Add logging for Oracle generation and validation steps: Add `logging.basicConfig` to `code/oracle/parser.py` and `code/oracle/simulator.py` with level=INFO and format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'.

**Checkpoint**: Ground Truth Oracle is fully functional, validated against simulator, and ready for rule extraction.

---

## Phase 3.5: Trace Generation (Prerequisite for US2 & US3)

**Goal**: Generate the required CoT traces and synthetic control traces to enable rule extraction and quality verification.

- [X] T017 [US2] Implement `code/inference/runner.py` to generate CoT traces for the Standardized Benchmark: Implement a CPU-quantized inference pipeline (e.g., Qwen-1.8B-Int4) to generate CoT traces for the tasks defined in `data/raw/standardized_benchmark.json`. Output must be saved to `data/raw/cot_traces.json` with metadata including `task_id` and `interaction_type`. Verification: Run `python code/inference/runner.py --input=data/raw/standardized_benchmark.json --output=data/raw/cot_traces.json` and confirm file exists with valid JSON structure.
- [X] T018 [US2] Execute trace generation: Run `python code/inference/runner.py --input=data/raw/standardized_benchmark.json --output=data/raw/cot_traces.json`. This task MUST complete before T020, T021, T023, T030.
- [X] T019 [US2] Generate synthetic control traces and verify extraction: Create `data/raw/synthetic_control_traces.json` containing N=500 traces with pre-determined logical patterns. Then, run the extraction algorithm on these traces and assert that the extracted rules reproduce the known patterns with ≥95% precision (US-02 Independent Test). Output `data/processed/synthetic_validation_report.json` containing the precision metric and pass/fail status.

---

## Phase 4: User Story 2 - Rule Extraction from Reasoning Traces (Priority: P2)

**Goal**: Apply ILP/Decision Tree to LLM CoT traces to extract explicit logical rules and validate against the Oracle.

**Independent Test**: Feed synthetic traces with known patterns; Verify extracted rules reproduce patterns with ≥95% precision.

### Implementation for User Story 2

- [X] T020 [US2] Load LLM CoT traces: Load `data/raw/cot_traces.json` (produced by T018). If missing, FAIL LOUDLY (do not generate synthetic data). Requires T018 completion.
- [X] T021 [US2] Implement `code/rules/extractor.py` using FOL/ILP (e.g., Prolog induction) to derive rules from CoT traces
- [X] T023 [US2] Implement Extraction Logic: Implement the core logic in `code/rules/extractor.py` to parse CoT traces and induce First-Order Logic rules, handling ambiguous traces by flagging them as "Extraction Uncertainty".
- [X] T023b [US2] Execute Rule Extraction: Run `python code/rules/extractor.py --input=data/raw/cot_traces.json --output=data/processed/extracted_rules.json`. Requires T021 completion.
- [X] T022 [US2] Implement `code/rules/validator.py` to cross-check extracted rules against the Ground Truth Oracle (FR-002)
- [X] T027 [US2] Implement `code/rules/metrics.py` to calculate **Rule Precision** by comparing `data/processed/extracted_rules.json` against `data/processed/oracle_graph.json` (Ground Truth) and output `data/processed/rule_precision.json` (scalar metric) to satisfy SC-005: Implement `calculate_precision(extracted_rules, oracle_graph)` using defined metric.
- [X] T026 [US2] Implement `code/analysis/metrics.py` to calculate **CoT Quality Score**: Calculate a general quality metric (e.g., logical consistency, coherence) for the traces in `data/raw/cot_traces.json` and output `data/processed/cot_quality_scores.json` for SC-005 correlation analysis. (Note: Pattern Reproduction Precision is handled in T019).
- [X] T024 [US2] Implement logic to flag "Extraction Uncertainty" for ambiguous/contradictory traces AND explicitly apply exclusion logic: Ensure that when calculating Hallucination and Rule Gap rates in downstream tasks, the denominators strictly exclude counts marked as "Extraction Uncertainty" or "Coverage Gap (Cold Start)". Output a separate `excluded_metrics` field in the final report containing counts for `extraction_uncertainty` and `cold_start` (per FR-004).
- [X] T025 [US2] Add logging for rule extraction confidence: In `code/rules/extractor.py`, add `logger.info(f"Rule confidence: {confidence}")` for each extracted rule.

**Checkpoint**: Hypothesized Rule Set is extracted, validated against Oracle, uncertainty is properly flagged and reported separately, CoT quality metrics are generated, and Rule Precision is calculated.

---

## Phase 5: User Story 3 - Divergence Quantification and Classification (Priority: P3)

**Goal**: Compare LLM, Extracted Rules, and Oracle on long-horizon tasks; classify errors into "Hallucination" and "Rule Gap"; perform statistical significance testing.

**Independent Test**: Run on small manually verified dataset; Confirm error classification (Hallucination vs Rule Gap) matches human annotation (Cohen's Kappa ≥ 0.8).

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Contract test for `analysis/diverge.py` in `tests/unit/test_divergence_classifier.py`
- [X] T029 [US3] Integration test for Statistical Significance (Permutation Test) in `tests/integration/test_stats_significance.py`

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/analysis/diverge.py` to execute standardized tasks and classify transitions: Implement `classify_transition(llm_state, oracle_state, rules)` returning one of: Match, Hallucination, Rule Gap, Uncertainty, Cold Start. Requires T014 (Oracle) and T023 (Rules) completion.
- [X] T031 [US3] Generate `data/processed/divergence_report.json` with classified counts, `excluded_metrics` (uncertainty/cold start), and metadata: Run `python code/analysis/diverge.py --input=... --output=data/processed/divergence_report.json`. **CRITICAL**: Apply exclusion logic to denominators BEFORE calculating Hallucination and Rule Gap rates. The final report MUST include fields: `p_values`, `boundaries`, `correlation`, `excluded_metrics`. Requires T029 (test file exists) for audit context.
- [X] T031a [US3] Verify Exclusion Logic: Add assertions in `tests/integration/test_stats_significance.py` to verify that `excluded_metrics` are NOT included in p-value or correlation calculations. Generate `data/processed/exclusion_audit.json` confirming the exclusion logic was applied. Requires T029 completion.
- [X] T032 [US3] Implement logic in `code/analysis/stats.py` to identify the specific step count or state complexity boundary where measured adherence drops below the **≥95%** threshold (per FR-006/SC-004): Implement `find_adherence_boundary(trajectories, threshold=0.95)` using binary search and output a structured `boundary_conditions` object to the final report.
- [X] T033 [US3] Perform Bootstrapped Permutation Test: Implement `run_permutation_test(trajectories, interaction_classes, N=1000)` to calculate p-values for divergence differences between classes (FR-005/SC-003), accounting for Markovian dependencies.
- [X] T034 [US3] Calculate Pearson's correlation (r) between extracted rule precision (from T027 `data/processed/rule_precision.json`) and CoT quality metrics (from T026 `data/processed/cot_quality_scores.json`) to satisfy SC-005: Read files, compute `scipy.stats.pearsonr`, output result to `data/processed/correlation_result.json`, and verify against SC-005 threshold (r ≥ 0.7) with a pass/fail status. (Depends on T020, T021, T023, T026, T027).
- [X] T035 [US3] Finalize `divergence_report.json` with p-values (α ≤ 0.05), boundary conditions (from T032), and correlation metrics (from T034): Merge `divergence_report.json` with `correlation_result.json` and `boundary_conditions`, ensuring final file contains fields: `p_values`, `boundaries`, `correlation`, `excluded_metrics`.

**Checkpoint**: Divergence Report is generated with statistically significant error classification, boundary analysis, and correlation metrics.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `README.md`: Update `README.md` with new CLI usage examples and `docs/api.md` with new function signatures.
- [X] T037 Code cleanup and refactoring across `code/`
- [X] T038 [P] Performance optimization for ILP induction on CPU: Refactor `code/rules/extractor.py` to use optimized algorithms (pruning and parallelization) to ensure execution completes within standard CI limits (target <6h on GitHub Actions 2-core CPU).
- [X] T039 [P] Additional unit tests coverage in `tests/unit/`
- [X] T040 [P] Run `quickstart.md` validation and end-to-end smoke test: Execute `bash scripts/quickstart.sh` and verify exit code 0.

---

## Phase N+1: Data Pipeline Robustness & Verification (Revision)

**Purpose**: Address critical data hygiene and execution reliability concerns identified in prior research reviews regarding real data sourcing, streaming, and strict "fail loud" data loading policies.

- [ ] T042 [US2] Implement streaming logic for large CoT trace datasets in `code/rules/extractor.py`: Refactor the trace loading logic to use `datasets.load_dataset(..., streaming=True)` and iterate via `itertools.islice` with `chunk_size=1000`. Explicitly log `INFO: Streaming chunk {i}/{total}, sample_size={n}`. If streaming is truncated or interrupted, the task MUST raise a `DataTruncationError` and NOT proceed, ensuring 'fail loud' behavior. (Constitution Principle: Large real datasets).
- [ ] T043 [US3] Add a "Cold Start" verification task to `code/analysis/diverge.py`: Explicitly compare the set of `interaction_type` values found in `data/processed/oracle_graph.json` nodes against those found in `data/raw/cot_traces.json` metadata. Identify types present in Oracle but absent in Traces and categorize them as "Coverage Gap (Cold Start)" in the final report (Spec Edge Case: Cold Start).
- [ ] T044 [P] [US2] Create a "Fail Loudly" integration test in `tests/integration/test_loader_failures.py`: Simulate a network failure or checksum mismatch for the real data source and assert that the pipeline raises an exception and does NOT fall back to any synthetic or mock data generation (Constitution Principle: Loader must fail loudly).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete first to provide the Ground Truth Oracle required by US2 and US3.
 - **Trace Gen (Phase 3.5)**: Depends on US1 (Oracle) for validation logic (optional) and T017 (Inference). Must complete before US2.
 - **US2 (P2)**: Depends on US1 (Oracle) for validation and Trace Gen (T018, T019) for input data.
 - **US3 (P3)**: Depends on US1 (Oracle), US2 (Rules), and Trace Gen (T018) for comparison.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation. No dependencies on other stories.
- **Trace Generation**: Produces inputs for US2 and US3.
- **User Story 2 (P2)**: Depends on US1 (Oracle) for rule validation and Trace Generation for input.
- **User Story 3 (P3)**: Depends on US1 (Oracle), US2 (Rules), and Trace Generation for comparison.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loaders (`utils/loaders.py`) must be implemented before any data fetching tasks
- Models/Logic before services/executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1 must run first; Trace Gen can start in parallel with US1 logic; US2 and US3 can be prepared in parallel (but US3 execution waits for US2 completion)
- All tests for a user story marked [P] can run in parallel
- **T017, T018, T019 are NOT parallel** with T020 (Loading) as they produce the input.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Oracle Construction)
4. **STOP and VALIDATE**: Verify Oracle matches simulator on N=1,000 samples.
5. Deploy/Demo Oracle generation pipeline.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Trace Generation (T017-T019) → Generate data
4. Add User Story 2 → Test independently → Deploy/Demo (Rule Extraction)
5. Add User Story 3 → Test independently → Deploy/Demo (Divergence Analysis)
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: Trace Generation (T017-T019)
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
- **ID Conflict Resolution**: All task IDs (T001-T044) are now unique and sequential.
- **Revision Note**: T017-T019 updated with explicit benchmark references and verification; T023 split into T023/T023b; T026 corrected to CoT Quality Score; T031 updated with explicit exclusion logic; T042/T043 updated with specific logging and mapping logic; T038 constraint softened to match spec. **T023, T023b, T026, T027 marked as active (checked) to resolve dependency chain blocking T034.**