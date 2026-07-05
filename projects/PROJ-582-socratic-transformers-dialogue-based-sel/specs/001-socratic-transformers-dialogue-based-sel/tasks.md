# Tasks: Socratic Transformers: Dialogue-Based Self-Teaching Through Adversarial Questioning

**Input**: Design documents from `/specs/582-socratic-transformers-dialogue-based-sel/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`, `src/data/`, `src/train/`, `src/eval/`, `src/analyze/`, `src/utils/`, `tests/`, `tests/contract/`, `tests/integration/` and files `requirements.txt`, `src/__init__.py`, `tests/__init__.py`.
- [X] T002 Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files
- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle `DEGENERATE_DIALOGUE_TRUNCATED` events as JSON lines (Edge Case requirement)
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`
- [~] T007 Create base model loader utility in `src/utils/model_loader.py` supporting Low-bit quantization (GGUF or `bitsandbytes` CPU backend) to fit Limited RAM constraint.
- [~] T008 Implement prediction error proxy calculator in `src/utils/metrics.py` using log-probability normalized by sequence length (per Assumptions)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset (e.g., 50 samples) and verify the output files contain both static tuples and dialogue tuples with critique fields populated.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for dialogue tuple schema in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique` (with `confidence_score`, `reasoning_snippet`), and `revised_answer`.
- [~] T011 [P] [US1] Integration test for degenerate dialogue truncation in `tests/integration/test_generation.py`: implement `test_degenerate_dialogue_truncation` to assert that n-gram overlap > 0.9 triggers `DEGENERATE_DIALOGUE_TRUNCATED` log and truncates the dialogue.

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement)
- [~] T013 [US1] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001).
- [~] T014 [US1] Implement self-critique generator in `src/data/generate_dialogue.py` that:
 1. Uses the base model to generate an initial answer.
 2. Generates a critique prompt dynamically to identify logical contradictions or unsupported assumptions (per FR-002).
 3. Outputs a structured JSON with `confidence_score` and `reasoning_snippet`.
 4. Detects n-gram overlap > 0.9 and logs `DEGENERATE_DIALOGUE_TRUNCATED` (Edge Case).
- [~] T015 [US1] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent token length (FR-007). **Note**: This task depends on T014 output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Contract test for training completion and OOM handling in `tests/contract/test_training.py`: implement `test_training_completion` to assert training finishes within 6 hours and logs accuracy; `test_oom_fallback` to assert fallback to a smaller-scale model on OOM

Research question: How can computational resource constraints be managed during model inference?
Method: Implement an adaptive fallback mechanism that switches to a lower-capacity model when out-of-memory errors occur.
References: [Citation placeholder].
- [~] T019 [P] [US2] Integration test for hard timeout enforcement in `tests/integration/test_train_loop.py`: implement `test_timeout_enforcement` to assert the *job* fails gracefully within the 6-hour limit and that the *experiment runner* enforces this across the 10 seeds (FR-008, SC-003).

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [~] T021 [US2] Implement CPU-safe training loop in `src/train/train_loop.py` with hard timeout (FR-008) and fallback to smaller model (B Phi-1.5) if OOM occurs.
- [~] T022 [US2] Implement evaluation script in `src/eval/benchmark.py` running GSM8K test split and MMLU STEM subset, logging accuracy.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from 10 seeds and verify the statistical test output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for statistical significance output in `tests/contract/test_stats.py`: implement `test_statistical_output` to assert JSON output contains `p_value`, `method`, and `corrected_alpha`.
- [ ] T026 [P] [US3] Integration test for multiple-comparison correction in `tests/integration/test_analysis.py`: implement `test_bonferroni_correction` to assert p-values are adjusted when testing ≥ 2 benchmarks.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement statistical analysis script in `src/analyze/stats.py` running paired t-tests on multiple seeds per condition.
- [ ] T028 [US3] Implement Bonferroni/FDR correction in `src/analyze/stats.py` for multiple benchmarks (FR-006).
- [ ] T029 [US3] Implement sensitivity analysis sweep over prediction error threshold values {0.01, 0.05, 0.1} as defined in SC-004 (log-prob proxy) to validate robustness.
- [ ] T031 [US3] Implement ablation comparison logic in `src/analyze/stats.py` contrasting Dialogue vs. Ablation vs. Static conditions to isolate the critique signal. **Note**: This task depends on T015 and T014 output.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T032 [P] Update `research.md` to explicitly distinguish between (a) engine executing a pre-ordained self-improvement procedure and (b) genuine origination, addressing **Ada Lovelace's** repeated concerns about "origination" vs. "operations".
- [ ] T033 [P] Refine problem statement in `spec.md` to frame the adversarial component as "evolutionary pressure" or "negative selection on belief" rather than "self-teaching", addressing **David Krakauer's review**.
- [ ] T034 Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T035 Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.
- [ ] T044 [P] [Review] Document the operational distinction between "generative capability" (required by FR-001) and "deterministic operation" (Ada Lovelace's constraint) in `docs/philosophy.md`, clarifying that the system generates via ordered operations on internal states rather than spontaneous origination (Review: ada-lovelace-simulated__2026-05-17, alan-turing-simulated__2026-05-17).

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
 - **Internal Dependency**: T013 depends on T012 completion.
 - **Internal Dependency**: T014 depends on T012 completion.
 - **Internal Dependency**: T015 depends on T014 completion.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **Internal Dependency**: T031 depends on T014 and T015 completion.

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
Task: "Contract test for dialogue tuple schema in tests/contract/test_schemas.py"
Task: "Integration test for degenerate dialogue truncation in tests/integration/test_generation.py"

# Launch independent models for User Story 1 together:
Task: "Implement dataset downloader in src/data/download.py" (T012)
Task: "Implement static QA extractor in src/data/static_extractor.py" (T013)
Task: "Implement self-critique generator in src/data/generate_dialogue.py" (T014)

# Note: T015 (ablation generator) MUST run AFTER T014 completes.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012 -> T013 -> T014 -> T015)
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
 - Developer A: User Story 1 (Data Generation: T012, T013, T014, T015)
 - Developer B: User Story 2 (Training & Evaluation: T020, T021, T022)
 - Developer C: User Story 3 (Stats & Ablation: T027, T028, T029, T031)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Review Alignment**:
 - **Alan Turing**: Tasks T008 (prediction error proxy), T029 (sensitivity sweep), T038 (Verification Step - removed), T039 (Threshold Gate), and T040 (Attention Analysis - removed) address the need for operational definitions, learning signals, and empirical evidence. T044 documents the operational distinction.
 - **Ada Lovelace**: Tasks T032 (Origination vs. Operations) and T044 (Operational Distinction) address the philosophical constraint that the engine cannot originate, only execute ordered operations. T036/T037 (Formal Question Language) were removed as contradictory to FR-001.
 - **Daniel Kahneman**: Tasks T008 (Calibration), T029 (Sensitivity), and T042 (System 2 Checkpoint - removed) address over-confidence, availability heuristics, and bias detection.
 - **Dan Rockmore**: Task T041 (Productive Ignorance Metric) addresses the measurement of the "gap" and the limits of context.
 - **David Krakauer**: Tasks T033 (Reframing as negative selection) and T043 (Clarifying Instruction vs. Selection - removed) address the distinction between instruction and evolutionary pressure.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All training tasks (T021) must strictly adhere to 4-bit quantization and 1.5B model fallback to ensure execution on 7GB RAM free-tier runners. No GPU tasks allowed.