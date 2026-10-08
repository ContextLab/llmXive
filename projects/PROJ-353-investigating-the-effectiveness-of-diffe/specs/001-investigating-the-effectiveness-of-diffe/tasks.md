# Tasks: Investigating Loss Functions on Small-World Graphs

**Input**: Design documents from `/specs/001-investigating-the-effectiveness-of-diffe/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Must run in strict sequence (dependencies on previous tasks in the group)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per plan.md structure)
- **Data**: `data/raw/`, `data/processed/`, `data/analysis/`
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

## Phase 0: Research & Setup (Shared Infrastructure)

**Purpose**: Project initialization, documentation, and basic structure

- [ ] T001 [P] **Create Project Structure**: Create directories `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `artifacts/`, `contracts/`. **Verification**: Script must verify existence of all directories before exiting. **Dependency**: None.
- [X] T002 [P] **Initialize Python 3.11 project**: Create `requirements.txt` with pinned versions of `networkx`, `torch`, `scikit-learn`, `statsmodels`, `lifelines`, `numpy`, `pandas`. **Verification**: Run `pip install -r requirements.txt` and verify success. **Dependency**: T001.
- [ ] T040a [S] **Create Research Documentation**: Create `research.md` in `specs/001-investigating-the-effectiveness-of-diffe/`. **Action**: Write the initial research questions and methodology summary. **Content Requirement**: Must explicitly state the hypothesis (InfoNCE vs CE on small-world graphs) and the statistical approach (Tobit/Cox). **Constraint**: This is a Phase 0 deliverable as per `plan.md` Project Structure. **Dependency**: T001.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and SPEC ALIGNMENT that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The order of execution in this phase is strictly serial for the first block (Verification -> Data Model -> Code).

### 1.1: Plan & Spec Alignment (Strict Serial Order)

**Note**: The `spec.md` is the read-only source of truth. The `plan.md` is the active working document. This phase verifies that the Plan already reflects the Spec. No modification tasks are required if the Plan is correct.

- [X] T004 [S] **Implement `code/utils.py`**: Implement `seed_all()`, `hash_artifact(path: str)`, and constants `CONVERGENCE_THRESHOLD = 0.90 `, `MAX_EPOCHS = 1000 `, `SAMPLE_SIZE = 110 `. **Verification**: Include a unit test `tests/unit/test_utils.py::test_sample_size_is_110` that asserts `utils.SAMPLE_SIZE == 110`. **Dependency**: T001.
- [X] T011 [S] **Create Validation Script**: Create `code/validate_plan.py`. **Action**: The script must assert that `specs/001-investigating-the-effectiveness-of-diffe/spec.md` contains "N=110" (FR-001), and `specs/001-investigating-the-effectiveness-of-diffe/plan.md` contains "Tobit Regression", "Cox Proportional Hazards", "0.90", AND the phrase "interaction terms" or "interaction focus" to satisfy FR-008. **Constraint**: If values do not match, the script MUST log a WARNING but NOT exit with code 1 (to avoid circular build failure). **Dependency**: T001.
- [ ] T005 [S] **Write Data Model**: Create `data-model.md` including Markdown tables for `SyntheticGraph`, `TrainingRun`, and `AnalysisResult` entities, plus JSON Schema Draft 7 examples for each. **Verification**: File exists and contains valid JSON Schema. **Dependency**: T001.
- [ ] T006a [P] **Generate Graph Schema**: Generate `contracts/graph.schema.yaml` from `data-model.md` and T005. **Format**: JSON Schema Draft 7 embedded in YAML. **Verification**: Schema includes all fields from SyntheticGraph entity. **Dependency**: T005.
- [ ] T007 [P] **Generate Training Run Schema & Validate**: Generate `contracts/training_run.schema.yaml` from `data-model.md` and T005. **Format**: JSON Schema Draft 7 embedded in YAML. **Verification**: Schema includes the `trajectory` field (list of per-epoch `{loss, accuracy}` objects) as required by Constitution Principle VI and US-2. **Dependency**: T005.

### 1.3: Core Code Infrastructure

- [X] T008 [P] **Implement `code/models.py`**: Implement a multi-layer GCN class (CPU-only). **Verification**: Unit tests pass. **Dependency**: T005.
- [X] T009 [P] **Implement `code/losses.py`**: Implement Cross-Entropy and InfoNCE implementations. **Verification**: Unit tests pass. **Dependency**: T005.
- [X] T012 [S] **Implement Convergence Logic Validator**: Create `code/validate_convergence.py`. **Action**: Verify that the logic for marking a run as "censored" (accuracy < 0.90 within max epochs) matches the spec definition (FR-005). **Verification**: Run unit tests that assert censored status is correctly assigned for edge cases (e.g., accuracy=0.89 at max_epoch) AND that the logic is implemented consistently with FR-005 before training tasks begin. **Dependency**: T004, T008, T009.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Synthetic Graph Generation and Topology Annotation (Priority: P1) 🎯 MVP

**Goal**: Generate a set of Watts-Strogatz graphs with varying $\beta$ across the full spectrum of the parameter space, sampling multiple instances per level., annotate nodes with community labels from the initial lattice, and validate clustering coefficients.

**Independent Test**: Run `code/data_generation.py` and verify `data/raw/graphs.jsonl` contains a sufficient number of entries with correct $\beta$ distribution, measured clustering coefficients within theoretical bounds, and balanced class labels (<80% max).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T017 [P] [US1] Unit test for Watts-Strogatz generation logic in `tests/unit/test_generation.py`
- [X] T018 [P] [US1] Unit test for label annotation and class balance check in `tests/unit/test_generation.py`

### Implementation for User Story 1

- [X] T019 [US1] **Implement Graph Generation Pipeline**: Implement `code/data_generation.py` to:
 1. Read `utils.SAMPLE_SIZE` (expected 110) and generate exactly 10 graphs per $\beta$ level. **Explicit Levels**: Generate graphs for beta levels explicitly enumerated as: `[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]`.
 2. Derive community labels from the initial ring lattice (before rewiring).
 3. **Validation Loop**: Detect disconnected components. If a graph is disconnected, **immediately regenerate it** using the same seed and beta level until a valid connected graph is produced. **Validation Criteria**: A graph is valid if `nx.is_connected(graph)` is True AND `nx.transitivity(graph) > 0.0`.
 4. **Minimum Validity**: If the loop exceeds 1000 attempts for a specific beta level without success, log a WARNING, record the attempt count, and proceed with the valid subset (at least 1 graph) for that level. Do NOT crash the pipeline.
 5. Enforce class balance (<80% max).
 6. Save generated graphs to `data/raw/graphs.jsonl` with metadata (`id`, `beta`, `seed`, `clustering_coeff`, `edge_list`, `labels`).
 7. **Metadata Propagation**: Explicitly include `beta` and `node_count` in the metadata of every generated graph record to be propagated to training run files (T026/T027) as required by Constitution Principle VII.
 8. **Checksum**: Immediately after saving, generate a SHA-256 checksum and record it in `state/projects/PROJ-353-investigating-the-effectiveness-of-diffe.yaml` under `artifact_hashes`.
 9. **Verification**: Verify that `data/raw/graphs.jsonl` contains exactly 110 entries (or logs a warning if fewer due to topology constraints) and that the distribution is exactly 10 per beta level for valid levels. **Verification Step 9b**: Explicitly count the number of entries per beta level in the output file and assert the count is exactly 10 for each level, logging a failure if the distribution is unbalanced. **Dependency**: T004, T011, T005, T006a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Dual-Loss Training and Convergence Tracking (Priority: P2)

**Goal**: Train a multi-layer GCN on each graph using Cross-Entropy and InfoNCE. Track per-epoch loss/accuracy, record steps to convergence (high accuracy), and handle censored data (max epochs).

**Independent Test**: Run training on a single graph, verify two models saved, trajectory logs generated, and convergence steps recorded (or censored).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for Cross-Entropy training loop in `tests/unit/test_losses.py`
- [X] T024 [P] [US2] Unit test for InfoNCE + Linear Probe accuracy calculation in `tests/unit/test_losses.py`

### Implementation for User Story 2

**Note**: Code implementation is independent of US-1, but execution requires `data/raw/graphs.jsonl` (T019) to exist. This is a data-flow dependency, not a code-implementation dependency.

- [ ] T025 [S] [US2] **Implement Pipeline Logic**: Implement `code/main.py` pipeline logic to iterate over all graphs (using `utils.SAMPLE_SIZE`) and both loss types with sequential execution. **Constraint**: Must use `SAMPLE_SIZE` from `code/utils.py`. **Seed Management**: Reset random seed to a common value before training each loss type on the same graph to ensure fair comparison and control for weight initialization variance. **Dependency**: T019 (Script Implementation), T008, T009.
- [ ] T026 [US2] **Implement Cross-Entropy Training**: Implement `code/train.py` with training loop for Cross-Entropy loss, recording full per-epoch loss/accuracy arrays. **Output Schema**: Save per-run results to `data/processed/trajectories/training_run_{id}_ce.json` with top-level fields: `run_id`, `graph_id`, `loss_type`, `beta`, `node_count`, `convergence_status` ("converged" or "censored"), `steps_to_convergence`, `final_accuracy`, `trajectory` (list of `{epoch, loss, accuracy}`). **Verification**: Ensure `convergence_status` is recorded as "converged" if accuracy $\ge$ 0.90, or "censored" if max epochs reached. **Metadata**: Include `beta` and `node_count` from source graph in output JSON. **Dependency**: T008, T009, T004, T005, T007.
- [ ] T027 [US2] **Implement InfoNCE Training**: Implement `code/train.py` with training loop for InfoNCE loss. **Logic**: Train encoder for up to `MAX_EPOCHS`. **Convergence**: Record `steps_to_convergence` when accuracy $\ge$ `CONVERGENCE_THRESHOLD`. **Measurement**: Implement a linear probe for accuracy measurement as required by Spec US-2. **Censoring**: If `MAX_EPOCHS` reached without convergence, flag `convergence_status` as "censored". **Output Schema**: Save per-run results to `data/processed/trajectories/training_run_{id}_infonce.json` with top-level fields: `run_id`, `graph_id`, `loss_type`, `beta`, `node_count`, `convergence_status`, `steps_to_convergence`, `final_accuracy`, `trajectory`. **Dependency**: T008, T009, T004, T005, T007.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Interaction Analysis and Reporting (Priority: P3)

**Goal**: Perform Tobit Regression and Cox Proportional Hazards analysis to test interaction between $\beta$ and loss type on convergence steps. Apply multiple-comparison correction.

**Independent Test**: Run `code/analyze.py` on mock censored data and verify Tobit/Cox coefficients and interaction p-values are correctly computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for Tobit regression implementation in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Unit test for Cox PH implementation and interaction term extraction in `tests/unit/test_analysis.py`

### Implementation for User Story 3

**Note**: Code implementation is independent of US-2, but execution requires `data/processed/trajectories/` (T026, T027) to exist. This is a data-flow dependency, not a code-implementation dependency.

- [ ] T033 [US3] **Implement Data Aggregation**: Implement `code/analyze.py` to aggregate `data/processed/trajectories/` into a single DataFrame. **Logic**: Read files matching pattern `training_run_*.json`. **Aggregation**: Extract *scalar* fields (`steps_to_convergence`, `final_accuracy`, `max_loss`, `beta`, `loss_type`) to `data/processed/convergence_logs.csv`. **Constraint**: DO NOT include the full `trajectory` array in the CSV to avoid high cardinality; preserve trajectories only in the source JSON files. **Error Handling**: If source JSON files are missing or malformed, raise a clear error (do not fail silently). **Verification**: Verify that extracted scalar fields (e.g., `steps_to_convergence`) exactly match the values derivable from the full trajectory JSON files to ensure Single Source of Truth. **Verification**: Verify `data/processed/convergence_logs.csv` contains exactly 220 rows (110 graphs * 2 losses) with columns: `graph_id`, `loss_type`, `steps_to_convergence`, `final_accuracy`, `max_loss`, `beta`, `node_count`. **Dependency**: T026, T027 (Script Implementation), T005, T007.
- [ ] T034 [US3] **Implement Tobit Regression**: Implement Tobit Regression (`steps ~ loss_type * beta`) handling censored data (FR-005 correction). **Library**: Use `lifelines.TobitFitter`. **Constraint**: Do NOT implement a custom fallback; rely on the verified `lifelines` library for statistical correctness. **Formula**: `steps_to_convergence ~ C(loss_type) * beta`. **Censoring**: Set `lower=0` and `upper=utils.MAX_EPOCHS` to correctly handle censored observations (runs hitting max epochs without convergence). **Output**: Output `data/analysis_results.json` containing `tobit_interaction_p_value`. **Dependency**: T033.
- [ ] T035 [US3] **Implement Cox PH**: Implement Cox Proportional Hazards survival analysis for convergence "time". **Library**: Use `lifelines.CoxPHFitter`. **Formula**: `steps_to_convergence ~ C(loss_type) * beta`. **Censoring Logic**: Map the `convergence_status` from T026/T027 to an `event` column (1 if "converged", 0 if "censored"). **Explicit Requirement**: Rename the `convergence_status` column to `event` in the DataFrame before passing to `fit()` method as `event_col='event'` to correctly handle censored data. **Verification**: Ensure the `event` column correctly represents the censoring logic defined in FR-005 (accuracy < 0.90 within max epochs). **Output**: Output `data/analysis_results.json` containing `cox_interaction_p_value`. **Dependency**: T033.
- [ ] T036 [US3] **Extract Interaction Terms**: Extract the **interaction term's p-value** specifically from both models. **Tobit**: Extract the p-value for the coefficient corresponding to the interaction term (e.g., `C(loss_type)[T.1]:beta`). **Cox**: Extract the p-value for the interaction term hazard ratio. **Verification**: Ensure the specific interaction coefficient's p-value is extracted, not the model-level F-statistic or main effects. **Constraint**: Explicitly verify that main effects and correlation coefficients are NOT extracted for the final result, satisfying FR-008. **Verification Step**: Add an assertion that the final calculation only uses the extracted interaction p-values and explicitly ignores any main effect or correlation coefficient values. **Dependency**: T034, T035.
- [ ] T037 [US3] **Implement Bonferroni Correction**: Implement Bonferroni correction. **Logic**: Calculate `n_tests = 2`. Apply correction: `p_corr = p_raw * n_tests` to the **interaction term p-values only**. Determine significance: `is_significant = min(p_tobit_corr, p_cox_corr) < 0.05`. **Verification**: Assert that interaction terms were successfully extracted in T036 before applying the correction (raise error if null). **Dependency**: T036, T034, T035.
- [ ] T038 [US3] **Generate Analysis Results**: Generate `data/analysis_results.json` with corrected p-values, coefficients, and a boolean `is_significant` flag (SC-003). **Verification**: JSON file exists and `is_significant` is a boolean derived from Bonferroni-corrected p-values. **Dependency**: T037, T034, T035, T007.
- [ ] T039 [US3] **Generate Final Report**: Generate final report in `data/report.md` summarizing whether contrastive loss converges faster as $\beta$ increases. **Traceability**: Explicitly link the report's conclusion to the `is_significant` boolean in `data/analysis_results.json`. **Dependency**: T038, T034, T035, T007.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] **Implement Memory Profiling**: Create `code/profile_memory.py` to measure peak memory usage of `code/train.py` during a single run. **Verification**: Script outputs peak memory in MB. **Dependency**: T008, T009.
- [ ] T043b [S] **Analyze and Report Memory Usage**: Run `code/profile_memory.py` and generate `data/memory_report.md`. **Constraint**: Must verify peak memory < 7GB. **Dependency**: T043a.
- [ ] T044 [S] **Execute Full Pipeline & Validate Runtime**: Run the full pipeline (T019 -> T026/T027 -> T033-T039) and **assert total duration < 21600s (6 hours) **. If this fails, the build fails. **Note**: This task is an execution task that runs after all implementation tasks (T019, T026, T027, T033-T039) are complete and their respective data outputs have been generated. **Dependency**: T019 (Execution), T026 (Execution), T027 (Execution), T033 (Execution), T034 (Execution), T035 (Execution), T036 (Execution), T037 (Execution), T038 (Execution), T039 (Execution), T008, T009, T007.
- [ ] T045 [P] **Additional unit tests**: Add `tests/unit/test_analysis.py::test_bonferroni_correction` to verify p-value multiplication logic. **Dependency**: None.
- [ ] T040c [S] **Create Quickstart Documentation**: Create `quickstart.md` in `specs/001-investigating-the-effectiveness-of-diffe/`. **Action**: Write instructions to run the full pipeline. **Content Requirement**: Must include steps for graph generation, training, and analysis. **Constraint**: This is a Phase N deliverable as per `plan.md`. **Dependency**: T001, T019, T026, T027, T033, T008, T009, T007.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T004 (Utils) -> T011 (Verify) -> T005 (Data Model) -> T008/T009 (Code).
 - **Strict Serial**: T004, T011, T005, T008, T009.
 - **Documentation Ordering**: T040a (Research) is [S] and depends on T001. T040c (Quickstart) is [S] and depends on T001, T019, T026, T027, T033 (moved to Phase N).
- **User Stories (Phase 2+)**: All depend on Foundational completion.
 - **Implementation Independence**: US-1, US-2, and US-3 code can be written in parallel.
 - **Data Execution Prerequisites**:
 - US-2 execution requires US-1 data (T019) to exist.
 - US-3 execution requires US-2 data (T026/T027) to exist.
 - This is a data-flow dependency, not a code-implementation dependency.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational completion - No dependencies on other stories
- **User Story 2 (P2)**: Code implementation independent of US-1. Execution requires US-1 data.
- **User Story 3 (P3)**: Code implementation independent of US-2. Execution requires US-2 data.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001, T002).
 - T040a is [S] and cannot run in parallel with T001.
- T006a, T007 can run in parallel **after** T005 completes.
- T008, T009 can run in parallel **after** T005 and T004 complete.
- Once Foundational phase complete, all user story **code** can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Watts-Strogatz generation logic in tests/unit/test_generation.py"
Task: "Unit test for label annotation and class balance check in tests/unit/test_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_generation.py to generate N=110 graphs"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup & Research
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
 - **Strict Order**: Utils (T004) -> Verify (T011) -> Data Model (T005) -> Code (T008, T009).
3. Complete Phase 2: User Story 1
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

1. Team completes Setup + Foundational (strictly ordered) together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where noted)
- [S] tasks = strictly serial dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All training must run on CPU only (no CUDA, no bitsandbytes).
- **Constraint**: N is fixed at 110 (Spec FR-001), derived from power analysis.
- **Constraint**: Convergence threshold is set at a high level. Max epochs is set to a sufficiently high limit to ensure convergence. No loss-plateau early stopping.
- **Constraint**: Full per-epoch trajectory arrays must be stored in `data/processed/trajectories/` JSON files.
- **Constraint**: DO NOT modify `spec.md` directly.
- **Constraint**: InfoNCE accuracy MUST be measured via a linear probe as per Spec US-2.
- **Constraint**: `convergence_logs.csv` must contain only scalar fields, not full trajectory arrays.
- **Constraint**: Beta levels must be explicitly enumerated across the standard range from zero to one.
- **Constraint**: Seed must be reset between loss runs on the same graph.
- **Constraint**: Tobit censoring limits must be set to MAX_EPOCHS.
- **Constraint**: Bonferroni correction must derive factor from test count.
- **Constraint**: Beta metadata must be propagated to training run files.
- **Constraint**: Quickstart documentation must be generated after all user stories are complete.