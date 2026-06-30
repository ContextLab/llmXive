# Tasks: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

**Input**: Design documents from `/specs/611-antisd-reproduction/`
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

- [X] T001a [P] Create `src/` directory at repository root for source code
- [X] T001b [P] Create `scripts/` directory at repository root for utility scripts
- [X] T001c [P] Create `data/`, `data/processed/`, and `data/logs/` directories at repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Create `scripts/install_cpu_deps.sh` to install `torch` (CPU wheel), `transformers`, `datasets`
- [X] T005 [P] Create `scripts/diagnose.py` to verify `torch.cuda.is_available() == False` and `device="cpu"`
- [X] T006 Create `src/utils.py` for logging, clamping, and error handling infrastructure
- [X] T007 Create `src/antisd_core.py` skeleton for Divergence ascent & entropy gate logic
- [X] T008 [P] Setup `data/processed/` and `data/logs/` directories

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Initialize the project environment on a standard CPU-only CI runner without requiring GPU drivers, CUDA, or large model downloads.

**Independent Test**: A clean GitHub Actions runner executes the environment setup script and completes without crashing due to missing CUDA libraries or out-of-memory errors, producing a `requirements.txt` compatible with CPU-only execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `scripts/diagnose.py` CPU detection in `tests/unit/test_diagnose.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `scripts/install_cpu_deps.sh` using `pip install torch --index-url
- [X] T011 [US1] Implement `scripts/diagnose.py` to report "CPU Mode Active" and confirm PyTorch availability
- [X] T012a [US1] Implement model size check in `scripts/diagnose.py` to abort with error "Model too large for CPU-only runner" if model weights > 7GB are detected or requested
- [X] T014 [US1] Verify `requirements.txt` generation excludes CUDA-specific packages (e.g., `nvidia-cudnn`, `bitsandbytes`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preprocessing and Sample Execution (Priority: P2)

**Goal**: Preprocess a small, representative subset of the math dataset (GSM8k) and execute a single training step to verify the AntiSD logic.

**Independent Test**: The user runs the preprocessing script on a sample subset of GSM8k and executes the training script with `--max-steps 1` and `--use-cpu`, observing the generation of a loss log that reflects the AntiSD objective.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for `src/antisd_core.py` entropy gate logic in `tests/unit/test_antisd_core.py`
- [X] T016 [P] [US2] Unit test for NaN clamping in `src/utils.py` in `tests/unit/test_utils.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement `scripts/preprocess_math_datasets.py` to download `openai/gsm8k` and limit to 50 samples
- [X] T017a [US2] Download the `TinyLlama-Chat-v1.0` model weights and verify file size is approximately consistent with the expected scale for a model of this architecture. and matches SHA256 checksum to ensure availability for trace synthesis
- [X] T018 [US2] Implement "Trace Synthesis" logic in `scripts/preprocess_math_datasets.py` using `TinyLlama-1.1B-Chat-v1.0` to generate `reasoning_trace`
- [X] T018a [US2] Implement Trace Validator in `scripts/preprocess_math_datasets.py` to verify generated traces contain >= 3 logical steps; parse the last line of the trace for the boxed answer string, normalize both the extracted answer and the ground truth solution, and compare them to ensure the final answer matches.
- [X] T019 [US2] Add validation in `scripts/preprocess_math_datasets.py` to abort if `reasoning_trace` is missing, empty, or fails T018a validation
- [X] T020 [US2] Output `data/processed/gsm8k_cot_50_samples.jsonl` with required fields (prompt, solution, reasoning_trace)
- [X] T021 [US2] Implement `src/antisd_core.py` to calculate "Divergence" loss and "Teacher Entropy"
- [X] T022 [US2] Implement "entropy-triggered gate" in `src/antisd_core.py` (disable AntiSD if entropy < 0.01)
- [X] T023 [US2] Implement NaN clamping logic in `src/antisd_core.py` to clamp entropy to 0.0 if NaN
- [X] T024 [US2] Create `run/olmo3-instruct/antisd.sh` wrapper to launch training with `--max-steps` and `--use-cpu` flags
- [X] T025 [US2] Implement single-step training loop in `src/antisd_core.py` that logs `antisd_loss`, `teacher_entropy`, and `gate_status`, and explicitly returns/exposes the computed gradient vector for the AntiSD loss.
- [X] T026a [US2] Implement baseline gradient calculation in `src/antisd_core.py` by computing the gradient of the standard RL loss (PPO/GRPO) with AntiSD weight set to 0, to serve as the reference vector for comparison.
- [X] T026 [US2] Add "Gradient Direction Check" in `src/antisd_core.py` to compare the AntiSD gradient (from T025) against the baseline gradient (from T026a) and log direction (AntiSD vs SD)
- [X] T027 [US2] Output `data/logs/antisd_step_log.jsonl` with metrics for each step
- [X] T028 [US2] Verify memory usage < 6 GB during single-step execution using tracemalloc to measure peak RSS of the Python process

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Artifact Generation and Validation Report (Priority: P3)

**Goal**: Generate the final validation artifacts (figures, logs, and a summary report) comparing observed behavior against the paper's claims.

**Independent Test**: The pipeline finishes and generates a `validation_report.md` and `figures/validation_trace.png` in the `data/` directory, which are committed to the repository.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for `validation_report.md` structure in `tests/contract/test_report.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `scripts/rollout_viewer.py` to parse logs and generate report
- [X] T031 [US3] Generate `validation_report.md` with fields: Run ID, Steps Executed, Loss Value, Gate Status, Gradient Direction, Conclusion
- [X] T032 [US3] Add "Limitations" section to `validation_report.md` explicitly stating Statistical efficacy cannot be determined from a limited sample size.
- [X] T033a [US3] Implement logic to calculate "Paper Claimed Steps" (2-10x fewer than baseline) and generate the specific "Limitations" text comparing 1-step run to multi-step claim
- [X] T033 [US3] Add comparison table to `validation_report.md` (Observed Steps vs Paper Claimed Steps) using T033a output and ensure "Limitations" text is included in the report body
- [X] T034 [US3] Generate `data/figures/validation_trace.png` showing loss curve for the limited run
- [X] T035 [US3] Ensure `validation_report.md` status is "Partial Reproduction" or "Algorithm Validated" based on results, and includes Limitations section and comparison table as mandatory conditions
- [X] T036 [US3] Verify `data/figures/validation_trace.png` size is < 10 MB

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037a [P] Update `README.md` with project overview, setup instructions, and CPU-only constraints
- [X] T037b [P] Update `CONTRIBUTING.md` with development guidelines and task execution flow
- [X] T038a Code cleanup: Run `ruff check` and fix all linting errors across `src/` and `scripts/`
- [X] T040 [P] Additional unit tests (if requested) in `tests/unit/`
- [X] T041 Security hardening
- [X] T042 Run `quickstart.md` validation

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
Task: "Unit test for `scripts/diagnose.py` CPU detection in `tests/unit/test_diagnose.py`"

# Launch all models for User Story 1 together:
Task: "Implement `scripts/install_cpu_deps.sh`"
Task: "Implement `scripts/diagnose.py`"
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
