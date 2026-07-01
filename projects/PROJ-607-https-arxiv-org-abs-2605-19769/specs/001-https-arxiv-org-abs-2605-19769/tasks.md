# Tasks: Reproduce & Validate OpenComputer

**Input**: Design documents from `/specs/607-reproduce-opencomputer/`
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

- [X] T001 Create project structure per implementation plan (`projects/607-reproduce-opencomputer/`)
- [X] T002 Initialize Python 3.11 project with `docker-py`, `pytest`, `pandas`, `jinja2` dependencies in `projects/607-reproduce-opencomputer/requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (black, flake8) in `projects/607-reproduce-opencomputer/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup Docker daemon check script in `projects/607-reproduce-opencomputer/scripts/setup_plan.sh` to validate container runtime availability and disk quota (<14GB)
- [X] T005 [P] Implement error handling wrapper for Docker operations (image build, container run, cleanup) in `projects/607-reproduce-opencomputer/scripts/docker_utils.py`
- [X] T006 [P] Setup artifact directory structure (`results/`, `reports/`, `data/`) and JSON schema validators in `projects/607-reproduce-opencomputer/contracts/`
- [X] T007 Create base task runner logic that gracefully skips agents requiring missing API keys in `projects/607-reproduce-opencomputer/scripts/agent_registry.py`
- [X] T008 Configure environment variable loading for Docker context and task selection in `projects/607-reproduce-opencomputer/.env.example`
- [X] T007b [P] **Schema Definition**: Update `contracts/verification_report.schema.yaml` to include `manual_ground_truth` (object: task_id, manual_verdict, manual_judgment_notes) and `alignment_observation` (string) fields to support qualitative analysis (US-2).
- [X] T009 Implement "Blinding Protocol" helper script in `projects/607-reproduce-opencomputer/scripts/prepare_ground_truth.py` to anonymize artifacts for manual inspection (US-2)
- [X] T045 [P] **Schema Definition**: Define `contracts/verification_results.schema.yaml` based on the logical output requirements of FR-003 and SC-001 (not T024 implementation). Schema must include columns: `task_id`, `verifier_verdict`, `manual_verdict`, `discrepancy_reason`, `execution_status`. This schema must exist before T024 runs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Smoke Test on Local Docker Backend (Priority: P1) 🎯 MVP

**Goal**: Validate the end-to-end pipeline (provisioning, execution, verification) with a single task to ensure the Docker backend works on free-tier CI.

**Independent Test**: Run `python -m smoke.smoke_loop --task audacity_export_wav_440 --backend docker` and verify `smoke_report.json` is generated with status "success" or "partial_success".

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for smoke loop exit codes in `projects/607-reproduce-opencomputer/tests/contract/test_smoke_loop.py`
- [X] T011 [P] [US1] Integration test for Docker image build fallback in `projects/607-reproduce-opencomputer/tests/integration/test_docker_build.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Create wrapper script `run_smoke_test.sh` in `projects/607-reproduce-opencomputer/scripts/` to invoke `external/OpenComputer/smoke_loop.py` with exact arguments: `python -m smoke.smoke_loop --task audacity_export_wav_440 --backend docker --timeout 300`. Capture exit code 0 and validate `smoke_report.json` generation.
- [X] T013 [US1] Implement logic in `run_smoke_test.sh` to parse stdout from `smoke_loop.py` for "build_failed" status. If detected, log error details and exit with code 1; otherwise proceed. Ensure the wrapper executes the actual `smoke_loop.py` script as the primary driver.
- [X] T014 [US1] Implement logic to parse `smoke_report.json` and validate JSON schema in `projects/607-reproduce-opencomputer/scripts/parse_smoke_report.py`
- [X] T015 [US1] Add disk quota check before container provisioning to fail gracefully with "disk_quota_exceeded" in `projects/607-reproduce-opencomputer/scripts/docker_utils.py`
- [X] T015b [US1] **Metric Measurement**: Implement timer logic in `run_smoke_test.sh` to measure total execution time of the smoke test. Log the duration to `logs/smoke.log` and write the value to `data/summary.json` under `execution_time_seconds` to satisfy SC-005.
- [X] T015c [US1] **Execution Time Verification**: Extend `run_smoke_test.sh` to log the total execution time and verify it is under a feasible time threshold. Write the boolean `within_6h_limit` to `data/summary.json` to satisfy SC-005. **Dependency**: T015b.
- [X] T016 [US1] Add logging for smoke test execution steps (provision, run, verify) to `logs/smoke.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Verifier Alignment on a Sample Set (Priority: P2)

**Goal**: Execute a batch of ≥5 tasks, compare `hardcode` verifier results against **blinded manual inspection**, and generate a qualitative alignment report (replacing the impossible statistical margin requirement).

**Independent Test**: Run 5 distinct tasks via `run_eval.py`, manually inspect artifacts, and verify `verification_report.json` contains `manual_ground_truth` and `alignment_observation` fields.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for verification report schema (including manual fields) in `projects/607-reproduce-opencomputer/tests/contract/test_verification_report.py`
- [X] T019 [P] [US2] Integration test for manual ground truth injection in `projects/607-reproduce-opencomputer/tests/integration/test_manual_inspection.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Create batch task list `sample_tasks.json` in `projects/607-reproduce-opencomputer/data/` containing a set of distinct tasks with known mixed outcomes: `audacity_export_wav`, `gimp_resize_01`, `libre_calc_sum`, `vlc_play`, `notepad_save`.
- [X] T037 [US2] **Revision Task**: Update `sample_tasks.json` to include one additional task specifically designed to test "origination" behavior (agent deviating from card sequence). **Dependency: T020**. This task must be added to the sample set before execution.
- [X] T021 [US2] Implement `run_batch_eval.sh` in `projects/607-reproduce-opencomputer/scripts/` to execute `external/OpenComputer/run_eval.py` with `--agent claude_agent` and `--verifier hardcode`
- [X] T022 [US2] Implement script `collect_artifacts.py` in `projects/607-reproduce-opencomputer/scripts/` to copy generated artifacts (e.g., `.wav`, `.docx`) to a blinded folder for manual review
- [X] T023a [US2] **Auto**: Integrate `prepare_ground_truth.py` to generate `blinded_ground_truth.json` template with exact schema: `task_id`, `manual_verdict` (pass/fail), `manual_judgment_notes`. **Constraint**: The schema must support `inspector_1` and `inspector_2` fields to enforce the "Dual-Inspection" protocol mandated by the Plan. Logic: Remove all verifier results from the source data before saving.
- [X] T023b [US2] **Manual**: Manually populate `data/blinded_ground_truth.json` with the 5 inspected artifacts using the template generated by T023a. **Constraint**: Two independent researchers must inspect artifacts and fill `inspector_1` and `inspector_2` fields. This is a manual step outside the automated CI flow.
- [X] T024 [US2] Implement `compare_verdicts.py` in `projects/607-reproduce-opencomputer/scripts/` to merge `verification_report.json` with `blinded_ground_truth.json`. Logic: For each task, if `manual_verdict == verifier_verdict` then `match` else `mismatch`. Generate a string `alignment_observation` summarizing the matches and mismatches. Output this to the report. **Dependency**: Must validate output against `contracts/verification_results.schema.yaml` (T045).
- [X] T024c [US2] **Metric Calculation**: Extend `compare_verdicts.py` to calculate `verifier_alignment_rate` as a simple descriptive percentage: `(matches / total_tasks) * 100`. Write this value to `data/summary.json`. This satisfies FR-003 and SC-001. The report will contextualize this as a sample metric. **Dependency**: T024.
- [X] T025 [US2] Handle mid-execution failures by recording specific state mismatches (e.g., "file_not_found") in `projects/607-reproduce-opencomputer/scripts/parse_verification_report.py`
- [X] T025c [US2] **Metric Calculation**: Extend `compare_verdicts.py` to calculate `pipeline_reliability` as `(tasks_completed_without_crash / total_tasks_attempted) * 100`. Write this value to `data/summary.json` to satisfy SC-004. **Dependency**: T025 (must have failure logs).
- [X] T026 [US2] Add logic to skip tasks requiring missing GUI dependencies (e.g., GIMP not installed) and log "dependency_missing" in `projects/607-reproduce-opencomputer/scripts/run_batch_eval.sh`
- [X] T026c [US2] **Constraint Handling**: Implement logic to log the "A margin of error is maintained." requirement as a "Limitation" in the report, acknowledging it is impossible for N=5, rather than rejecting it in code. **Dependency**: T024c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Reproduction Report Against Paper Claims (Priority: P3)

**Goal**: Aggregate results from US-1 and US-2 to generate `reproduction_report.md` comparing results to paper claims, explicitly stating limitations (N=5, CPU-only).

**Independent Test**: Run `generate_report.py` and verify `reproduction_report.md` contains a "Conclusion" section with "Claims Partially Reproduced" and a "Limitations" section.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for report generation output schema in `projects/607-reproduce-opencomputer/tests/contract/test_report_gen.py`
- [X] T029 [P] [US3] Integration test for report generation with error logs in `projects/607-reproduce-opencomputer/tests/integration/test_report_gen.py`

### Implementation for User Story 3

- [X] T030 [US3] Create `generate_report.py` in `projects/607-reproduce-opencomputer/scripts/` using Jinja2 to aggregate `smoke_report.json` and `verification_report.json`. **Dependency**: Must run after T016 and T026 completion. **Tag**: Initial Version (without rate logic).
- [X] T031 [US3] Implement logic to calculate `tasks_attempted`, `tasks_passed`, and include the `verifier_alignment_rate` from `data/summary.json` in the report table. **Constraint**: The report MUST explicitly state that `verifier_alignment_rate` is a "descriptive sample metric" and not a statistically significant result, adhering to the Plan's constraints on N=5. **Dependency**: Must run after T024c and T030.
- [X] T032 [US3] Add logic to compare results against paper abstract claims (specifically: "a set of desktop applications", "large corpus of finalized tasks") and explicitly state "Claims Partially Reproduced" in the conclusion due to sample size constraints.
- [X] T033 [US3] Implement "Limitations" section generation to document runtime errors, disk quota issues, and the N=5 constraint.
- [X] T034 [US3] Ensure report generation fails gracefully if input JSONs are missing, logging an error but not crashing the pipeline

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Research Integrity (Addressing Prior Review)

**Purpose**: Address the "Ada Lovelace" review concern regarding the distinction between the "engine" (OpenComputer) and the "cards" (task definitions), ensuring the reproduction explicitly validates the *ordering* precision.

- [X] T035a [US2] **Metric Definition**: Define the specific "ordering" metric: Extract `step_execution_count` and `total_steps` from logs to calculate `step_adherence_ratio`. This metric definition is required for T035b.
- [X] T035b [US2] **Revision Task**: Implement `analyze_agent_intent.py` in `projects/607-reproduce-opencomputer/scripts/` to parse `task.json` and logs using the metric defined in T035a.
- [X] T035c [US2] **Revision Task**: Implement logic in `analyze_agent_intent.py` to flag "origination" events (agent deviating from card sequence) vs "execution" events.
- [X] T036 [US3] **Revision Task**: Update `generate_report.py` to include a section "## Engine vs. Agent" with headers: `step_execution_count`, `agent_origination_events`. Content: Discuss how results confirm the system acts as a precise engine. **Dependency**: T035b. **Tag**: Revision.

**Checkpoint**: All code quality, documentation, and data integrity requirements from prior reviews are addressed.

---

## Phase 7: Code Quality, Modularity & Documentation (Addressing Reviewer Concerns)

**Purpose**: Refactor monolithic scripts into modular components, add type hints, pin dependencies, and create required documentation to ensure reproducibility and clean checkout capability.

### Implementation for Code Quality & Modularity

- [ ] T039a [P] **Refactor**: Create `run_smoke_test.sh` as a standalone script in `projects/607-reproduce-opencomputer/scripts/`. Ensure file is < 200 lines and has a single responsibility.
- [ ] T039b [P] **Refactor**: Create `collect_artifacts.py` as a standalone script in `projects/607-reproduce-opencomputer/scripts/`. Ensure file is < 200 lines and has a single responsibility.
- [ ] T039c [P] **Refactor**: Create `compare_verdicts.py` as a standalone script in `projects/607-reproduce-opencomputer/scripts/`. Ensure file is < 200 lines and has a single responsibility.
- [ ] T039d [P] **Refactor**: Create `generate_report.py` as a standalone script in `projects/607-reproduce-opencomputer/scripts/`. Ensure file is < 200 lines and has a single responsibility.
- [ ] T040 [P] **Type Safety**: Add Python type hints to all function signatures in the refactored scripts (`docker_utils.py`, `collect_artifacts.py`, `compare_verdicts.py`, `generate_report.py`). Use `contracts/verification_results.schema.yaml` for `Verdict` and `Report` types, and `contracts/task.schema.yaml` for `Task` type definitions.
- [ ] T041 [P] **Dependency Pinning**: Update `requirements.txt` to include specific version constraints for all dependencies (e.g., `docker==7.1.0`, `pandas==2.2.0`, `pyyaml==6.0.1`, `jinja2==3.1.4`) to ensure environment reproducibility.
- [ ] T042 [P] **Documentation**: Create `docs/reproducibility/quickstart.md` with step-by-step instructions to run the smoke test and batch evaluation from a clean checkout.
- [ ] T043 [P] **Documentation**: Create `docs/reproducibility/research.md` explaining the "Blinding Protocol", the manual ground truth establishment process, and the rationale for the qualitative approach.
- [ ] T044 [P] **Documentation**: Create `docs/reproducibility/reproduction_report.md` (template or final) containing the aggregated results, qualitative alignment narrative, and explicit limitations (N=5, CPU-only).

### Implementation for Data Quality & Schema

- [ ] T047 [P] **Metadata Update**: Update `data/summary.json` to include a `metadata` section containing `opencomputer_submodule_commit_hash`, `docker_image_id`, `inspection_timestamp`, and the list of `task_ids` included in the sample.
- [ ] T048 [P] **Status Handling**: Verify and update `data/verification_results.csv` generation logic to include a distinct status for "skipped" tasks (due to missing dependencies) separate from "failed" tasks, and document this in T045 schema.

**Checkpoint**: All code quality, documentation, and data integrity requirements from prior reviews are addressed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 6)**: Depends on US-2 completion to analyze specific task execution behaviors
- **Code Quality (Phase 7)**: Depends on Phase 2-6 completion to refactor and document the final pipeline.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Must run after US1 and US2 completion** to aggregate results.

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
- Phase 7 tasks (Refactoring, Documentation, Schema) can be executed in parallel once the core logic is stable.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for smoke loop exit codes in projects/607-reproduce-opencomputer/tests/contract/test_smoke_loop.py"
Task: "Integration test for Docker image build fallback in projects/607-reproduce-opencomputer/tests/integration/test_docker_build.py"

# Launch all models for User Story 1 together:
Task: "Create wrapper script run_smoke_test.sh in projects/607-reproduce-opencomputer/scripts/"
Task: "Implement logic to handle 'build_failed' status in projects/607-reproduce-opencomputer/scripts/run_smoke_test.sh"
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
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US1/US2 data)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3 (Wait for US1/US2 data)
3. Stories complete and integrate independently
4. Developer D (or rotation): Phase 7 (Refactoring, Documentation, Schema) to ensure clean checkout readiness.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Research Integrity**: All tasks involving manual inspection must adhere to the "Blinding Protocol" to prevent confirmation bias.
- **Feasibility**: All tasks are scoped to run on CPU-only free-tier CI (≤6h, ≤7GB RAM, ≤14GB disk). No GPU or heavy quantization tasks are included.
- **Modularity**: Phase 7 tasks are critical for ensuring the codebase meets the "clean checkout" and "modularity" criteria required for reproducibility.