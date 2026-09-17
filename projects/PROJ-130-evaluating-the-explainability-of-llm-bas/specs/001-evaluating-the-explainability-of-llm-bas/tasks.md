# Tasks: Evaluating the Explainability of LLM-Based Bug Fixes

**Input**: Design documents from `/specs/001-evaluating-the-explainability-of-llm-bas/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `data/.gitkeep` and `data/defects4j/.gitkeep` to initialize directory structure. **Verify**: Run `ls data/` to confirm files exist.
- [X] T002 [P] Create `code/.gitkeep`, `code/utils/.gitkeep`, and `code/models/.gitkeep` to initialize directory structure. **Verify**: Run `ls code/` to confirm files exist.
- [X] T003 [P] Create `explanations/.gitkeep`, `state/.gitkeep`, and `tests/.gitkeep` to initialize directory structure. **Verify**: Run `ls explanations/` to confirm files exist.
- [X] T004 [P] Initialize Python 3.11 project with dependencies in `code/requirements.txt` (transformers==4.36.0, datasets==2.16.0, captum==0.7.0, scikit-learn==1.4.0, pytest==7.4.0, pandas==2.1.0, numpy==1.26.0, evaluate==0.4.1, sentence-transformers==2.2.2, radon==6.0.1)
- [X] T005 [P] Create `.ruff.toml` and `pyproject.toml` (with `[tool.black]` section) for linting and formatting. **Verify**: Run `ruff check .` and `black --check .` to confirm configuration is valid.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create `code/models/bug.py` defining Bug entity (id, file_path, test_suite, reference_text)
- [X] T006b-IMPL [P] Create `code/models/explainability.py` defining ExplainabilityScore entity (bug_id, attention_score, saliency_score, coherence_score) with `coherence_score` as a float field.
- [X] T007 [P] Create `code/models/patch.py` defining Patch entity (id, bug_id, diff_content, rationale_text)
- [X] T008 [P] Create `code/models/correctness.py` defining CorrectnessLabel entity (bug_id, pass_fail, unsafe_flag)
- [X] T009 [P] Create `code/models/statistical.py` defining StatisticalResult entity (correlation_coeff, auc_roc, p_value)
- [X] T011 [P] Create YAML schemas for validation in `specs/001-evaluating-the-explainability-of-llm-bas/contracts/`. Explicitly create: `dataset.schema.yaml`, `patch.schema.yaml`, `correctness.schema.yaml`, `explainability.schema.yaml`, `statistical.schema.yaml` with explicit field definitions. **Verify**: Run `pytest tests/contract/test_schema_validation.py` to confirm schemas are valid.
- [X] T012 [P] Implement contract test framework in `tests/contract/` to validate against YAML schemas using pytest. **Verify**: Run `pytest tests/contract/` to confirm framework works.
- [X] T013 [P] Setup environment configuration management and random seed pinning utility in `code/utils/seeding.py`. Implement `set_global_seed(seed: int)` and `get_config()` functions. **Verify**: Run `pytest tests/unit/test_seeding.py` to confirm functions work.
- [X] T013b [P] Create `code/utils/config.py` to store research parameters (coherence_threshold=0.6, temperature=0.7, max_tokens=512). **Verify**: Run `python -c "from code.utils.config import config; print(config)"` to confirm file is loadable.
- [X] T014-IMPL [P] Create `code/utils/logger.py` implementing structured JSON logging for edge cases (invalid patches, timeouts, missing rationales). Define log format and output to `state/error_log.json`. **Verify**: Run `pytest tests/unit/test_logger.py` to confirm log output format.
- [X] T014-VERIFY [P] Trigger an invalid patch scenario in a test script and verify `state/error_log.json` contains the expected error code and message.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Patches and Assess Correctness (Priority: P1) 🎯 MVP

**Goal**: Download Defects4J, generate patches using CodeLlama-7B-Instruct, and determine correctness via test suite execution.

**Independent Test**: Run pipeline on 5 bugs; verify each produces a patch file, a correctness label (pass/fail), and an unsafe flag if applicable.

### Tests for User Story 1

- [X] T015 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T016 [P] [US1] Contract test for patch schema in `tests/contract/test_patch_schema.py`
- [X] T017 [P] [US1] Contract test for correctness schema in `tests/contract/test_correctness_schema.py`
- [X] T018 [US1] Integration test: Verify patch generation and test execution on a single sample bug (e.g., Lang-1) in `tests/integration/test_us1_sample.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement `code/01_download_data.py` to download Defects4J v2.0 from official GitHub repo (https://github.com/rjust/defects4j/archive/refs/tags/v2.0.0.zip), verify SHA256 checksum against release page, and extract to `data/defects4j/` (FR-001, FR-012). **Invoke**: Call `seeding.set_global_seed()` at start. **Verify**: Check `data/defects4j/` contains expected files and checksum matches.
- [X] T020 [US1] Implement `code/02_generate_patches.py` to prompt CodeLlama-7B-Instruct (16-bit CPU precision, temperature from `config.py`, max_tokens from `config.py`) using prompt template from `code/prompts/patch_gen.txt` and output diff format patches AND generate rationale text (FR-002, FR-011). **Invoke**: Call `seeding.set_global_seed()` at start. **Output**: Write rationale directly to `explanations/<bug-id>_rationale.txt` and patch to `explanations/<bug-id>_patch.diff`. **Verify**: Check `explanations/<bug-id>_rationale.txt` exists.
- [X] T021 [US1] Implement `code/03_execute_tests.py` to run DefectsJ test suite with a fixed timeout per bug and record pass/fail/unsafe status (FR-003, FR-010). **Invoke**: Call `seeding.set_global_seed()` at start. **Verify**: Check `state/correctness.json` contains results.
- [X] T022 [US1] Implement error handling for invalid patches, generation failures, and timeouts; log counts to `state/error_log.json` with specific error codes using `code/utils/logger.py`. **Verify**: Trigger an invalid patch and verify `state/error_log.json` contains count > 0 with correct error code.
- [X] T023 [US1] Create metadata recorder to save dataset checksums and model revision in `code/model_revision.txt` and `state/metadata.json`
- [X] T024 [US1] Implement `code/04_compute_complexity.py` to calculate bug complexity (LOC, cyclomatic) using `radon` library and store in `state/complexity_metrics.json` (Producer for T036). **Output**: JSON format `{ "bug_id": { "loc": int, "cyclomatic": int } }`. **Verify**: Check `state/complexity_metrics.json` contains expected keys and structure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Explainability Scores (Priority: P2)

**Goal**: Compute attention weights, Integrated Gradients saliency, and rationale coherence scores for generated patches.

**Independent Test**: Process generated patches; verify output includes attention heatmap, saliency magnitude, and coherence score.

### Tests for User Story 2

- [X] T025 [P] [US2] Contract test for explainability schema in `tests/contract/test_explainability_schema.py`
- [X] T026 [P] [US2] Integration test: Verify attention extraction and saliency computation on a sample patch in `tests/integration/test_us2_sample.py`

### Implementation for User Story 2

- [X] T027 [US2] Implement `code/05_extract_attention.py` to extract per-token attention weights from last decoder layer and aggregate to file-level heatmaps (FR-004)
- [X] T028 [US2] Implement `code/06_compute_saliency.py` to apply Captum's Integrated Gradients on tokenized diffs and compute summed saliency magnitude (FR-005)
- [X] T029 [US2] Implement `code/07_compute_rationale_coherence.py` to compute internal coherence of generated rationales against code change semantics using `sentence-transformers/all-MiniLM-L6-v2` (cosine similarity). **Input**: Read rationale from `explanations/<bug-id>_rationale.txt` (output of T020) and code change from patch. **Threshold**: Read from `config.py`. **Output**: Record `coherence_score` and flag if >= threshold. **Handle**: If no rationale, record `coherence_score` as null and log reason ('missing_rationale') to `state/error_log.json`. **Verify**: Assert loaded model name is exactly `sentence-transformers/all-MiniLM-L6-v2` and log the revision ID. **Depends on**: T020 (rationale generation).
- [X] T030 [US2] Save explainability artifacts to `explanations/` with standardized naming (`<bug-id>_attention.png`, `<bug-id>_saliency.npy`, `<bug-id>_metadata.json`). **Action**: Ensure attention and saliency files are saved in final location. **Depends on**: T027, T028.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation Testing (Priority: P3)

**Goal**: Compute correlations, fit logistic regression models, and perform paired t-tests with Bonferroni correction.

**Independent Test**: Run analysis on pre-computed scores from a representative set of bugs.; verify output includes correlation coefficients, AUC-ROC, and corrected p-values.

### Tests for User Story 3

- [X] T031 [P] [US3] Contract test for statistical schema in `tests/contract/test_statistical_schema.py`
- [X] T032 [P] [US3] Integration test: Verify full statistical pipeline on a small synthetic dataset in `tests/integration/test_us3_sample.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/08_statistical_analysis.py` to compute point-biserial correlations between scores and correctness (FR-007)
- [X] T034 [US3] Implement logistic regression modeling to predict correctness from scores and evaluate via AUC-ROC (FR-008)
- [X] T035 [US3] Implement paired t-tests comparing predictive power of the three techniques with Bonferroni correction (α_corrected = 0.05 / N, where N is the actual number of comparisons performed). **Verify**: Log the calculated divisor N. (FR-009)
- [X] T036 [US3] Add confound controls: load bug complexity from `state/complexity_metrics.json` (output of T024) and test suite quality as covariates in analysis (FR-007, FR-008). **Depends on**: T024. **Verify**: Check `state/complexity_metrics.json` is loadable and contains expected keys.
- [X] T037 [US3] Generate final research output: correlation coefficients, AUC-ROC values, and Bonferroni-corrected p-values in `state/statistical_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T038 [P] Documentation updates: Finalize `quickstart.md` and `research.md` with methodology and limitations
- [X] T039-IMPL [P] Create `run_pipeline.sh` script with `--verify-hashes` flag to re-run pipeline on fresh runner and verify artifact hashes match `state/` records (FR-011, SC-008). **Verify**: Run `./run_pipeline.sh --verify-hashes` and confirm exit code 0.
- [X] T039 [P] Documentation updates: Finalize `quickstart.md` and `research.md` with methodology and limitations
- [X] T040 [P] Run full reproducibility check: Re-run pipeline on fresh runner and verify artifact hashes match. **Invoke**: `./run_pipeline.sh --verify-hashes`. **Verify**: Run `./run_pipeline.sh --verify-hashes` and confirm hash match report.
- [X] T041 [P] Run quickstart.md validation to ensure all steps execute without error. **Verify**: Run `bash -c "$(cat quickstart.md | grep -v '^#')"` and confirm exit code 0.
- [X] T042 Document power analysis limitations and sample size constraints in `research.md` under section "Limitations"

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **BLOCKED by US1 completion**. Cannot start until T020 (Patch Generation) produces rationale text artifacts. **T029 and T030 explicitly depend on T020.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (scores) for input. **T036 explicitly depends on T024.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **US2 and US3 CANNOT start in parallel with US1**. US2 is strictly blocked by US1 completion (T020).
- Once Foundational phase completes AND US1 is complete:
 - US2 (T027-T030) can start
 - US3 (T033-T037) can start (if data is pre-generated, otherwise waits for US2)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies are met)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Contract test for patch schema in tests/contract/test_patch_schema.py"
Task: "Contract test for correctness schema in tests/contract/test_correctness_schema.py"

# Launch implementation tasks for US1 (sequential dependencies):
Task: "Implement code/01_download_data.py" -> Task: "Implement code/02_generate_patches.py" -> Task: "Implement code/03_execute_tests.py"
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
 - Developer A: User Story 1 (Data & Patch Gen)
 - Developer B: User Story 2 (Explainability) - *Must wait for US1 completion*
 - Developer C: User Story 3 (Stats) - *Must wait for US2 completion*
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
- **Critical Constraint**: CodeLlama-7B-Instruct MUST run in 16-bit precision on CPU. Do NOT use `load_in_8bit` or `bitsandbytes` as they require CUDA.
- **Metric Correction**: FR-006 (BLEU/ROUGE) is overridden by the Plan's "Critical Limitation Note". Task T029 implements "internal coherence" via semantic similarity (FR-006-REV) after T006b-IMPL verification.
- **Data Flow**: T020 writes rationale directly to `explanations/`; T029 reads from `explanations/`. T030 is removed.
- **Configuration**: Research parameters (threshold, temperature) are defined in `code/utils/config.py` (T013b) and read by T020, T029, T033.
- **Seeding**: `seeding.set_global_seed()` is invoked in T019, T020, T021.
- **Complexity**: T036 depends on T024 output structure.
- **Statistics**: T035 calculates Bonferroni divisor dynamically.
- **Reproducibility**: T039-IMPL creates `run_pipeline.sh` for hash verification.
- **Logging**: T014-IMPL creates `code/utils/logger.py` for structured logging.