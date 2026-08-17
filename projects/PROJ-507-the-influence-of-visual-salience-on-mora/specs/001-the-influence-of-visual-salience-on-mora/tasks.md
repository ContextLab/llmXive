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
- [X] T002 Initialize Python project with `requirements.txt` (numpy, pandas, scipy, statsmodels, Pillow, requests, matplotlib, seaborn, opencv-python-headless, streamlit, torch, transformers, diffusers, ordinal, ordinal-mixed-models)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup random seed configuration module (`code/config.py`) to ensure reproducibility across all scripts. **Mechanism**: Define `seed_everything(seed=42)` function that sets seeds for `numpy`, `random`, and `torch` at module import.
- [X] T005 [P] Create data directory structure and checksum verification script (`code/verify_data_integrity.py`)
- [X] T006 [P] Implement basic logging infrastructure (`code/logging_config.py`)
- [X] T007 [P] Create base data models/entities in `code/models.py`: Define `Scenario` (id, image_path, ambiguity_label), `StimulusVariant` (id, scenario_id, salience_level, image_path), `Response` (id, participant_id, stimulus_id, rating, timestamp), and `Participant` (id, status) classes with explicit attributes per spec. **Reproducibility**: Any stochastic operations within these models (e.g., default initialization) MUST explicitly call `seed_everything()` with a fixed seed to ensure reproducibility as per the Constitution.
- [ ] T008 [P] Setup environment variable management for dataset paths and API keys

**Data Integrity & Constitution Compliance (Moved to Foundational)**
- [X] T052 [P] [US1] Implement strict "Fail Loudly" data loader in `code/data_prep.py`. **Constraint**: Remove any `try/except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` when the real Visual Genome fetch fails. If the download fails, raise a `DataFetchError` immediately to halt execution, UNLESS the synthetic fallback path is explicitly configured and available. **Rationale**: Prevents silent substitution of fake data which triggers the fabrication gate, while allowing the valid synthetic fallback path defined in the Plan.
- [X] T053 [US1] Implement deterministic dataset ingestion for Visual Genome in `code/data_prep.py`. **Logic**: (1) Generate `data/raw/selected_ids.json` containing a fixed, sorted list of 1000 image IDs (seed=42) to ensure a deterministic subset. (2) Use `datasets.load_dataset("visual_genome", split="train", streaming=False)` to fetch ONLY the images matching these IDs. (3) Compute SHA-256 checksum of the downloaded subset and store in `data/raw/sample_metadata.json`. **Constraint**: The subset MUST be fixed by ID list, not by streaming order. **Rationale**: Ensures exact reproducibility on a fresh runner by using a fixed, checksummed local copy.
- [X] T053b [US1] Implement Reproducibility Verification in `code/data_prep.py`. **Logic**: On startup, read `data/raw/selected_ids.json` and re-download the subset; verify the SHA-256 checksum matches `data/raw/sample_metadata.json`. If mismatch, raise `ReproducibilityError`. **Rationale**: Guarantees the "fixed sample" is identical across runs, satisfying Constitution Principle I.
- [X] T054 [US1] Implement "Verified Source" injection handler in `code/data_prep.py`. **Logic**: Check for an environment variable `VERIFIED_DATA_SOURCE`. If present, use the specified package/recipe (e.g., `huggingface_hub.hf_hub_download`) as the *single* source of truth, ignoring any other configured URLs. **Rationale**: Adopts execution-stage verified sources as mandated by the constitution.
- [X] T055 [US1] Add unit test for "Fail Loudly" behavior in `tests/unit/test_data_loader.py`. **Logic**: Simulate a network failure for the Visual Genome URL and assert that the script raises `DataFetchError` rather than returning synthetic data.
- [X] T056 [US3] Implement "Straight-lining" detection unit test in `tests/unit/test_data_cleaning.py`. **Logic**: Verify that the cleaning routine correctly identifies and excludes participants with variance < 0.1 or >90% identical ratings, ensuring the analysis only includes valid data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Salience Manipulation (Priority: P1) 🎯 MVP

**Goal**: Ingest open visual datasets, identify morally ambiguous images, and generate manipulated variants with controlled luminance contrast.

**Independent Test**: Run pipeline on a set of raw images; verify metadata filter, human coding reliability (≥80%), and pixel-level contrast changes without semantic alteration.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement dataset ingestion and URL verification in `code/data_prep.py`. **Target**: **MoralD** (Primary) OR Visual Genome (Secondary) OR Validated Synthetic Pipeline. **Constraint**: MUST attempt to fetch from `huggingface.co/datasets/morald` first. If unavailable, fallback to `huggingface.co/datasets/visual_genome`. If BOTH fail, fallback to the validated synthetic generation pipeline defined in the Plan. **Output**: `data/processed/stimuli_raw.csv` (Real Data) OR `data/processed/synthetic_stimuli.csv` (Synthetic). **Rationale**: Aligns with Spec US-001 and Plan Summary which prioritize MoralD and allow synthetic fallback only if real sources are unavailable.
- [X] T014 [US1] Implement metadata filtering for 'social'/'conflict' tags in `code/data_prep.py`. **Logic**: Filter candidates based on metadata tags AND load external validation (MoralD tags OR theoretical framework config). **Output**: `data/processed/validated_candidates.csv`.
- [X] T015a [P] [US1] **TEST HARNESS ONLY**: Implement Unit Test Harness for Human Coding in `code/human_coding.py`. **Logic**: Programmatically generate mock annotation data for ≥3 independent annotators to simulate human coding for unit testing. **Output**: `data/processed/human_coding_annotations_mock.csv`. **Constraint**: This task is for testing ONLY; it does NOT fulfill FR-008. Real data must come from T015c. **Rationale**: Supports testing without violating real data requirements.
- [X] T015b [P] [US1] **SIMULATION ONLY**: Implement Unit Test for Human Coding Logic in `tests/unit/test_human_coding.py`. **Logic**: Verify that the `calculate_cohens_kappa` function works correctly on the mock data generated in T015a. **Constraint**: Do not use this data for empirical claims. **Rationale**: Validates the logic of the human coding pipeline.
- [X] T015c [US1] **MANDATORY FOR FR-008**: Execute Real Human Coding Protocol in `code/human_coding.py`. **Logic**: Read raw annotator data from `data/raw/human_coding/` (CSV/JSON files) collected from ≥3 independent human annotators. Calculate Cohen's κ for each scenario. Filter scenarios with mean ambiguity ≥ 3.5 AND κ ≥ 0.6. **Output**: `data/processed/valid_scenarios.csv`. **Constraint**: This is the ONLY task that fulfills the FR-008 requirement for real human coding. T015a/b are for testing only. **Rationale**: Implements the core FR-008 requirement to process real human coding data.
- [X] T016a [P] [US1] Generate Versioned Manipulation Config in `code/manipulation_config.py`. **Logic**: Write `config/manipulation.yaml` with fields: `version` (e.g., "1.0.0"), `seed` (42), `luminance_levels` (low, medium, high), `target_region` (bounding box logic), `output_path` (e.g., `data/processed/stimuli_manipulated.csv`). **Constraint**: Must be run before T016. **Constitution Principle VI Compliance**: This task ensures explicit, versioned parameters for stimulus generation. **Rationale**: Ensures explicit, versioned parameters for stimulus generation per Constitution Principle VI.
- [X] T016 [US1] Implement salience manipulation function (low/med/high luminance) in `code/data_prep.py` ensuring no semantic change. **Logic**: Read parameters from `config/manipulation.yaml` generated in T016a. Apply luminance changes to target regions. **Output**: `data/processed/stimuli_manipulated.csv` linking `scenario_id` to `variant_id` AND a directory `data/processed/images/` containing the manipulated images. **Dependency**: Depends on T016a. **Constitution Principle VI Compliance**: Uses versioned config to ensure reproducibility.
- [X] T017 [US1] Implement semantic preservation verification in `code/validation.py`. **MUST** use CLIP (default precision, CPU) to compute embeddings. **Logic**: (1) Crop target region using bounding box; compute CLIP embedding for ROI in original vs ROI in manipulated; verify cosine similarity ≥ 0.95. (2) Crop background region (non-ROI); compute CLIP embedding for background in original vs manipulated; verify cosine similarity ≥ 0.99 (to ensure background is unchanged). (3) Compute texture and edge density changes (Laplacian variance) in ROI using `cv2.Laplacian`; verify change < 0.05 (Stimulus-Control Integrity). **DO NOT** compare full images.
- [X] T017b [US1] Implement unit test for memory constraints regarding CLIP inference in `tests/unit/test_manipulation.py`. **Logic**: Verify that CLIP inference on a single image stays within 2GB RAM limit on CPU.
- [X] T018 [US1] Implement failure logging and exclusion logic for unmanipulatable images in `code/data_prep.py`
- [X] T019 [US1] Implement Pilot Human Manipulation Check in `code/manipulation_check.py`. **Logic**: Present manipulated images to a separate coder panel. Calculate agreement as (number of coders agreeing on narrative preservation) / (total coders). If agreement < 0.80, flag scenario as failed. Output results to `data/processed/narrative_check.csv`.
- [X] T019a [US1] Generate Stimulus Manifest: Create `data/processed/stimulus_manifest.json` linking `scenario_id`, `variant_id`, and `salience_level` for all generated stimuli. **Logic**: This file is required by the survey engine (T023) to map stimuli to survey items. **Dependency**: Depends on T016/T017 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Survey Deployment and Data Collection (Priority: P2)

**Goal**: Present manipulated images in a randomized within-subject design and collect blame ratings.

**Independent Test**: Pilot survey with small cohort; verify randomization, within-subject constraints, and correct data logging.

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement survey randomization engine (within-subject design) in `code/survey_sim.py` to generate sequences where no scenario appears twice with the same salience level for a participant.
- [X] T023a [P] [US2] **PILOT/SIMULATION ONLY**: Implement Survey Simulation Interface in `code/survey_deploy.py`. **Logic**: Generate `data/survey/survey_sequences.json` for simulated participants. **Constraint**: Output to `data/synth/` directory. **Rationale**: For pilot testing logic only; does not fulfill FR-002 for real data collection.
- [X] T023b [P] [US2] **MANDATORY FOR FR-002**: Implement Real Survey Deployment Interface in `code/survey_deploy.py`. **Logic**: Generate `config/survey_api.yaml` for API keys (Prolific/Qualtrics). Implement Streamlit app that renders the survey interface, enforces within-subject constraints, and logs responses to `data/survey/real_responses.csv`. **Output**: `config/survey_api.yaml` and `code/survey_deploy.py` (production ready). **Dependency**: Requires completion of T016/T017 (Stimuli Generation) and T019a (Stimulus Manifest) before execution. **Rationale**: This is the primary task for collecting real data as required by FR-002.
- [X] T024 [US2] Implement data collection handler to log responses to `data/survey/pilot_responses_real.csv` (Real Data) or `data/synth/pilot_responses_synth.csv` (Synthetic).
- [X] T024b [US2] **MANDATORY FOR FR-002**: Execute Real Survey Deployment in `code/survey_deploy.py`. **Logic**: Run the Streamlit app in production mode (or generate the Prolific/Qualtrics deployment configuration) to collect real participant data. **Output**: `data/survey/real_responses.csv`. **Dependency**: Requires T023b completion. **Rationale**: This is the execution step that fulfills the core data collection requirement.
- [X] T026 [US2] Implement pilot data simulation script (`code/survey_sim.py`) to generate synthetic data for pipeline validation (strictly for testing logic, not empirical claims). **Constraint**: Output MUST be written to `data/synth/` directory to prevent conflation with real data. **Logic**: Synthetic data MUST NOT be used for any empirical claims.
- [X] T026a [US2] **PILOT/SIMULATION ONLY**: Implement Simulated Pilot Data Collection: Deploy survey to a simulated cohort (n>=20) and collect simulated blame ratings. **Output**: `data/survey/pilot_responses_sim.csv`. **Constraint**: Must be distinct from synthetic validation data. **Dependency**: Requires T023 completion. **Rationale**: For pilot testing only; real data collection is handled by T024b.
- [X] T026b [US2] Enforce Data Separation: Ensure `data/survey/` contains only real/simulated data and `data/synth/` contains only synthetic data. Verify via directory structure and file naming conventions. **Logic**: If files are misplaced, raise `DataHygieneError`.

### Tests for User Story 2 (Restored) ⚠️

- [X] T020 [P] [US2] Unit test for randomization logic (within-subject constraint) in `tests/unit/test_survey_logic.py`
- [X] T021 [P] [US2] Unit test for data schema validation (participant_id, image_id, salience, rating) in `tests/unit/test_data_schema.py`
- [X] T022 [P] [US2] Integration test for pilot data collection flow in `tests/integration/test_survey_flow.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform Cumulative Link Mixed Models (CLMM) analysis to test for salience effects, apply ordinal-specific corrections, and generate reports.

**Independent Test**: Run analysis on synthetic datasets with known effects; verify CLMM convergence, ordinal post-hoc tests, and effect sizes.

### Implementation for User Story 3

- [X] T036 [US3] Implement pipeline validation script (Positive Control/Negative Control) in `code/validation.py`. **Logic**: Run synthetic data injection to verify CLMM logic BEFORE processing real data. **Dependency**: MUST run before T030/T031.
- [X] T045 [US3] Execute Data Cleaning: Run the straight-lining detection routine on `data/survey/pilot_responses_sim.csv` (or real data) to exclude participants with identical ratings across all items; output cleaned dataset `data/processed/cleaned_responses.csv`. **Logic**: Exclude if variance < 0.1 OR >90% identical ratings. **Dependency**: MUST run before T030/T031.
- [X] T032a [US3] Implement CLMM Convergence Check and Fallback Logic in `code/analysis.py`. **Logic**: Define function `def check_convergence_and_fallback(model) -> tuple[Model, str]:`. If `model.converged` is False, switch to 'LMM with Cluster-Robust Standard Errors' or 'Non-parametric Bootstrap CLMM'. **Constraint**: DO NOT use Wilcoxon signed-rank test as it does not account for nested data structure (Participant/Scenario). If fallback fails, raise `ConvergenceError`. **Note**: This task implements the *orchestration* logic (detect and switch). **Rationale**: Ensures fallback methods preserve the nested data structure required by FR-004.
- [X] T032b [US3] Implement Fallback Model Selection Logic in `code/analysis.py`. **Logic**: Define specific functions for 'LMM with Cluster-Robust SE' and 'Non-parametric Bootstrap CLMM'. **Constraint**: Must preserve random intercepts for Participant and Scenario. **Dependency**: Must be implemented before T030/T031 execution.
- [X] T030 [US3] Implement Primary Analysis: Implement the Cumulative Link Mixed Model (`Rating ~ Salience + (1|Participant) + (1|Scenario)`) in `code/analysis.py` using the `ordinal` package (per FR-004). **MUST** include random intercepts for Participant and Scenario. This is the PRIMARY analysis method for ordinal data. **Output**: `data/analysis/clmm_results.csv`. **Dependency**: Calls the logic implemented in T032a/T032b.
- [X] T031 [US3] Implement Secondary Validation: Implement Robustness Checks for CLMM in `code/analysis.py`. **Logic**: If CLMM converges, run bootstrap resampling to verify stability of coefficients. If CLMM fails, run the robust alternative identified in T032a (LMM/Bootstrap). **DO NOT** implement ANOVA as it assumes continuous data.
- [X] T031b [US3] Execute Fallback Logic in `code/analysis.py`. **Logic**: Explicitly call `check_convergence_and_fallback` from T030. If `ConvergenceError` is raised, execute the fallback model defined in T032b. **Output**: Update `data/analysis/results.csv` with fallback model results. **Dependency**: Depends on T030 completion.
- [X] T034 [US3] Implement Ordinal Post-Hoc Pairwise Comparisons in `code/analysis.py`. **Logic**: Perform Tukey-adjusted (or Bonferroni) pairwise comparisons for ordinal regression (Low vs Medium, Medium vs High, Low vs High). **Constraint**: If using the fallback path (LMM/Bootstrap), MUST use Bonferroni correction only. If using CLMM primary, Tukey is allowed.
- [X] T035 [US3] Implement effect size (odds ratio) and % CI calculation in `code/analysis.py` using Type III Sums of Squares or equivalent for CLMM.
- [X] T046 [US3] Implement Precision Threshold Check: In `code/config.py`, define `MIN_PRECISION` as a variable loaded from `config/research.yaml`. Default value: a small positive constant. In `code/analysis.py`, calculate the 95% CI width for the `salience` coefficient: `ci_width = abs(conf_int_upper - conf_int_lower)`. Compare against `MIN_PRECISION`. If `MIN_PRECISION` is 'deferred', use default 0.1 and log a warning. **Output**: Update `data/analysis/results.json` with keys `ci_width`, `precision_adequate`, `ci_level`. **Rationale**: Makes SC-005 testable by default.
- [X] T047 [US3] Implement Post-Hoc Power Analysis in `code/power_analysis.py`. **Logic**: Use observed effect size to calculate power. If calculated power < 0.80, write a warning to the report and set `power_adequate=false` in `data/analysis/power_results.json`.
- [X] T047b [US3] Integrate Power Analysis into Report in `code/analysis.py`. **Logic**: Read `data/analysis/power_results.json` and merge `power_adequate` and `power_value` into `data/analysis/results.json`. **Output**: Updated `data/analysis/results.json`. **Dependency**: Depends on T047 completion.
- [X] T047c [US3] **MANDATORY REPORTING**: Integrate Power Analysis into Final Report Generator. **Logic**: Update `code/analysis.py` (T037) to explicitly read `data/analysis/results.json` and include `power_adequate` and `power_value` in the console summary and final report output. **Constraint**: The report MUST state if power < 0.80 and note wider confidence intervals. **Rationale**: Ensures the spec's acceptance scenario for reporting reduced power is met.
- [X] T037 [US3] Implement report generator to output `data/analysis/results.json` and console summary, explicitly documenting the CLMM primary analysis and ordinal post-hoc results. **Logic**: Read `data/analysis/results.json` (which includes power data from T047b/T047c) and generate report. **Constraint**: Must include `power_adequate` and `ci_width` in output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for CLMM model fitting (Positive/Negative control) in `tests/unit/test_analysis.py`
- [X] T028 [P] [US3] Unit test for Ordinal Tukey-adjusted correction logic in `tests/unit/test_corrections.py`
- [X] T029 [P] [US3] Unit test for effect size (odds ratio) calculation in `tests/unit/test_metrics.py`
- [X] T030 [P] [US3] Integration test for full analysis pipeline on synthetic data in `tests/integration/test_analysis_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038a [P] Documentation updates: Add section **3.1 'Methods'** to `docs/paper_draft.md` describing the CLMM model specification, data cleaning procedure, and ordinal post-hoc corrections.
- [X] T038b [P] Documentation updates: Add section **4.1 'Results'** to `docs/paper_draft.md` with placeholders for CLMM tables, effect sizes, and CI widths.
- [X] T039a [P] Code cleanup: Refactor `code/data_prep.py` to reduce cyclomatic complexity < 10. Verify with `ruff`.
- [X] T039b [P] Code cleanup: Refactor `code/analysis.py` to separate model fitting from result reporting. Verify with `ruff`.
- [X] T050 [P] Add profiling script to measure runtime of the full pipeline (`code/profile_pipeline.py`)
- [X] T051 Refactor code to ensure <6h runtime on 2 CPU/7GB RAM, verified by running `code/profile_pipeline.py` on full dataset. **Verification**: Run `code/profile_pipeline.py`; if runtime > 6h, refactor and re-run until <6h is achieved. **Output**: `data/analysis/runtime_log.txt`.
- [ ] T040 [P] Additional unit tests for edge cases (sample size < planned) in `tests/unit/`
- [ ] T041 Run quickstart.md validation

---

## Phase 7: Review Resolution & Constitution Hardening (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data integrity, reproducibility, and constitutional compliance.

**Independent Test**: Verify that all "Fail Loudly" mechanisms trigger correctly on simulated network failure, and that no synthetic data is used in the primary analysis pipeline unless explicitly configured.

### Implementation for Review Resolution

- [X] T060 [P] [US1] Refactor `code/data_prep.py` to remove all `try/except` blocks that catch `Exception` during dataset download. **Constraint**: Replace with specific `requests.exceptions.RequestException` handling that raises `DataFetchError` if the fetch fails. **Rationale**: Prevents silent fallback to synthetic data which violates the "Fail Loudly" rule and triggers the fabrication gate.
- [ ] T061 [US1] Implement explicit sample size logging in `code/data_prep.py`. **Logic**: When downloading a fixed sample, compute SHA-256 checksum of the subset. Log exact count, checksum, and seed used to `data/raw/sample_metadata.json`. **Output Schema**: `{"count": int, "checksum_sha256": str, "seed": int, "timestamp": str}`. **Rationale**: Ensures reproducibility and transparency for the fixed sample approach required by the plan.
- [X] T062 [US3] Add explicit check for CLMM convergence in `code/analysis.py` before proceeding to post-hoc tests. **Logic**: If `model.converged` is False, log a critical warning and immediately switch to the fallback (LMM/Bootstrap) as per FR-004. **Rationale**: Ensures the analysis does not proceed with invalid model parameters.
- [X] T063 [US3] Implement strict separation of synthetic and real data paths in `code/analysis.py`. **Logic**: If the input file path contains `data/synth/`, raise a `DataHygieneError` unless the `--allow-synthetic` flag is explicitly passed. **Rationale**: Prevents accidental analysis of synthetic data for empirical claims.
- [X] T064 [US2] Verify that the survey randomization logic in `code/survey_sim.py` correctly handles the "no same scenario twice" constraint for all participants. **Logic**: Add a unit test that simulates 100 participants and verifies that no participant sees the same scenario with the same salience level twice. **Rationale**: Ensures the within-subject design integrity.
- [X] T065 [US1] Add a task to document the "Verified Source" injection mechanism in `docs/data_hygiene.md`. **Logic**: Explain how the `VERIFIED_DATA_SOURCE` environment variable overrides default URLs and why this is critical for reproducibility. **Rationale**: Provides transparency for the execution-stage verified source adoption.

**Checkpoint**: Review concerns resolved; pipeline is constitutionally compliant.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Depends on completion of all User Story implementations.

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
3. **T032a** (Convergence Logic Implementation) - **Implementation**: MUST be implemented (static code) before T030/T031 execution. This task defines the *function* that checks convergence and switches; it does not run the check itself.
4. **T032b** (Fallback Model Selection Logic) - **Implementation**: MUST be implemented (static code) before T030/T031 execution. This task defines the *function* that selects the fallback model; it does not run the selection itself.
5. **T030** (Primary CLMM) - **Execution**: MUST run on cleaned data, calling the logic implemented in T032a/T032b to determine if it converges.
6. **T031b** (Execute Fallback Logic) - **Execution**: MUST run on cleaned data, explicitly calling the fallback if T030 fails.
7. **T031** (Secondary Robustness) - **Execution**: MUST run on cleaned data, calling the logic implemented in T032a/T032b to execute the fallback if needed.
8. **T034** (Ordinal Post-Hoc) - **Execution**: Depends on T030/T031 results.
9. **T035** (Effect Sizes) - **Execution**: Depends on T030/T031 results.
10. **T046** (Precision Check) - **Execution**: Depends on T035.
11. **T047** (Power Analysis) - **Execution**: Depends on T035.
12. **T047b** (Integrate Power) - **Execution**: Depends on T047.
13. **T047c** (Report Integration) - **Execution**: Depends on T047b.
14. **T037** (Report Generation) - **Execution**: Depends on all above.

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
- **FR-002/003 Compliance**: Current phase is Pilot/Simulation; real deployment is deferred to T024b.
- **Plan vs Spec**: Tasks follow Spec.md (Visual Genome ingestion) over Plan.md (Manual Curation).
- **Constitution Compliance**: All data loaders MUST fail loudly on real data fetch failure. No synthetic fallbacks allowed unless explicitly configured as a valid path. Streaming is replaced by fixed sample download for reproducibility.
- **SC-005 Compliance**: Precision thresholds are configurable, default 0.1.
- **Data Separation**: Real data in `data/survey/`, synthetic data in `data/synth/`. No mixing.
- **Revision Pass**: Phase 7 tasks address specific reviewer concerns regarding data integrity, reproducibility, and constitutional compliance.
- **FR-002/FR-008 Compliance**: T015c and T024b are the mandatory tasks for real data collection; T015a/b and T023a/T026a are for testing/simulation only.
- **Constitution Principle VI Compliance**: T016a ensures versioned parameters for stimulus generation.
- **Nested Data Structure**: T032a/T032b ensure fallback models preserve random intercepts for Participant and Scenario.