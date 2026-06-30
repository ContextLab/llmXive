# Tasks: Reproduce & Validate EmbFilter

**Input**: Design documents from `/specs/682-reproduce-embfilter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

**Purpose**: Project initialization, basic structure, and issue tracking

- [X] T000 [P] Flag spec.md "Assumption about model availability" fragmentation issue (F001) for spec author review; document in `docs/issues.md`
- [X] T001 Create project structure per implementation plan (`src/embfilter_repro/`, `data/`, `outputs/`)
- [X] T002 Initialize Python project with CPU-only dependencies (`torch`, `transformers`, `datasets`, `numpy`, `scikit-learn`) in `requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (black, flake8) and pre-commit hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/embfilter_repro/utils.py` with logging helpers and CPU-device enforcement logic
- [X] T005 Create `specs/682-reproduce-embfilter/contracts/output-report.schema.yaml` defining the JSON schema for `report.json`
- [X] T006 Implement `src/embfilter_repro/run_pipeline.py` wrapper to orchestrate execution and enforce CPU constraints
- [X] T007 Create `src/embfilter_repro/__init__.py` and initialize package structure
- [X] T008 Configure environment configuration management for model paths and sample limits
- [X] T009 [P] Configure and integrate "Causal-Verb Linter" as a CI gate: create `scripts/causal_verb_lint.py` with regex pattern `r'\b(cause|causes|leads to|drives)\b'` (case-insensitive) targeting `report.json` and `outputs/*.md`; configure `.pre-commit-config.yaml` to run this script; ensure pipeline fails if matches found

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run the vendored `EmbFilter` codebase on a standard CPU-only CI runner to confirm execution without errors and production of primary artifacts.

**Independent Test**: The CI job runs `run4llama_echo.py` with a minimal sample dataset, exits with code 0, and generates non-empty `.pt` and `.json` artifacts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for pipeline execution in `tests/contract/test_pipeline_run.py`: implement `test_pipeline_execution` asserting `exit_code == 0` and `os.path.exists('outputs/embeddings.pt')`

### Implementation for User Story 1

- [X] T013 [US1] Configure and invoke existing vendored script `run4llama_echo.py`: set up environment variables (`MODEL_PATH`, `MAX_SAMPLES`) and CLI arguments (`--max_samples`, `--model_path`, `--apply_embfilter`) to load model on `device="cpu"`; ensure T013b is called to enforce CPU-only constraints
- [X] T013b [US1] Implement `check_cpu_only_env()` in `src/embfilter_repro/utils.py` to detect and raise errors if `bitsandbytes` or `torch.cuda` is available, satisfying FR-006
- [X] T012 [P] [US1] Implement `sample_dataset(input_path, max_samples, seed=42)` function in `src/embfilter_repro/utils.py` using random sampling with seed=42; accepts path to dataset file or list of strings, returns list of sampled items; `max_samples` is configurable via CLI arg `--max_samples` (no hardcoded values)
- [X] T014 [US1] Verify `EmbFilter` transformation logic in vendored code; if missing, implement wrapper to apply linear frequency-based transformation via `embfilter.apply_transformation` in `src/embfilter_repro/utils.py`
- [X] T015 [US1] Implement artifact generation in `src/embfilter_repro/run_pipeline.py` to save `.pt` embedding files to `outputs/`
- [X] T016 [US1] Add validation to ensure no CUDA memory allocation attempts occur during initialization
- [X] T017 [US1] Add logging for input/output embedding dimensions and execution duration

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Performance Against Paper Claims (Priority: P2)

**Goal**: Compare reproduction results (zero-shot downstream performance) against baseline and paper claims.

**Independent Test**: The system runs `eval.py` on a subset (e.g., STS), outputs a JSON report with Spearman correlation, and confirms the filtered score > baseline score.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for report schema validation in `tests/contract/test_report_schema.py`
- [X] T019 [P] [US2] Integration test for performance delta calculation in `tests/integration/test_performance_delta.py`

### Implementation for User Story 2

- [X] T028 [P] [US2] Implement Jinja2 report template with mandatory "Observational Study" phrasing in `src/embfilter_repro/templates/report.j2`
- [X] T020 [P] [US2] Create evaluation utility `src/embfilter_repro/eval.py` to compute Spearman correlation on STS subset (Note: Execution/Validation depends on US1 artifacts)
- [X] T021 [US2] Implement baseline (unfiltered) embedding computation in `src/embfilter_repro/eval.py` (Note: Execution/Validation depends on US1 artifacts)
- [X] T022 [US2] Implement filtered embedding evaluation in `src/embfilter_repro/eval.py` (Note: Execution/Validation depends on US1 artifacts)
- [X] T023 [US2] Implement `src/embfilter_repro/run_pipeline.py` logic to calculate and log performance delta (filtered vs baseline)
- [X] T024 [US2] Integrate `report.json` generation adhering to `specs/682-reproduce-embfilter/contracts/output-report.schema.yaml` using the template from T028
- [X] T025 [US2] Add logic to flag "Reproduction Successful" if delta meets paper's trend direction

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Document Methodological Constraints & Sensitivity (Priority: P3)

**Goal**: Confirm adherence to methodological constraints (associational analysis, explicit thresholds) and transparency.

**Independent Test**: The system parses logs to verify "Associational Analysis" framing and explicit threshold justifications in `report.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for methodology statement in `tests/contract/test_methodology_statement.py`
- [X] T027 [P] [US3] Integration test for parameter logging in `tests/integration/test_parameter_logging.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement parameter logging in `src/embfilter_repro/run_pipeline.py` to record `freq_threshold`, `dim_reduction`, and paper rationale in `report.json`
- [X] T030 [US3] Implement multiple-comparison correction logic (Bonferroni) in `src/embfilter_repro/eval.py` using `statsmodels.stats.multitest.multipletests` with warning fallback if no correction applied
- [X] T031 [US3] Add metadata to `report.json` citing the specific paper section (e.g., "Section 3.2") for threshold selection
- [X] T031b [US3] Implement 'Associational Analysis' injection logic in `run_pipeline.py` to ensure the statement is present in the final report even if template is bypassed; integrate T009 linter check as a hard gate in the pipeline run (not just pre-commit)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `docs/` including quickstart and methodology notes
- [X] T034 Code cleanup and refactoring for `src/embfilter_repro/`
- [X] T035 Performance optimization for CPU-only inference (batching adjustments)
- [X] T036 [P] Additional unit tests for edge cases (missing model, unsupported architecture) in `tests/unit/`
- [X] T037 Run `quickstart.md` validation to ensure end-to-end flow works

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 artifacts (embeddings) to evaluate
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 to generate data for reporting

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
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
Task: "Contract test for pipeline execution in tests/contract/test_pipeline_run.py"
Task: "Integration test for CPU-only model loading in tests/integration/test_cpu_loading.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset sampling logic in src/embfilter_repro/utils.py"
Task: "Configure and invoke existing vendored script run4llama_echo.py"
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
- **Critical Constraint**: All tasks MUST run on CPU-only CI with limited CPU resources and 7GB RAM. No CUDA, no 8-bit/4-bit quantization requiring `bitsandbytes`.