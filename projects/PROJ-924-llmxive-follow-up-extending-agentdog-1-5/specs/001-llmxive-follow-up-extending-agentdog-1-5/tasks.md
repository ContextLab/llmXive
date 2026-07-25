# Tasks: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Input**: Design documents from `/specs/001-llmxive-drift-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The specification explicitly requires statistical validation and contract tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on specific prior task in same phase)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T002 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`
- [ ] T003 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/raw/`
- [ ] T004 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/processed/`
- [ ] T005 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/test/`
- [ ] T006 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/specs/`
- [ ] T007 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/docs/`
- [ ] T008 [P] Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/specs/001-llmxive-drift-detection/`
- [X] T009 Initialize Python 3.11 project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate)
- [ ] T010 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/` (create `.ruff.toml` and `pyproject.toml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [P] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes
- [ ] T012a [P] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks
- [X] T012b [P] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`
- [X] T012c [P] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US-01 testing; ensure this file contains `log_id`, `text`, and `label` columns
- [X] T012d [P] Implement `fetch_taxonomy` function in `data_loader.py` to download the OWASP Top LLM taxonomy from Hugging Face dataset `OWASP/Top-LLM` (revision `main`), save to `data/raw/taxonomy_owasp.json`; ensure this task runs before T013-map
- [ ] T012e [P] Generate REAL human-annotated ground truth fixture from AdvBench/OWASP labels to `data/test/real_ground_truth_fixture.json` for US-01 independent MVP testing; ensure this file contains `log_id`, `text`, `label` (benign/attack) and is derived from REAL data, NOT synthetic generation (DEPENDS ON T012a)
- [ ] T013-map [P] Implement `map_taxonomy` function in `data_loader.py` to map OWASP taxonomy categories to the AgentDoG 1.5 safety taxonomy schema; validate that each AgentDoG category has a corresponding OWASP mapping; save to `data/raw/taxonomy_agentdog.json`; **IF mapping validation fails, raise a LoudFailureError with a specific error code and artifact path, halting the pipeline immediately**
- [ ] T014 [P] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading
- [ ] T015 [P] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking
- [X] T016a [P] Implement `taxonomy_builder.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to generate centroid embeddings using `all-MiniLM-L6-v2` (CPU-first, batched to fit <100MB RAM) using the taxonomy mapped by T013-map (input: `data/raw/taxonomy_agentdog.json`)
- [ ] T016b [S] Implement runtime memory monitoring logic in `taxonomy_builder.py` using `tracemalloc` to profile centroid generation and enforce a strict peak RAM limit of < 7GB; raise an exception if exceeded (DEPENDS ON T016a execution)
- [ ] T016c [P] Save the generated taxonomy with embeddings to `data/processed/taxonomy_centroids.json` as a persistent artifact for reproducibility (input: output of T016a)
- [ ] T017 [P] Implement `handle_taxonomy_failure` logic in `data_loader.py` to generate `data/raw/taxonomy_mapping_failed.json` containing the error details and mapping state if T013-map fails; raise `LoudFailureError` with exit code 1 to halt pipeline if mapping is impossible (DEPENDS ON T013-map)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Drift Scoring (Priority: P1) 🎯 MVP

**Goal**: Implement the core drift scoring mechanism to compute cosine distances between logs and taxonomy centroids.

**Independent Test**: The system can be tested by feeding a static JSON file of a sufficient number of known benign logs and a comparable number of known novel attack logs (where novelty is defined by human annotation from the US-02 process) and verifying that the "Drift Score" distribution is statistically distinguishable between the two groups with p < 0.05 and an effect size (Cohen's d) ≥ 0.5. **CRITICAL**: Statistical validation (T025) requires REAL human-annotated data. For MVP independent testing, use the REAL fixture from T012e. No synthetic data is used for statistical validation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T018 [P] [US1] Contract test for `drift_scoring.py` output schema: implement `test_drift_score_schema_matches_drift_result_yaml` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_contracts.py` validating against `specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml` (from T009)
- [X] T019 [P] [US1] Unit test for empty/whitespace log handling: implement `test_empty_log_returns_drift_score_2_0` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_drift_scoring.py` using `data/test_empty_log.json` and asserting `result['drift_score'] == 2.0` using the formula `1 - cosine_similarity(L2_normalized_vectors)`
- [X] T020 [P] [US1] Integration test for batch processing memory limits: implement `test_batch_memory_limit_7gb` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/integration/test_end_to_end.py` using a dataset of logs and asserting `peak_memory < 7GB`

### Implementation for User Story 1

- [~] T021a [US1] Implement `compute_cosine_distance` function in `drift_scoring.py` to calculate minimum cosine distance to centroids using the formula: `1 - cosine_similarity(L2_normalized_vectors)` to guarantee max distance of 2.0 for orthogonal vectors
- [~] T021b [US1] Implement `batch_process_logs` function in `drift_scoring.py` with memory limits to handle large datasets within 7GB RAM
- [~] T022 [US1] Add logic to handle empty/whitespace logs by explicitly assigning a Drift Score indicative of a moderate level of deviation (based on formula in T021a: `1 - cosine_similarity(L2_normalized_vectors)`) and adding a 'review_flag' column to the output CSV set to 'true' for these records, as per Edge Cases
- [ ] T023 [US1] Implement `export_results` function in `drift_scoring.py` to export results to CSV (`data/processed/drift_scores.csv`) with columns: `log_id`, `drift_score`, `review_flag`; verify file is generated with correct columns before marking task complete
- [~] T024 [US1] Create `main.py` orchestration script in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run the full scoring pipeline including export (DEPENDS ON T023)
- [ ] T025 [S] [US1] Implement statistical validation logic in `validation.py` to calculate p-values and Cohen's d for US-01 validation using REAL human-annotated ground truth: **MVP** uses `data/test/real_ground_truth_fixture.json` (T012e); **Final** uses `data/processed/merged_annotations.csv` (T031b); output: `data/processed/us01_final_stats.json` (DEPENDS ON T012e OR T031b)
- [~] T026 [S] [US1] Implement final validation logic in `validation.py` to confirm US-01 acceptance criteria are met using the output from T025; **BLOCKS project advancement if T025 is skipped or fails** (DEPENDS ON T025)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (with US-02 data for final validation)

---

## Phase 4: User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**Goal**: Stratify logs for human annotation and perform statistical validation against ground truth.

**Independent Test**: The system can be tested by generating stratified CSVs and verifying the output format matches annotation requirements (log_id, text, label) and statistical tests (Logistic Regression, Mann-Whitney U) run correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US2] Unit test for stratification logic (top/bottom percentiles) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_validation.py`
- [~] T028 [P] [US2] Unit test for Kappa statistic calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_kappa.py`
- [ ] T029 [P] [US2] Unit test for blind export (removing drift scores) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_blind.py`

### Implementation for User Story 2

- [ ] T030a [US2] Implement `stratify_logs` function in `annotator_interface.py` to calculate indices, sort, slice, and bin logs based on drift scores and config parameters (input: `data/processed/drift_scores.csv`)
- [ ] T031a [US2] Implement blinding logic (remove `drift_score` column) in `annotator_interface.py` prior to export for human review
- [ ] T030b [US2] Implement `generate_blinded_annotation_files` function in `annotator_interface.py` to combine stratification (T030a) and blinding (T031a) logic to generate final blinded CSVs for human annotators; save to `data/processed/blinded_annotation_batches/*.csv` (DEPENDS ON T030a AND T031a)
- [ ] T032a [US2] Implement `ingest_human_annotations` function in `validation.py` to load annotation CSVs from `data/processed/blinded_annotation_batches/` (wildcard `*.csv`). Use `glob` to dynamically discover files. **Raise a ValueError if fewer than a sufficient number of distinct files are found. (matching Constitution Principle VI).** (input: `data/processed/blinded_annotation_batches/*.csv`, output: `data/raw/validated_annotations/` directory with individual files)
- [ ] T031b [US2] Implement `merge_annotations` logic in `validation.py` to read the validated annotated CSVs from T032a, merge with drift scores, and output `data/processed/merged_annotations.csv` (DEPENDS ON T032a)
- [ ] T031c [US2] Implement `validation.py` logic to perform logistic regression (using `statsmodels.formula.api.logit`) and Mann-Whitney U tests on `data/processed/merged_annotations.csv`, outputting `data/processed/validation_stats.json`
- [ ] T031d [US2] Implement `prepare_annotation_interface` function in `annotator_interface.py` to generate a CSV template ready for human upload (columns: `log_id`, `text`, `drift_score` for reference ONLY, but `drift_score` must be removed before export) based on stratified bins from T030a (DEPENDS ON T030a)
- [ ] T032b [US2] Generate mock annotation fixtures for testing purposes (input: `data/processed/drift_scores.csv`, output: `data/test/mock_annot_1.csv`, `data/test/mock_annot_2.csv`, `data/test/mock_annot_3.csv`)
- [ ] T033 [US2] Implement `export_stratified_bins` function in `annotator_interface.py` to export pre-calculated bins as blinded CSVs for annotation (using T031a logic) (DEPENDS ON T030a AND T031a)
- [ ] T034 [US2] Implement logic to handle stratification parameters (deferred percentiles) via `config.py`
- [ ] T035 [US2] Implement inter-annotator agreement (Kappa) calculation in `validation.py` using `sklearn.metrics.cohen_kappa_score` on the merged annotations from T031b (input: `data/processed/merged_annotations.csv`). **Threshold**: Kappa > 0.6 indicates substantial agreement. **IF Kappa < 0.6, raise a ValueError, write 'kappa_failed.json' artifact with error details, update 'state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml' to set 'current_stage: unproven', and DO NOT proceed with data.** (DEPENDS ON T031b)
- [ ] T036 [US2] Verify output CSVs contain required columns: `log_id`, `text`, `label` (blinded) and no `drift_score` column

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (with human input)

---

## Phase 5: User Story 3 - Baseline Performance Comparison (Priority: P3)

**Goal**: Compare Drift Score detector against a standard zero-shot LLM classifier (local model).

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs. where both the Drift Score and a zero-shot LLM inference (using a local CPU-friendly model) are available, and verifying the output includes AUC-ROC and inference time metrics against the human-annotated ground truth from US-02.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US3] Unit test for AUC-ROC calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`
- [ ] T038 [P] [US3] Unit test for inference time measurement in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`

### Implementation for User Story 3

- [ ] T039a [P] [US3] Implement `validate_proxy_model` function in `comparison.py` to run a preliminary statistical test on a small subset to verify `facebook/bart-large-mnli` performance is a **sufficient proxy** for the 'computationally efficient alternative' claim by comparing its AUC to a cached 'gpt-4o-mini' benchmark if available; **FAILS if proxy validation fails**
- [ ] T039-local [S] [US3] Implement `comparison.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a zero-shot LLM classifier using a **local CPU-friendly model** (`facebook/bart-large-mnli`) on `data/processed/merged_annotations.csv`, comparing with Drift Scores. **Authorized Narrowing**: Substitute `gpt-4o-mini` with `facebook/bart-large-mnli` to satisfy Constitution Principle VII (Resource-Constrained Integrity). A validation report (T039a) must pass before this task proceeds. The Drift Score method remains CPU-only, and the baseline MUST also be CPU-only to satisfy Constitution Principle I (Reproducibility) and Principle VII. **Constraint**: NO external API calls (e.g., OpenAI) are permitted for this baseline. (DEPENDS ON T039a)
- [ ] T040 [US3] Implement bootstrap iteration logic for AUC-ROC stability
- [ ] T040a [US3] Implement deterministic inference caching mechanism in `comparison.py` for local model outputs to ensure reproducibility (Constitution Principle I)
- [ ] T041 [US3] Generate comparison report containing AUC-ROC for both methods and average inference time per log (DEPENDS ON T039-local AND T035 (Kappa check passed))
- [ ] T041a [S] [US3] Implement logic to block T041 if 'state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml' indicates 'current_stage: unproven' (DEPENDS ON T035)
- [ ] T042 [US3] Add logic to flag "computationally efficient alternative" if |AUC_drift - AUC_llm| ≤ 0.10

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions
- [ ] T043b [P] Update `docs/data-model.md` with new data model fields and schema definitions
- [ ] T044a [P] Run black and ruff on `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to enforce formatting and linting
- [ ] T044b [P] Remove unused imports and variables from `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T045a [P] Implement `benchmark_performance.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a large-scale log benchmark and assert completion time ≤ 30 minutes (SC-003)
- [ ] T045b [P] Integrate `benchmark_performance.py` into GitHub Actions workflow to fail the build if the 30-minute threshold is exceeded
- [ ] T046 [P] Additional unit tests for edge cases (leetspeak, obfuscation) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/`
- [ ] T047 Run `quickstart.md` validation to ensure reproducibility
- [ ] T048 [P] **Validation Handoff**: Implement logic in `validation.py` to replace `data/processed/mock_ground_truth.csv` with `data/processed/merged_annotations.csv` for the final US-01 validation run. Ensure T025 is executed with real data and T026 is marked as MVP-only. (DEPENDS ON T031b)
- [ ] T049 [P] **Full System Orchestration**: Implement `run_full_pipeline.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to orchestrate US-01, US-02, and US-03 pipelines in the correct dependency order (DEPENDS ON T024, T030b, T039-local)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T025/T026 which depend on US-02 or T012e)
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T016b)
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
3. Complete Phase 3: User Story 1 (including T025 for real validation using T012e fixture, T026 for final check)
4. **STOP and VALIDATE**: Test User Story 1 independently (requires US-02 data for full validation, but T012e allows MVP testing)
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
- [S] tasks = sequential (depends on specific prior task)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: Ensure `data_loader.py` fails loudly on real data fetch errors; never use synthetic fallbacks.
- **Memory**: Ensure batch processing in `drift_scoring.py` respects 7GB RAM limits.
- **Compute**: Use `all-MiniLM-L6-v2` on CPU for drift scoring; use `facebook/bart-large-mnli` for CPU-only reproducibility comparison (authorized narrowing).
- **Reproducibility**: All inference (including baseline comparison) must use local models or cached data; no external API calls for Drift Score or Baseline.
- **Taxonomy Fetch**: Ensure T012d successfully retrieves the taxonomy from the canonical source (OWASP/Top-LLM) before T013-map runs.
- **Taxonomy Mapping**: Ensure T013-map successfully maps OWASP taxonomy to AgentDoG 1.5 schema before T016a runs; fails loudly if mapping fails.
- **Ground Truth**: T025 requires REAL human data from T012e (MVP) or T031b (Final); T032a requires 3 files.
- **Edge Cases**: Ensure T022 explicitly flags empty logs with Drift Score 2.0 (formula defined in T021a).
- **Performance**: Ensure T045a and T045b enforce a time limit.
- **Blinding**: Ensure T031a explicitly removes `drift_score` before export.
- **RAM Limit**: Ensure T016b enforces a strict peak RAM limit of < 7GB.
- **US-02 Threshold**: Ensure T035 explicitly defines Kappa > 0.6 as the threshold for substantial agreement and FAILS if < 0.6 (writes kappa_failed.json and updates project state).
- **Ordering**: Ensure T023 precedes T024, T030a/T031a precede T030b, T032a precedes T031b, and T039a precedes T039-local.
- **Proxy Validation**: Ensure T039a validates the BART proxy before T039-local runs.
- **Full System**: Ensure T049 orchestrates the full pipeline after all phases are complete.