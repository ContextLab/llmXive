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

- [ ] T001a Create project directory structure (`code/`, `data/raw/`, `data/processed/`, `data/survey/`, `data/synth/`, `tests/`, `contracts/`, `config/`, `docs/`). **Verification**: Script `code/verify_structure.py` asserts all directories exist.
- [ ] T001b-INIT [P] **INIT**: Generate missing config files (.gitignore, .ruff.toml, .env.example) and verify. **Logic**: (1) Write `.gitignore` excluding `data/`, `__pycache__`, `*.pyc`. (2) Write `.ruff.toml` with `max-line-length=100`. (3) Write `.env.example` with `VISUAL_GENOME_URL`, `SURVEY_API_KEY`. (4) Run verification script to assert all files exist and contain required keys. **Dependency**: None.
- [ ] T001c [P] **CONFIG**: Generate `config/pre_registration.yaml` with pre-registered precision threshold. **Logic**: Create `config/pre_registration.yaml` containing `MIN_PRECISION: <value_to_be_set_by_researcher>` and `verification_status: UNVERIFIED`. This file is required by T046. **Dependency**: None.
- [ ] T002 Initialize Python project with `requirements.txt` (numpy, pandas, scipy, statsmodels, Pillow, requests, matplotlib, seaborn, opencv-python-headless, streamlit, torch, transformers, diffusers, ordinal, ordinal-mixed-models).
- [X] T003a Verify `.ruff.toml` exists and is valid. **Logic**: Assert file exists and contains required keys. **Dependency**: T001b-INIT.
- [X] T008a Verify `.env.example` exists and contains required keys. **Logic**: Assert file contains `VISUAL_GENOME_URL` and `SURVEY_API_KEY`. **Dependency**: T001b-INIT.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup random seed configuration module (`code/config.py`) to ensure reproducibility across all scripts. **Mechanism**: Define `seed_everything(seed=42)` function that sets seeds for `numpy`, `random`, and `torch` at module import.
- [X] T005 [P] Create data directory structure and checksum verification script (`code/verify_data_integrity.py`)
- [X] T006 [P] Implement basic logging infrastructure (`code/logging_config.py`)
- [X] T007 [P] Create base data models/entities in `code/models.py`: Define `Scenario` (id, image_path, ambiguity_label), `StimulusVariant` (id, scenario_id, salience_level, image_path), `Response` (id, participant_id, stimulus_id, rating, timestamp), and `Participant` (id, status) classes with explicit attributes per spec. **Reproducibility**: Any stochastic operations within these models (e.g., default initialization) MUST explicitly call `seed_everything()` with a fixed seed to ensure reproducibility as per the Constitution.
- [X] T052 [P] [US1] Implement strict "Fail Loudly" data loader in `code/data_prep.py`. **Constraint**: Remove any `try/except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` when the real Visual Genome fetch fails. If the download fails, raise a `DataFetchError` immediately to halt execution, UNLESS the synthetic fallback path is explicitly configured and available. **Rationale**: Prevents silent substitution of fake data which triggers the fabrication gate, while allowing the valid synthetic fallback path defined in the Plan.
- [X] T052-VERIFY-AND-FIX [P] [US1] **VERIFY & FIX**: Verify T052 logic and auto-fix if broken. **Logic**: (1) Run T052 logic on a mock network failure. (2) If it does not raise `DataFetchError`, automatically patch `code/data_prep.py` to enforce the "Fail Loudly" behavior. (3) Re-run verification. **Rationale**: Ensures T052 (the Producer) is valid before downstream consumption, resolving the "Producer incomplete" concern.
- [X] T053-GEN [P] [US1] Generate deterministic dataset ID list. **Logic**: Generate `data/raw/selected_ids.json` containing a fixed, sorted list of 1000 image IDs (seed=42) derived from a **verified source** (e.g., specific commit hash or checksum of the MoralD/Visual Genome subset). **Rationale**: Ensures exact reproducibility on a fresh runner by using a fixed, checksummed local copy. **Dependency**: T053-RAW-CHECKSUM.
- [X] T053-RAW-CHECKSUM [P] [US1] **MANDATORY**: Download and checksum the full raw dataset from the canonical source BEFORE ID generation. **Logic**: (1) Fetch the full raw dataset (e.g., Visual Genome) from the canonical source (Hugging Face). (2) Compute SHA-256 checksum of the raw file. (3) Store checksum in `data/raw/source_checksum.txt`. (4) Verify the checksum matches the canonical source's published hash. **Constraint**: This task MUST complete before T053-GEN. **Rationale**: Ensures the source data integrity is guaranteed before subset selection, satisfying Constitution Principle I for fresh runners.
- [X] T053-EXEC [P] [US1] Execute dataset download for selected IDs. **Logic**: Use `datasets.load_dataset("visual_genome", split="train", streaming=False)` to fetch ONLY the images matching IDs in `data/raw/selected_ids.json`. Compute SHA-256 checksum and store in `data/raw/sample_metadata.json`. **Constraint**: The subset MUST be fixed by ID list, not by streaming order. **Dependency**: T053-GEN.
- [X] T053c [US1] Verify `selected_ids.json` exists before proceeding. **Logic**: Assert `data/raw/selected_ids.json` exists. If missing, raise `FileNotFoundError`. **Dependency**: T053-GEN.
- [X] T053b [US1] Implement Reproducibility Verification in `code/data_prep.py`. **Logic**: On startup, read `data/raw/selected_ids.json` (output of T053-GEN) and re-download the subset; verify the SHA-256 checksum matches `data/raw/sample_metadata.json` (output of T053-EXEC). If mismatch, raise `ReproducibilityError`. **Rationale**: Guarantees the "fixed sample" is identical across runs, satisfying Constitution Principle I. **Dependency**: T053-EXEC must complete (code written and executed) before this runs.
- [X] T054 [US1] Implement "Verified Source" injection handler in `code/data_prep.py`. **Logic**: Check for an environment variable `VERIFIED_DATA_SOURCE`. If present, use the specified package/recipe (e.g., `huggingface_hub.hf_hub_download`) as the *single* source of truth, ignoring any other configured URLs. **Rationale**: Adopts execution-stage verified sources as mandated by the constitution.
- [X] T055 [US1] Add unit test for "Fail Loudly" behavior in `tests/unit/test_data_loader.py`. **Logic**: Simulate a network failure for the Visual Genome URL and assert that the script raises `DataFetchError` rather than returning synthetic data. **Constraint**: Must create `tests/unit/test_data_loader.py`.
- [X] T055a [US1] Verify `tests/unit/test_data_loader.py` exists and passes. **Logic**: Run `pytest tests/unit/test_data_loader.py`. **Dependency**: T055 must complete.
- [X] T056 [US3] Implement "Straight-lining" detection unit test in `tests/unit/test_data_cleaning.py`. **Logic**: Verify that the cleaning routine correctly identifies and excludes participants with variance < 0.1 or >90% identical ratings, ensuring the analysis only includes valid data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Salience Manipulation (Priority: P1) 🎯 MVP

**Goal**: Ingest open visual datasets, identify morally ambiguous images, and generate manipulated variants with controlled luminance contrast.

**Independent Test**: Run pipeline on a set of raw images; verify metadata filter, human coding reliability (≥80%), and pixel-level contrast changes without semantic alteration.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement dataset ingestion and URL verification in `code/data_prep.py`. **Target**: **Visual Genome** (Primary) OR MoralD (Secondary) OR Validated Synthetic Pipeline. **Logic**: (1) Attempt to fetch from `huggingface.co/datasets/visual_genome`. (2) If available, scan for 'social'/'conflict' tags. (3) If tags insufficient, fallback to MoralD. (4) If both fail, fallback to validated synthetic generation. **Constraint**: MUST verify content tags in MoralD if used. **Output**: `data/processed/stimuli_raw.csv` (Real Data) OR `data/processed/synthetic_stimuli.csv` (Synthetic). **Rationale**: Aligns with Spec US-001 and Plan Summary which prioritize Visual Genome tags and allow fallback only if content is insufficient.
- [X] T013-SOURCE-VERIFY [US1] **VERIFY**: Ensure the checksummed source (T053-RAW-CHECKSUM) matches the selected source in this task. **Logic**: Compare the source type (Visual Genome vs MoralD) selected in T013 with the source checksummed in T053-RAW-CHECKSUM. If they differ, raise `SourceMismatchError` unless the project is explicitly switching to a new source (which requires re-running T053-RAW-CHECKSUM). **Constraint**: Must run before T014-FILTER. **Rationale**: Prevents wasted execution if the source chosen in Phase 3 differs from the one checksummed in Phase 2.
- [X] T013b [US1] **DOWNLOAD**: Fetch external validation source (MoralD or Framework). **Logic**: Download the MoralD dataset or the specified theoretical framework config file from a verified source (e.g., Hugging Face) and store in `data/raw/external_validation/`. **Constraint**: This task must complete before T014-CROSSREF-EXEC. **Rationale**: Provides the external source required for cross-reference verification (FR-008).
- [X] T014-FILTER [US1] Implement metadata filtering for 'social'/'conflict' tags in `code/data_prep.py`. **Logic**: Filter candidates based on metadata tags. **Output**: `data/processed/candidates_filtered.csv`. **Dependency**: T013-SOURCE-VERIFY.
- [X] T014-CROSSREF-EXEC [US1] **MANDATORY FOR FR-008**: Perform cross-reference verification for ambiguity definition. **Logic**: (1) Load external validation source (from T013b). (2) Cross-reference the ambiguity definition against the external framework or MoralD dataset. (3) Log the alignment in `data/processed/cross_reference_log.txt`. (4) If the cross-reference fails (e.g., definitions do not align), raise `CrossReferenceError`. **Constraint**: This task MUST complete before T015d. **Rationale**: Ensures the ambiguity definition is not circular (FR-008).
- [X] T015d [US1] **MANDATORY FOR FR-008**: Implement Human Coding Protocol & Interface in `code/human_coding.py`. **Logic**: (1) Define recruitment protocol (≥3 independent annotators). (2) Generate `code/human_coding_interface.py` to ingest raw annotator data from `data/raw/human_coding/` (CSV/JSON). (3) Calculate Cohen's κ for each scenario. (4) Filter scenarios with mean ambiguity ≥ 3.5 AND κ ≥ 0.6. **Output**: `data/processed/valid_scenarios.csv`. **Constraint**: This task generates the *interface* and *protocol*; real data must be placed in `data/raw/human_coding/` by the researcher or via a verified source injection. **Rationale**: Provides the missing upstream task to make T015c executable.
- [X] T015e-RECRUIT [US1] **RECRUIT**: Generate recruitment survey and polling mechanism. **Logic**: (1) Generate `code/generate_survey.py` for local polling or Qualtrics API config. (2) Implement `code/poll_responses.py` to check for new responses. **Rationale**: Provides the concrete mechanism for data collection.
- [X] T015e-WAIT [US1] **WAIT**: Block until ≥3 human responses collected. **Logic**: Poll `data/raw/human_coding/` until >=3 valid response files exist. **Constraint**: This task MUST NOT complete until the data exists. **Dependency**: T015e-RECRUIT. **Rationale**: Ensures data producer step is complete before T015c.
- [X] T015a [P] [US1] **TEST HARNESS ONLY**: Implement Unit Test Harness for Human Coding in `code/human_coding.py`. **Logic**: Programmatically generate mock annotation data for ≥3 independent annotators to simulate human coding for unit testing. **Output**: `data/raw/human_coding/mock_annotations.csv`. **Constraint**: **DO NOT USE FOR EMPIRICAL CLAIMS**. This data is strictly for testing logic and must be written to `data/raw/human_coding/` to match T015e-WAIT polling. **Rationale**: Supports testing without violating real data requirements.
- [X] T015a1 [US1] Verify Mock Data Isolation. **Logic**: Assert `data/raw/human_coding/mock_annotations.csv` exists and is NOT in `data/processed/`. **Rationale**: Ensures mock data cannot leak into empirical analysis.
- [X] T015b [P] [US1] **SIMULATION ONLY**: Implement Unit Test for Human Coding Logic in `tests/unit/test_human_coding.py`. **Logic**: Verify that the `calculate_cohens_kappa` function works correctly on the mock data generated in T015a. **Constraint**: Do not use this data for empirical claims. **Rationale**: Validates the logic of the human coding pipeline.
- [X] T015c [US1] **MANDATORY FOR FR-008**: Execute Real Human Coding Protocol in `code/human_coding.py`. **Logic**: Read raw annotator data from `data/raw/human_coding/` (CSV/JSON files) collected from ≥3 independent human annotators. Calculate Cohen's κ for each scenario. Filter scenarios with mean ambiguity ≥ 3.5 AND κ ≥ 0.6. **Output**: `data/processed/valid_scenarios.csv`. **Constraint**: This is the ONLY task that fulfills the FR-008 requirement for real human coding. T015a/b are for testing only. **Dependency**: T015d and T015e-WAIT must complete first. **Rationale**: Implements the core FR-008 requirement to process real human coding data.
- [X] T016a [P] [US1] Generate Versioned Manipulation Config in `code/manipulation_config.py`. **Logic**: Write `config/manipulation.yaml` with fields: `version` (e.g., "1.0.0"), `seed` (42), `luminance_levels` (low, medium, high), `target_region` (bounding box logic), `output_path` (e., `data/processed/stimuli_manipulated.csv`). **Constraint**: Must be run before T016. **Constitution Principle VI Compliance**: This task ensures explicit, versioned parameters for stimulus generation. **Rationale**: Ensures explicit, versioned parameters for stimulus generation per Constitution Principle VI.
- [X] T016 [US1] Implement salience manipulation function (low/med/high luminance) in `code/data_prep.py` ensuring no semantic change. **Logic**: Read parameters from `config/manipulation.yaml` generated in T016a. Apply luminance changes to target regions. **Output**: `data/processed/stimuli_manipulated.csv` linking `scenario_id` to `variant_id` AND a directory `data/processed/images/` containing the manipulated images. **Dependency**: Depends on T016a completion. **Note**: This task can run in parallel with T015c if mock data (from T015a) is available, as the dependency is on data availability, not the specific real-data execution path. **Constitution Principle VI Compliance**: Uses versioned config to ensure reproducibility.
- [X] T017 [US1] Implement semantic preservation verification in `code/validation.py`. **MUST** use CLIP (default precision, CPU) to compute embeddings. **Logic**: (1) Crop target region using bounding box; compute CLIP embedding for ROI in original vs ROI in manipulated; verify cosine similarity ≥ 0.95. (2) Crop background region (non-ROI); compute CLIP embedding for background in original vs manipulated; verify cosine similarity ≥ 0.99 (to ensure background is unchanged). (3) Compute texture and edge density changes (Laplacian variance) in ROI using `cv2.Laplacian`; verify change < 0.05 (Stimulus-Control Integrity). **Constraint**: MUST run on CPU only. If memory error occurs, raise `MemoryError` and halt. **DO NOT** compare full images.
- [X] T017-CPU-OPT [US1] Implement CPU-optimized CLIP inference. **Logic**: Use `torch.no_grad()` and batch processing to ensure CLIP inference stays within 2GB RAM on CPU. **Rationale**: Replaces GPU offload tasks with CPU-optimized alternatives to adhere to CPU-only constraint.
- [X] T018 [US1] Implement failure logging and exclusion logic for unmanipulatable images in `code/data_prep.py`
- [X] T019-INT [US1] **INTERFACE**: Implement Pilot Human Manipulation Check Interface in `code/manipulation_check.py`. **Logic**: Generate the interface to present manipulated images to a separate coder panel. Output results to `data/processed/narrative_check.csv`. **Constraint**: This task generates the interface; real data must be collected separately. **Rationale**: Provides the interface for the manipulation check.
- [X] T019b-RECRUIT [US1] **RECRUIT**: Generate recruitment survey for manipulation check coder panel. **Logic**: (1) Generate `code/generate_manipulation_check_survey.py` for local polling or external API config. (2) Implement `code/poll_manipulation_check_responses.py` to check for new responses. **Rationale**: Provides the concrete mechanism for collecting manipulation check data.
- [X] T019b-WAIT [US1] **WAIT**: Block until manipulation check responses collected. **Logic**: Poll `data/raw/manipulation_check/` until >=3 valid response files exist. **Constraint**: This task MUST NOT complete until the data exists. **Dependency**: T019b-RECRUIT. **Rationale**: Ensures data producer step is complete before T019-EXEC.
- [X] T019-EXEC [US1] **MANDATORY FOR FR-001**: Enforce Pilot Human Manipulation Check Threshold. **Logic**: (1) Read raw coder data from `data/raw/manipulation_check/` (CSV/JSON). (2) Calculate agreement as (number of coders agreeing on narrative preservation) / (total coders). (3) If agreement < 0.80, flag scenario as failed and exclude from final manifest. (4) Update `data/processed/narrative_check_validated.csv` with exclusion flags. **Constraint**: This task MUST complete before T019a. **Rationale**: Enforces the ≥80% threshold required by FR-001 and US-001.
- [X] T019a [US1] Generate Stimulus Manifest: Create `data/processed/stimulus_manifest.json` linking `scenario_id`, `variant_id`, and `salience_level` for all generated stimuli. **Logic**: This file is required by the survey engine (T023) to map stimuli to survey items. **Constraint**: MUST include `source_type` field ('real' or 'synthetic') to enable T069. **Dependency**: Depends on T016/T017/T019-EXEC completion.
- [X] T016b [US1] Generate Stimulus Contract Schema. **Logic**: Create `contracts/stimulus.schema.yaml` defining the structure of `stimulus_manifest.json` and manipulated image metadata. **Rationale**: Fulfills Plan.md Constitution Check requirement for Principle VI enforcement.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Survey Deployment and Data Collection (Priority: P2)

**Goal**: Present manipulated images in a randomized within-subject design and collect blame ratings.

**Independent Test**: Pilot survey with small cohort; verify randomization, within-subject constraints, and correct data logging.

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement survey randomization engine (within-subject design) in `code/survey_sim.py` to generate sequences where no scenario appears twice with the same salience level for a participant.
- [X] T023a [P] [US2] **PILOT/SIMULATION ONLY**: Implement Survey Simulation Interface in `code/survey_deploy.py`. **Logic**: Generate `data/synth/survey_sequences.json` for simulated participants. **Constraint**: **DO NOT USE FOR EMPIRICAL CLAIMS**. Output MUST be written to `data/synth/` directory. **Rationale**: For pilot testing logic only; does not fulfill FR-002 for real data collection.
- [X] T023a1 [US2] Verify Simulation Data Isolation. **Logic**: Assert `data/synth/survey_sequences.json` exists and is NOT in `data/survey/`. **Rationale**: Ensures simulated data cannot leak into real deployment.
- [X] T023c [US2] **MANDATORY FOR FR-002**: Generate Production Survey Configuration & Deployment Script. **Logic**: (1) Generate `config/survey_api.yaml` with placeholders for Prolific/Qualtrics API keys. (2) Generate `code/survey_deploy_production.py` which renders the survey interface, enforces within-subject constraints, and logs responses to `data/survey/real_responses.csv`. **Output**: `config/survey_api.yaml` and `code/survey_deploy_production.py`. **Rationale**: Provides the executable artifact required for real data collection.
- [X] T023b [US2] **MANDATORY FOR FR-002**: Implement Real Survey Deployment Interface in `code/survey_deploy.py`. **Logic**: Integrate `code/survey_deploy_production.py` with the Streamlit app. **Dependency**: Requires T023c completion. **Rationale**: This is the primary task for collecting real data as required by FR-002.
- [X] T024 [US2] Implement data collection handler to log responses to `data/survey/pilot_responses_real.csv` (Real Data) or `data/synth/pilot_responses_synth.csv` (Synthetic).
- [X] T024c-IMPL [US2] **IMPLEMENT**: Create `scripts/generate_prolific_link.py`. **Logic**: Implement the script that generates a deterministic recruitment link for the survey platform. **Rationale**: Provides the script required by T024c.
- [X] T024c [US2] **CONFIGURE**: Generate survey platform links. **Logic**: Run `scripts/generate_prolific_link.py` (from T024c-IMPL) to create a deterministic recruitment link. **Rationale**: Provides concrete mechanism for link generation.
- [X] T024c-VERIFY [US2] **VERIFY**: Test survey link with within-subject constraints. **Logic**: Execute a mock survey session using the generated link to verify that the within-subject constraints are enforced and the link is functional. **Dependency**: Requires T024c completion. **Rationale**: Ensures the deployed link enforces the constraints before real deployment.
- [X] T024b [US2] **MANDATORY FOR FR-002**: Execute Real Survey Deployment in `code/survey_deploy_production.py`. **Logic**: Run the production script with `--mock-mode` for local verification (generates `data/survey/mock_responses.csv`) or real mode for deployment. **Output**: `data/survey/mock_responses.csv` (if mock) or `data/survey/real_responses.csv`. **Dependency**: Requires T023c and T024c completion. **Rationale**: This is the execution step that fulfills the core data collection requirement.
- [X] T026 [US2] Implement pilot data simulation script (`code/survey_sim.py`) to generate synthetic data for pipeline validation (strictly for testing logic, not empirical claims). **Constraint**: Output MUST be written to `data/synth/` directory to prevent conflation with real data. **Logic**: Synthetic data MUST NOT be used for any empirical claims.
- [X] T026a [US2] **PILOT/SIMULATION ONLY**: Implement Simulated Pilot Data Collection: Deploy survey to a simulated cohort (n>=20) and collect simulated blame ratings. **Output**: `data/survey/pilot_responses_sim.csv`. **Constraint**: Must be distinct from synthetic validation data. **Dependency**: Requires T023 completion. **Rationale**: For pilot testing only; real data collection is handled by T024b.
- [X] T026b [US2] Enforce Data Separation: Ensure `data/survey/` contains only real/simulated data and `data/synth/` contains only synthetic data. Verify via directory structure and file naming conventions. **Logic**: If files are misplaced, raise `DataHygieneError`.
- [X] T023e [US2] Generate Response Contract Schema. **Logic**: Create `contracts/response.schema.yaml` defining the structure of survey responses. **Rationale**: Fulfills Plan.md Constitution Check requirement for Principle VII enforcement.

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

- [X] T036 [US3] Implement pipeline validation script (Positive Control/Negative Control) in `code/validation.py`. **Logic**: Run synthetic data injection to verify CLMM logic BEFORE processing real data. **Dependency**: MUST run before T030-EXEC/T031-EXEC.
- [X] T045 [US3] Execute Data Cleaning: Run the straight-lining detection routine on `data/survey/pilot_responses_sim.csv` (or real data) to exclude participants with identical ratings across all items; output cleaned dataset `data/processed/cleaned_responses.csv`. **Logic**: Exclude if variance < 0.1 OR >90% identical ratings. **Dependency**: MUST run before T030-EXEC/T031-EXEC.
- [X] T045-SYNTH [US3] **SYNTHETIC**: Generate synthetic cleaned data for independent testing. **Logic**: Run T045 on synthetic data to produce `data/processed/cleaned_responses_synth.csv`. **Dependency**: T026a must complete. **Rationale**: Enables independent testing of US3 without real data.
- [X] T045b [US3] **SET FLAG**: Set `is_real_data` flag in cleaned responses. **Logic**: During data cleaning (T045), explicitly set the `is_real_data` flag in `data/processed/cleaned_responses.csv` based on the source path (True for real, False for synthetic). **Rationale**: Provides the metadata field required by T068.
- [X] T032a [US3] Implement CLMM Convergence Check and Fallback Logic in `code/analysis.py`. **Logic**: Define function `def check_convergence_and_fallback(model) -> tuple[Model, str]:`. If `model.converged` is False, switch to 'LMM with Cluster-Robust Standard Errors' OR 'Non-parametric Bootstrap CLMM' (per FR-004). **Constraint**: DO NOT use Wilcoxon as the *only* fallback; it must be an option alongside LMM/Bootstrap. If fallback fails, raise `ConvergenceError`. **Priority**: 1. LMM with Robust SE, 2. Bootstrap CLMM. **Note**: This task implements the *orchestration* logic (detect and switch). **Rationale**: Ensures fallback methods preserve the nested data structure required by FR-004 and align with FR-005.
- [X] T032b [US3] Implement Fallback Model Selection Logic in `code/analysis.py`. **Logic**: Define specific functions for 'LMM with Cluster-Robust SE' and 'Non-parametric Bootstrap CLMM'. **Constraint**: Must preserve random intercepts for Participant and Scenario where applicable. **Dependency**: Must be implemented before T030-EXEC/T031-EXEC.
- [X] T030-IMPL [US3] Implement Primary Analysis: Implement the Cumulative Link Mixed Model (`Rating ~ Salience + (1|Participant) + (1|Scenario)`) in `code/analysis.py` using the `ordinal` package (per FR-004). **MUST** include random intercepts for Participant and Scenario. This is the PRIMARY analysis method for ordinal data. **Output**: `data/analysis/clmm_results.csv`. **Dependency**: Calls the logic implemented in T032a/T032b. **Pre-Run Check**: Verify T032a/T032b functions are importable. **Note**: T032a/T032b must be COMPLETED (code written) before T030-IMPL is executed.
- [X] T031-IMPL [US3] Implement Secondary Validation: Implement Robustness Checks for CLMM in `code/analysis.py`. **Logic**: If CLMM converges, run bootstrap resampling to verify stability of coefficients. If CLMM fails, run the robust alternative identified in T032a (LMM/Bootstrap). **DO NOT** implement ANOVA as it assumes continuous data. **Dependency**: T032a/T032b must be COMPLETED (code written) before T031-IMPL is executed.
- [X] T030-EXEC [US3] Execute Primary Analysis. **Logic**: Execute the `run_clmm_analysis()` function from `code/analysis.py` on cleaned data (either real from T045 or synthetic from T045-SYNTH). **Dependency**: T032a/T032b IMPL must be done. T045 (or T045-SYNTH) must be done. **Note**: This task can run on synthetic data to enable independent testing of US3.
- [X] T031-EXEC [US3] Execute Secondary Validation. **Logic**: Execute the `run_robustness_checks()` function from `code/analysis.py` on cleaned data (either real from T045 or synthetic from T045-SYNTH). **Dependency**: T032a/T032b IMPL must be done. T045 (or T045-SYNTH) must be done. **Note**: This task can run on synthetic data to enable independent testing of US3.
- [X] T031b [US3] Execute Fallback Logic in `code/analysis.py`. **Logic**: Explicitly call `check_convergence_and_fallback` from T030-EXEC. If `ConvergenceError` is raised, execute the fallback model defined in T032b. **Output**: Update `data/analysis/results.csv` with fallback model results. **Dependency**: Depends on T030-EXEC completion.
- [X] T034 [US3] Implement Ordinal Post-Hoc Pairwise Comparisons in `code/analysis.py`. **Logic**: Perform Tukey-adjusted (or Bonferroni) pairwise comparisons for ordinal regression (Low vs Medium, Medium vs High, Low vs High). **Constraint**: If using the fallback path (LMM/Bootstrap), MUST use **Bonferroni correction** only. If using CLMM primary, Tukey is allowed.
- [X] T035 [US3] Implement effect size (odds ratio) and % CI calculation in `code/analysis.py` using Type III Sums of Squares or equivalent for CLMM.
- [X] T046 [US3] Implement Precision Threshold Check: Load `MIN_PRECISION` from `config/pre_registration.yaml` (created in T001c). Calculate the 95% CI width for the `salience` coefficient: `ci_width = abs(conf_int_upper - conf_int_lower)`. Compare against `MIN_PRECISION`. **Constraint**: If `MIN_PRECISION` is missing, deferred, or `verification_status` is `UNVERIFIED`, raise `PreRegistrationError`. **Output**: Update `data/analysis/results.json` with keys `ci_width`, `precision_adequate`, `ci_level`, `verification_status`. **Rationale**: Makes SC-005 testable by default and enforces the pre-registered constraint.
- [X] T047 [US3] Implement Post-Hoc Power Analysis in `code/power_analysis.py`. **Logic**: Use observed effect size to calculate power. If calculated power < 0.80, write a warning to the report and set `power_adequate=false` in `data/analysis/power_results.json`.
- [X] T047-RECOVERY [US3] **RECOVERY**: Generate sample size adjustment plan if power < 0.80. **Logic**: If `power_adequate=false`, generate `data/analysis/adjustment_plan.md` with recommended N increase or re-run script. **Rationale**: Provides a resolution path for low power state.
- [X] T047b [US3] Integrate Power Analysis into Report in `code/analysis.py`. **Logic**: Read `data/analysis/power_results.json` and merge `power_adequate` and `power_value` into `data/analysis/results.json`. **Output**: Updated `data/analysis/results.json`. **Dependency**: Depends on T047 completion.
- [X] T047c [US3] **MANDATORY REPORTING**: Integrate Power Analysis into Final Report Generator. **Logic**: Update `code/analysis.py` (T037) to explicitly read `data/analysis/results.json` and include `power_adequate` and `power_value` in the console summary and final report output. **Constraint**: The report MUST state if power < 0.80 and note wider confidence intervals. **Rationale**: Ensures the spec's acceptance scenario for reporting reduced power is met.
- [X] T070 [US3] **POWER GATE**: Enforce Power Adequacy and Report Reduced Power. **Logic**: (1) After T047 executes, check `power_adequate`. (2) If False, check if `data/analysis/adjustment_plan.md` exists. (3) If the plan is missing, generate a default plan in `data/analysis/adjustment_plan.md` (do not halt). (4) Ensure the final report (T037) explicitly flags the reduced power and wider CIs. **Constraint**: This task MUST run before T037. **Dependency**: T047. **Note**: T047-RECOVERY is not a hard dependency; T070 generates a default plan if T047-RECOVERY fails or is not run. **Rationale**: Ensures the project does not proceed to reporting (T037) with an underpowered study without a documented recovery strategy, addressing the "Sample Size Edge Case" requirement, and adheres to the spec's Edge Cases by reporting reduced power rather than halting.
- [X] T037 [US3] Implement report generator to output `data/analysis/results.json` and console summary, explicitly documenting the CLMM primary analysis and ordinal post-hoc results. **Logic**: Read `data/analysis/results.json` (which includes power data from T047b/T047c/T070) and generate report. **Constraint**: Must include `power_adequate`, `ci_width`, and `verification_status` in output. **Dependency**: T047c and T070 must complete first.

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
- [X] T051a [P] Implement profiling script `code/profile_pipeline.py`. **Logic**: Measure runtime of each major stage (ingest, manipulate, survey, analysis).
- [X] T051b [P] Run profiler and log results. **Logic**: Execute `code/profile_pipeline.py` on full dataset. Output: `data/analysis/runtime_log.txt`.
- [X] T051c [P] Refactor code to ensure <6h runtime if needed. **Logic**: If `runtime_log.txt` shows >6h, refactor `code/analysis.py` or `code/data_prep.py` and re-run T051b until <6h is achieved.
- [X] T040a [US3] Implement Sample Size Edge Case Logic. **Logic**: In `code/analysis.py`, detect if `n_participants` < planned threshold. If so, flag `power_adequate=false` and generate a warning message about reduced power and wider CIs. **Rationale**: Implements the specific logic required by Edge Cases section.
- [X] T040b [US3] Unit Test for Sample Size Edge Case. **Logic**: Verify that the detection logic correctly flags underpowered samples and generates the warning. **Rationale**: Ensures the edge case is testable.
- [X] T041a [P] Generate `quickstart.md`. **Logic**: Create a comprehensive guide covering installation, data setup, and pipeline execution.
- [X] T041b [P] Validate `quickstart.md`. **Logic**: Run a validation script that checks `quickstart.md` against the implementation plan and task list. Output: `data/logs/quickstart_validation.txt`.

---

## Phase 7: Review Resolution & Constitution Hardening (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data integrity, reproducibility, and constitutional compliance.

**Independent Test**: Verify that all "Fail Loudly" mechanisms trigger correctly on simulated network failure, and that no synthetic data is used in the primary analysis pipeline unless explicitly configured.

### Implementation for Review Resolution

- [X] T065 [US1] Add a task to document the "Verified Source" injection mechanism in `docs/data_hygiene.md`. **Logic**: Explain how the `VERIFIED_DATA_SOURCE` environment variable overrides default URLs and why this is critical for reproducibility. **Rationale**: Provides transparency for the execution-stage verified source adoption.
- [X] T068 [US1] **REVISION**: Implement explicit "Real Data Only" gate in `code/analysis.py` to prevent any execution if the input dataset is flagged as synthetic or mock. **Logic**: (1) Add a metadata flag `is_real_data` to `data/processed/cleaned_responses.csv` derived from the source path (produced by T045b). (2) In `code/analysis.py`, check this flag before running T030-EXEC. (3) If `is_real_data` is False and `--allow-synthetic` is not passed, raise `DataIntegrityError` and halt. **Rationale**: Enforces the constitution's "Real data + real results only" rule at the execution gate, preventing accidental analysis of pilot/simulation data.
- [X] T069 [US2] **REVISION**: Add explicit "Real Data Only" gate in `code/survey_deploy.py` to prevent deployment of survey logic if stimuli are from the synthetic pipeline. **Logic**: (1) Check `data/processed/stimulus_manifest.json` for a `source_type` field (produced by T019a). (2) If `source_type` is 'synthetic' and `--allow-synthetic` is not passed, raise `DataIntegrityError`. **Rationale**: Ensures the survey engine (US2) cannot be deployed with fake stimuli, preventing circular validation with synthetic data.
- [X] T071 [US1] **REVISION**: Add a "Human Coding Completeness" check in `code/human_coding.py` to ensure T015c cannot run with fewer than 3 unique annotators. **Logic**: (1) Before calculating Cohen's κ, verify that `data/raw/human_coding/` contains at least 3 distinct files from different annotators. (2) If count < 3, raise `InsufficientAnnotatorsError`. **Rationale**: Enforces the FR-008 requirement for ≥3 independent annotators at the code level, preventing accidental execution with insufficient data.
- [X] T072 [US3] **REVISION**: Implement "Model Convergence" logging in `code/analysis.py` to explicitly record convergence status and fallback reason in `data/analysis/results.json`. **Logic**: (1) Add `convergence_status` and `fallback_reason` fields to the results JSON. (2) Log these values regardless of whether the primary or fallback model was used. **Rationale**: Ensures transparency and reproducibility of the statistical analysis, addressing the "Constitutional Hardening" requirement for traceability.

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
3. **T045-SYNTH** (Synthetic Cleaning) - **Execution**: MUST run on synthetic data if testing US3 independently.
4. **T045b** (Set Flag) - **Execution**: MUST run during data cleaning to set `is_real_data`.
5. **T032a** (Convergence Logic Implementation) - **Implementation**: MUST be implemented (static code) before T030-EXEC/T031-EXEC. This task defines the *function* that checks convergence and switches; it does not run the check itself.
6. **T032b** (Fallback Model Selection Logic) - **Implementation**: MUST be implemented (static code) before T030-EXEC/T031-EXEC. This task defines the *function* that selects the fallback model; it does not run the selection itself.
7. **T030-IMPL** (Primary CLMM Code) - **Implementation**: MUST be implemented (static code) before T030-EXEC.
8. **T031-IMPL** (Secondary Validation Code) - **Implementation**: MUST be implemented (static code) before T031-EXEC.
9. **T030-EXEC** (Primary CLMM Run) - **Execution**: MUST run on cleaned data (real or synthetic), calling the logic implemented in T032a/T032b to determine if it converges. **Dependency**: T032a/T032b must be COMPLETED. **Pre-Run Check**: Verify T032a/T032b functions are importable.
10. **T031b** (Execute Fallback Logic) - **Execution**: MUST run on cleaned data, explicitly calling the fallback if T030-EXEC fails.
11. **T031-EXEC** (Secondary Robustness) - **Execution**: MUST run on cleaned data, calling the logic implemented in T032a/T032b to execute the fallback if needed. **Dependency**: T032a/T032b must be COMPLETED.
12. **T034** (Ordinal Post-Hoc) - **Execution**: Depends on T030-EXEC/T031-EXEC results.
13. **T035** (Effect Sizes) - **Execution**: Depends on T030-EXEC/T031-EXEC results.
14. **T046** (Precision Check) - **Execution**: Depends on T035.
15. **T047** (Power Analysis) - **Execution**: Depends on T035.
16. **T047-RECOVERY** (Recovery Plan) - **Execution**: Depends on T047.
17. **T047b** (Integrate Power) - **Execution**: Depends on T047.
18. **T047c** (Report Integration) - **Execution**: Depends on T047b.
19. **T070** (Power Gate) - **Execution**: MUST run after T047 and before T037. Checks power adequacy and ensures a plan exists (generating one if necessary).
20. **T037** (Report Generation) - **Execution**: Depends on T047c and T070. **Note**: T037 must be executed AFTER T070 to include power analysis results and ensure the power gate has passed.

**Note**: T030-EXEC/T031-EXEC DEPEND ON T045 (or T045-SYNTH) and the *implementation* of T032a/T032b. T030-EXEC/T031-EXEC DEPEND ON T036 completion. T032a/T032b are *implementation* tasks that must be completed (code written) before T030-EXEC/T031-EXEC can be *executed*.

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
- **SC-005 Compliance**: Precision thresholds are configurable, default a small positive value (but must be pre-registered). **Strict Enforcement**: If `MIN_PRECISION` is missing or `UNVERIFIED`, the system raises `PreRegistrationError` and halts.
- **Data Separation**: Real data in `data/survey/`, synthetic data in `data/synth/`. No mixing.
- **Revision Pass**: Phase 7 tasks address specific reviewer concerns regarding data integrity, reproducibility, and constitutional compliance.
- **FR-002/FR-008 Compliance**: T015c and T024b are the mandatory tasks for real data collection; T015a/b and T023a/T026a are for testing/simulation only.
- **Constitution Principle VI Compliance**: T016a ensures versioned parameters for stimulus generation.
- **Nested Data Structure**: T032a/T032b ensure fallback models preserve random intercepts for Participant and Scenario.
- **Execution Order Note**: T032a/T032b must be implemented (code written) before T030-EXEC/T031-EXEC are executed. T037 must be executed after T047c and T070.
- **CPU-Only Constraint**: The project strictly adheres to CPU-only infrastructure. No GPU offload or streaming fallback paths are implemented by default. T017-CPU-OPT ensures CPU efficiency.
- **T015c1**: Added to generate mock human coding data for CI testing.
- **T046**: Updated to strictly enforce pre-registration (raise error if missing/unverified).
- **T066/T067**: Removed to adhere to CPU-only constraint. Replaced with T017-CPU-OPT.
- **T032a/T032b**: Updated to exclude Wilcoxon and use GEE/Bootstrap for nested data.
- **T052-VERIFY-AND-FIX**: Added to ensure T052 is correct before consumption.
- **T047-RECOVERY**: Added to handle low power state with an adjustment plan.
- **T001b-RETRY**: Renamed to T001b-INIT.
- **T053-GEN/T053-EXEC**: Split to resolve circular dependency. Added T053-RAW-CHECKSUM to ensure source integrity before ID generation.
- **T015e-RECRUIT/T015e-WAIT**: Split to ensure data collection mechanism is active and data exists.
- **T030-IMPL/T030-EXEC**: Split to clarify code writing vs execution.
- **T016a**: Removed [P] tag to prevent parallel execution with T016.
- **T068-T072**: Added in Revision Pass to address specific reviewer concerns regarding data integrity gates, power adequacy enforcement, and model convergence logging.
- **T013b**: Added to fetch external validation source.
- **T014-FILTER/T014-CROSSREF-EXEC**: Split to separate metadata filtering from cross-reference verification.
- **T001c**: Added to generate pre-registration config.
- **T024c-IMPL**: Added to implement survey link script.
- **T024c-VERIFY**: Added to verify survey link.
- **T045-SYNTH**: Added to enable independent testing of US3.
- **T045b**: Added to set `is_real_data` flag.
- **T070**: Moved to Phase 5 and updated to report reduced power rather than halt.
- **T019b-RECRUIT/T019b-WAIT**: Added to produce manipulation check data.
- **T019-EXEC**: Added to enforce manipulation check threshold.
- **T019a**: Updated to include `source_type` field.
- **T015a**: Updated output path to match T015e-WAIT.
- **T016**: Updated to clarify parallel execution with mock data.
- **T030-EXEC/T031-EXEC**: Updated to clarify support for synthetic data paths.
- **T015a/T015b**: Updated to clarify artifact isolation.
- **T013-SOURCE-VERIFY**: Added to ensure the checksummed source matches the selected source.