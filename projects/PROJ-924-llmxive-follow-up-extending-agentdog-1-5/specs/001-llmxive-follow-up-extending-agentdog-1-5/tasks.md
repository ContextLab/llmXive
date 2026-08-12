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

## Phase -1: Spec Amendment & Deviation Logging

- [ ] T-000-RatifySpecAmendment [S] **Ratify Spec Amendment**: Update `specs/001-llmxive-follow-up-extending-agentdog-1-5/spec.md` to reflect the substitution of `gpt-4o-mini` with `google/flan-t5-small` in US‑03 Acceptance Criteria. **Action**: Modify `spec.md` to replace `gpt-4o-mini` with `google/flan-t5-small` in US-03. Verify the change is present. **DEPENDS ON**: None.
- [ ] T-001-DeviationLog [S] **Log Plan Deviation**: Create `docs/plan_deviation_log.md` documenting the substitution of `gpt-4o-mini` with `google/flan-t5-small` in US‑03 due to memory constraints on GitHub Actions free-tier. **Action**: Write a formal log entry citing the constraint (7GB RAM) and the selected alternative. **DEPENDS ON**: T-000-RatifySpecAmendment.

## Phase 0: Scope Verification (Post‑Spec Fix)

- [ ] T000-ScopeVerify [S] [US3] **Verify Spec Amendment**: Confirm `spec.md` has been updated to reflect the `google/flan-t5-small` substitution. **Action**: Read `spec.md` and assert the updated text is present. **DEPENDS ON**: T-000-RatifySpecAmendment.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001a [S] **Initialize Project Directories**: Create directories `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/test/`, `specs/`, `docs/`, and `specs/001-llmxive-drift-detection/`. **Acceptance Criteria**: All directories exist.
- [ ] T001b [S] **Verify Directory Structure**: Create `tests/test_setup.py` with function `test_directories_exist` that asserts the existence of the directories created in T001a. Run `pytest` to confirm `test_directories_exist` passes. **Acceptance Criteria**: `test_directories_exist` passes. (DEPENDS ON T001a)
- [ ] T009 [S] Initialize a Python project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate) using a modern, stable Python 3 release. **Note**: Removed `llama-cpp-python` as it is not used.
- [ ] T010 [S] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`. **Acceptance Criteria**:
 1. Create `.ruff.toml` with EXACT content:
 ```toml
 [lint]
 select = ["E", "F", "W", "I"]
 ignore = []
 [format]
 quote-style = "double"
 ```
 2. Create `pyproject.toml` with EXACT content (including project metadata):
 ```toml
 [project]
 name = "agentdog-drift"
 version = "0.1.0"

 [tool.black]
 line-length = 88
 target-version = ['py3']
 ```
 3. Verify `.ruff.toml` and `pyproject.toml` exist and are non-empty via `pytest` (test `test_ruff_config_exists` and `test_black_config_exists`).

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T011 [S] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42`, `MAX_RAM_GB=7`, and `BATCH_SIZE = 64`. Run `pytest` to confirm `test_config.py` passes.
- [ ] T012a [S] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with `streaming=True`. **Timestamp Handling**: If the source dataset lacks a `timestamp` field, derive it deterministically from `log_id` hash using `hash(log_id) % 24 * 3600`. **NEVER raise ValueError for a missing timestamp if log_id is present.** Raise `ValueError` only if the fetch fails or `log_id` is missing. **Acceptance Criteria**: Functions derive timestamps correctly and raise `ValueError` only on fetch failure or missing log_id. Run `pytest` to confirm `test_data_loader.py` passes.
- [ ] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a)
- [ ] T012d-fixed [S] **Fetch Taxonomy**: Implement `fetch_taxonomy` in `data_loader.py` to load the fixed AgentDoG safety taxonomy from `https://huggingface.co/datasets/AgentDoG/safety-taxonomy`. **Fallback**: If the dataset does not exist or is unreachable, implement the derivation logic from the *AgentDoG 1.5* paper definitions as described in `plan.md` (Dataset & Taxonomy Strategy). **Action**: Raise `FileNotFoundError` only if both the dataset and the paper derivation logic fail. **DEPENDS ON**: T009, T010.
- [ ] T012f [S] Fetch the large‑scale log dataset for performance benchmarking. **Source**: `datasets.load_dataset("mlfoundations/agent_logs", split="train", streaming=True)`. **Action**: Stream and save to `data/raw/agent_logs.csv` in chunks. **Constraint**: Required for T045a. **DEPENDS ON T012a**.
- [ ] T014 [S] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes.
- [ ] T015 [S] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking. **DEPENDS ON T009**.
- [ ] T016a [S] Implement `taxonomy_builder.py` to generate centroid embeddings using `all-MiniLM-L6-v2` (CPU‑first, dynamic batching to stay <7 GB RAM) with input from `data/processed/taxonomy_agentdog.json` (produced by T012d-fixed). **DEPENDS ON T012d-fixed**.
- [ ] T016b [S] Add runtime memory monitoring in `taxonomy_builder.py` using `tracemalloc`; raise `MemoryError` if peak RAM > 7 GB. **DEPENDS ON T016a**.
- [ ] T016c [S] Save generated taxonomy centroids to `data/processed/taxonomy_centroids.json`. **DEPENDS ON T016a**.

## Phase 3: User Story 1 – Zero‑Shot Drift Scoring (Priority: P1)

- [ ] T018 [S] [US1] Contract test for `drift_scoring.py` output schema (`drift_result.schema.yaml`). **DEPENDS ON** T014.
- [ ] T019 [S] [US1] Unit test for empty/whitespace log handling (`test_empty_log_returns_drift_score_max`). **DEPENDS ON** T014.
- [ ] T020 [S] [US1] Integration test for batch memory limits (`test_batch_memory_limit_gb`). **DEPENDS ON** T014.
- [ ] T021a [S] [US1] Implement `compute_cosine_distance` in `drift_scoring.py` (minimum cosine distance to centroids). **DEPENDS ON T016c**.
- [ ] T021b [S] [US1] Implement `batch_process_logs` handling large datasets within 7 GB RAM. **DEPENDS ON T016c**.
- [ ] T021c [S] [US1] Implement `handle_empty_logs` assigning the dynamic theoretical maximum cosine distance and setting `review_flag=True`. **DEPENDS ON T016c**.
- [ ] T021d [S] [US1] Implement `export_results` to CSV `data/processed/drift_scores.csv` (`log_id`, `drift_score`, `review_flag`). **DEPENDS ON** T016c, T012a.
- [ ] T022 [S] [US1] Create `main.py` orchestration script to run full scoring pipeline. **DEPENDS ON** T021a‑T021d.
- [ ] T025a [S] [US1] **Final Statistical Validation**: Compute p‑value and Cohen's d using the **Human‑Annotated Gold Standard** (`data/processed/merged_annotations.csv`). **Label Mapping**: For `AI45Research/ATBench`, map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. Output `data/processed/us01_final_stats.json`. **DEPENDS ON** T035-real-ingest, T031b.
- [ ] T026 [S] [US1] Validate US‑01 acceptance (p < 0.05, Cohen's d ≥ 0.5) using output from T025a; block advancement if criteria not met. **DEPENDS ON** T025a.

## Phase 4: User Story 2 – Human‑in‑the‑Loop Validation (Priority: P2)

- [ ] T027 [S] [US2] Unit test for stratification logic (`test_stratification`). **DEPENDS ON** T030a-bins.
- [ ] T028 [S] [US2] Unit test for Kappa calculation (`test_kappa`). **DEPENDS ON** T031b-Kappa.
- [ ] T029 [S] [US2] Unit test for blind export (`test_blind`). **DEPENDS ON** T031a.
- [ ] T030a [S] [US2] Implement `stratify_logs` reading `drift_scores.csv` and producing high/low drift bins. **DEPENDS ON** T021d, T012a.
- [ ] T030a-bins [S] [US2] **System Generates Bins for Annotation**: Implement `generate_annotation_bins` which reads `drift_scores.csv`, selects top/bottom percentiles (e.g., extreme quantiles), and exports these specific log_ids to `data/processed/annotation_request_bins.csv`. **Action**: This task explicitly fulfills the US-02 requirement for the system to "generate stratified bins for annotation". **DEPENDS ON** T030a.
- [ ] T030a-streaming [S] [US2] **Streaming Stratification**: `stratify_logs_streaming` reads `drift_scores.csv` line‑by‑line, extracts top/bottom percentiles without loading whole file into memory. **DEPENDS ON** T030a.
- [ ] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) before export. **DEPENDS ON** T030a-bins.
- [ ] T030b [S] [US2] Generate blinded annotation CSVs (`data/processed/blinded_annotation_batches/*.csv`) from the system-generated bins. **DEPENDS ON** T030a-bins, T031a, T021d.
- [ ] T032a [S] [US2] Ingest human annotations from `blinded_annotation_batches/*.csv`; raise `ValueError` if too few files. **DEPENDS ON** T030b.
- [ ] T032a-annot-id [S] Assign `annotator_id` from filename if missing column. **DEPENDS ON** T032a.
- [ ] T031b-Kappa [S] Compute Cohen's Kappa on merged annotations. **DEPENDS ON** T032a-annot-id.
- [ ] T031b [S] Merge annotations, calculate Kappa, output `data/processed/merged_annotations.csv`. **DEPENDS ON** T032a, T031b-Kappa.
- [ ] T035-real-ingest [S] **Real Annotation Ingestion**: Ingest a file `data/processed/human_annotations_for_bins.csv` containing labels for the `log_id`s in `data/processed/annotation_request_bins.csv`. **Action**: This file must be generated by a human (or simulated human) process acting on the system-generated bins. The task must verify that the `log_id`s in the ingested file match those in `annotation_request_bins.csv`. **DEPENDS ON** T030a-bins.
- [ ] T031c [S] Perform logistic regression and Mann‑Whitney U tests on `merged_annotations.csv`; output `data/processed/validation_stats.json`. **DEPENDS ON** T031b.
- [ ] T032b [S] Generate mock annotation fixtures for unit tests (`data/test/mock_annot_*.csv`). **DEPENDS ON** T021d.

## Phase 5: User Story 3 – Baseline Performance Comparison (Priority: P3)

- [ ] T037 [S] [US3] Unit test for AUC‑ROC calculation (`test_auc`). **DEPENDS ON** T039-metrics-auc.
- [ ] T038 [S] [US3] Unit test for inference time measurement (`test_inference_time`). **DEPENDS ON** T039-metrics-time.
- [ ] T039-scope-change-doc [S] Document model substitution (gpt‑o‑mini → google/flan-t5-small). **DEPENDS ON** T-000-RatifySpecAmendment.
- [ ] T039-gpt-setup [S] Prepare `flan_config.json` (model name, tokenizer cache, prompt template). Assert plan deviation present. **Schema**: `{"model_name": "google/flan-t5-small", "temperature": 0.0, "prompt_template": "Classify the following text as 'benign' or 'novel': {text}"}`. **DEPENDS ON** T012c-dynamic, T039-scope-change-doc, T-000-RatifySpecAmendment.
- [ ] T039-model-runner [S] Implement `run_flant5` to load `google/flan-t5-small`, perform zero‑shot classification on a given dataset, cache outputs. **DEPENDS ON** T039-gpt-setup.
- [ ] T039-metrics-auc [S] Implement `calculate_auc_roc` using predictions vs. ground truth. **DEPENDS ON** T039-model-runner.
- [ ] T039-metrics-time [S] Implement `measure_inference_time` per log. **DEPENDS ON** T039-model-runner.
- [ ] T039-proxy-validation [S] Run quick sanity check of Flan‑T5 against the **REAL GROUND TRUTH (PROXY)** (generated dynamically from T012a). Require statistically significant AUC (p < 0.05). **DEPENDS ON** T039-gpt-setup, T039-metrics-auc.
- [ ] T039-gpt-run [S] **MVP Baseline Run**: Execute Flan‑T5 on the proxy dataset (generated dynamically), store predictions in `data/processed/flan_predictions_proxy.json`. **DEPENDS ON** T039-model-runner, T012a, T039-scope-change-doc.
- [ ] T039-generate-report [S] Generate MVP comparison report (`data/processed/mvp_comparison_report.json`) containing AUC‑ROC and average inference time for both drift and Flan‑T5 baselines. **DEPENDS ON** T039-gpt-run, T025a.
- [ ] T039-gpt-final [S] **Final Baseline Run**: Execute Flan‑T5 on the **Simulated Gold Standard** (`data/processed/merged_annotations.csv` from T035-real-ingest or T032b). **DEPENDS ON** T035-real-ingest, T039-model-runner.
- [ ] T040 [S] Implement bootstrap iteration logic for AUC‑ROC stability, output `bootstrap_stats.json`. If CPU time exceeds limit, set `timeout_limited: true`. **DEPENDS ON** T039-gpt-run.
- [ ] T040a [S] **Final Timeout Enforcement**: If `timeout_limited` is true in `bootstrap_stats.json` during final report generation, abort with error to satisfy resource‑constrained integrity. **DEPENDS ON** T040.
- [ ] T040b-deterministic-cache [S] Add deterministic caching of model outputs to ensure reproducibility. **DEPENDS ON** T039-model-runner.
- [ ] T041-mvp [S] Generate MVP Comparison Report (AUC‑ROC, inference time) using proxy data. **DEPENDS ON** T039-generate-report, T025a.
- [ ] T041-final [S] Generate Final Comparison Report using simulated gold standard; require Flan‑T5 AUC p < 0.05 and drift AUC within 0.10 of baseline. **DEPENDS ON** T039-gpt-final, T025a, T035-real-ingest.
- [ ] T041a [S] Block T041-final if `state/projects/...yaml` indicates `current_stage: unproven`. **DEPENDS ON** T035-real-ingest.
- [ ] T042 [S] Flag "computationally efficient alternative" if `|AUC_drift - AUC_llm| ≤ 0.10`. **DEPENDS ON** T041-final.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T043a [S] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions. **DEPENDS ON** T021d.
- [ ] T043b [S] Update `docs/data-model.md` with new data model fields and schema definitions. **DEPENDS ON** T021d.
- [ ] T044a [S] Run black and ruff on `code/` to enforce formatting and linting. **DEPENDS ON** T021d.
- [ ] T044b [S] Remove unused imports and variables from `code/`. **DEPENDS ON** T021d.
- [ ] T045-opt-impl [S] Implement batch size tuning logic in `benchmark_performance.py`. Output helper `get_optimal_batch_size`. **DEPENDS ON** T016a.
- [ ] T045-opt-run [S] Run benchmark on a subset of logs using the logic from T045-opt-impl. **DEPENDS ON** T045-opt-impl.
- [ ] T045-opt-report [S] Generate `optimization_report.json` with optimal batch size and strategy. **DEPENDS ON** T045-opt-run.
- [ ] T045a [S] Implement `benchmark_performance.py` to run large‑scale log benchmark on `data/raw/agent_logs.csv` using optimal batch size; enforce ≤ 30 min runtime, raise `TimeoutError` otherwise. **DEPENDS ON** T045-opt-report, T012f.
- [ ] T045b [S] Integrate benchmark into GitHub Actions workflow to fail the build if time threshold exceeded. **DEPENDS ON** T045a.
- [ ] T046a [S] Implement `test_leetspeak_drift_score` (edge case). **DEPENDS ON** T021d.
- [ ] T046b [S] Implement `test_obfuscation_drift_score`. **DEPENDS ON** T021d.
- [ ] T046c [S] Implement `test_unicode_normalization`. **DEPENDS ON** T021d.
- [ ] T047 [S] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated outputs. **DEPENDS ON** T021d.
- [ ] T048 [S] In `validation.py`, replace mock ground truth with `merged_annotations.csv` for final US‑01 validation. **DEPENDS ON** T031b.
- [ ] T049 [S] Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in correct order. **DEPENDS ON** T041-final, T025a, T030b, T039-gpt-final.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase O)**: Removed; streaming requirements integrated into T012a/T012f.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T025a for MVP validation)
4. **STOP and VALIDATE**: Test User Story 1 independently using real data for CI/MVP
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
- **Revision Note**: Phase -1 tasks updated to ratify spec first. T012a updated to mandate timestamp derivation. T030a-bins added to explicitly generate bins for annotation. T035-real-fetch removed; T035-real-ingest updated to ingest annotations for system-generated bins. Mock data tasks (T025b-mock-data) removed to enforce human-verified validation.