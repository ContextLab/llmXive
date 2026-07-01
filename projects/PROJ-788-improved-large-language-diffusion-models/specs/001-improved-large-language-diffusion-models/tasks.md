# Tasks: Reproduce & Validate iLLaDA

**Input**: Design documents from `/specs/788-reproduce-illada/`
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

- [X] T001 Create project structure per implementation plan (`src/llada`, `src/data/subsets`, `src/results`)
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (torch-cpu, transformers, accelerate, datasets, opencompass)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/evaluation_result.schema.yaml` for result validation
- [X] T005 Create `contracts/dataset_subset.schema.yaml` for subset metadata
- [X] T006 [P] Implement `src/utils/hardware_logger.py` to log CPU cores, RAM peak, and `torch.cuda.is_available()` status
- [X] T007 Create `src/utils/memory_guard.py` to handle OOM fallback (N=5 -> N=1) and update `subset_id`
- [X] T008 [P] Configure environment configuration to explicitly enforce CPU-only device selection, ensuring no GPU device selection is attempted and verifying `torch.cuda.is_available()` returns False

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-Tractable Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run `eval_llada.py` on a CPU-only runner with a restricted subset (N=5) to confirm execution without CUDA errors or OOM crashes.

**Independent Test**: Trigger CI job with minimal subset; verify exit code 0 and non-empty `results.json`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `eval_llada.py` output schema in `tests/contract/test_eval_schema.py`
- [X] T010 [P] [US1] Integration test for memory fallback logic in `tests/integration/test_oom_fallback.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Create `src/llada/eval_llada.py` entry point with `--device cpu` and `--subset_size` flags
- [X] T012 [US1] Implement model loading logic in `src/llada/model_loader.py` using `torch_dtype=torch.float16` (no bitsandbytes) with explicit fallback to float32 or lower precision if OOM occurs
- [X] T013 [US1] Implement dataset loading in `src/llada/data_loader.py` using `datasets.load_dataset` to fetch 'bbh', 'arc', or 'gsm8k' datasets from HuggingFace
- [X] T014 [US1] Integrate `src/utils/memory_guard.py` to handle OOM and fallback to N=1 if needed
- [X] T015 [US1] Add hardware logging via `src/utils/hardware_logger.py` at the start of `eval_llada.py`
- [X] T016 [US1] Ensure `results.json` is written with benchmark names and scores even if partial, verifying schema keys: `{"status": "partial", "subset_id": "...", "metrics": {"key": "value"}}`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural & Qualitative Verification (Priority: P2)

**Goal**: Parse generated metrics and verify structural conformance to the defined schema (qualitative check only). Quantitative score matching against the paper is NOT APPLICABLE per Plan.

**Independent Test**: Run evaluation on `bbh` subset; verify output JSON keys match `opencompass` standard and values are present.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for result parsing in `tests/contract/test_result_parser.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Create `src/llada/validator.py` to parse `results.json` and check against `contracts/evaluation_result.schema.yaml`
- [X] T019 [US2] Implement qualitative logging in `src/llada/comparator.py` to log metric names, data types, and structural validity (non-null values) without comparing against paper claims
- [X] T020 [US2] Update `eval_llada.py` to call `validator` and `comparator` post-evaluation
- [X] T021 [US2] Integrate with User Story 1 components (use `results.json` from T016)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Visual Artifacts and Logs (Priority: P3)

**Goal**: Generate visualization artifacts (SVG/PNG) demonstrating the diffusion generation process (masking/unmasking steps).

**Independent Test**: Run visualization script; check for existence of SVG/PNG files in `results/artifacts/`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Contract test for artifact generation in `tests/contract/test_artifact_gen.py`

### Implementation for User Story 3

- [X] T023 [P] [US3] Create `src/llada/visualization/diffusion_visualizer.py` to generate `diff_remask.gif` or `LLaDA_vs_LLaMA.svg`
- [X] T024 [US3] Implement `src/llada/generate.py` to output intermediate token states (masking steps) to a log file
- [X] T025 [US3] Update `eval_llada.py` to trigger `diffusion_visualizer` after generation
- [X] T026 [US3] Ensure output directory `src/results/artifacts/` is created and populated

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027a [P] Update README.md with `--device`, `--subset_size`, and `--seed` flags
- [X] T027b [P] Verify CLI help text matches spec requirements for all new flags
- [X] T028 Refactor `src/llada/eval_llada.py` to reduce cyclomatic complexity to <10 and remove unused imports
- [X] T029 Run `quickstart.md` validation to ensure end-to-end flow works
- [X] T030 [P] Add unit tests for `src/utils/memory_guard.py` and `src/llada/data_loader.py`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `results.json` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on generation output from US1

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
Task: "Contract test for eval_llada.py output schema in tests/contract/test_eval_schema.py"
Task: "Integration test for memory fallback logic in tests/integration/test_oom_fallback.py"

# Launch all models for User Story 1 together:
Task: "Create src/llada/eval_llada.py entry point"
Task: "Create src/llada/model_loader.py"
Task: "Create src/llada/data_loader.py"
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
- **Critical Constraint**: All tasks must run on CPU-only, multi-core, 7GB RAM runner. No low-bit quantization, no CUDA, no full dataset loads.