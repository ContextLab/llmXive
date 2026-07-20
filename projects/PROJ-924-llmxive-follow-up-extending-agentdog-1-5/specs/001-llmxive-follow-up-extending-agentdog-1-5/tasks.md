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

- [ ] T001a Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T001b Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/` <!-- FAILED: unspecified -->
- [ ] T001c Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/raw/`
- [ ] T001d Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/`
- [ ] T001e Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/test/`
- [ ] T001f Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/specs/`
- [ ] T001g Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/docs/`
- [ ] T001h Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/specs/001-llmxive-drift-detection/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate, openai)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/` (create `.ruff.toml` and `pyproject.toml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes
- [ ] T005a [P] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks
- [X] T005b [P] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`
- [ ] T005c [P] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US-01 testing; ensure this file contains `log_id`, `text`, and `label` columns
- [X] T005d [P] Implement `fetch_taxonomy` function in `data_loader.py` to download the OWASP Top LLM taxonomy from Hugging Face dataset `OWASP/Top-LLM` (revision `main`), save to `data/raw/taxonomy_owasp.json`; ensure this task runs before T005-map
- [ ] T005-map [P] Implement `map_taxonomy` function in `data_loader.py` to map OWASP taxonomy categories to the AgentDoG 1.5 safety taxonomy schema; validate that each AgentDoG category has a corresponding OWASP mapping; save to `data/raw/taxonomy_agentdog.json`; this task MUST fail if mapping validation fails
- [ ] T006 [P] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading
- [ ] T007 [P] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking
- [X] T008a [P] Implement `taxonomy_builder.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to generate centroid embeddings using `all-MiniLM-L6-v2` (CPU-first, batched to fit <100MB RAM) using the taxonomy mapped by T005-map (input: `data/raw/taxonomy_agentdog.json`)
- [ ] T008b [US2] Implement runtime memory monitoring logic in `taxonomy_builder.py` using `tracemalloc` to profile centroid generation and enforce a strict peak RAM limit of < 7GB; raise an exception if exceeded (DEPENDS ON T008a execution)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Drift Scoring (Priority: P1) 🎯 MVP

**Goal**: Implement the core drift scoring mechanism to compute cosine distances between logs and taxonomy centroids.

**Independent Test**: The system can be tested by feeding a static JSON file of a sufficient number of known benign logs and a comparable number of known novel attack logs (where novelty is defined by human annotation from the US-02 process, not merely by absence from the taxonomy) and verifying that the "Drift Score" distribution is statistically distinguishable between the two groups with p < 0.05 and an effect size (Cohen's d) ≥ 0.5. **CRITICAL**: Task T018b generates a synthetic ground truth fixture to satisfy the 'Independent Test' requirement for US-01 without requiring US-02 completion. Task T018c performs the final validation against human-annotated ground truth from US-02. Static fixtures from T018b are sufficient for the independent test; T018c is reserved for the final validation against real human judgment.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Contract test for `drift_scoring.py` output schema: implement `test_drift_score_schema_matches_drift_result_yaml` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_contracts.py` validating against `specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml` (from T009)
- [X] T011 [P] [US1] Unit test for empty/whitespace log handling: implement `test_empty_log_returns_drift_score_2_0` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_drift_scoring.py` using `data/test_empty_log.json` and asserting `result['drift_score'] == 2.0`
- [X] T012 [P] [US1] Integration test for batch processing memory limits: implement `test_batch_memory_limit_7gb` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/integration/test_end_to_end.py` using a dataset of logs and asserting `peak_memory < 7GB`

### Implementation for User Story 1

- [ ] T013a [US1] Implement `compute_cosine_distance` function in `drift_scoring.py` to calculate minimum cosine distance to centroids
- [ ] T013b [US1] Implement `batch_process_logs` function in `drift_scoring.py` with memory limits to handle large datasets within 7GB RAM
- [ ] T014 [US1] Add logic to handle empty/whitespace logs by explicitly assigning a Drift Score representing the maximum theoretical cosine distance and adding a 'review_flag' column to the output CSV set to 'true' for these records, as per Edge Cases
- [ ] T017 [US1] Implement `export_results` function in `drift_scoring.py` to export results to CSV (`data/processed/drift_scores.csv`) with columns: `log_id`, `drift_score`, `review_flag`; verify file is generated with correct columns before marking task complete
- [ ] T016 [US1] Create `main.py` orchestration script in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run the full scoring pipeline including export (DEPENDS ON T017)
- [ ] T018b [US1] Implement `generate_synthetic_ground_truth` function in `validation.py` to create `data/processed/synthetic_ground_truth.json` with 'benign' and 'novel attack' labels for independent US-01 testing; this task MUST run before T018c
- [ ] T018c [US1] Implement statistical validation logic in `validation.py` to calculate p-values and Cohen's d for US-01 Independent Test verification using human-annotated ground truth from US-02 (input: `data/processed/merged_annotations.csv`, output: `data/processed/us01_stats.json`); ensure `data/processed/us01_stats.json` is generated. **Note**: This task depends on US-02 completion and is NOT independent. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (T018b for synthetic test, T018c for final human validation)

---

## Phase 4: User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**Goal**: Stratify logs for human annotation and perform statistical validation against ground truth.

**Independent Test**: The system can be tested by generating stratified CSVs and verifying the output format matches annotation requirements (log_id, text, label) and statistical tests (Logistic Regression, Mann-Whitney U) run correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for stratification logic (top/bottom percentiles) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_validation.py`
- [ ] T019 [P] [US2] Unit test for Kappa statistic calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_kappa.py`
- [ ] T020 [P] [US2] Unit test for blind export (removing drift scores) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_blind.py`

### Implementation for User Story 2

- [ ] T021d [US2] Implement `ingest_human_annotations` function in `validation.py` to load annotation CSVs from `data/raw/human_annotations/` (wildcard `*.csv`). Use `glob` to dynamically discover files. If fewer than 2 distinct files are found, raise an error. If 2 or more are found but fewer than 3, log a warning but proceed. The system must re-run ingestion if new files are added (iterative). (input: `data/raw/human_annotations/*.csv`, output: `data/raw/validated_annotations/` directory with individual files)
- [ ] T021a [US2] Implement `merge_annotations` logic in `validation.py` to read the validated annotated CSVs from T021d, merge with drift scores, and output `data/processed/merged_annotations.csv` (DEPENDS ON T021d)
- [ ] T021b [US2] Implement `validation.py` logic to perform logistic regression (using `statsmodels.formula.api.logit`) and Mann-Whitney U tests on `data/processed/merged_annotations.csv`, outputting `data/processed/validation_stats.json`
- [ ] T021c [US2] Implement `prepare_annotation_interface` function in `annotator_interface.py` to generate a CSV template ready for human upload (columns: `log_id`, `text`, `drift_score` for reference ONLY, but `drift_score` must be removed before export) based on stratified bins from T023a
- [ ] T021e [US2] Generate mock annotation fixtures for testing purposes (input: `data/processed/drift_scores.csv`, output: `data/test/mock_annot_1.csv`, `data/test/mock_annot_2.csv`, `data/test/mock_annot_3.csv`)
- [ ] T022 [US2] Implement `export_stratified_bins` function in `annotator_interface.py` to export pre-calculated bins as blinded CSVs for annotation (using T025a logic)
- [ ] T023 [US2] Implement logic to handle stratification parameters (deferred percentiles) via `config.py`
- [ ] T023a [US2] Implement `stratify_logs` function in `annotator_interface.py` to calculate indices, sort, slice, and bin logs based on drift scores and config parameters
- [ ] T024 [US2] Implement inter-annotator agreement (Kappa) calculation in `validation.py` using `sklearn.metrics.cohen_kappa_score` on the merged annotations from T021a (input: `data/processed/merged_annotations.csv`). **Threshold**: Kappa > 0.6 indicates substantial agreement. If Kappa < 0.6, log a warning, set `confidence_level` to 'low' in `data/processed/kappa_stats.json`, but proceed with the data. Do NOT fail the system. (DEPENDS ON T021a)
- [ ] T025 [US2] Verify output CSVs contain required columns: `log_id`, `text`, `label` (blinded) and no `drift_score` column
- [ ] T025a [US2] Implement blinding logic (remove `drift_score` column) in `annotator_interface.py` prior to export for human review

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (with human input)

---

## Phase 5: User Story 3 - Baseline Performance Comparison (Priority: P3)

**Goal**: Compare Drift Score detector against a standard zero-shot LLM classifier (local model or API).

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs. where both the Drift Score and a zero-shot LLM inference (using a local CPU-friendly model by default, or gpt-4o-mini if API key is provided) are available, and verifying the output includes AUC-ROC and inference time metrics against the human-annotated ground truth from US-02.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for AUC-ROC calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`
- [ ] T027 [P] [US3] Unit test for inference time measurement in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`

### Implementation for User Story 3

- [ ] T028-gpt [US3] Implement `comparison.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a zero-shot LLM classifier using a large language model (via OpenAI API) on `data/processed/merged_annotations.csv`, comparing with Drift Scores. The task MUST use the `gpt-4o-mini` model with a system prompt for attack detection. Implement deterministic inference caching mechanism to ensure reproducibility (Constitution Principle I).
- [ ] T028-local [US3] Implement `comparison.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a zero-shot LLM classifier using a **local CPU-friendly model** (`facebook/bart-large-mnli`) on `data/processed/merged_annotations.csv`, comparing with Drift Scores. The Drift Score method remains CPU-only, and the baseline MUST also be CPU-only to satisfy Constitution Principle I (Reproducibility) and Principle VII (Resource-Constrained Integrity). *Note: This task provides a CPU-only baseline for reproducibility comparison, while T028-gpt provides the Spec US-03 required baseline.*
- [ ] T029 [US3] Implement bootstrap iteration logic for AUC-ROC stability
- [ ] T029a [US3] Implement deterministic inference caching mechanism in `comparison.py` for local model outputs to ensure reproducibility (Constitution Principle I)
- [ ] T030 [US3] Generate comparison report containing AUC-ROC for both methods and average inference time per log
- [ ] T031 [US3] Add logic to flag "computationally efficient alternative" if |AUC_drift - AUC_llm| ≤ 0.10

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions
- [ ] T032b [P] Update `docs/data-model.md` with new data model fields and schema definitions
- [ ] T033a [P] Run black and ruff on `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to enforce formatting and linting
- [ ] T033b [P] Remove unused imports and variables from `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T034a [P] Implement `benchmark_performance.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a large-scale log benchmark and assert completion time ≤ 30 minutes (SC-003)
- [ ] T034b [P] Integrate `benchmark_performance.py` into GitHub Actions workflow to fail the build if the 30-minute threshold is exceeded
- [ ] T035 [P] Additional unit tests for edge cases (leetspeak, obfuscation) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/`
- [ ] T036 Run `quickstart.md` validation to ensure reproducibility
- [ ] T037 [P] **Validation Handoff**: Implement logic in `validation.py` to replace `data/processed/mock_ground_truth.csv` with `data/processed/merged_annotations.csv` for the final US-01 validation run. Ensure T018a is executed with real data and T018c is marked as MVP-only. (DEPENDS ON T021a)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T018c which is now in Phase 3 and depends on US-02)
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T008b)
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
3. Complete Phase 3: User Story 1 (including T018b for independent testing, T018c for final validation)
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
- **Compute**: Use `all-MiniLM-L6-v2` on CPU for drift scoring; use `gpt-4o-mini` for baseline comparison (as per Spec US-03) and `facebook/bart-large-mnli` for CPU-only reproducibility comparison.
- **Reproducibility**: All inference (including baseline comparison) must use local models or cached data; no external API calls for Drift Score or Baseline.
- **Taxonomy Fetch**: Ensure T005d successfully retrieves the taxonomy from the canonical source (OWASP/Top-LLM) before T005-map runs.
- **Taxonomy Mapping**: Ensure T005-map successfully maps OWASP taxonomy to AgentDoG 1.5 schema before T008a runs.
- **Ground Truth**: Ensure T018b (synthetic) runs before T018c (final validation) and T021d (human ingestion) runs before T024 (Kappa) and T018c (US-01 stats) is complete.
- **Edge Cases**: Ensure T014 explicitly flags empty logs with Drift Score 2.0.
- **Performance**: Ensure T034a and T034b enforce the 30-minute limit.
- **Blinding**: Ensure T025a explicitly removes `drift_score` before export.
- **RAM Limit**: Ensure T008b enforces a strict peak RAM limit of < 7GB.
- **US-02 Threshold**: Ensure T024 explicitly defines Kappa > 0.6 as the threshold for substantial agreement and handles <0.6 gracefully.
- **Ordering**: Ensure T017 precedes T016, and T021d precedes T021a which precedes T024.