# Tasks: Memory Load‑Adaptive Text Presentation for Abstract Concept Retention

**Input**: Design documents from `/specs/001-memory-load-adaptive-text/`
**Prerequisites**: plan.md, spec.md

**Tests**: Included per spec requirements (US-1, US-2, US-3 acceptance scenarios).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Dependencies are strictly enforced to ensure data flow from preprocessing to analysis.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `data/`, `code/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`data/raw`, `data/derived`, `code`, `tests`, `results`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `pandas`, `numpy`, `scipy`, `statsmodels`, `pyarrow`, `openneuro-py`, `pytest`, `transformers`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Execution Order Note**: T004 (Download) MUST precede T005 (Schema) to ensure the schema validates against the actual fetched data. T005b/c depend on T004 to confirm dataset characteristics.

- [ ] T004 [US1] Implement data download script in `code/download.py` using `openneuro-py` to fetch **ds004041** (Pupil Labs Reading) to `data/raw/`, explicitly verifying the dataset version hash against `data/metadata.yaml` (Constitution Principle I)
- [ ] T005 [US1] Create data model schema in `code/data_model.py` defining `Participant`, `Passage`, `Window`, and `AdaptationLabel` entities; **explicitly define `simplified_text` attribute as nullable** to reflect dataset limitations
- [X] T005b [US1] Define luminance normalization algorithm in `code/preprocessing.py` (not data_model.py) as a function or constant, and document the ingestion method for screen luminance logs from `ds004041`
- [X] T005c [US1] Create `data/metadata.yaml` entry to flag that the source dataset **lacks simplified text** for all passages, ensuring this is traceable for downstream graceful degradation logic (or counterfactual generation)
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` with structured JSON output for pipeline steps
- [X] T007 [P] Setup environment configuration management in `code/config.py` (handling data paths, random seeds, CLI thresholds)

**Checkpoint**: Foundation ready - user story implementation can now begin in sequence

---

## Phase 3: User Story 1 - Cognitive Load Index Calculation and Thresholding (Priority: P1) 🎯 MVP

**Goal**: Process raw pupil data to compute a valid Cognitive Load Index (CLI) and identify high-load windows.

**Independent Test**: Run preprocessing on a subset; verify CLI mean/variance and 0.5 SD segmentation logic.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Note: T009 assumes T005b (Phase 2) is complete.

- [X] T008 [P] [US1] Unit test for blink removal and 4Hz low-pass filtering in `tests/unit/test_preprocessing.py`
- [X] T009 [P] [US1] Unit test for baseline correction and luminance normalization (using algorithm from T005b in `preprocessing.py`) in `tests/unit/test_preprocessing.py`
- [X] T010 [P] [US1] Unit test for CLI z-score calculation and 0.5 SD thresholding in `tests/unit/test_cli_engine.py`
- [X] T011 [P] [US1] Integration test for full US-1 pipeline on sample data in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `preprocessing.py` functions: `remove_blinks`, `low_pass_filter` with a low cutoff frequency., `baseline_correct`, `normalize_luminance` (using algorithm defined in T005b), handling ingestion of luminance logs
- [ ] T013 [US1] Implement `cli_engine.py` functions: `compute_moving_average_zscore`, `identify_high_load_windows` (threshold defined by a statistically significant standard deviation deviation)
- [ ] T014 [US1] Implement outlier handling in `cli_engine.py`: flag windows > 3 SD from mean for exclusion
- [ ] T015 [US1] Create `code/us1_main.py` to orchestrate preprocessing and CLI generation, outputting `data/derived/cli_time_series.parquet`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulated Adaptive Text Rendering (Priority: P2)

**Goal**: Dynamically select original vs. simplified (counterfactual) text based on CLI state to simulate the adaptive condition.
**Dependency**: MUST run **after** T015 (CLI Time Series generation) and T021a (Passage Data Extraction).

**Independent Test**: Simulate presentation sequence; verify simplified text appears only during high-CLI windows (or defaults to original if missing).

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for text selection logic (high-CLI -> simplified if exists, else original) in `tests/unit/test_simulation.py`
- [ ] T017 [P] [US2] Unit test for graceful degradation (missing paraphrase -> original) in `tests/unit/test_simulation.py`
- [ ] T018 [P] [US2] Integration test for US-2 simulation on full dataset in `tests/integration/test_us2_simulation.py`

### Implementation for User Story 2

- [ ] T021a [US2] **Extract Passage Text Data**: Implement `code/simulation.py` function to ingest raw passage text (original) from `ds004041` and prepare it for joining with CLI data. Output `data/derived/passage_data.parquet`.
- [ ] T021b [US2] **Generate Counterfactual Text**: Implement `code/simulation.py` function to generate a "simplified" version of the original text for each passage using a CPU-tractable method (e.g., T5-small in 16-bit or rule-based simplification) to create the necessary "Adaptive" condition data. Output `data/derived/counterfactual_text.parquet`.
- [ ] T019 [US2] Implement `simulation.py` function: `select_text_version` (logic: if CLI > 0.5 SD -> use generated `counterfactual_text` from T021b, **else** -> use `original_text` from T021a; explicitly handle cases where generation fails by defaulting to original)
- [ ] T020 [US2] Implement `simulation.py` function: `generate_adaptation_labels` to create binary `AdaptationLabel` per window (flagging "adaptive" vs "control" conditions)
- [ ] T021 [US2] Create `code/us2_main.py` to join CLI data (from T015) with passage data (T021a) and counterfactual text (T021b), outputting `data/derived/adaptation_labels.parquet`
- [ ] T022 [US2] Implement logging for "adaptive selection" events (when simplified text is used) and "graceful degradation" events (if generation fails)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Interaction Analysis (Priority: P3)

**Goal**: Fit LME model and perform permutation tests to analyze the association between adaptation and recall.
**Dependency**: MUST run **after** T021 (AdaptationLabels generation).

**Independent Test**: Run analysis on simulated dataset; verify model coefficients, CI, and p-values match output format.

### Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for LME model formula construction in `tests/unit/test_analysis.py`
- [ ] T024 [P] [US3] Unit test for permutation test logic (10,000 shuffles) in `tests/unit/test_analysis.py`
- [ ] T025 [P] [US3] Integration test for full US-3 analysis pipeline in `tests/integration/test_us3_analysis.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `analysis.py` function: `fit_lme_model` using formula `Recall ~ Adaptation*PassageType + (1|Participant)` (statsmodels)
- [ ] T026b [US3] Implement `analysis.py` function: `run_likelihood_ratio_test` to **compare the full model (T026) against a reduced model without the interaction term** to extract the p-value for the interaction (distinct from permutation test)
- [ ] T027 [US3] Implement `analysis.py` function: `run_permutation_test` with a sufficient number of shuffles on adaptation labels to validate **associational strength** of the **simulated counterfactual**
- [ ] T028 [US3] Implement `analysis.py` function: `compute_sensitivity_analysis` sweeping CLI thresholds across a range of values SD (scoped as robustness check per FR-007)
- [ ] T029 [US3] Implement `analysis.py` function: `calculate_post_hoc_power` for observed effect size
- [ ] T030 [US3] Create `code/us3_main.py` to orchestrate analysis, generating `results/model_summary.csv` and `results/permutation_pvalue.csv`
- [ ] T031a [US3] **Define** the specific confounding risk text and non-causal disclaimer string (per FR-008) as a distinct artifact in `code/report_assets/disclaimer.txt`
- [ ] T031b [US3] Implement `code/report.py` to render the final report, explicitly including the disclaimer text from T031a and reporting the interaction term's β, 95% CI, and LRT p-value

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Response & Validation (Priority: P1)

**Goal**: Address specific concerns from prior research-stage reviews regarding the dataset's limitations, the non-causal nature of the findings, and the distinction between retention and understanding.
**Dependency**: MUST run **after** T030 (results) and T032 (Limitation Text) and T022 (Logs).

**Independent Test**: Verify that the analysis explicitly addresses these conceptual gaps in the final report and data collection.

### Implementation for Reviewer Response

- [ ] T032 [US3] Update `code/report.py` to include a dedicated section addressing the **limitation of the dataset**: explicitly state that the "adaptive" condition is a simulation (generated via T021b), that the source dataset lacks simplified text, and that findings are associational, not causal (referencing FR-008 and the "graceful degradation" logic from T022).
- [ ] T033 [US3] **Address Construct Validity**: Add a "Retention vs. Understanding" section to `code/report.py` that explicitly distinguishes between the measured outcome (delayed recall scores) and the unmeasured construct (comprehension/reasoning), framing the study's scope as strictly "memory of the text" rather than "memory of the concept."
- [ ] T034 [US3] **Address Ecological Validity**: Add a "Spatial Rigidity vs. Topological Flexibility" section to `code/report.py` discussing how the fixed spatial mapping in the Pupil Labs dataset (which lacks dynamic VR interaction) may limit the generalizability of findings to "deformable" cognitive spaces, explicitly stating that the study does not test topological deformation.
- [ ] T035 [US3] **Address Mechanistic Validity**: Add a "Neural Consolidation vs. Rehearsal" section to `code/report.py` that acknowledges the study measures behavioral retention (which may reflect short-term rehearsal) and explicitly states that the dataset cannot verify the molecular cascades (cAMP-PKA-CREB) required for long-term synaptic growth, framing the results as a proxy for engagement rather than a direct measure of consolidation mechanisms.

**Checkpoint**: All limitations and validity threats addressed in the report.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` (including `quickstart.md` and `data-model.md`)
- [ ] T037 Code cleanup and refactoring
- [ ] T038a [US3] Implement caching for CLI calculation in `code/cli_engine.py` to optimize runtime
- [ ] T038b [US3] Add integration test in `tests/integration/test_us3_analysis.py` that asserts total pipeline runtime ≤ 30 minutes
- [ ] T039 [P] Additional unit tests for edge cases (missing recall scores, extreme outliers) in `tests/unit/`
- [ ] T040 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Order within Phase 2**: T004 (Download) -> T005 (Schema) -> T005b/T005c -> T006/T007
- **User Stories (Phase 3+)**: Sequential dependency chain
 - **Phase 3 (US-1)**: Can start after Foundational
 - **Phase 4 (US-2)**: Depends on Phase 3 completion (T015) AND T021a (Passage Data)
 - **Phase 5 (US-3)**: Depends on Phase 4 completion (T021)
 - **Phase 6 (Reviewer Response)**: Depends on Phase 5 completion (T030) and T022 (Logs)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: **Depends on US-1 data (CLI)** (T015) AND **Passage Data Extraction** (T021a)
- **User Story 3 (P3)**: **Depends on US-2 data (AdaptationLabels)** (T021)
- **Phase 6 (Reviewer Response)**: Must wait for US-3 results to be generated and Limitation Text (T032) to be written

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006, T007) can run in parallel (within Phase 2, after T004/T005)
- Once Foundational phase completes, **User Stories must run sequentially** due to data dependencies (CLI -> Adaptation -> Analysis)
- All tests for a user story marked [P] can run in parallel (assuming Phase 2 is complete)
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for blink removal and 4Hz low-pass filtering in tests/unit/test_preprocessing.py"
Task: "Unit test for baseline correction and luminance normalization in tests/unit/test_preprocessing.py"
Task: "Unit test for CLI z-score calculation and 0.5 SD thresholding in tests/unit/test_cli_engine.py"

# Launch all models for User Story 1 together:
Task: "Implement preprocessing.py functions"
Task: "Implement cli_engine.py functions"
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
3. Add User Story 2 → Test independently → Deploy/Demo (Dependent on US-1)
4. Add User Story 3 → Test independently → Deploy/Demo (Dependent on US-2)
5. Add Phase 6 Reviewer Response → Validate conceptual completeness
6. Each story adds value without breaking previous stories

### Sequential Team Strategy (Recommended for Data Flow)

Given the strict data dependencies (CLI -> Adaptation -> Analysis):

1. Team completes Setup + Foundational together
2. Developer A: User Story 1
3. Once US-1 complete: Developer B: User Story 2 (including Counterfactual Generation T021b)
4. Once US-2 complete: Developer C: User Story 3
5. Team: Phase 6 Reviewer Response

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU-only CI with limited CPU resources (e.g., constrained RAM)

The research question, method, and references remain as specified in the original planning document.. No GPU models or 8-bit quantization. T021b uses CPU-tractable methods (e.g., T5-small 16-bit or rule-based).
- **Data Integrity**: No fabrication of data. All analysis must use the real Pupil Labs Reading dataset. T021b generates *counterfactual* text for simulation purposes only; raw data remains untouched.
- **Simplified Text**: The dataset **lacks** simplified text. T021b generates the necessary counterfactuals to create a distinct "Adaptive" condition. T019/T020 must handle generation failures gracefully.
- **Reviewer Concerns**: Phase 6 tasks explicitly address the methodological gaps identified by the research-stage reviewers (Aristotle, Rockmore, Kandel) regarding the distinction between memory and understanding, spatial rigidity, and neural consolidation mechanisms, framed as "Limitation Analysis" sections.