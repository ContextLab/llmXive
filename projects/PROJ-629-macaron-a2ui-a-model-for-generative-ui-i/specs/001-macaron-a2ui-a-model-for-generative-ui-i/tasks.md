# Tasks: Macaron-A2UI Reproduction & Validation

**Input**: Design documents from `/specs/001-macaron-a2ui-reproduction/`
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

## Phase 0: Research & Feasibility (Blocking Prerequisite)

**Purpose**: Verify weights and feasibility. **MUST complete before Phase 1**.

- [X] T001 [P] **Inspect `vendor/Macaron-A2UI-Bench`**: 
  1. Identify default model weights and configuration files.
  2. Check `vendor/Macaron-A2UI-Bench/models/` for exact weights or GGUF equivalents.
  3. Create `research.md` with findings, listing specific file paths found.
- [X] T002 [P] **Verify Model Weights**: 
  1. Check if exact model weights (or GGUF equivalent) exist in `vendor/Macaron-A2UI-Bench`.
  2. **Deliverable**: Update `research.md` with a JSON block: `{"weight_status": "found"}` OR `{"weight_status": "uncomputable", "reason": "Missing exact weights"}`.
  3. If `uncomputable`, **STOP** downstream execution.
- [X] T003 [P] **Determine Inference Engine**: 
  1. If T002 status is `found`, select `llama-cpp-python` for CPU quantization.
  2. Document decision in `research.md`.
  3. If T002 status is `uncomputable`, mark `research.md` status as `uncomputable` and exit.

**Checkpoint**: Phase 0 complete. If `research.md` status is `uncomputable`, **STOP**. Do not proceed to Phase 1.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004 [P] **Create Project Structure**: 
  Run the following commands to create directories:
  `mkdir -p vendor/Macaron-A2UI-Bench data/eval_300 results render/public/showcase scripts tests/contract tests/integration contracts`
  Verify all directories exist.
- [X] T005 [P] **Initialize Python 3.10 Project**: 
  1. Run `python -m venv venv`.
  2. Create `requirements.txt` using: `cat > requirements.txt << 'EOF'
torch>=2.0.0
transformers>=4.30.0
llama-cpp-python>=0.2.0
Pillow>=9.0.0
jsonschema>=4.0.0
pytest>=7.0.0
EOF`
- [X] T006 [P] **Configure Linting**: Install `flake8` and `black`. Add `.flake8` config to project root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **All tasks here depend on T002 status 'found'**.

- [X] T007 [P] **Verify Submodule & Dependencies**: 
  1. Ensure `vendor/Macaron-A2UI-Bench` is checked out.
  2. Run `pip install -r vendor/Macaron-A2UI-Bench/requirements.txt` (if exists) and `pip install -r requirements.txt`.
  3. **Check T002 status in `research.md`**. If `uncomputable`, skip to Phase 5 (T030).
- [X] T008 [P] **Create Evaluation Report Schema**: 
  Create `contracts/evaluation_report.schema.yaml` defining: `model_name`, `status` (success/uncomputable/timeout/incomplete), `overall_score`, `dataset_scores`, `delta`.
  **Note**: `status` must accept 'incomplete' for runs that time out but produced partial results.
- [X] T009 [P] **Create Task Instance Schema**: 
  Create `contracts/task_instance.schema.yaml` defining input data structure for `annomi`, `esconv`, `multiwoz`, `sgd`.
- [X] T010 [P] **Implement Setup Script**: 
  Create `scripts/setup-evaluation.sh` to:
  1. Configure `device="cpu"`, `quantization="q4_k_m"`.
  2. Install `llama-cpp-python`.
  3. Set a timeout for the main execution.
- [X] T011 [P] **Implement Dataset Handling Logic**: 
  Update `scripts/setup-evaluation.sh` to:
  1. Copy files from `vendor/Macaron-A2UI-Bench/data/eval_300/` to `data/eval_300/`.
  2. Validate that `annomi_tasks.json`, `esconv_tasks.json`, `multiwoz_tasks.json`, `sgd_tasks.json` exist.
  3. Validate JSON structure against `contracts/task_instance.schema.yaml`.
- [X] T012 [P] **Implement Contract Tests**: 
  Create `tests/contract/test_evaluation_schema.py` to validate generated reports against `contracts/evaluation_report.schema.yaml`.
- [X] T013 [P] **Implement Integration Tests**: 
  Create `tests/integration/test_cpu_execution.py` to verify `evaluate_api_model.py` runs without CUDA errors.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Execution of Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored `Macaron-A2UI-Bench` evaluation script on a CPU-only CI runner to verify end-to-end execution and artifact generation.

**Independent Test**: The CI job completes successfully (exit code 0), and the output directory contains `results/evaluation_report.json`.

### Implementation for User Story 1

- [X] T016 [US1] **Configure Evaluation Script**: 
  1. **Verify T002 status in `research.md`**. If status is `uncomputable`, DO NOT configure; skip to T030.
  2. If `found`, configure `evaluate_api_model.py` to use `llama-cpp-python` with `Q4_K_M` quantization and `batch_size=1`.
  3. Ensure `device="cpu"` is hardcoded.
- [X] T017 [US1] **Add Timeout Handling & Status Flag**: 
  Ensure `scripts/setup-evaluation.sh` and `evaluate_api_model.py`:
  1. Detect if the time limit is exceeded.
  2. If timeout occurs, write `results/evaluation_report.json` with `status: "incomplete"` (as defined in T008 schema).
  3. Ensure the script exits with code 0 even on timeout to allow artifact inspection.
- [X] T018 [US1] **Ensure Partial Results**: 
  Ensure `results/evaluation_report.json` is generated even if the run is incomplete (partial results) with `status="incomplete"`.
- [X] T019 [US1] **Validate CUDA Errors**: 
  Add validation to ensure no CUDA-related errors occur during model loading or inference.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Artifact Generation and Visualization (Priority: P2)

**Goal**: Generate specific visual comparison artifacts (PNG images) and renderable data files to validate the "Generative UI" aspect.

**Independent Test**: The run produces at least 10 distinct PNG comparison images in `render/public/showcase/qwen-235b-rl/images/compare/`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for PNG generation count in `tests/contract/test_artifact_count.py`.
- [X] T021 [P] [US2] Integration test for `render/index.html` rendering in `tests/integration/test_render_display.py`.

### Implementation for User Story 2

- [X] T022 [P] [US2] **Verify PNG Generation**: 
  1. Check `render/public/showcase/` for files generated by `evaluate_api_model.py`.
  2. Verify PNGs exist for tasks from `annomi_tasks.json`, `esconv_tasks.json`, `multiwoz_tasks.json`, `sgd_tasks.json`.
  3. **Do not use `render_check.py`**; rely on `evaluate_api_model.py` output.
- [X] T023 [US2] **Implement PNG Logic**: 
  Ensure PNGs are saved to `render/public/showcase/qwen-235b-rl/images/compare/`.
- [X] T024 [US2] **Verify HTML Rendering**: 
  Ensure `render/index.html` correctly references generated PNGs without broken links.
- [X] T025 [US2] **Validate PNG Count**: 
  Add validation to confirm at least 10 distinct PNG images are generated from the four specific dataset files (`annomi`, `esconv`, `multiwoz`, `sgd`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantitative Score Validation (Priority: P3)

**Goal**: Calculate and report the "Overall" score and sub-metrics to compare against the paper's claimed score.

**Independent Test**: The evaluation report contains a numeric "Overall" score and a summary table comparing the reproduced score to the paper's baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for score delta calculation in `tests/contract/test_score_delta.py`.
- [X] T027 [P] [US3] Integration test for score validation logic in `tests/integration/test_score_validation.py`.

### Implementation for User Story 3

- [X] T028 [P] [US3] **Extract Scores**: 
  Implement logic to extract "Overall" score and sub-scores (consistency, execution rate) from `results/evaluation_report.json`.
- [X] T029 [US3] **Calculate Delta**: 
  Implement logic to calculate the delta between the reproduced score and the paper's claim. **ONLY IF T002 status is 'found'**.
- [X] T030 [US3] **Flag Uncomputable**: 
  1. Read `research.md` status.
  2. If `uncomputable`, set report status to `Uncomputable` and skip delta calculation.
  3. If `found`, proceed with T029.
- [X] T031 [US3] **Handle Timeouts**: 
  Ensure the report includes `status: "incomplete"` if the run fails to produce a valid score due to timeout. Do not use 'uncomputable' for timeouts; use 'incomplete' as per T008/T017.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] **Documentation**: Update `quickstart.md` with specific reproduction commands (e.g., `./scripts/setup-evaluation.sh`).
- [X] T033 **Code Cleanup**: Refactor `scripts/setup-evaluation.sh` to reduce complexity.
- [X] T034 **Performance Optimization**: Tune `n_threads`, `n_ctx` for `llama-cpp-python` inference on CPU.
- [X] T035 [P] **Unit Tests**: Add additional unit tests for schema validation in `tests/unit/`.
- [X] T036 **Security Hardening**: 
  1. Create `.env.example` with `HUGGING_FACE_HUB_TOKEN` placeholder.
  2. Implement log masking for environment variables in `scripts/setup-evaluation.sh`.
- [X] T037 **Validation**: Run `quickstart.md` validation to ensure reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately. **MUST complete with status 'success'**.
- **Phase 1 (Setup)**: Depends on Phase 0 completion (T002 status 'found'). **Blocks all downstream tasks**.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion. **Blocks all user stories**.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
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
Task: "Contract test for evaluate_api_model.py output schema in tests/contract/test_evaluation_schema.py"
Task: "Integration test for CPU-only execution in tests/integration/test_cpu_execution.py"

# Launch all models for User Story 1 together:
Task: "Configure evaluate_api_model.py to use llama-cpp-python with Q4_K_M quantization"
Task: "Implement logic in scripts/setup-evaluation.sh to handle datasets"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research (T001-T003) - **CRITICAL GATE**
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
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
- **CRITICAL**: If T002 sets `research.md` status to `uncomputable`, **STOP**. Do not proceed.
- **Status Definitions**:
  - `success`: Run completed within time limits and produced full results.
  - `timeout`: Run exceeded time limits but produced partial results (status: incomplete).
  - `uncomputable`: Run could not proceed due to missing weights or critical errors.
  - `incomplete`: The status value written to the report when a timeout occurs.