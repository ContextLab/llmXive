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

- [ ] T001 [P] Create `data/` and `data/defects4j/` directories
- [ ] T002 [P] Create `code/`, `code/utils/`, `code/models/` directories
- [ ] T003 [P] Create `explanations/`, `state/`, `tests/` directories
- [X] T004 [P] Initialize Python 3.11 project with dependencies in `code/requirements.txt` (transformers==4.36.0, datasets==2.16.0, captum==0.7.0, scikit-learn==1.4.0, pytest==7.4.0, pandas==2.1.0, numpy==1.26.0, evaluate==0.4.1, sentence-transformers==2.2.2, radon==6.0.1)
- [ ] T005 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create `code/models/bug.py` defining Bug entity (id, file_path, test_suite, reference_text)
- [ ] T006b [P] **SPEC AMENDMENT**: Update `spec.md` to replace FR-006 (BLEU/ROUGE) with FR-006-REV (Internal Coherence), update US-2 Acceptance Scenario 3 to output `coherence_score`, and update SC-007 to define expected range for cosine similarity (0-1). This task creates the formal requirement alignment needed for T029.
- [X] T007 [P] Create `code/models/patch.py` defining Patch entity (id, bug_id, diff_content, rationale_text)
- [X] T008 [P] Create `code/models/correctness.py` defining CorrectnessLabel entity (bug_id, pass_fail, unsafe_flag)
- [ ] T009 [P] Create `code/models/explainability.py` defining ExplainabilityScore entity (bug_id, attention_score, saliency_score, coherence_score)
- [ ] T010 [P] Create `code/models/statistical.py` defining StatisticalResult entity (correlation_coeff, auc_roc, p_value)
- [ ] T011 [P] Create YAML schemas for validation in `specs/001-evaluating-the-explainability-of-llm-bas/contracts/` (dataset, patch, correctness, explainability, statistical)
- [ ] T012 [P] Implement contract test framework in `tests/contract/` to validate against YAML schemas
- [ ] T013 [P] Setup environment configuration management and random seed pinning utility in `code/utils/seeding.py` (FR-011)
- [ ] T014 [P] Configure logging infrastructure to record edge cases (invalid patches, timeouts, missing rationales)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Patches and Assess Correctness (Priority: P1) 🎯 MVP

**Goal**: Download Defects4J, generate patches using CodeLlama-7B-Instruct, and determine correctness via test suite execution.

**Independent Test**: Run pipeline on 5 bugs; verify each produces a patch file, a correctness label (pass/fail), and an unsafe flag if applicable.

### Tests for User Story 1

- [ ] T015 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T016 [P] [US1] Contract test for patch schema in `tests/contract/test_patch_schema.py`
- [ ] T017 [P] [US1] Contract test for correctness schema in `tests/contract/test_correctness_schema.py`
- [ ] T018 [US1] Integration test: Verify patch generation and test execution on a single sample bug (e.g., Lang-1) in `tests/integration/test_us1_sample.py`

### Implementation for User Story 1

- [ ] T019 [US1] Implement `code/01_download_data.py` to download Defects4J v2.0 from official GitHub repo (https://github.com/rjust/defects4j/archive/refs/tags/v2.0.0.zip), verify SHA256 checksum against release page, and extract to `data/defects4j/` (FR-001, FR-012)
- [ ] T020 [US1] Implement `code/02_generate_patches.py` to prompt CodeLlama-7B-Instruct (16-bit CPU precision, temperature=0.7, max_tokens=512) using prompt template from `code/prompts/patch_gen.txt` and output diff format patches AND generate rationale text (FR-002, FR-011)
- [ ] T021 [US1] Implement `code/03_execute_tests.py` to run Defects4J test suite with 60s timeout per bug and record pass/fail/unsafe status (FR-003, FR-010)
- [ ] T022 [US1] Implement error handling for invalid patches, generation failures, and timeouts; log counts to `state/error_log.json`
- [ ] T023 [US1] Create metadata recorder to save dataset checksums and model revision in `code/model_revision.txt` and `state/metadata.json`
- [ ] T024 [US1] Implement `code/04_compute_complexity.py` to calculate bug complexity (LOC, cyclomatic) using `radon` library and store in `state/complexity_metrics.json` (Producer for T036, NOT T030)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Explainability Scores (Priority: P2)

**Goal**: Compute attention weights, Integrated Gradients saliency, and rationale coherence scores for generated patches.

**Independent Test**: Process 2 generated patches; verify output includes attention heatmap, saliency magnitude, and coherence score.

### Tests for User Story 2

- [ ] T025 [P] [US2] Contract test for explainability schema in `tests/contract/test_explainability_schema.py`
- [ ] T026 [P] [US2] Integration test: Verify attention extraction and saliency computation on a sample patch in `tests/integration/test_us2_sample.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `code/05_extract_attention.py` to extract per-token attention weights from last decoder layer and aggregate to file-level heatmaps (FR-004)
- [ ] T028 [US2] Implement `code/06_compute_saliency.py` to apply Captum's Integrated Gradients on tokenized diffs and compute summed saliency magnitude (FR-005)
- [ ] T029 [US2] Implement `code/07_compute_rationale_coherence.py` to compute internal coherence of generated rationales against code change semantics using `sentence-transformers/all-MiniLM-L6-v2` (cosine similarity). Threshold for valid coherence: `cosine_similarity >= 0.6`. Handles missing rationales by recording `coherence_score` as null and logging the event. (FR-006-REV). **Depends on: T020** (rationale text artifact).
- [ ] T030 [US2] Save explainability artifacts to `explanations/` with standardized naming (`<bug-id>_attention.png`, `<bug-id>_saliency.npy`, `<bug-id>_rationale.txt`, `<bug-id>_metadata.json`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation Testing (Priority: P3)

**Goal**: Compute correlations, fit logistic regression models, and perform paired t-tests with Bonferroni correction.

**Independent Test**: Run analysis on pre-computed scores from 10 bugs; verify output includes correlation coefficients, AUC-ROC, and corrected p-values.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for statistical schema in `tests/contract/test_statistical_schema.py`
- [ ] T032 [P] [US3] Integration test: Verify full statistical pipeline on a small synthetic dataset in `tests/integration/test_us3_sample.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/08_statistical_analysis.py` to compute point-biserial correlations between scores and correctness (FR-007)
- [ ] T034 [US3] Implement logistic regression modeling to predict correctness from scores and evaluate via AUC-ROC (FR-008)
- [ ] T035 [US3] Implement paired t-tests comparing predictive power of the three techniques with Bonferroni correction (α_corrected = 0.05 / 6 = 0.0083 for 6 comparisons: 3 techniques × 2 tests) (FR-009)
- [ ] T036 [US3] Add confound controls: load bug complexity (from T024) and test suite quality as covariates in analysis (FR-007, FR-008)
- [ ] T037 [US3] Generate final research output: correlation coefficients, AUC-ROC values, and Bonferroni-corrected p-values in `state/statistical_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T038 [P] Documentation updates: Finalize `quickstart.md` and `research.md` with methodology and limitations
- [ ] T039 Code cleanup and refactoring: Reduce cyclomatic complexity of `code/07_statistical_analysis.py` to < 10 and `code/08_statistical_analysis.py` to < 10; remove unused imports in `code/`
- [ ] T040 Run full reproducibility check: Re-run pipeline on fresh runner and verify artifact hashes match
- [ ] T041 [P] Run quickstart.md validation to ensure all steps execute without error
- [ ] T042 Document power analysis limitations and sample size constraints in `research.md` under section "Limitations"

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (patches AND rationale text from T020) for input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (scores) for input

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel if data is pre-generated, but US2 strictly depends on US1 completion
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
 - Developer B: User Story 2 (Explainability) - *Can start once US1 data is generated*
 - Developer C: User Story 3 (Stats) - *Can start once US2 data is generated*
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
- **Metric Correction**: FR-006 (BLEU/ROUGE) is overridden by the Plan's "Critical Limitation Note". Task T029 implements "internal coherence" via semantic similarity (FR-006-REV) after T006b amends the spec.