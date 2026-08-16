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
- [ ] T002 Initialize Python project with `requirements.txt` (numpy, pandas, scipy, statsmodels, Pillow, requests, matplotlib, seaborn, opencv-python-headless, streamlit, torch, transformers, diffusers, ordinal)
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

- [ ] T013 [P] [US1] Implement dataset ingestion and URL verification in `code/data_prep.py`. **Target**: **MoralD** (Primary) OR Visual Genome (Secondary) OR Validated Synthetic Pipeline. **Constraint**: MUST attempt to fetch from `huggingface.co/datasets/morald` first. If unavailable, fallback to `https://visualgenome.org/api/`. If BOTH fail, fallback to the validated synthetic generation pipeline defined in the Plan. If ALL fail, raise `DataFetchError` immediately. **Rationale**: Aligns with Spec US-001 and Plan Summary which prioritize MoralD and allow synthetic fallback only if real sources are unavailable.
- [ ] T014 [US1] Implement metadata filtering for 'social'/'conflict' tags in `code/data_prep.py`. **Logic**: Filter candidates based on metadata tags AND load external validation (MoralD tags OR theoretical framework config). **Output**: `data/processed/validated_candidates.csv`.
- [ ] T015 [US1] Implement human coding workflow script (`code/human_coding.py`) to calculate Cohen's κ from annotations (input from T015a), apply the ≥0.6 threshold as required by FR-008, and **exclude** scenarios failing the threshold. **Logic**: Explicitly cross-reference the coding output with the external validation source (MoralD OR framework config) to ensure scenarios are genuinely ambiguous independent of current study distribution. **Command**: Run `code/human_coding_ui.py` to collect annotations, then execute `code/human_coding.py` to process them into `data/processed/valid_scenarios.csv`. **Dependency**: Depends on T015a.
- [ ] T015a [US1] Implement Human Coding Interface: Create a Streamlit app (`code/human_coding_ui.py`) to allow ≥3 independent annotators to upload labels for candidate images. The app MUST enforce the ≥3 annotator requirement. **Logic**: If <3 annotators are available, the task is BLOCKED. If 3 annotators disagree, use majority vote to resolve. If no majority (e.g., 1-1-1), exclude scenario. **Output Contract**: Generate `data/processed/human_coding_annotations.csv` with columns `scenario_id`, `annotator_id`, `rating`.
- [ ] T016 [US1] Implement salience manipulation function (low/med/high luminance) in `code/data_prep.py` ensuring no semantic change
- [ ] T017 [US1] Implement semantic preservation verification in `code/validation.py`. **MUST** use CLIP (default precision, CPU) to compute embeddings. **Logic**: (1) Crop target region using bounding box; compute CLIP embedding for ROI in original vs ROI in manipulated; verify cosine similarity ≥ 0.95. (2) Crop background region (non-ROI); compute CLIP embedding for background in original vs manipulated; verify cosine similarity ≥ 0.99 (to ensure background is unchanged). (3) Compute texture and edge density changes (Laplacian variance) in ROI; verify change < 0.05 (Stimulus-Control Integrity). **DO NOT** compare full images.
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
- [ ] T023 [US2] Implement survey deployment interface using Streamlit in `code/survey_deploy.py`. **MUST** enforce the 'never the same one twice' constraint by implementing a `SessionState` dictionary. **Algorithm**: Use Latin Square randomization for within-subject design to ensure balanced order across participants. Check `session_state['seen_scenarios'][participant_id]`; if present, skip to next available salience level. **Output**: Generate `data/survey/survey_sequences.json` containing the randomized order for each participant ID. **Dependencies**: Requires completion of T016/T017 (Stimuli Generation) before execution.
- [ ] T024 [US2] Implement data collection handler to log responses to `data/survey/pilot_responses_real.csv` (Real Data) or `data/synth/pilot_responses_synth.csv` (Synthetic).
- [ ] T026 [US2] Implement pilot data simulation script (`code/survey_sim.py`) to generate synthetic data for pipeline validation (strictly for testing logic, not empirical claims). **Constraint**: Output MUST be written to `data/synth/` directory to prevent conflation with real data. **Logic**: Synthetic data MUST NOT be used for any empirical claims.
- [ ] T026a [US2] Implement Real Pilot Data Collection: Deploy survey to a small cohort (n>=20) and collect real blame ratings. **Output**: `data/survey/pilot_responses_real.csv`. **Constraint**: Must be distinct from synthetic validation data.
- [ ] T026b [US2] Enforce Data Separation: Ensure `data/survey/` contains only real data and `data/synth/` contains only synthetic data. Verify via directory structure and file naming conventions. **Logic**: If files are misplaced, raise `DataHygieneError`.

### Tests for User Story 2 (Restored) ⚠️

- [ ] T020 [P] [US2] Unit test for randomization logic (within-subject constraint) in `tests/unit/test_survey_logic.py`
- [ ] T021 [P] [US2] Unit test for data schema validation (participant_id, image_id, salience, rating) in `tests/unit/test_data_schema.py`
- [ ] T022 [P] [US2] Integration test for pilot data collection flow in `tests/integration/test_survey_flow.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform Cumulative Link Mixed Models (CLMM) analysis to test for salience effects, apply ordinal-specific corrections, and generate reports.

**Independent Test**: Run analysis on synthetic datasets with known effects; verify CLMM convergence, ordinal post-hoc tests, and effect sizes.

### Implementation for User Story 3

- [ ] T036 [US3] Implement pipeline validation script (Positive Control/Negative Control) in `code/validation.py`. **Logic**: Run synthetic data injection to verify CLMM logic BEFORE processing real data. **Dependency**: MUST run before T030/T031.
- [ ] T045 [US3] Execute Data Cleaning: Run the straight-lining detection routine on `data/survey/pilot_responses_real.csv` to exclude participants with identical ratings across all items; output cleaned dataset `data/processed/cleaned_responses.csv`. **Logic**: Exclude if variance < 0.1 OR >90% identical ratings. **Dependency**: MUST run before T030/T031.
- [ ] T032a [US3] Implement CLMM Convergence Check Logic in `code/analysis.py`. **Logic**: Implement the function to check for CLMM convergence. **Note**: This task implements the *logic* (static code), not the *execution* of the check. The execution happens in T030. **Dependency**: Must be implemented before T030/T031 execution.
- [ ] T032b [US3] Implement Fallback Model Selection Logic in `code/analysis.py`. **Logic**: If CLMM fails to converge, switch to a robust alternative: **Wilcoxon signed-rank test with Bonferroni correction**. **Constraint**: Do NOT use Bootstrap CLMM or generic ordinal regression without Bonferroni.
- [ ] T030 [US3] Implement Primary Analysis: Implement the Cumulative Link Mixed Model (`Rating ~ Salience + (1|Participant) + (1|Scenario)`) in `code/analysis.py` using the `ordinal` package (per FR-004). **MUST** include random intercepts for Participant and Scenario. This is the PRIMARY analysis method for ordinal data. **Output**: `data/analysis/clmm_results.csv`.
- [ ] T031 [US3] Implement Secondary Validation: Implement Robustness Checks for CLMM in `code/analysis.py`. **Logic**: If CLMM converges, run bootstrap resampling to verify stability of coefficients. If CLMM fails, run the robust alternative identified in T032b (Wilcoxon + Bonferroni). **DO NOT** implement ANOVA as it assumes continuous data.
- [ ] T034 [US3] Implement Ordinal Post-Hoc Pairwise Comparisons in `code/analysis.py`. **Logic**: Perform Tukey-adjusted (or Bonferroni) pairwise comparisons for ordinal regression (Low vs Medium, Medium vs High, Low vs High). **Constraint**: If using the fallback path (Wilcoxon), MUST use Bonferroni correction only. If using CLMM primary, Tukey is allowed.
- [ ] T035 [US3] Implement effect size (odds ratio) and % CI calculation in `code/analysis.py` using Type III Sums of Squares or equivalent for CLMM.
- [ ] T046 [US3] Implement Precision Threshold Check: In `code/config.py`, define `MIN_PRECISION` as a variable loaded from `config/research.yaml` (defaulting to 'deferred' if not set). In `code/analysis.py`, calculate the 95% CI width for the main effect. If `MIN_PRECISION` is 'deferred', calculate `min_acceptable_width` based on the observed effect size magnitude (e.g., width < 0.5 * effect_size) and compare. If `CI_width` > `min_acceptable_width`, set `precision_adequate=false` and log a warning. If `MIN_PRECISION` is set, compare directly. **Output**: Update `data/analysis/results.json` with key `precision_adequate`.
- [ ] T047 [US3] Implement Post-Hoc Power Analysis in `code/power_analysis.py`. **Logic**: Use observed effect size to calculate power. If calculated power < 0.80, write a warning to the report and set `power_adequate=false` in `data/analysis/results.json`.
- [ ] T037 [US3] Implement report generator to output `data/analysis/results.json` and console summary, explicitly documenting the CLMM primary analysis and ordinal post-hoc results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for CLMM model fitting (Positive/Negative control) in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for Ordinal Tukey-adjusted correction logic in `tests/unit/test_corrections.py`
- [ ] T029 [P] [US3] Unit test for effect size (odds ratio) calculation in `tests/unit/test_metrics.py`
- [ ] T030 [P] [US3] Integration test for full analysis pipeline on synthetic data in `tests/integration/test_analysis_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Documentation updates: Add section **3.1 'Methods'** to `docs/paper_draft.md` describing the CLMM model specification, data cleaning procedure, and ordinal post-hoc corrections.
- [ ] T038b [P] Documentation updates: Add section **4.1 'Results'** to `docs/paper_draft.md` with placeholders for CLMM tables, effect sizes, and CI widths.
- [ ] T039a [P] Code cleanup: Refactor `code/data_prep.py` to reduce cyclomatic complexity < 10. Verify with `ruff`.
- [ ] T039b [P] Code cleanup: Refactor `code/analysis.py` to separate model fitting from result reporting. Verify with `ruff`.
- [ ] T050 [P] Add profiling script to measure runtime of the full pipeline (`code/profile_pipeline.py`)
- [ ] T051 Refactor code to ensure <6h runtime on 2 CPU/7GB RAM, verified by running `code/profile_pipeline.py` on full dataset. **Verification**: Run `code/profile_pipeline.py`; if runtime > 6h, refactor and re-run until <6h is achieved. **Output**: `data/analysis/runtime_log.txt`.
- [ ] T040 [P] Additional unit tests for edge cases (sample size < planned) in `tests/unit/`
- [ ] T041 Run quickstart.md validation

---

## Phase 7: Data Integrity & Constitution Compliance (Revision)

**Goal**: Ensure strict adherence to the "Real Data Only" and "Fail Loudly" principles, addressing specific concerns regarding data sourcing and fabrication prevention.

### Implementation for Data Integrity

- [ ] T052 [P] [US1] Implement strict "Fail Loudly" data loader in `code/data_prep.py`. **Constraint**: Remove any `try/except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` when the real Visual Genome fetch fails. If the download fails, raise a `DataFetchError` immediately to halt execution. **Rationale**: Prevents silent substitution of fake data which triggers the fabrication gate.
- [ ] T053 [US1] Implement streaming logic for large dataset ingestion in `code/data_prep.py`. **Logic**: Use `datasets.load_dataset("visual_genome", split="train", streaming=True)` to process images in chunks, accumulating statistics without loading the full dataset into RAM. **Constraint**: If streaming is not feasible for the specific split, implement a deterministic sampling strategy (e.g., `itertools.islice` first N rows) and log the exact sample size and seed used. **Rationale**: Ensures the full dataset contributes to results without exceeding 7GB RAM limits, avoiding the need for toy datasets.
- [ ] T054 [US1] Implement "Verified Source" injection handler in `code/data_prep.py`. **Logic**: Check for an environment variable `VERIFIED_DATA_SOURCE`. If present, use the specified package/recipe (e.g., `huggingface_hub.hf_hub_download`) as the *single* source of truth, ignoring any other configured URLs. **Rationale**: Adopts execution-stage verified sources as mandated by the constitution.
- [ ] T055 [US1] Add unit test for "Fail Loudly" behavior in `tests/unit/test_data_loader.py`. **Logic**: Simulate a network failure for the Visual Genome URL and assert that the script raises `DataFetchError` rather than returning synthetic data.
- [ ] T056 [US3] Implement "Straight-lining" detection unit test in `tests/unit/test_data_cleaning.py`. **Logic**: Verify that the cleaning routine correctly identifies and excludes participants with variance < 0.1 or >90% identical ratings, ensuring the analysis only includes valid data.

**Checkpoint**: Data integrity and fabrication prevention mechanisms are verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Must be completed before any data ingestion tasks (T013) are executed to ensure safety.

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

The following order is **MANDATORY** for Phase 5 tasks. Note the distinction between **Implementation** (writing code) and **Execution** (running code).

1. **T036** (Pipeline Validation) - **Implementation & Execution**: MUST be implemented and run first to verify logic.
2. **T045** (Data Cleaning) - **Execution**: MUST run on raw data before analysis.
3. **T032a** (Convergence Logic Implementation) - **Implementation**: MUST be implemented (static code) before T030/T031 execution. This task defines the *function* that checks convergence; it does not run the check itself.
4. **T032b** (Fallback Model Selection Logic) - **Implementation**: MUST be implemented (static code) before T030/T031 execution. This task defines the *function* that selects the fallback model; it does not run the selection itself.
5. **T030** (Primary CLMM) - **Execution**: MUST run on cleaned data, calling the logic implemented in T032a/T032b to determine if it converges.
6. **T031** (Secondary Robustness) - **Execution**: MUST run on cleaned data, calling the logic implemented in T032a/T032b to execute the fallback if needed.
7. **T034** (Ordinal Post-Hoc) - **Execution**: Depends on T030/T031 results.
8. **T035** (Effect Sizes) - **Execution**: Depends on T030/T031 results.
9. **T046** (Precision Check) - **Execution**: Depends on T035.
10. **T047** (Power Analysis) - **Execution**: Depends on T035.
11. **T037** (Report Generation) - **Execution**: Depends on all above.

**Note**: T030/T031 DEPEND ON T045 and the *implementation* of T032a/T032b. T030/T031 DEPEND ON T036 completion. T032a/T032b are *implementation* tasks that must be completed (code written) before T030/T031 can be *executed*.

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
3. Complete Phase 7: Data Integrity (Ensure safety)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Data Integrity → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Data Integrity together
2. Once Foundation is done:
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
- **FR-004 Compliance**: Cumulative Link Mixed Models (CLMM) is the PRIMARY analysis method for ordinal data. ANOVA is NOT used.
- **FR-008 Compliance**: Human coding interface requires ≥3 annotators. Majority vote resolution is mandatory. κ ≥ 0.6 is the threshold. External cross-referencing (MoralD OR theoretical framework) is mandatory.
- **FR-002/003 Compliance**: Current phase is Pilot/Simulation; real deployment is deferred.
- **Plan vs Spec**: Tasks follow Spec.md (Visual Genome ingestion) over Plan.md (Manual Curation).
- **Constitution Compliance**: All data loaders MUST fail loudly on real data fetch failure. No synthetic fallbacks allowed. Streaming is preferred for large datasets.
- **SC-005 Compliance**: Precision thresholds are deferred/configurable, not hardcoded.
- **Data Separation**: Real data in `data/survey/`, synthetic data in `data/synth/`. No mixing.