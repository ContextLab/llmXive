# Tasks: Heterogeneous Scientific Foundation Model Collaboration Benchmark

**Input**: Design documents from `/specs/001-https-arxiv-org-abs-2604-27351/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

## Phase 0: Research & Dataset Verification (Week 1)

**Purpose**: Verify dataset availability, model weights, and statistical methodology BEFORE implementation begins

**⚠️ CRITICAL**: Implementation cannot proceed until Phase 0 tasks complete and research.md is finalized

- [X] T001 [P] Verify time-series dataset availability (UCI_HAR) via `datasets.load_dataset('UCI_HAR')`; create `src/research/verify_timeseries.py` script; document in research.md section "Dataset Verification" with fields: dataset_name, url, variables (list), size_mb, verification_status (FR-001, Phase 0.1)
- [X] T002 [P] Verify tabular dataset availability (selected UCI sets) via HuggingFace datasets; create `src/research/verify_tabular.py` script; document in research.md section "Dataset Verification" with fields: dataset_name, url, variables (list), size_mb, verification_status (FR-001, Phase 0.1)
- [X] T003 [P] Verify text dataset availability (DROP/MUST) via HuggingFace datasets; create `src/research/verify_text.py` script;document in research.md section "Dataset Verification" with fields: dataset_name, url, variables (list), size_mb, verification_status (FR-001, Phase 0.1)
- [ ] T004 Validate statistical methodology ({{claim:c_5cb9c0de}} (1311.5354, https://arxiv.org/abs/1311.5354 [UNRESOLVED-CLAIM: c_076cb98d — status=verified]), {{claim:c_55db4237}})); document in research.md section "Methodology" with formula, {{claim:c_101df1fb}}, and effect size calculation (FR-007, FR-014, Phase 0.3) <!-- SKIPPED: non-mapping output --> <!-- SKIPPED: non-mapping output -->
- [X] T005 Document dataset-variable fit and flag any missing variables in research.md section "Gap Analysis" with fields: dataset_name, missing_variables (list), impact_assessment (FR-001, Phase 0.4)
- [X] T006 Verify model weights <1 GB for TimeSeries-Transformer, TabPFN, distilled LLM via HuggingFace model cards; create `src/research/verify_models.py` script; document in research.md section "Model Verification" with fields: model_name, hf_id, size_mb, cpu_tractable (boolean) (FR-002, SC-002, Phase 0.5)
- [ ] T006a Implement Reference-Validator Agent in `src/validators/reference_validator.py` with title-token-overlap ≥ 0.7 check before contributing review points; add blocking gate for Constitution II compliance (Constitution II, Plan Gap)

**Checkpoint**: Research gate complete - plan.md Constitution Check must show ✅ COMPLIANT before Phase 1 begins

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T007 Create project structure with exact directories: src/, tests/, data/, data/processed/, state/, contracts/, src/benchmark/, src/models/, src/tasks/, src/evaluation/, src/utils/, src/benchmark/config/, src/benchmark/config/modalities/, src/research/, src/validators/ (per plan.md project structure)
- [ ] T008 Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_493ca185 — status=not_enough_info] with {{claim:c_9da78e09}}
- [ ] T009 [P] Configure linting and formatting tools: ruff.toml (line-length=88 [UNRESOLVED-CLAIM: c_992d09db — status=not_enough_info], target-version=py311 [UNRESOLVED-CLAIM: c_49ece9de — status=not_enough_info]) and pyproject.toml (black config) in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T010 [P] Create dataset schema contract in contracts/dataset.schema.yaml with required fields (name, url, variables, size_mb, checksum)
- [X] T011 [P] Create task schema contract in contracts/task.schema.yaml with required fields (task_id, modalities, label, datasets)
- [X] T012 [P] Create results schema contract in contracts/results.schema.yaml with required fields (task_id, condition, accuracy, timestamp)
- [X] T013 [P] Create modality_model schema contract in contracts/modality_model.schema.yaml with required fields (model_id, model_type, max_memory_gb)
- [X] T014 Create data-model.md with entity relationships (Dataset, ModalityModel, Task); include sections: (1) Entity definitions with attributes, (2) Relationship diagram (Mermaid or PlantUML), (3) Cardinality specifications (Plan Consistency)
- [ ] T015 Create quickstart.md with setup instructions; include sections: (1) {{claim:c_68a619c4}}, (2) Setup commands (clone, venv, install), (3) Verification steps (run --help, check data/), (4) Troubleshooting common issues (US-1)
- [X] T016 [P] Setup base logging module in src/utils/logging.py with functions: setup_logger(), get_logger(), log_environment() (foundation for seed/version/environment logging)
- [ ] T017 Create checksum tracking infrastructure in state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml artifact_hashes map with sha256 format (Constitution III)
- [X] T018 Update state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml updated_at timestamp on any artifact change; create helper function in src/utils/versioning.py with function update_artifact_timestamp(artifact_path) (Constitution V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Run Full Benchmark (Priority: P1) 🎯 MVP

**Goal**: Execute the benchmark script on a fresh environment with default parameters and verify that a results report (CSV + summary PDF) is produced within the allotted compute budget.

**Independent Test**: Run `python run_benchmark.py --config default.yaml` and verify `results.csv` and `summary.pdf` are generated within 4 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US1] Contract test for dataset schema validation in tests/contract/test_dataset_schema.py
- [X] T020 [P] [US1] Contract test for results schema validation in tests/contract/test_results_schema.py
- [X] T021 [P] [US1] Integration test for full benchmark execution in tests/integration/test_benchmark_run.py

### Implementation for User Story 1

- [ ] T022 [US1] Implement dataset download with 3-retry logic in src/data/download.py (FR-010); function signatures: download_dataset(url, max_retries=3, timeout=300) -> (path, checksum); verify URLs: UCI_HAR via `datasets.load_dataset('UCI_HAR')`, DROP/MUST via HuggingFace datasets; depends on T007/T008 complete
- [X] T023 [US1] Create task_runner.py in src/tasks/task_runner.py (FR-001, FR-006); class TaskRunner with methods: run_task(task_id), get_task(task_id), validate_task(task_id); depends on T017 complete
- [ ] T024 [US1] Implement timeout enforcement in src/utils/timeout.py (FR-006, FR-013); function signatures: enforce_timeout(func, timeout_seconds=300) -> result; raise TimeoutError if exceeded; depends on T016 complete
- [X] T025 [US1] Implement seed/version AND environment details logging in src/utils/logging.py (FR-005); depends on T016 completion; functions: log_random_seed(seed), log_model_versions(models), log_environment_details(); log random seeds, model versions, AND environment details (Python version, OS, CPU info)
- [X] T026 [US1] Implement metrics computation (F1, MAPE) in src/evaluation/metrics.py (FR-004); function signatures: compute_f1(y_true, y_pred) -> float, compute_mape(y_true, y_pred) -> float; handle edge cases (division by zero, empty arrays)
- [ ] T027 [US1] Implement statistical tests in src/evaluation/statistical_tests.py (FR-007, FR-014, FR-011); MUST include: {{claim:c_2c09cbc3}}, {{claim:c_2c7597de}} (1809.01635, https://arxiv.org/abs/1809.01635 [UNRESOLVED-CLAIM: c_fe19ce29 — status=verified]) with {{claim:c_7c3d210d}} and 95% CI as PRIMARY outcome (document formula), {{claim:c_55db4237}} (explicit count), configurable α threshold (default 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value) [UNRESOLVED-CLAIM: c_e86ab192 — status=verified]) with logging; function signatures: paired_ttest(condition_a, condition_b, {{claim:c_08e60571}}), wilcoxon_effect_size(condition_a, condition_b), bootstrap_ci(values, {{claim:c_e50ac6bc}}, {{claim:c_dadece63}} (1710.08708, https://arxiv.org/abs/1710.08708 [UNRESOLVED-CLAIM: c_fa899f79 — status=verified]))
- [ ] T028 [US1] Implement report generator in src/evaluation/report_generator.py (FR-007); MUST verify report includes (a) t-statistic, (b) p-value, (c) bootstrap CI ({{claim:c_8176747a}}), (d) Wilcoxon effect size as PRIMARY outcome with 95% CI; function signatures: generate_csv_report(results, output_path), generate_pdf_report(results, output_path)
- [ ] T029 [US1] Create run_benchmark.py main entry point in src/benchmark/run_benchmark.py (FR-001, FR-006, FR-010); CLI arguments: --config (default default.yaml), --mode (heterogeneous|unified), --seeds (5); depends on T024, T025 logging complete
- [ ] T030 [US1] Create default.yaml config in src/benchmark/config/default.yaml with required keys: datasets (list), modalities (list), seeds (5), timeout_per_task (300), {{claim:c_340e25bd}} (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics) [UNRESOLVED-CLAIM: c_b8ef2310 — status=not_enough_info])
- [X] T031 [US1] Create task_definitions.yaml with {{claim:c_3bd8ba9e}} in src/tasks/task_definitions.yaml (not "multiple" - explicit count); schema: task_id (T001-T020), modalities(list), datasets (list), label_column (string); depends on T010, T011 complete
- [X] T032 [US1] Create StatisticalSummary persistence in data/statistical_summary.yaml (Constitution IV); YAML structure: task_results (list of {task_id, accuracy, condition, timestamp}), aggregate_stats (mean_accuracy_diff, p_value, effect_size, ci_lower, ci_upper); schema reference: contracts/results.schema.yaml

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneous Modality-Specific Orchestration (Priority: P2)

**Goal**: Add a new modality to the heterogeneous pipeline without breaking existing tasks.

**Independent Test**: Add a dummy "image" modality configuration file and run a single task that includes the new modality; verify that the pipeline processes it using the specified model and includes its output in the final prediction.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US2] Contract test for modality_model schema in tests/contract/test_modality_model_schema.py
- [X] T034 [P] [US2] Integration test for modality addition in tests/integration/test_modality_addition.py

### Implementation for User Story 2

- [ ] T035 [P] [US2] Implement modality-specific model wrapper for time-series in src/models/timeseries_model.py (FR-002); use CPU-tractable TimeSeries-Transformer (< 1 GB); class TimeSeriesModel with methods: load_model(model_id), predict(input_data), get_embedding(input_data); handle CPU-only inference
- [ ] T036 [P] [US2] Implement modality-specific model wrapper for tabular in src/models/tabular_model.py (FR-002); use TabPFN (< 1 GB); class TabularModel with methods: load_model(model_id), predict(input_data), get_embedding(input_data); handle CPU-only inference
- [ ] T037 [P] [US2] Implement modality-specific model wrapper for text in src/models/text_model.py (FR-002); use distilled LLM (< 1 GB); class TextModel with methods: load_model(model_id), predict(input_data), get_embedding(input_data); handle CPU-only inference
- [X] T038 [US2] Implement heterogeneous routing layer in src/models/routing.py (FR-002); depends on T035-T037 complete; class ModalityRouter with methods: route(modality, input_data), get_model(modality); routing logic: forward each modality's raw input to its native model; interface: predict(modalities_dict) -> prediction
- [X] T039 [US2] Implement missing modality handler in src/utils/missing_handler.py (FR-009, FR-012); function signatures: handle_missing_modality(task_id, missing_modality, condition) -> placeholder; fallback behavior: heterogeneous condition skips modality, unified condition inserts placeholder text; logging format: "WARNING: Missing modality {modality} for task {task_id}"
- [X] T040 [US2] Create timeseries.yaml modality config in src/benchmark/config/modalities/timeseries.yaml (FR-008); required keys: model_id, model_type, max_memory_gb, inference_script; depends on T017, T018 complete; update state/artifact_hashes after config changes
- [X] T041 [US2] Create tabular.yaml modality config in src/benchmark/config/modalities/tabular.yaml (FR-008); required keys: model_id, model_type, max_memory_gb, inference_script; depends on T017, T018 complete; update state/artifact_hashes after config changes
- [X] T042 [US2] Create text.yaml modality config in src/benchmark/config/modalities/text.yaml (FR-008); required keys: model_id, model_type, max_memory_gb, inference_script; depends on T017, T018 complete; update state/artifact_hashes after config changes
- [X] T043 [US2] Implement run_task.py single task execution in src/benchmark/run_task.py (FR-008, FR-009); CLI arguments: --task-id (required), --add-modality (optional); task loading logic: load task from task_definitions.yaml, load modality configs; output format: JSON with prediction, modality_contributions, timing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Unified Text-Only Translation (Priority: P3)

**Goal**: Run the benchmark with the `--mode unified` flag and confirm that all inputs are translated to text before feeding to a single LLM.

**Independent Test**: Run the benchmark with `--mode unified` and confirm that time-series and tabular data are converted to text representations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T044 [P] [US3] Contract test for unified translation schema in tests/contract/test_translation_schema.py
- [X] T045 [P] [US3] Integration test for unified mode execution in tests/integration/test_unified_mode.py

### Implementation for User Story 3

- [X] T046 [US3] Implement unified translation layer in src/models/translation.py (FR-003); class UnifiedTranslator with methods: translate_timeseries(input_data), translate_tabular(input_data), translate_all(modalities_dict); deterministic schema documented
- [ ] T047 [US3] Implement time-series to text conversion logic in src/models/translation.py (US-3 Scenario 1); deterministic schema: "Mean heart rate = X bpm, max = Y bpm, min = Z bpm, std = W bpm " (all quantitative information retained); function signature: timeseries_to_text(data, label_name) -> string
- [X] T048 [US3] Implement tabular to text conversion logic in src/models/translation.py (US-3 Scenario 1); deterministic schema: CSV-style text representation with column names and values; function signature: tabular_to_text(df, label_column) -> string
- [X] T049 [US3] Add fidelity validation for translation quality in src/models/translation.py (FR-003); function signature: validate_translation(original_data, translated_text) -> fidelity_score; measure information loss; log warning if fidelity < threshold
- [X] T050 [US3] Update run_benchmark.py to support --mode unified flag (US-3); CLI argument: --mode (heterogeneous|unified, default heterogeneous); when unified, route all inputs through UnifiedTranslator

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T051 [P] Documentation updates: quickstart.md (setup/dependencies sections) and data-model.md (entity relationships and schema references); update specific sections: quickstart.md "Setup Commands", data-model.md "Entity Attributes"
- [X] T052 Code cleanup and refactoring across src/: remove unused imports, consolidate duplicate code, resolve TODO comments, remove dead code; scope: all files in src/; criteria: no linting errors, no dead code warnings
- [X] T053 [P] Additional unit tests in tests/unit/ (model wrappers, metrics, statistical tests); specific tests: test_timeseries_model.py, test_tabular_model.py, test_text_model.py, test_metrics.py, test_statistical_tests.py
- [X] T054 Run quickstart.md validation to ensure reproducible setup; validation method: fresh venv, pip install -r requirements.txt, run --help, verify no errors
- [X] T055a Create runtime measurement script in src/utils/runtime_monitor.py (SC-003, SC-002); function signatures: measure_total_benchmark_time(), measure_per_task_time(task_id); record results to data/runtime_metrics.yaml
- [ ] T055b Implement total runtime verification in src/evaluation/runtime_verification.py; verify total runtime ≤4 hours on reference hardware (SC-003); record pass/fail to data/runtime_metrics.yaml <!-- FAILED: unspecified -->
- [ ] T055c Implement per-task inference verification in src/evaluation/runtime_verification.py; Verify per-task inference ≤5 minutes [UNRESOLVED-CLAIM: c_fb68858f — status=not_enough_info] (SC-002); record pass/fail to data/runtime_metrics.yaml
- [ ] T056 Verify reproducibility across multiple seeds (SC-004); mean accuracy differences within 95% CI with CI width ≤15% [UNRESOLVED-CLAIM: c_5fd26799 — status=not_enough_info] (implementation-specific threshold - document in spec as staged); run benchmark 5 times with different seeds [UNRESOLVED-CLAIM: c_b49acdf2 — status=not_enough_info], compare results
- [ ] T057 Archive artifacts with content hashes in state/artifact_hashes (Constitution V); artifacts to archive: data/, state/, src/ (excluding __pycache__); {{claim:c_b7d66b08}} (Wikipedia: SHA-2, https://en.wikipedia.org/wiki/SHA-2 [UNRESOLVED-CLAIM: c_8ffdbaa7 — status=verified]); update procedure: compute hash for each file, write to state/artifact_hashes.yaml with file_path and hash value
- [X] T058 Update state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml updated_at timestamp on artifact changes; depends on T018; helper function: update_timestamp_on_change(artifact_path); integrate with T040-T042 config updates

**Checkpoint**: All user stories complete; verification tasks executed; artifacts archived

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Contract test for results schema validation in tests/contract/test_results_schema.py"

# Launch model implementations for User Story 1 together (after T024 logging complete):
Task: "Implement dataset download with 3-retry logic in src/data/download.py "
Task: "Create task_runner.py in src/tasks/task_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Dataset Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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

## Compute Feasibility Notes

- All models must be CPU-tractable (< 1 GB weights) [UNRESOLVED-CLAIM: c_132b9cdd — status=not_enough_info] - validated in T006
- No GPU/CUDA dependencies
- {{claim:c_b9b3cab2}} (Wikipedia: {{claim:c_0929bcb6}}, https://en.wikipedia.org/wiki/Hutter_Prize)
- {{claim:c_e38700cc}}
- Full benchmark ≤ 4 hours wall-clock time [UNRESOLVED-CLAIM: c_fd929a6a — status=not_enough_info]
- Use UCI_HAR for time-series, DROP/MUST for text (per plan.md substitution strategy) [UNRESOLVED-CLAIM: c_d9bbbbd3 — status=not_enough_info]
- No 8-bit/4-bit quantization (bitsandbytes requires CUDA)
- Dataset downloads MUST use verified URLs or HuggingFace datasets.load_dataset()

## SC-001 Empirical Determination Note

Success Criterion SC-001 specifies "≥ [deferred] %" accuracy threshold which will be empirically determined during implementation (Phase 4 reproducibility runs). T056 captures reproducibility verification; final threshold documented in paper after pilot data analysis.
