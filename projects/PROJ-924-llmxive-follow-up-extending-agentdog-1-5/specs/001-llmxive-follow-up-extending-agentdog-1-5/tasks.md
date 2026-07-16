# Tasks: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Input**: Design documents from `/specs/001-llmxive-drift-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The specification explicitly requires statistical validation and contract tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`
- Paths shown below assume single project structure per `plan.md`

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

- [ ] T001 Create project structure per `plan.md` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes
- [ ] T005a [P] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks
- [X] T005b [P] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`
- [X] T005c [P] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US-01 testing
- [ ] T005d [P] Implement `fetch_taxonomy` function in `data_loader.py` to download the AgentDoG 1.5 taxonomy definition from the verified Hugging Face dataset source (e.g., `agentdog/taxonomy-v1.5` or the specific URL provided in `plan.md`) and save to `data/raw/taxonomy.json`; ensure this task runs before T008
- [ ] T006 [P] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading
- [ ] T007 Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking
- [ ] T008a [P] Implement `taxonomy_builder.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to generate centroid embeddings using `all-MiniLM-L6-v2` (CPU-first, batched to fit <100MB RAM) using the taxonomy fetched by T005d (input: `data/raw/taxonomy.json`)
- [ ] T008b [P] Implement runtime memory monitoring logic in `taxonomy_builder.py` using `tracemalloc` to profile centroid generation and enforce a strict peak RAM limit; raise an exception if exceeded (input: output of T008a)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Drift Scoring (Priority: P1) 🎯 MVP

**Goal**: Implement the core drift scoring mechanism to compute cosine distances between logs and taxonomy centroids.

**Independent Test**: The system can be tested by feeding a static JSON file of known benign and novel attack logs, verifying that the "Drift Score" distribution is statistically distinguishable (p < 0.05, Cohen's d ≥ 0.5). *Note: Full statistical validation against human labels is deferred to Phase 4.*

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for `drift_scoring.py` output schema: implement `test_drift_score_schema_matches_drift_result_yaml` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_contracts.py` validating against `contracts/drift_result.schema.yaml`
- [ ] T011 [P] [US1] Unit test for empty/whitespace log handling: implement `test_empty_log_returns_drift_score_1_0` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_drift_scoring.py` using `data/test_empty_log.json` and asserting `result['drift_score'] == 1.0`
- [ ] T012 [P] [US1] Integration test for batch processing memory limits: implement `test_batch_memory_limit_4gb` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/integration/test_end_to_end.py` using a dataset of logs and asserting `peak_memory < 4GB`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `compute_cosine_distance` function in `drift_scoring.py` to calculate minimum cosine distance to centroids
- [ ] T013b [US1] Implement `batch_process_logs` function in `drift_scoring.py` with memory limits to handle large datasets within 7GB RAM
- [ ] T014 [US1] Add logic to handle empty/whitespace logs by assigning a Drift Score of a normalized magnitude and explicitly adding a 'review_flag' column to the output CSV set to 'true' for these records, as per Edge Cases
- [ ] T015 [US1] Implement batch processing logic in `drift_scoring.py` to handle large datasets within 7GB RAM limits (Note: Merged into T013b; T015 is kept for historical tracking of memory constraints)
- [ ] T016 [US1] Create `main.py` orchestration script in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run the full scoring pipeline including export to `data/processed/drift_scores.csv`
- [ ] T017 [US1] Export results to CSV (`data/processed/drift_scores.csv`) with columns: `log_id`, `drift_score`, `review_flag`
- [ ] T018a [US1] [MOVED TO PHASE 4] Implement statistical validation logic in `validation.py` to calculate p-values and Cohen's d for US-01 Independent Test verification (DEPENDS ON T021d)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (excluding human validation)

---

## Phase 4: User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**Goal**: Stratify logs for human annotation and perform statistical validation against ground truth.

**Independent Test**: The system can be tested by generating stratified CSVs and verifying the output format matches annotation requirements (log_id, text, label) and statistical tests (Logistic Regression, Mann-Whitney U) run correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for stratification logic (top/bottom percentiles) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_validation.py`
- [ ] T019 [P] [US2] Unit test for Kappa statistic calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_kappa.py`
- [ ] T020 [P] [US2] Unit test for blind export (removing drift scores) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_blind.py`

### Implementation for User Story 2

- [ ] T021a [US2] Implement `ingest_human_annotations` function in `validation.py` to read annotated CSVs (from T021d), merge with drift scores, and output `data/processed/merged_annotations.csv`
- [ ] T021b [US2] Implement `validation.py` logic to perform logistic regression (using `statsmodels.formula.api.logit`) and Mann-Whitney U tests on `data/processed/merged_annotations.csv`, outputting `data/processed/validation_stats.json`
- [ ] T021c [US2] Implement `prepare_annotation_interface` function in `annotator_interface.py` to generate a CSV template ready for human upload (columns: `log_id`, `text`, `drift_score` for reference ONLY, but `drift_score` must be removed before export) based on stratified bins from T023a
- [ ] T021d [US2] Implement `ingest_human_annotations` logic to load multiple distinct human annotation CSVs (e.g., `human_annot_1.csv`, `human_annot_2.csv`, `human_annot_3.csv`) provided by the user/runner. This task MUST fail if fewer than a minimum required number of distinct human annotation files are provided., as Kappa requires multiple annotators.
- [ ] T022 [US2] Implement `export_stratified_bins` function in `annotator_interface.py` to export pre-calculated bins as blinded CSVs for annotation (using T025a logic)
- [ ] T023 [US2] Implement logic to handle stratification parameters (deferred percentiles) via `config.py`
- [ ] T023a [US2] Implement `stratify_logs` function in `annotator_interface.py` to calculate indices, sort, slice, and bin logs based on drift scores and config parameters
- [ ] T024 [US2] Implement inter-annotator agreement (Kappa) calculation in `validation.py` using `sklearn.metrics.cohen_kappa_score` on the merged annotations from T021d (multiple distinct human files), with verification step `assert kappa > 0.6`. If only one human file is present, skip Kappa and log a warning.
- [ ] T025 [US2] Verify output CSVs contain required columns: `log_id`, `text`, `label` (blinded) and no `drift_score` column
- [ ] T025a [US2] Implement blinding logic (remove `drift_score` column) in `annotator_interface.py` prior to export for human review

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (with human input)

---

## Phase 5: User Story 3 - Baseline Performance Comparison (Priority: P3)

**Goal**: Compare Drift Score detector against a standard zero-shot LLM classifier (local).

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs and verifying the output includes AUC-ROC and inference time metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for AUC-ROC calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`
- [ ] T027 [P] [US3] Unit test for inference time measurement in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `comparison.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a zero-shot LLM classifier using a local open-weight model (e.g., `TinyLlama/TinyLlamaB-Chat-v1.0` via `transformers`) on `data/processed/merged_annotations.csv`, comparing with Drift Scores. NO external API calls (Constitution Principle I).
- [ ] T029 [US3] Implement bootstrap iteration logic for AUC-ROC stability
- [ ] T029a [US3] Implement deterministic inference caching mechanism in `comparison.py` for local model outputs to ensure reproducibility (Constitution Principle I)
- [ ] T030 [US3] Generate comparison report containing AUC-ROC for both methods and average inference time per log
- [ ] T031 [US3] Add logic to flag "computationally efficient alternative" if |AUC_drift - AUC_llm| ≤ 0.10

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` (quickstart.md, data-model.md)
- [ ] T033 Code cleanup and refactoring in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T034a [P] Implement `benchmark_performance.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a large-scale log benchmark and assert completion time ≤ 30 minutes (SC-003)
- [ ] T034b [P] Integrate `benchmark_performance.py` into GitHub Actions workflow to fail the build if the 30-minute threshold is exceeded
- [ ] T035 [P] Additional unit tests for edge cases (leetspeak, obfuscation) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/`
- [ ] T036 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T018a which is moved to Phase 4)
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for drift_scoring.py output schema in tests/contract/test_contracts.py"
Task: "Unit test for empty/whitespace log handling in tests/unit/test_drift_scoring.py"

# Launch all models for User Story 1 together:
Task: "Implement drift_scoring.py in code/drift_scoring.py"
Task: "Add logic to handle empty/whitespace logs in code/drift_scoring.py"
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
- **Data Hygiene**: Ensure `data_loader.py` fails loudly on real data fetch errors; never use synthetic fallbacks.
- **Memory**: Ensure batch processing in `drift_scoring.py` respects 7GB RAM limits.
- **Compute**: Use `all-MiniLM-L6-v2` on CPU for drift scoring; use local `TinyLlama` for baseline comparison (NO external API calls).
- **Reproducibility**: All inference (including baseline comparison) must use local models or cached data; no external API calls.
- **Taxonomy Fetch**: Ensure T005d successfully retrieves the taxonomy before T008 runs.
- **Ground Truth**: Ensure T021d (human ingestion) runs before T024 (Kappa) and T018a (US-01 stats).
- **Edge Cases**: Ensure T014 explicitly flags empty logs for review.
- **Performance**: Ensure T034a and T034b enforce the 30-minute limit.
- **Blinding**: Ensure T025a explicitly removes `drift_score` before export.