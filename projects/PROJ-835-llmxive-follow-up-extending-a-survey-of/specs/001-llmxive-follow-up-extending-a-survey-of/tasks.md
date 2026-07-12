# Tasks: LlmXive Follow-up: Latent-Space Jailbreak Detection

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-a-survey-of/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-835-llmxive-follow-up-extending-a-survey-of/code/`)
- [ ] T002 Initialize Python project with `requirements.txt` (transformers, torch-cpu, scikit-learn, pandas, numpy, librosa, datasets, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, design artifacts, and constraint verification that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This includes verifying the statistical methodology override and data schemas.

- [ ] T004 Create `config.py` with global paths, random seeds, and memory limits (limited capacity)
- [ ] T005 [P] Implement `utils/memory_monitor.py` to track peak RAM and enforce hard limits
- [ ] T006 [P] Implement `utils/logging.py` for structured logging of pipeline steps
- [~] T007 Create `data/` directory structure (`raw`, `processed`, `embeddings`)
- [~] T008 [P] **Generate `research.md`** artifact with dataset verification details (Moved from Phase 6 to align with Plan Phase 0)
- [~] T008b [P] **Generate `data-model.md`** artifact with schema definitions (Moved from Phase 6 to align with Plan Phase 0)
- [~] T008a [P] **Encoder Verification**: Implement `utils/encoder_verify.py` to test `distil-whisper/distil-large-v2` and `openai/whisper-distil-base` on CPU; log availability and memory footprint (Addresses FR-001 flexibility)
- [~] T008b [P] **Runtime Limit Assertion**: Implement `utils/runtime_verify.py` to assert that a dummy extraction of 100 samples completes in < 6h equivalent time (Addresses FR-007)
- [~] T014a [P] **Define Data Schemas**: Generate `contracts/dataset.schema.yaml` and `contracts/embedding.schema.yaml` defining input/output formats **BEFORE** data download (Addresses ordering-c952aaa0; moved from Phase 3 to Phase 2)
- [~] T018b [P] **Document Constitutional Override**: Generate `results/methodology_notes.md` explicitly documenting the override of Spec FR-006 (Binomial Test) with Constitution Principle VII (McNemar's Test) and the omission of Bonferroni correction (Addresses ordering-cd24e1ac; moved from Phase 4 to Phase 2)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Only Embedding Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Extract fixed-dimensional latent embeddings from audio samples using a frozen, lightweight encoder on CPU-only environment.

**Independent Test**: The pipeline runs on a representative subset of samples on a local CPU machine with ≤ 7 GB RAM [UNRESOLVED-CLAIM: c_12b9d44f — status=not_enough_info], outputting a valid matrix of floats without OOM errors.

### Implementation for User Story 1

- [~] T009 [US1] Implement `data/download.py` to fetch real audio data from verified source `audio_bench/jailbreak_v1` (via `datasets` library) with checksum verification; fallback to `audio_bench` if config missing (Addresses executability-926f92f3)
- [~] T014b [US1] **Validate Schemas**: Implement `data/validate.py` to verify downloaded data against `contracts/dataset.schema.yaml` (Addresses executability-d5676129)
- [~] T010 [US1] Implement `data/preprocess.py` to load audio files using `librosa`, normalize, and handle corrupted headers (skip/log)
- [ ] T011 [US1] Implement `data/extract.py` to load frozen `distil-whisper/distil-large-v` (CPU mode, fallback `openai/whisper-distil-base`) and extract embeddings in batches (Addresses executability-5bd844ff)
- [ ] T012 [US1] Add memory monitoring logic in `data/extract.py` to ensure peak RAM ≤ 6.5 GB [UNRESOLVED-CLAIM: c_7d54b83b — status=not_enough_info]
- [ ] T013 [US1] Write output embeddings to `data/embeddings/` as `.npy` or `.parquet` (verify no NaN/Inf)

**Checkpoint**: Embeddings extracted successfully; US1 functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Binary Classifier Training & Evaluation (Priority: P2)

**Goal**: Train a Logistic Regression classifier on embeddings to distinguish "jailbreak" vs "benign" and evaluate performance.

**Independent Test**: Model trains on pre-computed embeddings, outputs a confusion matrix, and calculates Recall/FPR.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `models/train.py` to load embeddings and labels
- [ ] T015b [US2] **Implement Stratified Split**: Explicitly implement and log the stratified 80/20 split [UNRESOLVED-CLAIM: c_ccc8fc44 — status=not_enough_info] logic in `models/train.py` to satisfy FR-003 (Addresses coverage-b51c41a3)
- [ ] T016 [US2] Train Logistic Regression model in `models/train.py` (with SVM fallback logic if needed)
- [ ] T017 [US2] Implement `models/eval.py` to compute Precision, Recall, FPR, and AUC-ROC on held-out test set
- [ ] T017a [US2] Implement **Majority-Class Predictor Baseline** in `models/eval.py` to compute metrics for SC-001 verification (Secondary Verification only; distinct from Primary Validation) (Addresses constraint_preservation-f1e7d30f)
- [ ] T018 [US2] Implement **McNemar's Test** in `models/eval.py` comparing classifier against a **random-guessing baseline** (using `DummyClassifier(strategy='stratified')` with fixed seed) per Constitution Principle VII. *Note: This is a Staged Deviation from Spec FR-006; see `results/methodology_notes.md` (T018b).* (Addresses executability-8128fa79, constraint_preservation-bcf9da83, F001)
- [ ] T018c [US2] **Implement Threshold Check**: Explicitly implement the `p < 0.05` threshold check and pass/fail logic for SC-003 in `models/eval.py` (Addresses coverage-5ebaf3a7)
- [ ] T019 [US2] Log all metrics to `results/metrics.json` for automated parsing (Constitution Principle IV)

**Checkpoint**: Classifier trained and evaluated; US2 functional and testable independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds and validate robustness.

**Independent Test**: Script sweeps thresholds across a range of values. and generates a report showing Recall/FPR variation.

### Implementation for User Story 3

- [ ] T020 [US3] Implement `models/eval.py` threshold sweep logic (Unit test logic)
- [ ] T020a [US3] **Generate Synthetic Data**: Implement `tests/generate_synthetic.py` to create synthetic data with known properties for T020 unit tests (Addresses executability-f0b31241)
- [ ] T021 [US3] Run sensitivity analysis unit tests with synthetic data to verify sweep logic independence
- [ ] T022 [US3] **Run Real Data Sensitivity**: Sweep thresholds over the **exact set {0.3, 0.4, 0.5, 0.6, 0.7}** on actual model scores from T017/T018 and generate `results/sensitivity_report.md` (Addresses coverage-82d145dd)
- [ ] T022a [US3] **Document Bonferroni Omission**: In `results/sensitivity_report.md`, explicitly cite Constitution Principle VII and link to `results/methodology_notes.md` (T018b) as the justification for omitting Bonferroni correction (Staged Deviation from Spec US-3) (Addresses constraint_preservation-71bbe128)
- [ ] T022b [US3] Document justification for threshold 0.5 default and confirm stability against minor deviations

**Checkpoint**: Sensitivity analysis complete; US3 functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T024 [P] Write unit tests for data loading and embedding extraction in `tests/test_data.py`
- [ ] T025 [P] Write unit tests for model training and statistical tests in `tests/test_model.py`
- [ ] T026 [P] Write unit tests for sensitivity analysis in `tests/test_stats.py`
- [ ] T027 Run full pipeline end-to-end on CI (GitHub Actions free-tier) to verify ≤ 6h runtime
- [ ] T027a [P] **Assert Runtime Limit**: Explicitly assert that the total pipeline runtime is ≤ 6h [UNRESOLVED-CLAIM: c_a90babae — status=not_enough_info] in the CI script; fail if exceeded (Addresses coverage-c452d5c7)
- [ ] T029a [P] Generate `specs/001-llmxive-follow-up-extending-a-survey-of/amendment_report.md` explicitly listing: (1) FR-006 Binomial Test vs Constitution McNemar's Test conflict, (2) Bonferroni omission justification, (3) Proposed spec amendments. *MUST be completed before final research acceptance.*
- [ ] T029b [P] Review `amendment_report.md` and update `spec.md` to reflect Constitution requirements (if approved)
- [ ] T030 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Depends on US1 completion (requires embeddings)
- **User Story 3 (P3)**: Depends on US2 completion (requires model scores)

### Within Each User Story

- Models before services (where applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data loading in tests/test_data.py"
Task: "Unit test for embedding extraction in tests/test_data.py"

# Launch all models for User Story 1 together:
Task: "Implement data/download.py"
Task: "Implement data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify embeddings extracted within RAM limits)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Sensitivity Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on free-tier CI (CPU, standard memory constraints, No GPU). No 8-bit quantization or CUDA usage allowed.
- **Critical Constraint**: Use **McNemar's Test** (Constitution) instead of Binomial Test (Spec). Primary test baseline is **random-guessing**. Spec's majority-class baseline is handled separately in T017a as a secondary verification.
- **Critical Constraint**: Use **real datasets** only; no synthetic data or fabricated results.
- **Critical Constraint**: **No Bonferroni correction** applied to dependent metrics per Constitution Principle VII (Staged Deviation; see T018b/T022a).
- **Critical Constraint**: Schema generation (T014a) is now in Phase 2 to define data flow before extraction (T013).
- **Critical Constraint**: T008a/T008b verify encoder availability and runtime limits before data processing begins.
- **Critical Constraint**: T027a explicitly asserts the 6h runtime limit as a pass/fail condition.