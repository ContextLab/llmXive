# Tasks: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

**Input**: Design documents from `/specs/001-eval-code-vuln-density/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `state/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (transformers, datasets, bandit, scikit-learn, statsmodels, pandas, matplotlib, seaborn, pyyaml, pingouin)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to manage global config, random seeds, and path constants <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 2, column 11:
 def test_get_config_structure(self):
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 3, column 17:
 """Verify get_config returns a dic...
 ^) -->
- [X] T005 [P] Create `code/config/bandit_config.yaml` defining the pinned rule-set and exclusions for static analysis (Constitution Principle VI)
- [ ] T006 [P] Implement `code/download.py` to fetch HumanEval and MBPP datasets from HuggingFace `datasets` library with SHA-256 checksum verification (Constitution Principle III)
- [X] T007 Create `code/state_utils.py` to compute and store artifact hashes in `state/artifact_hashes.yaml` upon data completion
- [X] T008 Implement `code/main.py` as the pipeline orchestrator with argument parsing for model selection and benchmark targets

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Vulnerability Density Measurement (Priority: P1) 🎯 MVP

**Goal**: Automatically generate code samples from LLMs for fixed tasks, run static analysis, and calculate baseline vulnerability counts.

**Independent Test**: Execute generation pipeline for StarCoder on HumanEval tasks with fixed seed; verify output directory contains valid code files and a JSON summary with non-zero lines and vulnerability counts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset download integrity in `tests/unit/test_download.py`
- [ ] T010 [P] [US1] Integration test for single-model generation and analysis loop in `tests/integration/test_generation_pipeline.py`

### Implementation for User Story 1

- [X] T011 Implement the loader function in `code/download.py` for StarCoder and CodeGen (CPU-only, default precision, no 8-bit/4-bit quantization) to fit ≤7GB RAM. **Note**: Must run sequentially to respect RAM limits; do not load multiple models simultaneously.
- [X] T012 [US1] Implement `code/generate.py` to select **ALL tasks** from HumanEval and MBPP benchmarks (FR-002) and execute the generation loop. **Logic**: For each task, iterate generation until ≥ 64 valid samples are obtained OR 200 attempts are exhausted. If 200 attempts are exhausted for any task, log the error, flag the dataset as 'insufficient data', and halt the pipeline. **Validation**: Execute benchmark tests on generated samples to determine validity. **Output**: Valid samples saved to `data/generated/{model}/{benchmark}/{task_id}/samples/`.
- [~] T013 [US1] Implement `code/analyze.py` to **execute Bandit** on all files in `data/generated/` and `data/human/` using `code/config/bandit_config.yaml`, handling syntax errors by skipping files and logging errors (US-1 Edge Case). **Output**: `data/processed/bandit_raw_reports.json`.
- [~] T013b [US1] Implement parsing logic in `code/analyze.py` to read `data/processed/bandit_raw_reports.json` and generate a structured vulnerability report `data/processed/vulnerability_reports.json` containing `file_path`, `cwe_id`, `severity`, and `line_number`.
- [~] T014 [US1] Implement `code/stats.py` to calculate `vulnerability_count` and `lines_of_code` **per sample** (one row per file) from `data/processed/vulnerability_reports.json`, producing `data/processed/raw_vulnerability_counts.csv` (FR-004). Schema: `task_id`, `source_type`, `file_path`, `lines_of_code`, `vulnerability_count`.
- [~] T015 [US1] Implement aggregation logic in `code/stats.py` to calculate **mean vulnerability count per task** (LLM) vs **single count per task** (Human) from `data/processed/raw_vulnerability_counts.csv`, producing `data/processed/aggregated_analysis_dataset.csv` (Plan Update: Unit of Analysis = Task).
- [X] T016 [US1] Add error handling in `code/generate.py` to halt and flag dataset as 'insufficient data' if <64 valid samples are obtained after 200 attempts per task (US-1 Acceptance 5).
- [X] T017 [US1] Add logging for generation failures and static analysis parse errors in `code/generate.py` and `code/analyze.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Statistical Analysis (Priority: P2)

**Goal**: Compare vulnerability counts of LLM-generated code vs. human-written solutions using ZINB regression with fallback to permutation tests, and perform sensitivity analysis.

**Independent Test**: Run analysis script on mock dataset; verify ZINB (or permutation fallback) executes, p-values and confidence intervals are printed, and stratified analysis skips categories with n<5.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for ZINB convergence fallback logic in `tests/unit/test_stats.py`
- [~] T019 [P] [US2] Integration test for stratified analysis and multiple-comparison correction in `tests/integration/test_statistical_analysis.py`

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/stats.py` (ZINB) to define and fit Zero-Inflated Negative Binomial regression: `vulnerability_count ~ source_type + lines_of_code + (1|benchmark)` using `data/processed/aggregated_analysis_dataset.csv`. **Note**: Do NOT use `(1|task_id)` as `task_id` is unique per row. **Fallback**: If ZINB fails to converge after 3 attempts, execute a permutation test on raw counts (FR-005, FR-015). **Input**: Raw counts (no FPR adjustment).
- [X] T021 [US2] Implement stratified analysis logic in `code/stats.py` to group by CWE ID, skip tests if n<5 per group, and apply Benjamini-Hochberg correction to p-values (FR-006, FR-007).
- [~] T022 [US2] Implement `code/validator.py` as the Reference-Validator Agent: **First**, implement deterministic seed-based subset selection to choose a stratified random sample (n=20) per group. **Second**, use rule-based heuristics to match CWE signatures to code patterns on the selected sample (FR-014, Constitution Principle II). **Output**: `data/processed/validator_flags.csv` (columns: `sample_id`, `is_valid`).
- [~] T023 [US2] Implement FPR calculation in `code/stats.py` using `data/processed/validator_flags.csv` to compute group-specific False Positive Rates (FR-012). **Output**: `data/processed/fpr_metrics.json`. **Note**: This FPR is reported as a sensitivity metric only; do NOT apply the adjustment formula to the primary outcome.
- [ ] T025 [US2] Implement post-hoc power analysis in `code/stats.py` if valid sample count <64; flag dataset as 'under-powered' if power <0.80 (FR-009).
- [ ] T026 [US2] Implement cross-benchmark (HumanEval vs MBPP) and cross-model (StarCoder vs CodeGen) comparison logic in `code/stats.py` (FR-011, FR-013).
- [ ] T027 [US2] Generate `data/processed/aggregated_analysis_dataset.csv` with final statistics, effect sizes (IRR), and flags (Plan Phase 2.2).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate visualizations comparing vulnerability distributions and create a summary report.

**Independent Test**: Run reporting script on analysis output; verify PNG/SVG files generated in `results/` and `results/summary.md` contains key stats and image paths.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for visualization generation in `tests/unit/test_viz.py`
- [ ] T029 [P] [US3] Contract test for report generation output format in `tests/contract/test_report.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/viz.py` to generate boxplots comparing LLM vs. Human vulnerability counts (FR-008).
- [ ] T031 [US3] Implement `code/viz.py` to generate bar charts for top 5 vulnerability types by frequency per source (FR-008).
- [ ] T032 [US3] Implement `code/report.py` to generate `results/summary.md` containing key statistics, effect sizes, FPR sensitivity metrics, and paths to generated images (FR-008).
- [ ] T033 [US3] Ensure report generation reads exclusively from `data/processed` to satisfy Single Source of Truth (Constitution Principle IV).
- [ ] T034 [US3] Add resource usage logging (CPU time, memory) to `code/main.py` to verify ≤6h / ≤7GB limits (SC-004).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Update `docs/quickstart.md` with instructions to run the full pipeline and reproduce results
- [ ] T036 Code cleanup and refactoring of `code/stats.py` for readability
- [ ] T037 Verify reproducibility by running pipeline twice with same seed and checking absolute difference ≤1e-6 in **all derived floating-point outputs** (SC-005).
- [ ] T038 [P] Run `pytest` suite to ensure all unit and integration tests pass
- [ ] T039 Security hardening: Verify no PII leakage in logs or generated reports
- [ ] T040 Run quickstart.md validation to ensure end-to-end execution works

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation and aggregation logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 statistical results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset download integrity in tests/unit/test_download.py"
Task: "Integration test for single-model generation and analysis loop in tests/integration/test_generation_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement model loading in code/download.py for StarCoder and CodeGen"
Task: "Implement code/generate.py to iterate HumanEval/MBPP tasks"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate 64 samples, run bandit, count vulns)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical significance)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualization/Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation & Analysis)
 - Developer B: User Story 2 (Stats & Validator)
 - Developer C: User Story 3 (Viz & Report)
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
- **Critical Constraint**: All model loading tasks (T011) MUST use CPU-only, default precision (no 8-bit/4-bit) to ensure feasibility on GitHub Actions free tier.
- **Critical Constraint**: All data generation (T012) MUST use real datasets (HumanEval/MBPP) and validate samples against benchmark tests; no synthetic/fake data allowed.