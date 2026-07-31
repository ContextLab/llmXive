# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Input**: Design documents from `/specs/001-gut-microbiome-sleep-architecture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001a Create `code/` directory and `__init__.py`
- [ ] T001b Create `tests/` directory structure (`contract/`, `unit/`, `integration/`)
- [ ] T001c Create `data/` directory structure (`raw/`, `processed/`, `results/`, `config/`)
- [X] T002a Generate `requirements.txt` with pinned versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `scikit-bio`, `pytest`, `spiec-easi`, `sparcc`
- [ ] T002b Create `.gitignore` and initialize virtualenv configuration
- [ ] [P] T003 Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **defining the structure (list of strings) for required predictors. The actual list of required taxa names must be provided in `data/config/research_design.yaml` at runtime.**
- [ ] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **defining the structure (list of strings) for required outcomes. The actual list of required metric names must be provided in `data/config/research_design.yaml` at runtime.**
- [~] T004c **IMPLEMENT REQUIRED VARIABLES SCHEMA**: Create `data/config/required_variables_schema.yaml` to define the *schema structure* for required variables (e.g., `required_predictors: [string]`, `required_outcomes: [string]`). **Constraint**: This file defines the *shape* of the configuration, not the *instance* data. **Output**: `data/config/required_variables_schema.yaml`. **Addresses FR-001.** **Note**: The *instance* data (actual list of required variables) MUST be provided in `data/config/research_design.yaml` by the user or generated synthetically for this phase.
- [ ] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation) <!-- FAILED: unspecified -->
- [X] T006d **IMPLEMENT CHECKSUM SCHEMA AND RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`. **Schema**: `artifact_hashes: { "<file_path>": "sha256:<hash>" }`. **Constraint**: This step MUST be invoked by T015 (Orchestration) as a blocking step before analysis begins. **IMPORTANT**: This task MUST record checksums for synthetic data to ensure reproducibility (Constitution Principle III). **Function Signature**: `def record_artifact_checksum(file_path: str, state_file: str) -> bool`. **Addresses Constitution Principle I & III.**
- [ ] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py` <!-- ATOMIZE: requested -->
- [~] T009b **IMPLEMENT REFERENCE-VALIDATOR AGENT**: Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`). **Constraint**: The gate MUST enforce the blocking requirement from Constitution Principle II: if any citation is unreachable or mismatch, the build MUST fail. **Integration**: Call `validate_references()` in `code/main.py` before analysis starts. **Note**: This task depends on T015 (orchestration) for integration context. **DEPENDS ON T015.** **Addresses FR-001 and Constitution Principle II.** <!-- FAILED: unspecified -->
- [X] T021c [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml`. **Format**: YAML list of lists `[[taxon_A, taxon_B],...]`. **Schema**: `pairs: [[string, string],...]`. **Addresses FR-006.** **Note**: This is optional and for documentation only; the primary detection method is matrix rank check in T021f_new.
- [ ] T021f_new [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION**: Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` using **matrix rank check** (e.g., `numpy.linalg.matrix_rank`) on the **entire predictor matrix**. **Logic**: 1) Construct the full predictor matrix from the dataset; 2) Perform a matrix rank check to detect any linearly dependent columns; 3) Flag any pair of columns that contribute to rank deficiency as "Perfect Multicollinearity". **Constraint**: This task MUST detect linear dependence for *any* pair of definitionally related taxa via the matrix rank check, regardless of config file presence or column naming conventions. **Output**: `data/metadata/static_collinearity_map.json` (JSON map of flagged pairs detected via rank check). **DEPENDS ON T021c (optional).** **Addresses FR-006.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T004a, T004b, T005a). **This task validates the existence and structure of the schema files **(T004a/b)
- [ ] [P] T011 [US1] Integration test for missing variable error handling in `tests/integration/test_missing_variable.py`

### Implementation for User Story 1

- [~] T012 [US1] **IMPLEMENT VALIDATION LOGIC AND METRIC CALCULATION**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics). **Logic**: Compare dataset columns against the list of required variables defined in `data/config/research_design.yaml`. **CRITICAL**: Do NOT write any artifacts in this task. This task MUST calculate the percentage of required variables successfully loaded, identify missing variables, and **RETURN** a status object (`{"status": "PASS" | "FAIL", "percentage_loaded": float, "missing_variables": [string], "total_required": int}`). **Addresses FR-001 and SC-001.**
- [X] T013 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC AND ARTIFACT WRITING**: Implement `load_data()` in `code/ingest.py` to call T012. **CRITICAL**: <!-- FAILED: unspecified -->
 1. If T012 returns "FAIL", **HALT EXECUTION** (`sys.exit(1`) immediately with the specific error message (e.g., "Variable 'SWS duration' is missing"). **DO NOT** write any artifacts.
 2. If T012 returns "PASS", write `data/results/variable_load_metrics.json` with the status object returned by T012.
 **Addresses FR-001.**
- [X] T014 Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or < 1.5x IQR below 25th)
- [~] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014.** **CRITICAL**: Also generate `data/results/outlier_report.json` containing the count of excluded points, the list of excluded row indices (exactly those identified by T014), and the percentage of total rows excluded. **Schema**: `{"count": int, "excluded_indices": [int], "percentage_total": float}`. **Addresses FR-001.**
- [ ] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b.** <!-- FAILED: unspecified -->
- [X] T015 Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution. **Constraint**: Must invoke T006d (checksum recording) as a blocking step before proceeding to analysis. **CRITICAL**: Must explicitly invoke T016 (timing check) as part of the orchestration flow.
- [ ] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE GENERATION**: Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact **(JSON log at `data/results/timing_evidence.json`) to satisfy SC-004. **CRITICAL**: If the time limit is exceeded, the system MUST **LOG THE VIOLATION**, generate `timing_evidence.json` with `status: "TIMEOUT"`, and THEN **HALT** (`sys.exit(1`). **Output**: `data/results/timing_evidence.json`. **Schema**: `{"start_time": string, "end_time": string, "duration_seconds": float, "status": "PASS" | "TIMEOUT"}`. **DEPENDS ON T014b, T015.**
- [ ] T016b [US1] **IMPLEMENT TIMING METRIC REPORTING**: Implement logic to read `data/results/timing_evidence.json` and append the `duration_seconds` and `status` to the final `data/results/final_report.md` (or a dedicated summary artifact if generated earlier). **DEPENDS ON T016.** **Addresses SC-004.**
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2)

**Goal**: Compute correlations with automatic method selection (ZINB/Spearman/Pearson) and FDR correction, explicitly framing results as associational.

**Independent Test**: Run analysis on synthetic data with known zero-inflation; verify ZINB selection and correct coefficients. Verify BH-adjusted p-values and associational language in report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [~] T020 [US2] **IMPLEMENT DATA DISTRIBUTION CHECKS AND LOG**: Implement `check_distribution()` in `code/analysis.py` to perform Shapiro-Wilk test and zero proportion calculation. **CRITICAL**: Must generate `data/metadata/method_selection_log.json` documenting the specific statistical tests performed (Shapiro-Wilk p-value, zero proportion), the decision logic path taken, and the final selected method. **Schema**: `{"shapiro_p_value": float, "zero_proportion": float, "decision_path": "string", "selected_method": "ZINB" | "Spearman" | "Pearson"}`. **Addresses FR-002 and Constitution Principle IV.** **DEPENDS ON T014b.**
- [ ] T020a Implement compositionality detection in `code/transform.py`. **CRITICAL**: If `scikit-bio` is not installed, the task MUST **FAIL LOUDLY** with a specific error message indicating the missing dependency. **Output**: `data/metadata/compositionality_flag.json`. <!-- FAILED: unspecified -->
- [ ] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json` exists and is valid. **DEPENDS ON T020a.**
- [ ] T021 [US2] **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05), use a Zero-Inflated Negative Binomial (ZINB) or Hurdle model; 2) Else if non-normality is detected (Shapiro-Wilk p < 0.05), use Spearman rank correlation; 3) Else use Pearson correlation. **CRITICAL**: Do NOT use library availability as a fallback. If the required library is missing, the pipeline must fail loudly. **MUST read `data/metadata/method_selection_log.json` (generated by T020) and `data/metadata/compositionality_flag.json` **(from T020a) **DEPENDS ON T020, T020a, T022a**.
- [ ] T022 [US2] **IMPLEMENT CLR TRANSFORMATION**: Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable). **CONDITIONAL**: Only run if T021 selects a method requiring compositional correction and the compositionality flag is set (from T020a). **Output**: `data/processed/processed_data.parquet`. **CRITICAL**: If the condition is false, skip execution, log the skip in `data/metadata/correction_skip_log.json` with schema `{"status": "SKIPPED", "reason": "string"}`, and generate a status file indicating the skip. **DEPENDS ON T021, T022a.**
- [ ] T023 Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [ ] T024 Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [ ] T025 [US2] **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and write the full correlation matrix to `data/results/correlation_matrix.json`. **Schema **(File): `data/results/correlation_matrix.json`. **Content**: A flat list of objects, each containing `taxon`, `sleep_metric`, `correlation_coefficient`, `p_value_raw`, `p_value_adjusted`, `is_significant`, `method_used`. **DEPENDS ON T022** (if CLR selected) **and T023/T024.**
- [ ] T026 [US2] **EXTEND PIPELINE ORCHESTRATION**: Extend pipeline orchestration in `code/main.py` to import and call US2 modules **after** analysis modules (T022, T025) are complete. **CRITICAL**: Must handle the conditional execution of T022. **DEPENDS ON T022, T025**. **Note**: T026 no longer depends on T087 (Report Generation) to avoid circular dependency.

**Checkpoint**: At this point, User Story 2 (Correlation Matrix) is functional and testable independently. Final reporting (T087) requires US3 diagnostics.

---

## Phase 4.5: Integration & Diagnostics (Cross-Cutting)

**Purpose**: Integrate US1 and US2 artifacts, implement missing diagnostics (Sensitivity, VIF, Power), and enforce associational framing.

- [ ] T078 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement logic to re-run significance tests at p < 0.01, p < 0.05, and p < 0.10 using results from T025. **CRITICAL**: Must generate `data/results/sensitivity_analysis.json` with the specific schema required by SC-002. **Schema**: `{"base_threshold": 0.05, "base_count": int, "threshold_0.01": {"count": int, "percentage_change": float}, "threshold_0.10": {"count": int, "percentage_change": float}}`. **Note**: `percentage_change` is calculated as `(threshold_count - base_count) / base_count * 100`. **Addresses FR-005 and SC-002.**
- [ ] T080 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py` to calculate minimum sample size required to detect r ≥ 0.3 with power ≥ 0.80 at α = 0.05. **Output**: `data/results/power_analysis.json` with calculated N and "Underpowered" flag if N < calculated threshold. **Addresses FR-005 and SC-005.** **Note**: Corrected FR reference from FR-006 to FR-005.

**Checkpoint**: US1 and US2 are integrated; Diagnostics complete.

---

## Phase 5: Final Reporting

**Purpose**: Generate the final report integrating all findings.

- [ ] T087 [US2/US3] **IMPLEMENT REPORT GENERATION WITH ASSOCIATIONAL FRAMING**: Implement `generate_report()` in `code/report.py`. **CRITICAL**:
 1. This task MUST enforce associational language **during generation** (e.g., via strict template constraints) rather than post-hoc scanning. The report MUST explicitly state "These results represent an associational relationship" and prohibit causal language like "causes" or "leads to".
 2. **MANDATORY**: This task MUST parse `data/results/sensitivity_analysis.json` (from T078) and include a summary of the stability of significant findings across thresholds in the final report.
 3. **MANDATORY**: This task MUST parse `data/results/timing_evidence.json` (from T016b) and include the execution duration in the final report.
 **Output**: `data/results/final_report.md`. **DEPENDS ON T025, T078, T080, T079, T022a, T026, T016b**. **Addresses FR-004 and SC-002/SC-004.**

**Checkpoint**: All diagnostics and reporting complete.

---

## Phase N+5: Real-Data Execution & GPU Offload Verification (Priority: P7) - REMOVED
**Note**: This phase was removed. The project is scoped as a "Pipeline Validation Study" using synthetic data. Real-data execution is out of scope for this phase.

---

## Phase N+6: Review Resolution & Final Validation (Priority: P10)

**Purpose**: Address specific reviewer concerns regarding the "Pipeline Validation Study" scope, the lack of real data, and the robustness of the synthetic validation logic. Ensure all artifacts are consistent with the current state of the project.

- [ ] T072 **DOCUMENT REAL DATA IMPOSSIBILITY**: Generate `docs/real_data_impossibility_report.md` documenting the search for a valid dataset.
- [ ] T073 Update `code/constitution_checker.py` to correctly identify the project as "Synthetic Only".

**Checkpoint**: The project is fully documented as a "Pipeline Validation Study", all constitutional checks pass for the synthetic scope, and the roadmap for future real-data integration is clearly defined.

---

## Phase N+7: Robustness & Scale Verification (Priority: P9) - REMOVED
**Note**: Removed T070 and T074. Robustness is now handled by T095 (Adaptive Subsampling) which ensures the pipeline works within constraints rather than testing violations.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup **(Phase 1) No dependencies - can start immediately
- **Foundational **(Phase 2) Depends on Setup completion - BLOCKS all user stories
- **User Stories **(Phase 3+) All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish **(Final Phase) Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 **(P1) Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 **(P2) Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 **(P3) Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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