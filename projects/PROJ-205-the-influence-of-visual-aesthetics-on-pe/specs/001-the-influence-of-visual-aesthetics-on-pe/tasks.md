---
description: "Task list template for feature implementation"
---

# Tasks: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

**Input**: Design documents from `/specs/001-visual-aesthetics-credibility/`
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

## Phase 1: Setup & Research (Shared Infrastructure)

**Purpose**: Project initialization, research validation, and basic structure

- [X] T000 [P] **Research & Validation**. **Action**: Create `research.md` with citations for visual aesthetics and credibility. Implement `code/utils/reference_validator.py` to verify all citations in `research.md` against primary sources (Title overlap >= 0.7). **Requirement**: This task MUST pass the "Verified Accuracy" gate before proceeding to Phase 2. **Output**: Validated `research.md` and passing validation report.
- [X] T001 Create project structure per `projects/PROJ-205-.../` in `plan.md`. Execute: `mkdir -p code/stimuli code/survey code/analysis code/utils data/raw data/processed tests/unit tests/integration tests/contract state/projects`
- [X] T002 Initialize Python project with `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pyyaml, **pingouin**). **Note**: `pingouin` is required for effect size calculations in US2.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting tools. Create `.ruff.toml` with rules E, W, F, I, N, D, UP, C90, B, C4, PT, RUF, SIM, TCH, TID, ARG, TCH, TID, ARG. Create `pyproject.toml` with `[tool.black]` and `[tool.isort]` sections.
- [X] T063 [P] **Implement Reproducibility Seed Enforcement**. **Action**: Add a global seed setting function in `code/utils/helpers.py` that sets `numpy.random.seed`, `random.seed` at the very start of `code/analysis/00_preprocess.py`, `code/analysis/01_anova.py`, `code/analysis/02_pairwise.py`, and `code/analysis/03_mixed_effects.py`. **Requirement**: The seed value must be read from an environment variable `RANDOM_SEED` (default to 42). **Verification**: Add a unit test in `tests/unit/test_seeds.py` that runs a small analysis pipeline twice with the same seed and asserts the output checksums are identical. **Note**: Removed `torch.manual_seed` to align with CPU-only stack.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/stimuli/text_content.txt` with the fixed neutral text source. **Content**: "The rapid evolution of digital communication has fundamentally altered how individuals perceive and process information. In an era where attention spans are shrinking, the visual presentation of online content plays a critical role in establishing initial trust and credibility. This study examines the psychological mechanisms underlying these perceptions. "
- [X] T005 [P] Create `code/stimuli/professional.html`. **Design**: High-fidelity CSS, serif fonts (Georgia/Times New Roman), balanced layout, professional color palette (navy #003366, white #FFFFFF, gray #F0F0F0), clean typography, no clutter. **CSS Rules**: `body { font-family: Georgia, serif; background: #FFFFFF; color: #333333; } h1 { color: #003366; }.container { max-width: 800px; margin: 0 auto; padding: 20px; }`.
- [X] T006 [P] Create `code/stimuli/minimalist.html`. **Design**: Low-fidelity CSS, sans-serif fonts (Arial/Helvetica), sparse layout, high contrast black (#000000) / white (#FFFFFF), minimal decoration, simple structure, no images. **CSS Rules**: `body { font-family: Arial, sans-serif; background: #FFFFFF; color: #000000; } h1 { font-weight: normal; }.container { max-width: 600px; margin: auto; }`.
- [X] T007 [P] Create `code/stimuli/low_quality.html`. **Design**: Broken CSS, mismatched fonts (Comic Sans MS / Times New Roman mix), cluttered layout, jarring colors (neon green, red), broken alignment, visual noise, overlapping elements. **CSS Rules**: `body { font-family: 'Comic Sans MS', 'Times New Roman', serif; background: #000000; color: #39FF14; } h1 { color: #FF0000; font-size: large; }.container { margin: -20px; }`.
- [X] T008 [P] Create `code/stimuli/neutral.html`. **Design**: Standard default browser styling, plain text, no custom CSS, minimal formatting, Times New Roman, black text on white background. **CSS Rules**: No custom CSS file; relies on browser defaults.
- [X] T009 Setup `data/raw/` and `data/processed/` directory structure. Execute: `touch data/raw/.gitkeep data/processed/.gitkeep`
- [X] T010 [P] Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function). **Requirement**: The IP hashing MUST use **PBKDF2** with **SHA-256** and a **minimum of 100,000 iterations** to satisfy the "IP hashing mandatory" security constraint. The salt for `hash_ip` MUST be loaded from the environment variable `IP_HASH_SALT`. The task must also create a `.env.example` file in the root with `IP_HASH_SALT=your_secure_salt_here` and a comment instructing the user to set this variable. The code must fail loudly if `IP_HASH_SALT` is not set.
- [X] T011e_new [P] **IRB File Requirement**. **Action**: Ensure `data/consent/irb_approved.txt` exists prior to execution. This file must be provided by the researcher and contains the approved IRB text. The code in T012 will read this file. **Note**: This is a prerequisite check, not a manual insertion task. **Implementation**: Create a script or validation step that checks for the file's existence and raises an error if missing, ensuring T012 has a concrete producer.
- [X] T011g [P] **IRB Protocol Registry Setup**. **Action**: Create `data/consent/protocol_registry.json` as a researcher-maintained list of approved IRB Protocol IDs. **Content**: A JSON list of valid protocol IDs (e.g., `["IRB-2024-001", "IRB-2024-002"]`). **Requirement**: This file serves as the source of truth for valid protocols. **Verification**: Unit test asserts the file exists and is valid JSON.
- [X] T011f [P] **IRB Content Validation**. **Action**: Create `code/utils/irb_validator.py`. **Logic**: 
  1. Read `data/consent/irb_approved.txt`.
  2. Extract the `IRB_PROTOCOL_ID` string from the content.
  3. **Validate**: Check if the extracted ID exists in `data/consent/protocol_registry.json`.
  4. **Requirement**: If the ID is missing or not in the registry, raise a fatal error. This ensures the file contains valid approved protocol text, not just an empty file or a placeholder ID.
  5. **Verification**: Unit test in `tests/unit/test_irb_validator.py` asserts that valid content (ID in registry) passes and invalid content (ID missing or not in registry) fails.
- [X] T057 [P] **Implement Data Integrity Checksums**. **Action**: Create `code/utils/checksums.py`. **Logic**: Compute a cryptographic checksum of the `data/raw/submissions.csv` file. **Trigger**: Execute `code/utils/checksums.py` immediately after any write operation in `code/survey/app.py` that appends to `data/raw/submissions.csv`. **Verification**: Add a check in `code/analysis/00_preprocess.py` to verify the checksum of the input file before processing. If the checksum mismatches, raise a fatal error.
- [X] T070 [US0/1] **Implement Stimulus Content Hashing**. **Action**: Create `code/utils/stimuli_hash.py`. **Logic**: Compute SHA-256 hashes for all HTML files in `code/stimuli/` upon project initialization or before survey launch. Store hashes in `state/stimuli_hashes.json`. **Requirement**: This is a **mandatory** blocking task for data collection. If hashes change, the survey MUST halt. **Verification**: Add a unit test in `tests/unit/test_stimuli_integrity.py` that asserts if a stimulus file is modified, the hash changes and a warning is raised during the next survey run. **Rationale**: Ensures stimulus consistency and prevents silent drift in experimental conditions, addressing Constitution Principle VII (Stimulus Standardization).
- [X] T073 [P] **Add Comprehensive Error Logging**. **Action**: Configure Python `logging` module in `code/utils/helpers.py` to write all errors, warnings, and critical events to `logs/survey_error.log`. **Logic**: Ensure log rotation is enabled with a maximum file size limit and a defined number of backup files. **Verification**: Unit test asserts that a simulated error is correctly captured in the log file. **Rationale**: Facilitates debugging and operational monitoring without exposing sensitive data in console outputs.
- [X] T072 [P] **Implement Automated Data Backup**. **Action**: Create `code/utils/backup.py`. **Logic**: Triggered after every successful write to `data/raw/submissions.csv`, copy the file to `data/backups/` with a timestamped filename (e.g., `submissions_20240115_120000.csv`). **Verification**: Unit test asserts backup file creation and content match. **Rationale**: Provides an immutable audit trail and protects against accidental data loss, reinforcing Constitution Principle III.
- [X] T024a [US2] **Create Preprocess Script**. **Action**: Create `code/analysis/00_preprocess.py`. **Dependency**: This script must call the checksum verification logic from T057 before processing `data/raw/submissions.csv`. **Logic**: 
  1. Load `data/raw/submissions.csv`.
  2. Verify checksum against `data/raw/.checksums.json`.
  3. **Transform**: Cast `age` to integer, `education` to string, `ratings` to float. Drop rows with missing `participant_id` or `stimulus_id`. Rename columns to snake_case if needed.
  4. Output: `data/processed/clean_data.csv`.
  5. **Verification**: Unit test in `tests/unit/test_preprocess.py` asserts that valid input produces clean output and invalid checksums raise `FileChecksumError`.
- [X] T024b [P] **Implement Dependency Order Verification**. **Action**: Create `code/analysis/00_verify_dependencies.py`. **Logic**: Before running `01_anova.py`, this script must verify that `00_preprocess.py` has successfully generated `data/processed/clean_data.csv` and that the file checksum matches the one recorded in `data/raw/submissions.csv`. **Requirement**: If dependencies are missing or stale, the script must raise an error and prevent the ANOVA from running. **Note**: Moved from Phase 8 to Phase 2 to resolve logical paradox. This task acts as a gate for Phase 5 (Analysis) execution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 & 1 - Informed Consent & Data Collection (Priority: P0/P1) 🛡️🎯

**Goal**: Present IRB-approved Informed Consent, block access until accepted, and collect data with session integrity.

**Independent Test**: Simulate a new user session; verify consent form appears, survey is blocked, and a consent record is logged upon "I Agree". Simulate session timeout; verify abandonment is logged.

### Implementation for User Story 0 & 1

- [X] T012 [US0] Implement consent modal in `code/survey/app.py` displaying IRB text from `data/consent/irb_approved.txt` and including the `IRB_PROTOCOL_ID` in the header. **Note**: The ID must be explicitly rendered in the modal title or header text. The file `data/consent/irb_approved.txt` must exist before running.
- [X] T013 [US0] Implement "I Agree" / "I Do Not Agree" logic in `code/survey/app.py`
- [X] T014 [US0] Create consent logging function in `code/utils/helpers.py` to write `consent_log.csv` (timestamp, user_id, decision, IRB_PROTOCOL_ID)
- [X] T015 [US0] Implement redirect logic to withdrawal page on "I Do Not Agree". Create `code/survey/withdrawal.py` with a simple "Thank you for your time" message. Add `st.switch_page("withdrawal.py")` in the "I Do Not Agree" handler.
- [X] T022a [US1] Implement session initialization in `code/survey/app.py`: Generate a unique `participant_id` (UUID v4) at the start of the session and store it in `st.session_state`. **This ID must persist for the entire session and be written to every row of the CSV.**
- [X] T022b [US1] Implement IP extraction, hashing, and session rejection logic in `code/survey/app.py`: Extract IP using `st.context.headers.get('X-Forwarded-For')`. If missing in production, display error "Session Rejected: Unable to verify identity." and call `st.stop()`. Hash the IP with `helpers.hash_ip()` immediately after extraction.
- [X] T069 [US1] **Define and Implement Metadata Schema**. **Action**: Create `code/survey/constants.py` with a `METADATA_SCHEMA` constant defining all required fields beyond Age/Education. **Fields**: `browser_version` (extracted from user_agent), `session_duration` (calculated from start/end timestamps). **Output**: This schema defines the columns for `data/raw/submissions.csv`. **Verification**: Unit test in `tests/unit/test_schema.py` asserts that exported CSV headers match this schema. **Note**: Resolves ambiguity of "metadata" in US1.
- [X] T022d [US1] **Render Form**. **Action**: Render the demographic input form in `code/survey/app.py` using the schema defined in T069. **Explicit Fields**: The form MUST include input fields for **Age** (numeric) and **Education** (categorical) as required by US1. **Verification**: Unit test asserts fields are present.
- [X] T022f [US1] **Capture and Export Data**. **Action**: On form submission, append a row to `data/raw/submissions.csv` with columns defined in `METADATA_SCHEMA` from T069. **Schema**: `participant_id` (UUID), `age` (int), `education` (str), `timestamp` (ISO8601), `hashed_ip` (str), `browser_version` (str), `session_duration` (int). **Robustness**: Use atomic writes (write to a temporary file `data/raw/submissions.csv.tmp`, then `os.rename` to `data/raw/submissions.csv`). **Verification**: Unit test asserts atomic write success and schema compliance.
- [X] T022g_test [US1] Verify CSV schema. **Action**: Create `tests/unit/test_csv_schema.py` with function `test_csv_columns_match_spec` to verify the exported CSV headers match the spec.
- [X] T022h [US1] **Implement Post-Hoc Duplicate Detection**. **Action**: Create `code/utils/dedup.py`. **Logic**: Read `data/raw/submissions.csv` after T022f writes it. Identify duplicate `participant_id` entries. **Output**: Generate `data/processed/dedup_report.csv` listing removed duplicates. **Verification**: Add a unit test in `tests/unit/test_dedup.py` that simulates duplicate entries and asserts that N duplicates are removed and the report is generated.
- [X] T028e [US1] **Define and Implement Latin Square Sequences**. **Action**: Create `code/survey/constants.py` with the `LATIN_SQUARE_SEQUENCES` constant. **Content**: `[['professional', 'minimalist', 'low_quality', 'neutral'], ['minimalist', 'neutral', 'professional', 'low_quality'], ['low_quality', 'professional', 'neutral', 'minimalist'], ['neutral', 'low_quality', 'minimalist', 'professional']]`. **Verification**: Unit test asserts this list forms a valid Latin Square.
- [X] T016a [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square.
- [X] T016b [US1] **Implement Balanced Latin Square Selection Logic**. **Action**: Create `code/survey/randomization.py` with function `generate_latin_square(stimuli_list)`. **Logic**: Select a sequence based on participant ID modulo N. **Verification**: Unit test asserts every stimulus appears exactly once per position across all sequences.
- [X] T016c [US1] **Verify Latin Square Runtime Selection**. **Action**: Create `tests/unit/test_randomization.py` with function `test_runtime_selection` that simulates 100 participants and asserts the distribution of sequences is uniform.
- [X] T017 [US1] **Implement Stimulus Rendering Loop**. **Action**: In `code/survey/app.py`, implement a loop that renders stimuli using `st.container` and `st.markdown`. **Mapping Logic**: The loop must map the Latin Square sequence indices (0, 1, 2, 3) to the specific file paths: `professional.html`, `minimalist.html`, `low_quality.html`, `neutral.html` respectively. **Requirement**: Before rendering, verify that current stimulus hashes match `state/stimuli_hashes.json` (from T070). If mismatch, halt with error. **Verification**: Unit test simulates 4 stimuli renders without error.
- [X] T018 [US1] **Create Multi-Point Likert Rating Inputs**. **Action**: Implement `st.radio` components in `code/survey/app.py` for Credibility and Professionalism using a multi-point Likert scale. **Verification**: Unit test asserts 7 radio buttons are rendered.
- [X] T019 [US1] **Implement Validation Logic**. **Action**: Add `validate_ratings()` function in `code/survey/app.py`. **Logic**: Block submission if < 4 stimuli rated. **Verification**: Create `tests/unit/test_validation.py` that asserts error on 3 ratings and success on 4.
- [X] T071 [US1] **Add Session Timeout and Abandonment Tracking**. **Action**: Modify `code/survey/app.py` to Implement an inactivity timeout using `st.session_state` timestamps. **Logic**: If a participant is inactive for 30 minutes, clear their session state and log an "Abandoned Session" entry to `data/processed/abandonment_log.csv` without saving partial ratings. **Verification**: Unit test in `tests/unit/test_session_timeout.py` simulates inactivity and asserts session reset and logging. **Rationale**: Prevents data contamination from incomplete sessions and improves data hygiene (Constitution Principle III).

**Checkpoint**: User Story 0 & 1 are fully functional; data can be collected and exported with integrity.

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [X] T025a [US2] **Create ANOVA Script**. **Action**: Create `code/analysis/01_anova.py`. **Input**: `data/processed/clean_data.csv`. **Logic**: 
  1. Load data.
  2. Run Repeated-Measures ANOVA using `pingouin.rm_anova` with formula: `Credibility ~ Condition + Error(Participant/Condition)`.
  3. Calculate **Effect Sizes**: Compute `eta_squared` (partial) and **`cohen_d` for the main effect** using `pingouin.compute_effsize`. **Note**: This task MUST output the aggregate main effect Cohen's d regardless of pairwise execution.
  4. **Output**: Save results to `data/processed/anova_results.json` with keys: `f_statistic`, `p_value`, `eta_squared`, `cohen_d_main`, `degrees_of_freedom`.
  5. **Verification**: Unit test asserts JSON schema validity and presence of `cohen_d_main`.
- [X] T025b [US2] **Execute ANOVA Script**. **Action**: Run `code/analysis/01_anova.py` on sample data. **Verification**: Unit test `tests/unit/test_anova_execution.py` asserts the script runs without error and produces a non-empty JSON file. **Note**: This is an automated pipeline step, not a manual one-off.
- [X] T026_integrated [US2] **Implement Conditional Pairwise T-Tests**. **Action**: Create `code/analysis/02_pairwise.py`. **Dependency**: Requires `data/processed/anova_results.json` from T025b. **Logic**: 
  1. Load ANOVA results.
  2. If `p_value < 0.05`, run Bonferroni-corrected pairwise t-tests using `pingouin.pairwise_ttests`.
  3. Calculate `cohen_d` for each pair.
  4. **Output**: Append `pairwise_comparisons` array (with `comparison`, `p_value`, `cohen_d`, `significant`) to `data/processed/anova_results.json`.
  5. **Verification**: Unit test asserts pairwise results are present if ANOVA is significant.
- [X] T026_verify [US2] **Verify Statistical Output**. **Action**: Create `tests/unit/test_anova_output.py` with assertions for JSON schema validity, presence of `eta_squared`, `cohen_d_main`, and the `pairwise_comparisons` array (if applicable).
- [X] T027a_b [US2] **Create Report Script**. **Action**: Create `code/analysis/02_report.py`. **Input**: `data/processed/anova_results.json`. **Output**: Generate `data/processed/summary_table.csv`. **Verification**: Unit test asserts CSV contains expected columns.

**Checkpoint**: Preprocessing scripts ready; data analysis blocked until T024a completes.

---

## Phase 5: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [X] T032a [US3] **Create Mixed-Effects Model**. **Action**: Create `code/analysis/03_mixed_effects.py`. **Logic**: Implement `run_mixed_effects()` function. **Formula**: `Credibility ~ Condition + Age + Education + (1|Participant)`. **Output**: Save results to `data/processed/mixed_effects_results.json` with keys: `condition_coefficient`, `condition_p_value`, `age_coefficient`, `education_coefficient`, `convergence_status`. **Verification**: Unit test asserts convergence and presence of covariate coefficients.
- [X] T032b [US3] **Verify Mixed-Effects Output**. **Action**: Create `tests/unit/test_mixed_effects_output.py` with assertions for JSON schema validity and specific statistical fields.
- [X] T035 [US3] **Implement Comparison Logic**. **Action**: Create `code/analysis/04_compare.py`. **Dependency**: Requires `data/processed/anova_results.json` from T025a and `data/processed/mixed_effects_results.json` from T032a. **Logic**: 
  1. Extract `condition_coefficient` and `condition_p_value` from Mixed-Effects results.
  2. Extract `f_statistic` and `p_value` from ANOVA results.
  3. **Compare**: Check if the sign of `condition_coefficient` matches the direction of the ANOVA effect. Check if `condition_p_value` is significant (p < 0.05) consistent with ANOVA.
  4. **Output**: Save comparison report to `data/processed/mixed_effects_comparison.json` with keys: `sign_consistent`, `significance_aligned`, `robustness_conclusion`.
  5. **Verification**: Unit test asserts comparison report contains both ANOVA and Mixed-Effects stats and the comparison logic.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 6: Post-Collection & Validation (Priority: P3) 🔬

**Goal**: Run post-collection analysis and validation checks.

### Implementation for Post-Collection

- [X] T064 [US2] **Implement Post-Collection Power Analysis**. **Action**: Create `code/analysis/04_power_analysis.py`. **Logic**: After data collection, calculate statistical power based on the **actual sample size (N)** from `data/raw/submissions.csv` and a default moderate effect size (Cohen's d). **Output**: Save report to `data/processed/power_analysis_report.json`. **Constraint**: If power < 0.80, print warning but do not halt. **Note**: Diagnostic only. Must run after Phase 4.
- [X] T074 [US1] **Validate Randomization Balance Post-Collection**. **Action**: Create `code/analysis/05_validate_randomization.py`. **Logic**: After data collection, verify that the distribution of stimuli orders matches the expected Latin Square proportions. **Output**: Save report to `data/processed/randomization_balance_report.json`. **Verification**: Unit test asserts that the report correctly identifies significant deviations from the expected distribution. **Rationale**: Ensures the experimental design was executed correctly and validates the internal validity of the study.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [P] T041 Update `README.md` with setup instructions and execution order
- [P] T042 Run `quickstart.md` validation.
- [X] T043b [P] Verify runtime benchmark.
- [X] T043c [P] **Verify File Size**.
- [X] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md`.

**Checkpoint**: Polish and validation tasks complete.

---

## Phase 8: Revision & Review Resolution

**Purpose**: Address specific concerns raised in prior research-stage reviews to ensure scientific rigor and data integrity.

**Removed Tasks (Scope Alignment)**:
- **T065 (Strict Data Loader Fail-Loud)**: **REMOVED**. This task referenced a network data loader and streaming architecture not present in the spec/plan (local CSV only). Removed to prevent "phantom architecture" confusion.
- **T060 (Real Data Streaming Fallback)**: **REMOVED**. This task referenced streaming/fallback logic not authorized by the spec. Removed to align with local CSV model.
- **T055 (Data Streaming for Large Datasets)**: **REMOVED**. This task addressed a non-existent streaming requirement. Removed to prevent scope creep.
- **T056 (Sensitivity Analysis)**: **REMOVED**. This task was not required by the functional requirements (US2/US3). Removed to prevent scope creep.
- **T061 (Robustness Check for Outlier Influence)**: **REMOVED**. This task was not required by the functional requirements. Removed to prevent scope creep.
- **T011h_new (GitHub Actions Workflow)**: **REMOVED**. This task implemented CI/CD infrastructure not defined in the plan. Removed to align with project scope.
- **T066 (Sample Size Declaration for Streaming)**: **REMOVED**. This task assumed a streaming/sampling architecture not present in the spec. Removed to prevent "silent constitution drift".

**Remaining Review Tasks**:
- [X] T062_new [US0] **Implement Withdrawal Logging**. **Action**: Create `code/survey/withdrawal_handler.py`. **Logic**: When a participant withdraws, log their `participant_id` and `timestamp` to `data/processed/withdrawal_log.csv`. **Constraint**: Do NOT modify `data/raw/submissions.csv`. This creates a new versioned artifact for audit purposes, satisfying Constitution Principle III.

**Checkpoint**: All prior research-stage review concerns have been addressed and verified.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires T024a (Preprocessing) which depends on T057 (Checksums) and T009 (Data Structure)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires T024a and T025a_b (ANOVA results)

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