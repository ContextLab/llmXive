# Tasks: Reproduce & Validate ProRL

**Input**: Design documents from `/specs/640-reproduce-prorl/`
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

- [X] T001 Create directory structure: `mkdir -p src/prorl tests/contract tests/integration data/books ckpt logs reports`
- [X] T002 Create `pyproject.toml` with `[project]` section and `dependencies` list (torch, transformers, scikit-learn, pandas, numpy) AND create `requirements.txt` with pinned CPU-only versions (e.g., `torch --index-url https://download.pytorch.org/whl/cpu`)
- [X] T003 Create `.flake8` config file and add `[tool.black]` section to `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/prorl/dataset.py` with `DatasetSampler` class structure (empty methods only)
- [X] T040 [P] Implement stratified sampling method in `src/prorl/dataset.py` (extends T004)
- [X] T041 [P] Implement RSS memory monitoring and abort logic (>7GB) in `src/prorl/dataset.py` (extends T004)
- [X] T005 Implement `src/prorl/model.py` ensuring no `bitsandbytes` or CUDA-specific imports; enforce `device="cpu"`
- [X] T006 Create `contracts/dataset.schema.yaml` defining input schema for `dataset.py` (Pre-req for T004/T040/T041 - NO [P] tag)
- [X] T007 Create `contracts/metrics.schema.yaml` defining output schema for `metrics.json` (HitRate, NDCG) (Pre-req for T021 - NO [P] tag)
- [X] T008 Create `src/scripts/run_pipeline.sh` skeleton file (empty script with shebang)
- [X] T042 [P] Implement timeout enforcement logic AND missing backbone detection/abort in `src/scripts/run_pipeline.sh` (extends T008)
- [X] T009 Implement `src/scripts/validate_artifacts.py` for contract validation (FR-003, FR-004)
- [X] T010 Create `.github/workflows/ci.yml` with steps: `actions/checkout`, `actions/setup-python`, `pip install`, `pytest`, `actions/upload-artifact` for CPU-only runner

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute ProRL Pre-training and RL Training Pipelines (Priority: P1) 🎯 MVP

**Goal**: Execute the ProRL codebase end-to-end on the `Books` dataset using only CPU resources.

**Independent Test**: Run `src/scripts/run_pipeline.sh` against `data/books/` and observe creation of `ckpt/` and `logs/` without CUDA errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for dataset loading in `tests/contract/test_dataset.py` (validates FR-006)
- [X] T012 [P] [US1] Integration test for pre-training pipeline in `tests/integration/test_pretrain.py` (validates FR-001)
- [X] T013 [P] [US1] Integration test for RL training pipeline in `tests/integration/test_rl.py` (validates FR-002)

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/prorl/trainer_pretrain.py`: Load `Books` dataset; apply stratified sampling IF dataset size > 7GB; train backbone with adaptive epochs (max 100) constrained by 3h time limit; output `ckpt/backbone.pth`. Relies on T041 for memory checks.
- [X] T015 [US1] Implement `src/prorl/trainer_rl.py`: Check for `ckpt/backbone.pth`; ABORT with clear error if missing; run RL training (adaptive epochs based on time limit); output `ckpt/policy.pth`. Relies on T041 for memory checks.
- [X] T018 [US1] Ensure `trainer_pretrain.py` and `trainer_rl.py` explicitly set `torch.device("cpu")` and fail early if CUDA is detected

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Output Artifacts and Reproducibility (Priority: P2)

**Goal**: Verify that generated artifacts are structurally valid and consistent with methodology.
**⚠️ DEPENDENCY**: This phase **MUST WAIT** for Phase 3 (US1) completion to generate artifacts (`ckpt/`, `logs/`).

**Independent Test**: Run `src/scripts/validate_artifacts.py` against generated `ckpt/` and `logs/` and assert non-zero metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for checkpoint validity in `tests/contract/test_checkpoints.py` (validates FR-003)
- [X] T020 [P] [US2] Contract test for metrics schema in `tests/contract/test_metrics.py` (validates FR-004)

### Implementation for User Story 2

- [X] T021 [US2] Implement `src/prorl/evaluator.py` to extract HitRate@K and NDCG@10 from training logs and write to `logs/metrics.json`
- [X] T022 [US2] Enhance `src/scripts/validate_artifacts.py` to load `ckpt/policy.pth`, assert file size > 0, and verify no NaN tensors
- [X] T023 [US2] Enhance `src/scripts/validate_artifacts.py` to parse `logs/metrics.json` and assert values are numeric and > 0.0
- [X] T024 [US2] Define expected directory structure (ckpt/*.pth, logs/*.json) as a hardcoded Python dictionary in `src/scripts/validate_artifacts.py`
- [X] T043 [US2] Implement directory structure comparison logic in `src/scripts/validate_artifacts.py` (compare actual vs T024 schema)
- [X] T044 [US2] Assert directory structure against hardcoded schema (T024) in `src/scripts/validate_artifacts.py` (do NOT depend on research.md)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Reproduction Report (Priority: P3)

**Goal**: Generate a human-readable report summarizing the reproduction results and constraints.
**⚠️ DEPENDENCY**: This phase **MUST WAIT** for Phase 4 (US2) completion (requires `logs/metrics.json`).

**Independent Test**: Run report generation script and verify `reproduction_report.md` exists with required sections.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Integration test for report generation in `tests/integration/test_report.py` (validates FR-005)

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/scripts/generate_report.py` to aggregate `logs/metrics.json`, `ckpt/` stats, and environment info
- [X] T027 [US3] Ensure `generate_report.py` writes a section titled "Environment" with the exact text "2 vCPU, 7GB RAM, No GPU" to `reports/reproduction_report.md`
- [X] T028 [US3] Ensure `generate_report.py` includes a section comparing observed metrics against paper claims (if available) or notes deviation
- [X] T029 [US3] Write final output to `reports/reproduction_report.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Append a section titled "Running on CI" to `quickstart.md` containing the command `bash src/scripts/run_pipeline.sh`
- [X] T031 [P] Run `src/scripts/validate_artifacts.py` as a final sanity check in the CI workflow
- [X] T032 Run `black --check src/prorl/` and refactor `src/prorl/dataset.py` to remove duplicate imports
- [X] T033 [P] Additional unit tests for `DatasetSampler` logic in `tests/unit/test_dataset.py`
- [X] T034 Verify `requirements.txt` pins CPU-only versions of `torch` and `transformers`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - T006, T007 must be completed/reviewed before T004, T021 implementation
- **User Stories (Phase 3+)**: Strict serial dependency enforced
  - **Phase 3 (US1)**: Can start after Foundational (Phase 2).
  - **Phase 4 (US2)**: **MUST WAIT** for Phase 3 completion (requires `ckpt/` and `logs/` from US1).
  - **Phase 5 (US3)**: **MUST WAIT** for Phase 4 completion (requires `metrics.json` from US2).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Depends on User Story 1 completion** (needs artifacts)
- **User Story 3 (P3)**: **Depends on User Story 2 completion** (needs metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Foundational tasks T040, T041, T042, T018, T033, T034 can run in parallel once base classes/scripts are defined
- Once Foundational phase completes, US1 can start. US2 and US3 **cannot** start until their respective predecessors finish.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset loading in tests/contract/test_dataset.py"
Task: "Integration test for pre-training pipeline in tests/integration/test_pretrain.py"

# Launch all models for User Story 1 together:
Task: "Implement src/prorl/trainer_pretrain.py..."
Task: "Implement src/prorl/trainer_rl.py..."
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
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 artifacts)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US2 artifacts)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: (Wait for US1) then User Story 2
   - Developer C: (Wait for US2) then User Story 3
3. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on free-tier CPU-only CI (2 vCPU, 7GB RAM). No CUDA, no 8-bit quantization.
- **Sampling Strategy**: If dataset > 7GB, apply stratified sampling as per T040/T014.
- **Orchestration**: Pretrain/RL sequence and missing artifact recovery is handled in T008/T042, NOT in trainers.