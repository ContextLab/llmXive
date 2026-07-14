# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: Design documents from `/specs/001-visual-salience-moral-judgments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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
  
  Tasks MUST be organized by user story so each story can:
  - Be implemented independently
  - Be tested independently
  - Be delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/processed/`, `data/survey/`, `tests/`)
- [ ] T002 Initialize Python project with `requirements.txt` (numpy, pandas, scipy, statsmodels, Pillow, requests, matplotlib, seaborn, opencv-python-headless, streamlit, torch, transformers, diffusers)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup random seed configuration module (`code/config.py`) to ensure reproducibility across all scripts. **Mechanism**: Define `seed_everything(seed=42)` function that sets seeds for `numpy`, `random`, and `torch` at module import.
- [ ] T005 [P] Create data directory structure and checksum verification script (`code/verify_data_integrity.py`)
- [ ] T006 [P] Implement basic logging infrastructure (`code/logging_config.py`)
- [ ] T007 [P] Create base data models/entities in `code/models.py`: Define `Scenario` (id, image_path, ambiguity_label), `StimulusVariant` (id, scenario_id, salience_level, image_path), `Response` (id, participant_id, stimulus_id, rating, timestamp), and `Participant` (id, status) classes with explicit attributes per spec. **Reproducibility**: Any stochastic operations within these models (e.g., default initialization) MUST explicitly call `seed_everything()` with a fixed seed to ensure reproducibility as per the Constitution.
- [ ] T008 [P] Setup environment variable management for dataset paths and API keys

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Salience Manipulation (Priority: P1) 🎯 MVP

**Goal**: Ingest open visual datasets, identify morally ambiguous images, and generate manipulated variants with controlled luminance contrast.

**Independent Test**: Run pipeline on a set of raw images; verify metadata filter, human coding reliability (≥80%), and pixel-level contrast changes without semantic alteration.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement dataset ingestion and URL verification in `code/data_prep.py` (Target: Visual Genome or verified alternative). **Constraint**: MUST fetch from `https://visualgenome.org/api/` or verified HuggingFace mirror.
- [ ] T014 [US1] Implement metadata filtering for 'social'/'conflict' tags in `code/data_prep.py`
- [ ] T015a [US1] Implement Human Coding Interface: Create a Streamlit app (`code/human_coding_ui.py`) to allow ≥3 independent annotators to upload labels for candidate images. The app MUST enforce the ≥3 annotator requirement. **Logic**: If <3 annotators are available, the task is BLOCKED. If 3 annotators disagree, use majority vote to resolve. If no majority (e.g., 1-1-1), exclude scenario. Output a CSV (`data/processed/human_coding_annotations.csv`) compatible with T015.
- [ ] T015 [US1] Implement human coding workflow script (`code/human_coding.py`) to calculate Cohen's κ from annotations (input from T015a), apply the ≥0.6 threshold as required by FR-008, and **exclude** scenarios failing the threshold. If κ < 0.6, block and log failure. Output the filtered list of valid scenarios to `data/processed/valid_scenarios.csv`.
- [ ] T016 [US1] Implement salience manipulation function (low/med/high luminance) in `code/data_prep.py` ensuring no semantic change
- [ ] T017 [US1] Implement semantic preservation verification in `code/validation.py`. **MUST** use CLIP (default precision, CPU) to compute embeddings. **Logic**: Crop target region using bounding box from metadata. Compute CLIP embedding for ROI and full original image. Verify cosine similarity ≥ 0.95. **DO NOT** use YOLO or IoU.
- [ ] T017b [US1] Implement unit test for memory constraints regarding CLIP inference in `tests/unit/test_manipulation.py`. **Logic**: Verify that CLIP inference on a single image stays within 2GB RAM limit on CPU.
- [ ] T018 [US1] Implement failure logging and exclusion logic for unmanipulatable images in `code/data_prep.py`
- [ ] T019 [US1] Implement Pilot Human Manipulation Check in `code/manipulation_check.py`. **Logic**: Present manipulated images to a separate coder panel. Calculate agreement as (number of coders agreeing on narrative preservation) / (total coders). If agreement < 0.80, flag scenario as failed. Output results to `data/processed/narrative_check.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Survey Deployment and Data Collection (Priority: P2)

**Goal**: Present manipulated images in a randomized within-subject design and collect blame ratings.

**Independent Test**: Pilot survey with small cohort; verify randomization, within-subject constraints, and correct data logging.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement survey randomization engine (within-subject design) in `code/survey_sim.py` to generate sequences where no scenario appears twice with the same salience level for a participant.
- [ ] T023 [US2] Implement survey deployment interface using Streamlit in `code/survey_deploy.py`. **MUST** enforce the 'never the same one twice' constraint by implementing a `SessionState` dictionary. **Algorithm**: Use Latin Square randomization for within-subject design to ensure balanced order across participants. Check `session_state['seen_scenarios'][participant_id]`; if present, skip to next available salience level. Output schema: `participant_id`, `image_id`, `salience_level`, `rating`, `timestamp`. **Dependencies**: Requires completion of T016/T017 (Stimuli Generation) before execution.
- [ ] T023a [US2] Document Scope Limitation: Update `docs/paper_draft.md` under section **3.1 'Scope of Pilot Phase'**. Explicitly state that FR-002 and FR-003 are implemented as a *simulation* using `code/survey_sim.py` and local Streamlit, and that real participant recruitment is deferred.
- [ ] T024 [US2] Implement data collection handler to log responses to `data/survey/pilot_responses.csv`
- [ ] T026 [US2] Implement pilot data simulation script (`code/survey_sim.py`) to generate synthetic data for pipeline validation (strictly for testing logic, not empirical claims)

### Tests for User Story 2 (Restored) ⚠️

- [ ] T020 [P] [US2] Unit test for randomization logic (within-subject constraint) in `tests/unit/test_survey_logic.py`
- [ ] T021 [P] [US2] Unit test for data schema validation (participant_id, image_id, salience, rating) in `tests/unit/test_data_schema.py`
- [ ] T022 [P] [US2] Integration test for pilot data collection flow in `tests/integration/test_survey_flow.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform Linear Mixed-Effects Model (LMM) analysis (Primary) and Repeated-Measures ANOVA (Secondary) to test for salience effects, apply corrections, and generate reports.

**Independent Test**: Run analysis on synthetic datasets with known effects; verify F-statistics, p-values, effect sizes, and confidence intervals.

### Implementation for User Story 3

- [ ] T036 [US3] Implement pipeline validation script (Positive Control/Negative Control) in `code/validation.py`. **Logic**: Run synthetic data injection to verify LMM/ANOVA logic BEFORE processing real data. **Dependency**: MUST run before T030/T031.
- [ ] T045 [US3] Execute Data Cleaning: Run the straight-lining detection routine on `data/survey/pilot_responses.csv` to exclude participants with identical ratings across all items; output cleaned dataset `data/processed/cleaned_responses.csv`. **Logic**: Exclude if variance < 0.1 OR >90% identical ratings. **Dependency**: MUST run before T030/T031.
- [ ] T030 [US3] Implement Primary Analysis: Implement the Linear Mixed-Effects Model (`Rating ~ Salience + (1|Participant) + (1|Scenario)`) in `code/analysis.py` using `statsmodels` (per FR-004). **MUST** include random intercepts for Participant and Scenario. This is the PRIMARY analysis method.
- [ ] T031 [US3] Implement Secondary Validation: Implement the Repeated-Measures ANOVA (`Rating ~ Salience + Error(Subject/Salience)`) in `code/analysis.py` using `statsmodels`. This is the SECONDARY analysis method for robustness checking.
- [ ] T032 [US3] Implement ANOVA/LMM assumption checks (normality, homogeneity of variance) in `code/analysis.py`. **Logic**: Run Shapiro-Wilk test on residuals. If p < 0.05, switch to robust alternative: LMM with ordinal link function OR non-parametric bootstrap with a sufficient number of iterations to ensure robust resampling.
- [ ] T034 [US3] Implement pairwise comparisons in `code/analysis.py`. **Logic**: If normality holds, perform pairwise t-tests with Bonferroni correction. If normality violated, perform Wilcoxon signed-rank test with Bonferroni correction.
- [ ] T035 [US3] Implement effect size (partial eta-squared) and % CI calculation in `code/analysis.py` using Type III Sums of Squares.
- [ ] T046 [US3] Implement Precision Threshold Check: In `code/config.py`, set `MIN_PRECISION = 0.3`. In `code/analysis.py`, calculate the 95% CI width for the main effect. Compare `CI_width` against `MIN_PRECISION`. If `CI_width > 0.3`, log failure and set `precision_adequate=false` in `data/analysis/results.json`. **Do not use placeholder values; use the concrete constant.**
- [ ] T047 [US3] Implement Post-Hoc Power Analysis in `code/power_analysis.py`. **Logic**: Use observed effect size to calculate power. If calculated power < 0.80, write a warning to the report and set `power_adequate=false` in `data/analysis/results.json`.
- [ ] T037 [US3] Implement report generator to output `data/analysis/results.json` and console summary, explicitly documenting the LMM primary vs ANOVA secondary distinction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for LMM model fitting (Positive/Negative control) in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_corrections.py`
- [ ] T029 [P] [US3] Unit test for effect size (partial eta-squared) calculation in `tests/unit/test_metrics.py`
- [ ] T030 [P] [US3] Integration test for full analysis pipeline on synthetic data in `tests/integration/test_analysis_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Documentation updates: Add section **3.1 'Methods'** to `docs/paper_draft.md` describing the LMM model specification, data cleaning procedure, and Bonferroni correction.
- [ ] T038b [P] Documentation updates: Add section **4.1 'Results'** to `docs/paper_draft.md` with placeholders for LMM tables, effect sizes, and CI widths.
- [ ] T039a [P] Code cleanup: Refactor `code/data_prep.py` to reduce cyclomatic complexity < 10. Verify with `ruff`.
- [ ] T039b [P] Code cleanup: Refactor `code/analysis.py` to separate model fitting from result reporting. Verify with `ruff`.
- [ ] T050 [P] Add profiling script to measure runtime of the full pipeline (`code/profile_pipeline.py`)
- [ ] T051 Refactor code to ensure <6h runtime on 2 CPU/7GB RAM, verified by running `code/profile_pipeline.py` on full dataset
- [ ] T040 [P] Additional unit tests for edge cases (sample size < planned) in `tests/unit/`
- [ ] T041 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for stimuli data (T023 explicitly requires US1 completion)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for response data (T045 requires US2 output)

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

### Critical Execution Order (Phase 5)

The following order is **MANDATORY** for Phase 5 tasks:
1. **T036** (Pipeline Validation) - MUST run first to verify logic.
2. **T045** (Data Cleaning) - MUST run before analysis.
3. **T030** (Primary LMM) - MUST run on cleaned data.
4. **T031** (Secondary ANOVA) - MUST run on cleaned data.
5. **T032** (Assumption Checks) - Can run in parallel with T030/T031 or after.
6. **T034** (Pairwise Comparisons) - Depends on T030/T031 results.
7. **T035** (Effect Sizes) - Depends on T030/T031 results.
8. **T046** (Precision Check) - Depends on T035.
9. **T047** (Power Analysis) - Depends on T035.
10. **T037** (Report Generation) - Depends on all above.

**Note**: T030/T031 DEPEND ON T045 completion. T030/T031 DEPEND ON T036 completion.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for metadata filtering logic in tests/unit/test_data_prep.py"
Task: "Unit test for luminance manipulation (CLIP check) in tests/unit/test_manipulation.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset ingestion and URL verification in code/data_prep.py"
Task: "Implement human coding workflow script in code/human_coding.py"
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
- **FR-004 Compliance**: Linear Mixed-Effects Model (LMM) is the PRIMARY analysis method. Repeated-Measures ANOVA is secondary.
- **FR-008 Compliance**: Human coding interface requires ≥3 annotators. Majority vote resolution is mandatory. κ ≥ 0.6 is the threshold.
- **FR-002/003 Compliance**: Current phase is Pilot/Simulation; real deployment is deferred.
- **Plan vs Spec**: Tasks follow Spec.md (Visual Genome ingestion) over Plan.md (Manual Curation).