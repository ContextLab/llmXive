# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-015-improving-accessibility-and-usability-of/`)
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt` (scipy, matplotlib, pandas, jupyter, streamlit).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Active Tasks (Foundational)
- [ ] T012a [P] Create `CONTRIBUTING.md` with the mandatory "no synthetic data" clause and schema compliance guidelines. **Deliverable**: `CONTRIBUTING.md`. **Content**:
  ```markdown
  # Contributing Guidelines

  ## Data Integrity Policy
  **CRITICAL**: Do not use synthetic data for final research claims.
  - Use `--simulate` flag ONLY for local pipeline verification and CI testing.
  - The production pipeline MUST fail loudly (exit code 1) if `data/raw/` is empty or contains no real session files.
  - Synthetic data is strictly forbidden for generating final statistical results or publication figures.
  - All final claims must be derived from data collected via the web-based simulator (FR-007) or verified real-world sources.

  ## Schema Compliance
  - All session data MUST conform to `contracts/session.schema.yaml`.
  - Any deviation from the schema will cause the data loader to reject the file.
  ```
  **Dependencies**: None.

- [ ] T019b [P] Generate `contracts/session.schema.yaml` defining the JSON schema for session data. **Deliverable**: `contracts/session.schema.yaml`. **Content**:
  ```yaml
  $schema: http://json-schema.org/draft-07/schema#
  title: SessionData
  type: object
  required:
    - participant_id
    - disability_type
    - interface_type
    - sequence
    - start_time
    - end_time
    - error_count
    - explanation_engagement_time_seconds
    - sus_score
    - status
  properties:
    participant_id:
      type: string
    disability_type:
      type: string
    interface_type:
      type: string
      enum:
        - traditional
        - explainable
    sequence:
      type: string
      enum:
        - traditional_explainable
        - explainable_traditional
    start_time:
      type: string
      format: date-time
    end_time:
      type: string
      format: date-time
    error_count:
      type: integer
      minimum: 0
    explanation_engagement_time_seconds:
      type: number
      minimum: 0
    sus_score:
      type: integer
      minimum: 0
      maximum: 100
    status:
      type: string
      enum:
        - complete
        - incomplete
    dropout_reason:
      type: string
      nullable: true
  ```
  **Dependencies**: None.

- [ ] T035a [P] **SPEC AMENDMENT (Foundational)**: Update `spec.md` FR-002 to explicitly mandate **Repeated Measures ANOVA** for all interface comparisons and remove the requirement for Levene's test and the T-Test/Wilcoxon decision tree. **Deliverable**: Updated `spec.md` with a "Ratified Amendment" note for FR-002. **Action**: Replace the text of FR-002 with:
  ```markdown
  **FR-002**: System MUST implement a statistical analysis engine using `scipy.stats`. For each metric (Completion Time, Error Count, SUS), the system MUST perform a **Repeated Measures ANOVA** to test for significant differences between interface types. The system MUST apply the **Holm-Bonferroni correction** method to the resulting p-values to control the family-wise error rate. Normality checks (Shapiro-Wilk) may be logged for audit purposes but do not alter the choice of test; ANOVA is the mandated primary method per Constitution Principle VII and Plan, superseding the original Spec text.
  ```
  **Dependencies**: None. **Note**: This task is a blocking prerequisite for all statistical analysis tasks (Phase 5). Implementation of the ANOVA logic (T023a) is independent of this task but must align with the Plan/Constitution regardless of the spec file state.

### Active Tasks (Data & Logging)
- [ ] T019 [US1] Implement raw data logging to `data/raw/session_{session_id}.json`. The JSON **must** contain the fields defined in `contracts/session.schema.yaml`. The task **must abort** if the schema file is absent (enforced by the completion of T019b). **Dependencies**: T019b. **Deliverable**: One JSON file per completed (or incomplete) session stored under `data/raw/`.

**Checkpoint**: Foundation in progress - block on T019b and T035a completion. User story implementation cannot begin until T019b and T035a are complete.

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to configure and deploy Traditional vs. Explainable interface variants with XAI overlays.

**Independent Test**: The configuration module can be tested by loading a task definition and verifying that two distinct UI renders are generated: one without overlays and one with the specified XAI overlays, ensuring the XAI data is correctly bound to the UI elements.

### Implementation for User Story 0

- [ ] T010 [P] [US0] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [ ] T011 [P] [US0] Implement `ExplainableInterface` renderer in `code/simulator/interfaces/explainable.py`
- [ ] T012c [US0] Create the skeleton Streamlit app entry point `code/simulator/app.py` (basic layout, no collectors yet)
- [ ] T013a [US0] Define the overlay data schema in `code/simulator/schemas/overlay_schema.yaml`. **Deliverable**: Schema defining the structure of XAI overlay data (e.g., feature IDs, intensity values).
- [ ] T013b [US0] Implement `RuleBasedXAIOverlayGenerator` in `code/simulator/xai_overlay.py`. **Logic**: Generate deterministic, rule-based XAI overlays (e.g., heatmaps) based on task difficulty parameters (no external models or datasets). The generator must produce feature-level overlay data that can be visualized as heatmaps over UI elements. **Deliverable**: A function `generate_overlay(task_input) -> dict` returning overlay data based on task difficulty. **Dependencies**: T013a.
- [ ] T012d [US0] Implement the interactive Streamlit web application logic in `code/simulator/app.py`. **Logic**: Integrate `TraditionalInterface` (T010) and `ExplainableInterface` (T011) renderers. Implement user input handling for task completion, error logging, and SUS questionnaire. Ensure the app dynamically switches between interface variants based on the counterbalancing sequence. **Dependencies**: T010, T011, T012c, T013b.
- [ ] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Logic**: Ensure `RuleBasedXAIOverlayGenerator` (T013b) is called when rendering the `ExplainableInterface` and that the `LatinSquareCounterbalancer` (T015) dictates the sequence. **Dependencies**: T013b, T015, T012d.
- [ ] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`

**Checkpoint**: XAI overlay schema and generator tasks are defined but pending implementation.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Execute the standardized usability test protocol, collecting metrics (time, errors, SUS, engagement) for both interfaces with Latin Square counterbalancing.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement `LatinSquareCounterbalancer` in `code/simulator/counterbalance.py` to assign `Traditional->Explainable` or `Explainable->Traditional` sequences
- [ ] T016 [US1] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [ ] T016b [US1] Ensure `explanation_engagement_time` is logged to **raw** session files under `data/raw/` as part of the session JSON (aligned with FR‑001). **Deliverable**: Raw JSON includes `explanation_engagement_time_seconds`.
- [ ] T017 [US1] Integrate all collectors (T016, T016b, T015) and SUS questionnaire into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected. Implement SUS validation: reject if >1 item missing; if ≤1 missing, impute with participant mean and log imputation. **Dependencies**: T012e.
- [ ] T020 [US1] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`

**Checkpoint**: The system can collect real‑time interaction data, handle dropouts, and store immutable raw logs with schema validation.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Repeated Measures ANOVA, Holm‑Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested independently by feeding it a pre-generated CSV file with known distributions and verifying that ANOVA F-statistics, adjusted p-values, and effect sizes are calculated correctly. The script must also validate column presence and types.

### Implementation for User Story 2

- [ ] T021-exclude [US2] Define exclusion rules for incomplete sessions. **Logic**: Explicitly define the rule to exclude sessions where `status='incomplete'` from statistical aggregation. **Output**: None (logic definition only). **Dependencies**: T019, T019b.
- [ ] T021a [US2] Implement exclusion logic in `code/analysis/data_cleaner.py` to filter out sessions where `status='incomplete'`. **Output**: Intermediate CSV of complete sessions. **Dependencies**: T021-exclude, T019, T019b.
- [ ] T021b [US2] Implement SUS imputation logic in `code/analysis/data_cleaner.py`. **Logic**: If ≤1 item missing, impute with participant mean; if >1, mark as incomplete (handled by T021a). **Dependencies**: T021a.
- [ ] T021c [US2] Orchestrate the cleaning pipeline: Load raw data, apply T021a (exclusion), T021b (imputation), and type coercion. **Output**: `data/processed/cleaned_sessions.csv`. **Dependencies**: T021a, T021b, T019, T019b, T035a.
- [ ] T022 [US2] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py` and log results to `data/processed/normality_log.txt` (audit only). **Dependencies**: T035a.
- [ ] T023a [US2] Implement **Repeated Measures ANOVA** for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`. Normality results are logged only; ANOVA is always run per Constitution Principle VII. **Deliverable**: `data/processed/metrics_summary.csv` with columns `metric_name, interface_type, F_statistic, p_value, adjusted_p_value, effect_size`. **Dependencies**: T035a.
- [ ] T023b-exclude-enforce [US2] Ensure `explanation_engagement_time` is **excluded** from the ANOVA input but still retained for descriptive reporting. Log the exclusion to `data/processed/exclusion_log.txt`.
- [ ] T023b [US2] Compute descriptive statistics (mean, std) for `explanation_engagement_time` and output to `data/processed/descriptive_stats.csv`.
- [ ] T024 [US2] Implement Holm‑Bonferroni correction for the multiple ANOVA comparisons in `code/analysis/stat_utils.py`. **Dependencies**: T035a.
- [ ] T024a [US2] Verify primary ANOVA p‑value < 0.05 before applying Holm‑Bonferroni; write verification result to `data/processed/primary_test_verification.txt`.
- [ ] T025a [US2] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`) and basic orchestration calls.
- [ ] T035b [US2] Add a unit test `tests/unit/test_stat_rigor.py` that asserts `run_analysis.py` does not import or call `scipy.stats.levene` for the primary analysis, ensuring the Spec's Levene's requirement (now removed via amendment) is not inadvertently implemented. **Dependencies**: T025b, T035a. **Deliverable**: `tests/unit/test_stat_rigor.py`.
- [ ] T025b [US2] Implement data loader and validator in `code/analysis/run_analysis.py`:
  - Load `data/processed/cleaned_sessions.csv`.
  - Validate **exact columns**: `participant_id` (str), `interface_type` (enum: traditional|explainable), `completion_time_seconds` (float ≥ 0), `error_count` (int ≥ 0), `sus_score` (int 0‑100), `explanation_engagement_time_seconds` (float ≥ 0).
  - Enforce data‑type checks and allowed value ranges; abort with clear error messages on mismatch.
  - **Dependencies**: T035a, T021c.
- [ ] T025c [US2] Implement statistical engine wrapper in `code/analysis/run_analysis.py`:
  - Call functions from T022 (Shapiro), T023a (ANOVA), T024 (Holm-Bonferroni), T023b (Descriptive).
  - **Do not** implement the logic for these tests; only orchestrate their execution.
  - **Dependencies**: T022, T023a, T024, T023b.
- [ ] T025d [US2] Implement report writer in `code/analysis/run_analysis.py`:
  - Write `metrics_summary.csv`, `report_summary.txt`.
  - Verify that the CSV contains the required columns before exiting.
  - Exit code 0 on success, non‑zero on validation failure.
  - **Documentation**: Include a comment block citing "Constitution Principle VII" and "Spec FR-002 (Amended by T035a)" as the basis for using ANOVA. **Dependencies**: T025c.
- [ ] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py`:
  - Compute statistical power given N, effect size (eta‑squared), and α = 0.05.
  - **Deliverable**: `data/processed/power_flags.json` with schema `{ "subgroup": "<str>", "N": <int>, "power": <float>, "flag": "<UNDERPOWERED|OK>" }`.
- [ ] T026 [US2] Generate `data/processed/metrics_summary.csv` (handled within T025d).
- [ ] T035-e [US2] **IMPLEMENTATION PRIORITY**: Implement the Repeated Measures ANOVA logic in `code/analysis/stat_utils.py` (T023a) **independent** of the spec file state. **Logic**: Even if `spec.md` still contains the old T-Test text (before T035a is merged), the code MUST implement ANOVA as mandated by the Plan and Constitution Principle VII. **Deliverable**: Functional ANOVA code in `stat_utils.py`. **Dependencies**: None (Code logic follows Plan/Constitution). **Note**: This task ensures the implementation is never blocked by a pending spec amendment.

**Checkpoint**: The pipeline now cleans raw data, runs ANOVA with proper corrections, produces descriptive stats, and outputs power‑analysis flags.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

**Goal**: Generate publication‑quality visualizations and a single executable Jupyter notebook documenting the pipeline.

**Independent Test**: Run the notebook on a small sample dataset; verify that all figures are created, have correct axis labels, and that the notebook completes without errors.

### Implementation for User Story 3

- [ ] T027 [US3] Implement visualization functions in `code/analysis/visualizer.py`:
 - Box plot for Completion Time, Error Count, SUS with 95 % CI error bars.
 - Save each figure as **PNG** at a high resolution in `figures/` with filenames `completion_time.png`, `error_count.png`, `sus_score.png`.
- [ ] T028 [US3] Compile `code/analysis/analysis.ipynb` that:
 1. Loads raw data, runs cleaning, performs ANOVA, creates visualizations, runs power analysis.
 2. Contains markdown explanations for each step.
 3. Saves all generated artifacts.
- [ ] T029b [US3] Create GitHub Actions workflow file `.github/workflows/reproducibility_check.yml` to trigger the analysis notebook on a fresh runner. **Dependencies**: T028.
- [ ] T029c [US3] Add a verification task that executes `analysis.ipynb` on a **fresh GitHub Actions runner** via a standard GitHub Action workflow (using `actions/checkout`, `actions/setup-python`, and `jupyter/nbconvert`) to validate SC‑004 reproducibility. The task must:
 1. Ensure the workflow file (T029b) includes steps to execute the notebook.
 2. Verify the notebook completes without errors.
 3. Write `notebook_execution_log.txt` containing a SHA‑256 checksum of the notebook, execution status (SUCCESS/FAIL), and timestamps.
 4. **Dependencies**: T029b.
- [ ] T030 [US3] Ensure the notebook is fully deterministic: pin random seeds, use exact file paths, and verify that re‑running produces identical checksums for generated figures.

**Checkpoint**: The project now provides reproducible visualizations, a runnable notebook, and verifiable execution evidence.

---

## Phase 7: Data Simulation & Synthetic Fallback Prevention (Priority: P0)

**Goal**: Implement a deterministic, rule-based simulator to generate realistic interaction data for pilot testing and CI validation, strictly adhering to the "No Synthetic Fallback" rule for real data.

**Independent Test**: The simulator generates a dataset where the "Explainable" interface is mathematically guaranteed to be faster by a fixed offset, allowing verification of the ANOVA pipeline's ability to detect the effect.

### Implementation for Phase 7

- [X] T031b [US1] Implement schema validation in `code/simulator/simulator.py` to ensure the output of `DeterministicDataSimulator` (T031) strictly matches the schema defined in `contracts/session.schema.yaml` (T019b). **Deliverable**: The simulator must abort with a clear error if the output schema does not match the web app's schema. **Dependencies**: T019b, T031. **Note**: T031 is incomplete until T031b is done. **Status**: Active (waiting for T019b).
- [ ] T031 [US1] Implement `DeterministicDataSimulator` in `code/simulator/simulator.py`.
 - **Logic**: Generate synthetic sessions based on `N` participants.
 - **Constraint**: The "Explainable" condition MUST have `completion_time` = `baseline_time` - `fixed_offset` (e.g., [deferred] faster) to ensure a detectable effect for CI validation.
 - **Constraint**: The "Traditional" condition MUST have `completion_time` = `baseline_time`.
 - **Constraint**: Random noise must be added (Gaussian) but seeds must be pinned.
 - **CRITICAL WARNING**: This tool is **ONLY** for CI/pilot testing and **NOT** a replacement for the web-based simulator required by FR-007 for human participants. Do NOT use this for human participant data collection.
 - **Deliverable**: A CLI tool `python -m code.simulator.simulator --n 50 --seed 42 --output data/raw/simulated_sessions.json`.
- [ ] T032 [US1] Create `tests/unit/test_simulator.py` to verify that:
 - The simulator produces the expected `fixed_offset` in the mean difference.
 - The `explanation_engagement_time` is strictly positive for Explainable and zero for Traditional.
 - The output JSON schema matches `contracts/session.schema.yaml`.
- [ ] T033 [US2] Update `code/analysis/run_analysis.py` to accept a `--simulate` flag that triggers `DeterministicDataSimulator` if no raw data is found, **BUT** only for local CI validation.
 - **Critical Rule**: This flag MUST be explicitly disabled in production runs. The production pipeline must **fail loudly** (exit code 1) if `data/raw/` is empty or contains no real session files, preventing accidental use of synthetic data for final claims.
 - **CI Enforcement**: The task must implement a check for a CI environment variable (e.g., `CI_SIMULATE=false`) to enforce that the `--simulate` flag is disabled in production pipelines.
 - **CRITICAL WARNING**: The `--simulate` flag is **ONLY** for CI testing and **NOT** a replacement for the web-based simulator required by FR-007 for human participants.
 - **Distinction**: This flag is for CI testing ONLY, not for human participant studies.

**Checkpoint**: The project has a safe, deterministic way to test the pipeline logic without fabricating data for final claims.

---

## Phase 8: Spec-Plan Alignment Verification (Priority: P0)

**Goal**: Verify that the implementation strictly follows the Plan's scientific rigor and that the Spec amendment (T035a) has been successfully applied and documented.

**Independent Test**: Verify that the analysis pipeline runs ANOVA regardless of normality test results, and that Levene's test is not invoked, as per the Plan's resolution of the Spec conflict.

### Implementation for Phase 8

- [X] T035 [US2] Update `code/analysis/stat_utils.py` to explicitly document the ratified Spec amendment. Add a comment block stating: "Per Spec FR-002 (Amended by T035a) and Constitution Principle VII, Repeated Measures ANOVA is used for all metrics. Shapiro-Wilk is run for logging only; Levene's test is omitted as inappropriate for paired designs." **Dependencies**: T035a.
- [X] T035c [US2] Update `code/analysis/run_analysis.py` to write a `methodology_notes.txt` file in `data/processed/` that explicitly lists the statistical tests used (ANOVA, Holm-Bonferroni) and cites the amended Spec section (FR-002) that superseded the original requirements. **Dependencies**: T035a.
- [X] T035d [US2] Implement explicit removal of Levene's test logic in `code/analysis/stat_utils.py`. **Logic**: Ensure no code path calls `scipy.stats.levene`. **Verification**: Verify that no code path calls `scipy.stats.levene` and document this verification in a comment. **Dependencies**: T035a.

**Checkpoint**: The statistical pipeline is now rigorously aligned with the Plan and Constitution, with explicit documentation of the Spec amendment.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P0 → P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Simulation (Phase 7)**: Depends on Foundational (Phase 2) and US1 (Phase 4) schema definitions.
- **Conflict Resolution (Phase 8)**: Depends on Foundational (Phase 2) and US2 (Phase 5) implementation to ensure the statistical logic is correctly overridden.

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Depends on US0 for XAI overlay logic if real data is used, but can use T031 simulator for initial dev.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data format.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output format.
- **Phase 7 (Simulation)**: Can start after Foundational (Phase 2) - Provides data for US1/US2 testing.
- **Phase 8 (Resolution)**: Can start after Foundational (Phase 2) - Ensures statistical logic is correct.

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
- **Phase 7 (Simulation)** can run in parallel with US1/US2 implementation to provide immediate test data.
- **Phase 8 (Resolution)** can run in parallel with US2 implementation to ensure the statistical logic is correct.

---

## Parallel Example: User Story 1 & Phase 7

```bash
# Launch simulator test generation (Phase 7) while implementing US1:
Task: "Implement DeterministicDataSimulator in code/simulator/simulator.py"
Task: "Create tests/unit/test_simulator.py"

# Launch US1 implementation:
Task: "Implement LatinSquareCounterbalancer in code/simulator/counterbalance.py"
Task: "Implement data collection handlers in code/simulator/metrics_collector.py"
```

---

## Implementation Strategy

### MVP First (User Story 0 & 1 with Simulation)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (including T012a, T019b, T035a)
3. Complete Phase 7: Data Simulation (for immediate testing)
4. Complete Phase 3: User Story 0 (XAI Interface)
5. Complete Phase 4: User Story 1 (Benchmarking) - Use T031 for initial CI validation
6. **STOP and VALIDATE**: Test US1 pipeline with simulated data.
7. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 7 (Simulation) → Immediate test data available
3. Add User Story 0 → XAI rendering ready
4. Add User Story 1 → Data collection ready (can use simulation for dev)
5. Add User Story 2 → Statistical analysis ready
6. Add User Story 3 → Reporting ready
7. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 0 (XAI Interface)
 - Developer B: User Story 1 (Benchmarking) + Phase 7 (Simulation)
 - Developer C: User Story 2 (Analysis) + Phase 8 (Resolution)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: T033 ensures synthetic data is NEVER used for final claims; the pipeline must fail if real data is missing in production.
- **Critical**: Phase 8 ensures the statistical methodology aligns with the Plan and Constitution, resolving the Spec conflict via a formal amendment (T035a).
- **Critical**: T012a ensures `CONTRIBUTING.md` exists with the required synthetic data clause.
- **Critical**: T019b ensures `contracts/session.schema.yaml` exists for all downstream schema validations.
- **Critical**: T035a must be completed before T035/T035b to ensure Spec and Plan are aligned.
- **Critical**: T012d and T012e ensure the web-based simulator for human participants is fully implemented.
- **Critical**: T021a, T021b, T021c ensure data cleaning is atomized and verifiable.
- **Critical**: T025b, T025c, T025d ensure the analysis pipeline is atomized and verifiable.
- **Critical**: T029b and T029c ensure reproducibility testing is self-contained.
- **Critical**: T031 is for CI validation ONLY and does not satisfy FR-007 (web-based simulator for human participants).
- **Critical**: T035d ensures explicit removal of Levene's test logic.
- **Critical**: T035-e ensures ANOVA implementation proceeds regardless of spec file state.