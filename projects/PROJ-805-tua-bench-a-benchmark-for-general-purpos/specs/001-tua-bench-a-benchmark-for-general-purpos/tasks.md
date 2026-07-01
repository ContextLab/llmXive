# Tasks: Reproduce & validate: TUA-Bench

**Input**: Design documents from `/specs/805-reproduce-tua-bench/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure by executing `mkdir -p external/TUA-Bench results docs oracle control_cases scripts utils schemas`.
- [X] T002 Initialize Python environment by executing `pip install -r requirements.txt` and explicitly installing `docker`, `pytest`, `pyyaml`, `ruff`, `black`.
- [X] T003 [P] Configure linting and formatting tools by installing `ruff` and `black`, and creating `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 Create `scripts/count_tasks.py` that traverses `external/TUA-Bench/tasks/`, counts total directories and distinct families, outputs JSON to stdout, and aborts with exit code 1 if count < 110 (SC-005).
- [X] T005 Create `scripts/subset_tasks.py` that reads task metadata, selects **one task per family** (multiple tasks) **plus two edge‑case tasks**, explicitly **excludes any task containing 'live-web' or 'network' in metadata**, and writes IDs to `subset_tasks.txt` (first alphabetically per family).
- [X] T006 Create `scripts/run_with_timeout.sh` wrapper that enforces a hard timeout for any command using the `timeout` utility.
- [X] T007 Create `scripts/check_container_runtime.sh` that checks `which docker` or `which podman`; if neither found, aborts immediately with error message "Container runtime not available".
- [X] T008 Create `scripts/verify_cpu_only.sh` that scans all `Dockerfile`s for GPU flags, ensures CPU-only, and runs `docker system prune -f` after execution.
- [X] T009 Create `scripts/parse_error_reason.py` implementing the regex-to-reason map:
   - `FileNotFoundError` → "File Missing"
   - `ValueError|expected.*got` → "Value Mismatch"
   - `TimeoutError|Timed out` → "Timeout"
   - `MemoryError|OOM` → "OOM"
   - `NetworkError|Connection refused|Network timeout` → "Network Timeout"
   - default → "Unknown Error"

## Phase 3: User Story 1 - Execute the TUA-Bench Quickstart Validation Pipeline (Priority: P1)

- [X] T010 Create `scripts/run_task.sh` skeleton: Define the script structure to accept `--task <id>` and `--timeout <s>`, import `check_container_runtime.sh`, and prepare the loop logic (Must follow T007).
- [X] T011 Implement loop logic in `scripts/run_task.sh`: Add logic to pull/build Docker image for the task, run `repo_env/setup_env.py --task <task_id>`, and record init success/failure (Must follow T010).
- [X] T012 Implement pruning and timeout wrapper in `scripts/run_task.sh`: Add logic to call `docker system prune -f` after task completion and wrap execution in `scripts/run_with_timeout.sh` (Must follow T011).
- [X] T013 Run the task's agent script inside the container using `scripts/run_task.sh`, enforce -minute timeout, and record wall-clock `execution_time_seconds` (Must follow T012).
- [X] T014 Execute original `verify.py` on the task's output against the **unaltered** `tests/reference/` files, capturing exit code, stdout, and stderr (Must follow T013).
- [X] T015 Parse stderr with `scripts/parse_error_reason.py` and log the standardized reason to `stderr` (Must follow T014).
- [X] T016 Define `schemas/execution_result.schema.yaml` with fields: `task_id`, `execution_time_seconds`, `status`, `error_message`, `verification_score`, `timestamp` (Must follow T015).
- [X] T017 Implement `scripts/write_results.py` to write `results/<task_id>.json` conforming to the schema defined in T016 (Must follow T016).
- [X] T018 Compute SC-001: percentage of tasks that completed environment init without error, log to `results/init_success_rate.json` (Must follow T017).
- [X] T019 Compute SC-004: sum all `execution_time_seconds`; if total > 21600s (6h) abort with clear message, log to `results/runtime_budget.json` (Must follow T018).

## Phase 4: User Story 2 - Validate Execution‑Based Scoring Protocol (Priority: P2)

- [X] T020 Create `scripts/generate_oracles.py` that:
   1. Copies `tests/reference` content to `oracle/<task_id>.json` (Pass case).
   2. Programmatically generates multiple corrupted variations per task in `control_cases/` by:
      - Variation 1: Numeric drift > 5% (parse and modify numbers).
      - Variation 2: Append "CORRUPTED" to file content (Missing/Extra logic).
      - Variation 3: Reorder lines randomly (Wrong order).
      - Variation 4: Change formatting (e.g., spaces/indentation).
   (Must follow T019).
- [X] T021 Run `verify.py` on each corrupted variation in `control_cases/` against the **original** `tests/reference` (No swapping), capturing exit code and output (Must follow T020).
- [X] T022 Compute accuracy as the ratio of correct classifications to the total number of instances.; log shortfall if accuracy < 0.95 and abort (Must follow T021).
- [X] T023 Independent scoring test: run verification on a known good solution (using oracle) and on a deliberately corrupted solution, assert pass (score = 1.0) and fail (score = 0.0) respectively (Must follow T022).

## Phase 5: User Story 3 - Generate Reproduction Report for Paper Claims (Priority: P3)

- [X] T024 Implement `scripts/read_results.py` to load all `results/*.json` files (Must follow T017).
- [X] T025 Implement `scripts/write_summary.py` to merge data from T024 into `results/summary.json`, validating against `reproduction_report.schema.yaml` (Must follow T024).
- [X] T026 Compute offline-subset success rate = `passed / attempted`, add field `success_rate_scope: "offline_subset_only"` (Must follow T025).
- [X] T027 Generate `docs/reproduction_report.md` containing:
   - Task-level table (ID, family, execution time, status, error).
   - Scope-Limitation Notice (offline subset only).
   - Comparison of observed task count & family count to paper claims.
   - Control-test accuracy result.
   - Family-level pass rates.
   - Any deviations tagged with severity. (Must follow T026).
- [X] T028 Independent report test: parse `docs/reproduction_report.md` and verify numeric claims match the paper (≥ 110 tasks, exactly 5 families, reported success rate, etc.) (Must follow T027).

## Phase 6: Edge‑Case Handling (All Phases)

- [X] T029 Detect missing Docker/Podman at the start of the pipeline and abort with "Container runtime not available".
- [X] T030 Detect OOM inside container (exit code indicating memory exhaustion) and record status `oom` with `error_message: "OOM"`.
- [X] T031 Detect timeout wrapper non-zero exit and record status `timeout` with `error_message: "Timeout"`.
- [X] T032 Detect `NetworkError` exceptions during task setup and log `error_message: "Network Timeout"`.
- [X] T033 Verify `verify.py` uses tolerance ≥ 1e-5 (relative) or ≥ 1e-3 (absolute) for numerical comparisons; log if tolerance not met.
- [X] T034 Comprehensive edge-case test suite that runs simulated failures for each of the above conditions and asserts correct status/error_message.

## Phase 7: Compute Feasibility & Resource Management

- [X] T035 Ensure all Dockerfiles are CPU-only (no `--gpus` flags) and prune images after each task (`docker system prune -f`).

## Phase 8: Timeline & Governance

- [X] T036 Track start/end timestamps of each phase, validate total elapsed time < 2.5h, log result (Timeline tracking).
- [X] T037 Constitution audit: check for `constitution.md`; if absent, log "Constitution audit deferred" and record deferral status.
- [X] T038 Requirement Traceability Matrix: generate `docs/rtm.md` mapping each FR/SC to corresponding task IDs.
- [X] T039 Phase-step checklist: verify that every step described in the implementation plan for Phases 0a, 0b, 1, 2 has been executed.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T040 Create `docs/README.md` with usage instructions and `docs/contributing.md` with contribution guide.
- [X] T041 Extract error parsing logic into `utils/errors.py` and refactor `scripts/parse_error_reason.py` to import from it.
- [X] T042 Write unit tests for `utils/errors.py` using `pytest`, covering all regex patterns in `parse_error_reason.py`.
- [X] T043 Run quickstart validation (`quickstart.md`) to ensure end-to-end success.

## Dependencies & Execution Order

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup – blocks all user stories.
- **User Stories (Phases 3-5)**:
   - **Phase 3 (US1)**: Strictly sequential: T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019.
   - **Phase 4 (US2)**: Strictly sequential: T020 → T021 → T022 → T023.
   - **Phase 5 (US3)**: Strictly sequential: T024 → T025 → T026 → T027 → T028.
   - **Cross-Phase**: Phase 4 depends on Phase 3 completion (T019). Phase 5 depends on Phase 4 completion (T023).
- **Edge-Case Handling (Phase 6)**: Integrated into the main pipeline; tasks T029-T034 must be invoked where relevant.
- **Feasibility (Phase 7)**: Runs alongside Phase 3 tasks.
- **Timeline & Governance (Phase 8)**: Runs after Phase 5 completes.
- **Polish (Phase N)**: Runs after all above phases are successful.

### Parallel Opportunities

- Tasks marked `[P]` within a phase may run concurrently if they operate on independent files.
- Phase 2 tasks T004-T009 are largely independent and can run in parallel.
- Phase 1 tasks T002-T003 can run in parallel after T001.