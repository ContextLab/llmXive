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

- [ ] T001a [P] Create `code/` directory structure and verify with `ls -R code/` (artifact: `setup-code-dir.log`)
- [ ] T001b [P] Create `data/` directory structure and verify with `ls -R data/` (artifact: `setup-data-dir.log`)
- [ ] T001c [P] Create `results/` directory structure and verify with `ls -R results/` (artifact: `setup-results-dir.log`)
- [ ] T001d [P] Create `tests/` directory structure and verify with `ls -R tests/` (artifact: `setup-tests-dir.log`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (transformers, datasets, bandit, scikit-learn, statsmodels, pandas, matplotlib, seaborn, pyyaml, pingouin)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to manage global config, random seeds, and path constants
- [X] T005 [P] Create `code/config/bandit_config.yaml` defining the pinned rule-set and exclusions for static analysis (Constitution Principle VI)
- [X] T005b [P] Create `code/config/cwe_patterns.yaml` defining the complete mapping of CWE IDs to regex patterns for the Reference-Validator Agent
- [X] T006 [P] Implement `code/download.py` to fetch HumanEval and MBPP datasets from HuggingFace `datasets` library with SHA-256 checksum verification (Constitution Principle III)
- [X] T007 Create `code/state_utils.py` to compute and store artifact hashes in `state/artifact_hashes.yaml` upon data completion
- [X] T008 Implement `code/main.py` as the pipeline orchestrator with argument parsing for model selection and benchmark targets

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Vulnerability Density Measurement (Priority: P1) 🎯 MVP

**Goal**: Automatically generate code samples from LLMs for fixed tasks, run static analysis, and calculate baseline vulnerability counts.

**Independent Test**: Execute generation pipeline for StarCoder on HumanEval tasks with fixed seed; verify output directory contains valid code files and a JSON summary with non-zero lines and vulnerability counts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for dataset download integrity in `tests/unit/test_download.py`
- [X] T010 [P] [US1] Integration test for single-model generation and analysis loop in `tests/integration/test_generation_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement the loader function in `code/download.py` for StarCoder and CodeGen. **Constraint**: MUST use 8-bit quantization (`load_in_8bit=True`) to fit within the 7GB RAM limit of the GitHub Actions runner. **Note**: Models must be loaded sequentially; do not load multiple models simultaneously.
- [ ] T012 [US1] Implement `code/generate.py` to select a **random subset of tasks** (e.g., 10-20 tasks) from HumanEval and MBPP benchmarks to ensure runtime feasibility (FR-002, FR-011). **Logic**: Iterate generation for the selected tasks until **≥ 64 valid samples total per model** are obtained OR 200 attempts are exhausted. **Graceful Degradation**: If 200 attempts are exhausted for a specific task, log the error, flag that specific task as 'insufficient_data', and **continue** to the next task. Do NOT halt the entire pipeline unless the total valid sample count across all tasks is < 64. **Validation**: Execute benchmark tests using `evaluate.human_eval` for HumanEval and `mbpp.eval` for MBPP. **Output**: Valid samples saved to `data/generated/{model}/{benchmark}/{task_id}/samples/`.
- [ ] T013 [US1] Implement `code/analyze.py` to **execute Bandit** on all files in `data/generated/` and `data/raw/human_solutions/` using the exact command: `bandit -r <path> -f json -o <output> --ini code/config/bandit_config.yaml`. **Logic**: Parse file paths to map to `task_id` and `source_type`. Aggregate multiple Bandit issues per file into a single `vulnerability_count`. **Output 1**: `data/processed/raw_vulnerability_reports.json` (full Bandit details). **Output 2**: `data/processed/raw_vulnerability_counts.csv` (Columns: `task_id`, `source_type`, `file_path`, `lines_of_code`, `vulnerability_count`). **Verification**: Script MUST exit with code 1 if either output file is missing after execution. Log message "ERROR: Analysis output files missing" must be present on failure.
- [X] T016 [US1] Add error handling in `code/generate.py` to flag the dataset as 'insufficient data' if <64 valid samples are obtained after 200 attempts total, but continue processing other tasks if partial data exists.
- [X] T017 [US1] Add logging for generation failures and static analysis parse errors in `code/generate.py` and `code/analyze.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Statistical Analysis (Priority: P2)

**Goal**: Compare vulnerability counts of LLM-generated code vs. human-written solutions using Permutation Test as primary, with ZINB as secondary, and perform sensitivity analysis.

**Independent Test**: Run analysis script on mock dataset; verify Permutation Test executes, p-values and confidence intervals are printed, and stratified analysis skips categories with n<5.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Permutation Test logic in `tests/unit/test_stats.py`
- [X] T019 [P] [US2] Integration test for stratified analysis and multiple-comparison correction in `tests/integration/test_statistical_analysis.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/stats.py` to perform **Primary Statistical Analysis**. **Step 1**: Read `data/processed/raw_vulnerability_counts.csv` (individual sample level). **Step 2**: Use `vulnerability_count` (RAW) as the primary metric. **Step 3**: Execute a **Permutation Test** on raw counts between LLM and Human groups as the PRIMARY test. **Step 4**: If sample size n > 128, attempt ZINB regression as a secondary check; otherwise, skip ZINB. **Output**: Update `data/processed/aggregated_analysis_dataset.csv` with `test_type` ('Permutation'), `p_value`, `confidence_interval`, `effect_size` (IRR), and `convergence_status`. **Constraint**: Do NOT apply FPR adjustment here; this is for sensitivity analysis only.
- [ ] T020b [US2] Implement **Sensitivity Analysis** in `code/stats.py`. **Logic**: If `data/processed/fpr_metrics.json` exists, calculate `adjusted_vulnerability_count = vulnerability_count * (1 - group_FPR)`. Fit a secondary ZINB regression using `adjusted_vulnerability_count`. **Output**: Append results to `data/processed/aggregated_analysis_dataset.csv` with `analysis_type = 'sensitivity'`. If `fpr_metrics.json` is missing, skip this task and log "Sensitivity analysis skipped: fpr_metrics.json missing".
- [X] T021 [US2] Implement stratified analysis logic in `code/stats.py` to group by CWE ID. **Logic**: Check `n >= 5` per group (LLM vs Human) on the **raw** dataset. If `n < 5` for a category, log a warning and skip the test for that category. If `n >= 5`, perform the test and apply Benjamini-Hochberg correction to p-values (FR-006, FR-007).
- [X] T022 [US2] Implement `code/validator.py` as the Reference-Validator Agent: **First**, implement deterministic seed-based subset selection to choose a stratified random sample (n=20) per group. **Second**, use rule-based heuristics from `code/config/cwe_patterns.yaml` to match CWE signatures to code patterns on the selected sample (FR-014, Constitution Principle II). **Output**: `data/processed/validator_sample.csv` (columns: `sample_id`, `is_valid`).
- [ ] T023 [US2] Implement FPR calculation in `code/stats.py` using `data/processed/validator_sample.csv` to compute group-specific False Positive Rates (FR-012). **Logic**: FPR = (Count where Validator='Clean' AND Bandit='Vuln') / (Total Count where Validator='Clean'). **Constraint**: Calculation MUST be strictly bounded to the n=20 sample defined in T022. **Output Schema**: `data/processed/fpr_metrics.json` must contain: `{ "group_FPR": { "LLM": float, "Human": float }, "total_samples": 20, "false_positives": int }`.
- [X] T025 [US2] Implement post-hoc power analysis in `code/stats.py` if valid sample count <64; flag dataset as 'under-powered' if power <0.80 (FR-009).
- [X] T026 [US2] Implement cross-benchmark (HumanEval vs MBPP) and cross-model (StarCoder vs CodeGen) comparison logic in `code/stats.py` (FR-011, FR-013).
- [X] T027a [US2] Generate `data/processed/aggregated_analysis_dataset.csv` with final statistics, effect sizes (IRR), and flags. **Schema**: `task_id`, `source_type`, `benchmark`, `lines_of_code`, `vulnerability_count`, `adjusted_vulnerability_count` (nullable), `is_valid`, `power_flag`, `test_type`, `p_value`, `ci_lower`, `ci_upper`, `analysis_type` ('primary' or 'sensitivity').

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate visualizations comparing vulnerability distributions and create a summary report.

**Independent Test**: Run reporting script on analysis output; verify PNG/SVG files generated in `results/` and `results/summary.md` contains key stats and image paths.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for visualization generation in `tests/unit/test_viz.py`
- [X] T029 [P] [US3] Contract test for report generation output format in `tests/contract/test_report.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/viz.py` to generate boxplots comparing LLM vs. Human vulnerability counts (FR-008).
- [X] T031 [US3] Implement `code/viz.py` to generate bar charts for top vulnerability types by frequency per source (FR-008).
- [ ] T032 [US3] Implement `code/report.py` to generate `results/summary.md`. **Template**: Must include sections: `## Statistical Summary`, `## Sensitivity Analysis`, `## Visualizations`. **Content**: Must include key statistics (p-value, IRR, 95% CI bounds), FPR sensitivity metrics (read from `data/processed/fpr_metrics.json`), and paths to generated images (FR-008). **Constraint**: Script MUST verify it reads exclusively from `data/processed` and fails if hardcoded values are detected.
- [ ] T033 [US3] Ensure report generation reads exclusively from `data/processed` to satisfy Single Source of Truth (Constitution Principle IV). **Verification**: Add a unit test in `tests/contract/test_report.py` that mocks `data/processed` and verifies no external data sources are accessed.
- [X] T034 [US3] Add resource usage logging (CPU time, memory) to `code/main.py` to verify ≤6h / ≤7GB limits (SC-004). **Constraint**: Script MUST include an assertion that halts execution and raises an error if CPU time > 6h or RAM > 7340MB.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `docs/quickstart.md` with instructions to run the full pipeline and reproduce results
- [ ] T036a [P] Refactor `code/stats.py`: Remove unused imports; verify with `ruff check` (artifact: `refactor-logs.txt`)
- [ ] T036b [P] Refactor `code/stats.py`: Extract functions > 50 lines into smaller units; verify cyclomatic complexity < 10 (artifact: `complexity-report.txt`)
- [ ] T036c [P] Refactor `code/stats.py`: Ensure all statistical functions are pure and deterministic; verify with `pytest` (artifact: `refactor-logs.txt`)
- [ ] T037a [US2] [REQUIRED] Implement reproducibility check for floating-point outputs: Re-run pipeline with same seed, compare `data/processed/aggregated_analysis_dataset.csv` and `results/summary.md` using `pandas.testing.assert_frame_equal` with `rtol=1e-6`. **Artifact**: `reproducibility-float-diff.log`. **Status**: REQUIRED for SC-005.
- [ ] T037b [US2] [REQUIRED] Implement reproducibility check for status/seeds: Re-run pipeline, compare `convergence_status` and `random_seed` fields using exact string equality. **Artifact**: `reproducibility-status-diff.log`. **Status**: REQUIRED for SC-005.
- [ ] T038 [P] Run `pytest` suite and verify all tests pass. **Artifact**: `pytest-results.xml` and `pytest-console.log`.
- [ ] T039 [P] Security hardening: Verify no PII leakage in logs or generated reports. **Tool**: `grep -rE 'email|ssn|phone'`. **Artifact**: `pii-scan.log`.
- [ ] T040 [P] Run quickstart.md validation. **Success Criteria**: Exit code 0 and output contains "Pipeline Complete". **Artifact**: `quickstart-run.log`.

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
- **Critical Constraint**: All model loading tasks (T011) MUST use 8-bit quantization to ensure feasibility on GitHub Actions free tier.
- **Critical Constraint**: All data generation (T012) MUST use real datasets (HumanEval/MBPP) and validate samples against benchmark tests; no synthetic/fake data allowed.
- **Statistical Note**: T020 implements Permutation Test as primary. ZINB is secondary (n > 128).
- **Data Flow**: T023 produces `fpr_metrics.json` which is consumed by T020b (Sensitivity), NOT T020 (Primary).
- **Revision Note**: T013 explicitly defines the Bandit execution command and output schema to resolve ambiguity in the original analysis task.
- **Revision Note**: T023 is now explicitly required before T020b can apply the FPR adjustment, ensuring the data dependency is clear.
- **Revision Note**: T040 has been re-enabled to ensure end-to-end validation of the quickstart guide.
- **Revision Note**: T037 has been split into T037a (floats) and T037b (status/seeds) to resolve logical comparison errors.
- **Revision Note**: T012 now implements graceful degradation (continue) instead of hard exit.
- **Revision Note**: T015 (aggregation) removed to preserve unit of analysis.