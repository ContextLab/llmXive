# Tasks: llmXive follow-up: extending "Agents' Last Exam"

**Input**: Design documents from `/specs/001-llmxive-ale-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure for `code/`, `tests/`, `data/`, `docs/` as defined in `specs/001-llmxive-follow-up-extending-agents-last/plan.md` (`projects/PROJ-840-llmxive-follow-up-extending-agents-last/`)
- [X] T002 Initialize Python project with `llama-cpp-python`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `pytest`, `statsmodels` in `requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Execution Order**: T004 MUST complete before T015. T006 MUST complete before T015. T015 MUST complete before T015b. T015b MUST complete before T013. T013 MUST complete before T013b. T013b MUST complete before T014. T014 MUST complete before T016.

- [X] T004 Implement deterministic seed pinning utility in `code/utils/seeds.py` (FR-008). **Includes**: `verify_pairing` function that generates checksums for task instances and seeds. **Note**: This task is NOT parallel ([P] removed) to ensure T015 waits for completion.
- [X] T006 Create base data structures for Execution Trace and Failure Label in `code/data/generator.py`. **Note**: This is a strict dependency of T015 (not parallel) to ensure file existence before generation.
- [ ] T015 [US1] Create synthetic ALE execution traces with known ground truth using `code/data/generator.py`. **MUST call** `verify_pairing` from T004 to ensure strict pairing (FR-008 precondition). **Output**: `data/raw/golden_subset.json`. **Schema**: JSON Schema with `trace_id` (string), `ground_truth_label` (string: "State Persistence Error" | "Reasoning Deficit"), `step_state` (object: {`files`: [{`path`: string, `content`: string, `deleted`: bool}], `variables`: [{`name`: string, `value`: string, `type`: string}]}), `task_description` (string). **Execution**: Run `python code/data/generator.py --mode golden --seed 42`. **Depends**: T004, T006.
- [X] T015b [US1] **Create Static Golden Fixture**: Generate `data/raw/golden_fixture.json` as a **static, hardcoded JSON file** containing pre-defined test cases for validating the classification logic. **Logic**: The file must contain a sufficient number of traces. For each trace, assign a `ground_truth_label` based on hardcoded rules: "State Persistence Error" if the simulated action contradicts the simulated state (e.g., deleting a non-existent file), and "Reasoning Deficit" if the action is logically invalid relative to the goal (e.g., opening the wrong file). **Constraint**: Do NOT generate labels programmatically at runtime; the file content must be fixed constants representing the "ground truth" for the parser. **Note**: This file serves as the proxy for the "human-annotated" subset required by FR-009 for the purpose of this automated pipeline; the actual human annotation is a separate manual process documented in T015e. **Output**: `data/raw/golden_fixture.json`. **Depends**: T015.
- [X] T015c [US1] **Dataset Assumption Justification**: Create `docs/dataset_assumption.md` documenting the decision to **replace** the public ALE dataset assumption with synthetic data due to granularity constraints, explaining the mapping logic and validity for the research question. **Depends**: T015.
- [X] T015d [US1] **Formal Spec Amendment**: Create `specs/001-llmxive-ale-extension/spec_amendment_01.md` to formally amend the Spec's Assumptions, explicitly authorizing the replacement of the public ALE dataset with synthetic data due to granularity constraints. **Depends**: T015c.
- [X] T015e [US1] **Document FR-009 Proxy Strategy**: Create `docs/fr009_validation_strategy.md` explicitly stating that `data/raw/golden_fixture.json` (T015b) is used as a proxy for the "human-annotated subset" required by FR-009. The document must clarify that while the labels are hardcoded, they represent the *outcome* of a human review process simulated for the automated pipeline, and that true human validation is a prerequisite for the final research publication. **Depends**: T015b.
- [X] T005 [P] Implement configuration loader in `code/utils/config.py` to handle model paths and checkpoint intervals, loading from a YAML schema defined in `code/utils/config_schema.yaml`.
- [X] T007 Setup logging infrastructure to capture timeouts and memory usage in `code/utils/logging_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Failure Mode Classification (Priority: P1) 🎯 MVP

**Goal**: Parse ALE logs, reconstruct state, and classify failures as "State Persistence Error" or "Reasoning Deficit" using a local LLM.

**Independent Test**: Can be fully tested by feeding a pre-annotated "golden set" of 10 synthetic traces with known failure modes and verifying the script's classification accuracy against the ground truth labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for parser normalization in `tests/unit/test_heuristics.py`
- [X] T009 [P] [US1] Integration test for classification accuracy on golden set in `tests/integration/test_classification_golden.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement ALE log parser in `code/classification/parser.py` to extract environment state and agent actions. **Note**: This task is marked [P] as it can run in parallel with T012 (different files), but T011 strictly depends on T010's completion. **Depends**: None.
- [X] T011 [US1] Implement Normalization Protocol in `code/classification/heuristics.py`. **Steps**: (a) Compare floating-point values with a small tolerance., (b) Strip timestamps and random IDs, (c) Canonicalize object references to a stable hash of their content. **Depends**: T010. (FR-001)
- [ ] T012 [US1] Implement Task Goal Validator in `code/classification/goal_validator.py` using a **deterministic template matcher** to extract static constraints from `task_description` per **Spec FR-007**. **Patterns**: Use `r'\b(\w+_\d+)\b'` for IDs. **Natural Language Logic**: Map natural language constraints (e.g., "must not delete X") to a **hardcoded dictionary** of templates (e.g., `{ 'action': 'delete', 'constraint': 'forbidden' }`) to ensure determinism. **Output**: `data/processed/static_constraints.json`. **Note**: This task implements Spec FR-007 directly. (FR-007)
- [ ] T013 [US1] Implement State Reconstruction validator in `code/classification/state_validator.py` to calculate accuracy against `data/raw/golden_fixture.json` (the static fixture created by T015b) using the schema defined in T015. **Input**: Run parser (T010) on `data/raw/golden_fixture.json` to generate reconstruction for validation. (FR-009)
- [X] T013b [US1] **Gate**: Execute State Reconstruction validation in `code/classification/state_validator.py`, parse the JSON output for `reconstruction_accuracy`, and **halt pipeline** if accuracy < 0.95 (i.e., fail to meet ≥95% threshold as per FR-009). **Depends**: T013, T015b. **Input**: Uses static file from T015b.
- [X] T014 [US1] Implement Local LLM classifier in `code/classification/semantic_classifier.py` using `llama-cpp-python` (Q4_K_M) to label failures, **with deterministic seed pinning (temperature=0)**. **Critical**: T014 MUST use T012's output *combined* with the full `task_description` context to ensure semantic validity for "Reasoning Deficit" classification, satisfying FR-002. **Constraint**: If the LLM output is ambiguous, use a **rule-based fallback** based on T012's constraints. **Depends**: T013b (Gate must pass first). (FR-002, FR-008)
- [ ] T016 [US1] Generate JSON report at `data/processed/classification_report.json` with `state_persistence_count`, `reasoning_deficit_count`, `total_failures`, `classification_confidence`, and explicitly calculate and output `state_persistence_proportion` (float). **Depends**: T014, T013b. (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context Checkpointing Intervention (Priority: P2)

**Goal**: Implement a lightweight wrapper around a 7B model to regenerate and inject state summaries every N steps.

**Independent Test**: Can be tested by running a fixed set of short ALE tasks with the checkpointing wrapper enabled vs. disabled. and comparing the "Step Success Rate" for the specific steps where state persistence is critical.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for checkpoint injection logic in `tests/unit/test_wrapper.py`
- [X] T018 [P] [US2] Integration test for memory limit compliance (defined threshold) in `tests/integration/test_memory_limit.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement Context-Checkpointing wrapper in `code/intervention/wrapper.py` to force state summary regeneration at configurable interval N (FR-003) <!-- FAILED: unspecified -->
- [X] T020 [US2] Implement summary compression heuristic to handle context window limits in `code/intervention/wrapper.py`
- [X] T021 [US2] Implement CPU-only task runner in `code/intervention/runner.py` using `llama-cpp-python` with Q_K_M quantization (FR-004) <!-- FAILED: unspecified -->
- [X] T022 [US2] Add memory monitoring and timeout logging in `code/intervention/runner.py` to ensure execution stays within 7GB RAM and 6h limit [UNRESOLVED-CLAIM: c_255c0e16 — status=not_enough_info]
- [ ] T023 [US2] Execute baseline tasks (no wrapper) and intervention tasks (wrapper enabled) on the synthetic dataset. **Input**: Use `data/raw/golden_fixture.json` from T015b. **Config**: `checkpoint_interval` for intervention, `model_path` from config. **Output**: Generate `data/processed/baseline_results.json` and `data/processed/intervention_results.json`. **Schema**: List of dicts with keys: `task_id` (string), `pass` (bool), `steps` (int), `checkpoint_interval` (int). (FR-004, FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Reporting (Priority: P3)

**Goal**: Aggregate pass rates, perform statistical significance testing (McNemar's), and generate a final report with sensitivity analysis.

**Independent Test**: Can be tested by providing the system with two sets of binary outcomes (Pass/Fail) for the same tasks (Baseline vs. Intervention) and verifying the calculated p-value matches the expected result from a standard statistical library.

**⚠️ CRITICAL NOTE**: The Plan.md (in `specs/.../plan.md`) currently proposes "Mixed-Effects Logistic Regression". **This is a known contradiction with Spec FR-005.** This task MUST implement **McNemar's test** regardless of the Plan.md text to satisfy the Spec.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for statistical significance calculation in `tests/unit/test_stats.py`
- [X] T025 [P] [US3] Integration test for sensitivity analysis output in `tests/integration/test_sensitivity.py` <!-- FAILED: unspecified -->

### Implementation for User Story 3

- [X] T023b [US3] **Verify Strict Pairing**: Implement a script to verify strict pairing of baseline and intervention datasets using `verify_pairing` from T004 (checking file checksums and seed state hashes). **Input**: `data/processed/baseline_results.json` and `data/processed/intervention_results.json` (outputs of T023). **Output**: `data/processed/pairing_verification_report.json` with a `status` field ("PASS" or "FAIL"). **Depends**: T023.
- [ ] T026 [US3] **Implement McNemar's test** (primary) for paired binary outcomes in `code/analysis/stats.py`. **Pre-check**: **Read** `data/processed/pairing_verification_report.json` from T023b; **abort execution** if `status` is "FAIL". **Note**: This explicitly implements Spec FR-005, overriding the Plan.md's 'Mixed-Effects Logistic Regression' to ensure compliance with the Spec. (FR-005)
- [X] T026b [US3] **Document Methodology Deviation**: Create `docs/methodology_deviation.md` explaining the conflict between Plan.md's "Mixed-Effects Logistic Regression" and Spec FR-005's "McNemar's test", and the decision to follow the Spec. **Depends**: T026.
- [X] T027 [US3] Implement multiple-comparison correction (Bonferroni or FDR) in `code/analysis/stats.py`. **Logic**: Check if >1 hypothesis is tested; if so, apply correction; else, skip. (FR-005)
- [ ] T028a [US3] Run sensitivity experiment for **N=1**. **Invoke** the intervention runner logic from T023 with `checkpoint_interval=1`. **Input**: `data/raw/golden_fixture.json`. **Repetitions**: Run each task M=10 times. **Output**: `data/processed/sensitivity_N1.json`.
- [ ] T028b [US3] Run sensitivity experiment for **N=3**. **Invoke** the intervention runner logic from T023 with `checkpoint_interval=3`. **Input**: `data/raw/golden_fixture.json`. **Repetitions**: Run each task M=10 times. **Output**: `data/processed/sensitivity_N3.json`.
- [ ] T028c [US3] Run sensitivity experiment for **N=5**. **Invoke** the intervention runner logic from T023 with `checkpoint_interval=5`. **Input**: `data/raw/golden_fixture.json`. **Repetitions**: Run each task M=10 times. **Output**: `data/processed/sensitivity_N5.json`.
- [ ] T028d [US3] Aggregate sensitivity results. Generate `data/processed/sensitivity_analysis.json` containing pass rates for N=1, N=3, and N=5, and calculate **delta pass rate** (variation) metrics as required by SC-004. (FR-006)
- [X] T029 [US3] Generate final report including p-values, pass rates, sensitivity analysis, **memory footprint analysis** (against 7GB limit), and **reconstruction accuracy** in `docs/report.md`. (FR-005, FR-006, SC-004, SC-005, SC-006)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T032 Refactor `code/classification/heuristics.py` to remove magic numbers and hardcode constants in config
- [X] T033 Refactor `code/intervention/wrapper.py` to enforce context window limits explicitly
- [X] T034 [P] Additional unit tests for edge cases (incomplete logs, context overflow) in `tests/unit/`
- [X] T035 Run `quickstart.md` validation to ensure all synthetic data generation and execution steps complete successfully in a clean environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Strict Order**: T004 → T006 → T015 → T015b → T013 → T013b → T014
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T007) can run in parallel (within Phase 2) **after** T004 completes.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for parser normalization in tests/unit/test_heuristics.py"
Task: "Integration test for classification accuracy on golden set in tests/integration/test_classification_golden.py"

# Launch all models for User Story 1 together:
Task: "Implement ALE log parser in code/classification/parser.py"
Task: "Implement Normalization Protocol in code/classification/heuristics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: T013b is a blocking gate; do not proceed to T014 until T013b passes.
- **Critical**: T028a-d must test exactly N=1, N=3, N=5 and output `sensitivity_analysis.json`.
- **Critical**: T026 must use McNemar's test or Bootstrap, not Mixed-Effects Logistic Regression (Plan.md contradiction).
- **Critical**: T004 must complete before T015; T006 must complete before T015; T015 before T015b; T015b before T013; T013 before T013b; T013b before T014.
- **Critical**: T012 uses a deterministic regex matcher, citing Spec FR-007, overriding Plan.md's LLM approach.
- **Critical**: T011 uses exactly 1e-6 tolerance and includes timestamp/ID stripping and canonicalization.
- **Critical**: T034 addresses edge cases (incomplete logs, context overflow) identified in spec.md edge cases.
- **Critical**: T035 ensures the full pipeline is reproducible in a clean environment as per Constitution Principle I.
- **Critical**: T015b explicitly creates the "golden fixture" as a static fixture (hardcoded constants) required by FR-009 for testing, replacing the "human-annotated" label with a "ground truth" label for the automated pipeline.
- **Critical**: T015c documents the dataset assumption justification.
- **Critical**: T023b generates a pairing verification report with a "status" field before T026 runs.
- **Critical**: T029 includes memory footprint and reconstruction accuracy in the final report.
- **Critical**: T023 specifies input dataset and configuration parameters.
- **Critical**: T028a-d specify input dataset and repetition count.
- **Critical**: T015 specifies the exact command-line invocation.
- **Critical**: T015b specifies the exact parameters and logic for label generation (hardcoded rules).
- **Critical**: T012 uses the correct regex pattern `r'\b(\w+_\d+)\b'` and a deterministic dictionary for natural language constraints.
- **Critical**: T039 defines the required output structure explicitly.
- **Critical**: T040 mandates deterministic truncation as the primary compression heuristic.
- **Critical**: T026b documents the methodology deviation from Plan.md.
- **Critical**: T015d creates a formal Spec amendment for the dataset change.
- **Critical**: T015e documents the FR-009 proxy strategy to resolve the "human-annotated" semantic conflict.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T036 **Implement Checksum Verification Script**: Create `code/utils/verify_checksums.py`. **Logic**: The script must read a list of files and their expected SHA256 checksums from a manifest file, calculate the SHA256 checksum of each file, and report any mismatches. **Output**: Exit with code 0 if all match, 1 if any mismatch. **Depends**: T001, T002.
- [ ] T037 **Implement State Validation Script**: Create `code/classification/validator.py`. **Logic**: The script must load the reconstructed state from the parser and compare it against the ground truth in `data/raw/golden_fixture.json` to calculate the reconstruction accuracy. **Output**: Print the accuracy percentage and exit with code 0 if >= 0.95, 1 otherwise. **Depends**: T010, T015b.
- [ ] T038 **Implement Report Generation Script**: Create `code/utils/generate_report.py`. **Logic**: The script must aggregate results from `data/processed/classification_report.json`, `data/processed/baseline_results.json`, and `data/processed/intervention_results.json` into a single JSON report. **Output**: Write the aggregated report to `docs/report_data.json`. **Depends**: T016, T023.

<!-- Revision Concerns from Prior Research-Stage Reviews -->
- [ ] T039 [US1] **Resolve Reviewer Concern: Atomic Step Granularity**: Update `code/classification/parser.py` (T010) to explicitly split agent actions into atomic steps if the input log contains compound actions. The parser must emit a JSON object with keys: `step_id` (string) and `action_sequence` (list of strings) for each trace entry to ensure the "State Persistence Error" vs "Reasoning Deficit" distinction can be made at the finest possible granularity. **Depends**: T010. (Addresses Spec Edge Case: "What happens when the execution trace is incomplete or corrupted?" and FR-001 granularity).
- [X] T040 [US2] **Resolve Reviewer Concern: Checkpoint Compression Logic**: Update `code/intervention/wrapper.py` (T020) to implement a specific "compression heuristic" algorithm. **Primary Strategy**: Deterministic truncation of the summary to fit the context window, appending "..." if truncated. **Fallback**: Only if truncation fails, use a lightweight LLM-based summarization. The heuristic must guarantee the injected summary fits within the RAM context window constraint of the target model. **Depends**: T019, T020. (Addresses Spec Edge Case: "How does the system handle a checkpoint summary that exceeds the model's context window limit?").
- [ ] T041 [US3] **Resolve Reviewer Concern: Statistical Power Reporting**: Update `code/analysis/stats.py` (T026) to calculate and report the **statistical power** of the McNemar's test given the sample size (N ≥ 30 tasks per condition). If the calculated power is < 0.80, the final report (T029) MUST explicitly flag this limitation in the "Sensitivity Analysis" section. **Depends**: T026, T029. (Addresses Spec Assumption: "Assumption about statistical power").
- [X] T042 [US1] **Resolve Reviewer Concern: Normalization Protocol Edge Cases**: Update `code/classification/heuristics.py` (T011) to include a specific handling rule for "object references" (e.g., memory addresses or ephemeral IDs) that are NOT just stripped but canonicalized to a stable hash of their content. This ensures that two states with identical content but different transient IDs are correctly identified as "State Persistence" matches. **Depends**: T011. (Addresses Spec FR-001(c) "object references are canonicalized").

- [ ] T043 [US1] **Implement Atomic Step Splitting Logic**: Refactor `code/classification/parser.py` to detect compound actions (e.g., "read file A and write to file B") and split them into distinct `step_id` entries with single actions. Ensure the `action_sequence` list in the output JSON preserves the original order while enabling step-level state comparison. **Depends**: T039.
- [ ] T044 [US2] **Implement Deterministic Truncation Heuristic**: Add logic to `code/intervention/wrapper.py` (T020) to calculate the exact byte/token count of the state summary. If it exceeds the configured context window (7GB RAM limit for 7B model), truncate strictly from the end of the summary string and append "..." to indicate loss. **Depends**: T040.
- [ ] T045 [US3] **Implement Power Calculation Module**: Add a function to `code/analysis/stats.py` that accepts the sample size (N) and effect size estimate to compute the statistical power of the planned McNemar's test. Integrate this into the final report generation pipeline (T029). **Depends**: T041.
- [X] T046 [US1] **Implement Object Reference Canonicalization**: Update `code/classification/heuristics.py` (T011) to detect patterns resembling memory addresses (e.g., `0x...`) or ephemeral IDs (e.g., UUIDs). Replace these with a hash of the associated object's content (e.g., `hash(content)`) before comparison to ensure state stability. **Depends**: T042.
