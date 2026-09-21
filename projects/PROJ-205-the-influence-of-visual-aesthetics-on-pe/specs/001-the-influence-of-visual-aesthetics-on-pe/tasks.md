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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `projects/PROJ-205-.../` in `plan.md`. Execute: `mkdir -p code/stimuli code/survey code/analysis code/utils data/raw data/processed tests/unit tests/integration tests/contract state/projects`
- [X] T002 Initialize Python project with `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pyyaml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting tools. Create `.ruff.toml` with rules E, W, F, I, N, D, UP, C90, B, C4, PT, RUF, SIM, TCH, TID, ARG, UP, W, F. Create `pyproject.toml` with `[tool.black]` and `[tool.isort]` sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/stimuli/text_content.txt` with the fixed neutral text source. **Content**: "The rapid evolution of digital communication has fundamentally altered how individuals perceive and process information. In an era where attention spans are shrinking, the visual presentation of online content plays a critical role in establishing initial trust and credibility. This study examines the psychological mechanisms underlying these perceptions."
- [X] T005 [P] Create `code/stimuli/professional.html`. **Design**: High-fidelity CSS, serif fonts (Georgia/Times New Roman), balanced layout, professional color palette (navy #003366, white #FFFFFF, gray #F0F0F0), clean typography, no clutter. **CSS Rules**: `body { font-family: Georgia, serif; background: #FFFFFF; color: #333333; } h1 { color: #003366; }.container { max-width: 800px; margin: 0 auto; padding: 20px; }`.
- [X] T006 [P] Create `code/stimuli/minimalist.html`. **Design**: Low-fidelity CSS, sans-serif fonts (Arial/Helvetica), sparse layout, high contrast black (#000000) / white (#FFFFFF), minimal decoration, simple structure, no images. **CSS Rules**: `body { font-family: Arial, sans-serif; background: #FFFFFF; color: #000000; } h1 { font-weight: normal; }.container { max-width: 600px; margin: 0 auto; }`.
- [X] T007 [P] Create `code/stimuli/low_quality.html`. **Design**: Broken CSS, mismatched fonts (Comic Sans MS / Times New Roman mix), cluttered layout, jarring colors (neon green #39FF14, red #FF0000), broken alignment, visual noise, overlapping elements. **CSS Rules**: `body { font-family: 'Comic Sans MS', 'Times New Roman', serif; background: #000000; color: #39FF14; } h1 { color: #FF0000; font-size: 40px; }.container { margin: -20px; }`.
- [X] T008 [P] Create `code/stimuli/neutral.html`. **Design**: Standard default browser styling, plain text, no custom CSS, minimal formatting, Times New Roman, black text on white background. **CSS Rules**: No custom CSS file; relies on browser defaults.
- [X] T009 Setup `data/raw/` and `data/processed/` directory structure. Execute: `touch data/raw/.gitkeep data/processed/.gitkeep`
- [X] T010 Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function)
- [X] T011a [US0] Create `data/consent/irb_approved.txt` as a **template structure**. **Action**: Write a file containing the following sections as placeholders: `# Introduction`, `# Risks`, `# Benefits`, `# Confidentiality`, `# Consent Checkbox`. Include a header comment explaining that the actual IRB-approved text must be manually inserted from an external approved protocol before production use. **Do NOT** generate legal text or simulate approval.
- [X] T011b [US0] Define `IRB_PROTOCOL_ID` environment variable and ensure it is captured in every consent log entry (Constitution Principle VI compliance).
- [X] T011c [US0] Configure environment variables to point to `data/consent/irb_approved.txt` for the consent form source.
- [X] T011d [US0] Implement verification logic in `code/survey/app.py` to validate `data/consent/irb_approved.txt`. **Action**: Check if the file contains `<<INSERT_IRB_APPROVED_TEXT_HERE>>`. If found and `MODE=production`, raise a fatal error (fail loudly). Additionally, verify that the file contains substantial text (e.g., > 500 characters) excluding the placeholder header. If the text is insufficient or missing, raise a fatal error. If `MODE=development`, log a warning and allow execution for testing purposes.
- [X] T011e [US0] **MANDATORY**: Insert IRB-approved Text. **Action**: Before any production data collection, manually replace the placeholder in `data/consent/irb_approved.txt` with the actual IRB-approved text. **Verification Gate**: The system MUST implement a strict check in `code/survey/app.py` that raises a fatal error if the file contains the placeholder AND `MODE=production`. This task must be marked complete before US0 can be considered "Production Ready". **Note**: This is a manual administrative step. The system must not run data collection without this verification.
- [X] T016c [P] Create `code/utils/file_lock.py` for file-based locking mechanism to persist state across sessions. **Action**: Implement a thread-safe file lock utility using `fcntl` (Linux) or `msvcrt` (Windows) to allow atomic read/write of a counter file.
- [X] T054 [US0] **Add Consent Form Versioning**. Address reviewer concern about tracking consent form changes. **Action**: Modify `code/utils/helpers.py` to compute a SHA-256 hash of `data/consent/irb_approved.txt` for backend version tracking. **Crucial**: The hash is ONLY for internal logging and version tracking. The full, readable text of the consent form MUST be displayed to the participant. **Do NOT** display the hash to the participant. Update `data/consent/irb_approved.txt` to include a version header comment. Ensure `code/survey/app.py` logs the version hash with every consent decision.
- [X] T043a [P] **Generate Mock Data for Testing**. **Action**: Create a script `code/utils/generate_mock_data.py` to generate a synthetic `data/raw/submissions.csv` with N=250 participants, normal distribution (mean=4, std=1.5) for ratings, and all required fields (participant_id, stimulus_id, credibility, professionalism, timestamp, hashed_ip, age, education). **Purpose**: Ensure input data exists for analysis tasks in Phase 5. **Note**: This task is moved to Phase 2 to ensure data availability.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Informed Consent Workflow (Priority: P0) 🛡️

**Goal**: Present IRB-approved Informed Consent and block access until accepted.

**Independent Test**: Simulate a new user session; verify consent form appears, survey is blocked, and a consent record is logged upon "I Agree".

### Implementation for User Story 0

- [X] T012 [US0] Implement consent modal in `code/survey/app.py` displaying IRB text from `data/consent/irb_approved.txt` and including the `IRB_PROTOCOL_ID` in the header. **Note**: The ID must be explicitly rendered in the modal title or header text.
- [X] T013 [US0] Implement "I Agree" / "I Do Not Agree" logic in `code/survey/app.py`
- [X] T014 [US0] Create consent logging function in `code/utils/helpers.py` to write `consent_log.csv` (timestamp, user_id, decision, IRB_PROTOCOL_ID)
- [X] T015 [US0] Implement redirect logic to withdrawal page on "I Do Not Agree". Create `code/survey/withdrawal.py` with a simple "Thank you for your time" message. Add `st.switch_page("withdrawal.py")` in the "I Do Not Agree" handler.

**Checkpoint**: User Story 0 is functional; no data collection can occur without consent.

---

## Phase 4: User Story 1 - Participant Survey Data Collection (Priority: P1) 🎯 MVP

**Goal**: Deliver a set of stimuli in Latin Square order, collect multiple ratings, and export CSV.

**Independent Test**: Simulate a participant session; verify that stimuli load in a valid sequence, ensuring a sufficient number of ratings are captured, and the CSV export contains all fields.

### Implementation for User Story 1

- [X] T022a [US1] Implement session initialization in `code/survey/app.py`: Generate a unique `participant_id` (UUID v4) at the start of the session and store it in `st.session_state`. **This ID must persist for the entire session and be written to every row of the CSV.**
- [ ] T023f_heartbeat [US1] Implement session timeout detection in `code/survey/app.py`: Use `st.on_change` on a hidden widget or form to update `st.session_state.last_active` with `time.time()`. On page load or widget interaction, check if `time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD` (e.g., a configurable session timeout duration). If exceeded, set `session_status='timeout'` and `submission_status='incomplete'` in the session state. **Action**: This must run AFTER T022a to ensure session_state exists.
- [X] T022b [US1] Implement IP extraction, hashing, and session rejection logic in `code/survey/app.py`: Extract IP using `st.context.headers.get('X-Forwarded-For')`. If missing in production, display error "Session Rejected: Unable to verify identity." and call `st.stop()`. Hash the IP with `helpers.hash_ip()` immediately after extraction. **This single task covers both extraction and rejection.**
- [X] T022c [US1] **Define Form Schema**: Define the schema for demographic input (Age, Education) and the CSV export structure in `code/survey/constants.py`. **Action**: Define a dictionary `DEMOGRAPHIC_SCHEMA` with fields `age`, `education` and `CSV_SCHEMA` with all required columns. This task establishes the data structure before rendering or capturing.
- [ ] T022d [US1] **Render Form**: Render the demographic input form in `code/survey/app.py` using the schema defined in T022c. **Action**: Render the demographic input form (Age, Education) in `code/survey/app.py`. **Note**: This task depends on T022c.
- [ ] T022e [US1] **Capture Data**: Capture demographic data. **Action**: On form submission (triggered by T022d), append a row to `data/raw/submissions.csv` with columns `participant_id`, `age`, `education`, `timestamp`, `hashed_ip`. **Note**: This task depends on T022g_logic for file creation.
- [X] T022f [US1] Implement metadata truncation. **Action**: Truncate `user_agent` strings to a maximum of 255 characters before writing to CSV in `code/survey/app.py`.
- [X] T028e [US1] Implement Latin Square sequences as a hardcoded constant list in `code/survey/constants.py`. **Content**: Define a square matrix with the following permutations (Professional, Minimalist, Low-Quality, Neutral):
 1. [Professional, Minimalist, Low-Quality, Neutral]
 2. [Minimalist, Low-Quality, Neutral, Professional]
 3. [Low-Quality, Neutral, Professional, Minimalist]
 4. [Neutral, Professional, Minimalist, Low-Quality]
 **Action**: Write these exact permutations to `code/survey/constants.py` as a constant list `LATIN_SQUARE_MATRIX`.
- [X] T016a [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square for the specified number of conditions.
- [ ] T016b [US1] Implement balanced Latin Square selection logic. **Action**: In `code/survey/app.py`, implement a function that uses `hash(participant_id) % 4` to select a row index from `LATIN_SQUARE_MATRIX`. **Crucial**: Implement a round-robin counter using the file-locking utility from **T016c** to ensure that across the entire cohort, each row is selected an equal number of times, guaranteeing the balanced property (every stimulus appears in every position exactly once). **Output**: Return the specific order of stimuli for the current participant.
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py` to display HTML files sequentially based on the order returned by T016b.
- [X] T018 [US1] Create multi-point Likert rating inputs for Credibility and Professionalism in `code/survey/app.py`.
- [ ] T019 [US1] Implement validation logic to block submission if < 4 stimuli rated (8 total ratings). **Action**: In the submit handler of `app.py`, check if all 4 stimuli have been rated (8 total ratings: 4 stimuli * 2 scales). If not, display error "Please rate all stimuli before submitting." and block submission. **Note**: This explicitly enforces the 4-stimuli requirement.
- [X] T020 [US1] Implement client-side state management: Use **in-memory only** (Streamlit session state) to track progress.
- [X] T021 [US1] Implement submission handler to record Participant ID, Stimulus Condition, Ratings, Timestamp, Device Info in `code/survey/app.py`. **Action**: This handler aggregates all data and triggers the export logic defined in **T022g_logic**.
- [ ] T022g_logic [US1] Implement CSV export logic. **Action**: Write the aggregated data from T021 to `data/raw/submissions.csv`. **Schema**: `participant_id, stimulus_id, credibility, professionalism, timestamp, hashed_ip, age, education, duplicate_flag, session_status, submission_status`. **Constraint**: Truncate `user_agent` to 255 characters before writing. **Note**: This task must be executed before T022e (Capture) and T021 (Submission) to ensure file existence.
- [ ] T022g_test [US1] Verify CSV schema. **Action**: Run `pytest tests/contract/test_csv_schema.py` to verify header matches schema. **Note**: This task depends on T022g_logic creating the file.
- [ ] T022h [US1] Implement post-hoc duplicate detection. **Action**: Create script `code/analysis/05_audit.py`. Read `data/raw/submissions.csv`, flag rows where `hashed_ip` appears more than once, and log to `data/raw/duplicate_audit.csv`. **Verification**: Run `python code/analysis/05_audit.py` and verify `duplicate_audit.csv` content. **Note**: This task depends on T022g_test to ensure schema integrity.
- [X] T038 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py`.
- [X] T039 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`.
- [X] T040 [P] Add contract test for CSV schema validation (including hashed IP and flags) in `tests/contract/test_csv_schema.py`.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [ ] T024a_b [US2] Create and execute preprocess script `code/analysis/00_preprocess.py`. **Action**: Load `data/raw/submissions.csv`, filter **complete sessions** (those with the requisite number of ratings: stimuli x 2 scales), audit excluded rows, and reshape the dataframe into **wide format** (one row per participant, columns for each condition's rating) specifically for `statsmodels` Repeated-Measures ANOVA. **Artifact**: Generate `data/processed/cleaned_data.csv`. **Verification**: Run `python code/analysis/00_preprocess.py` and verify output file exists.
- [ ] T025a_b [US2] Create and execute ANOVA script using `statsmodels` to calculate F-statistic, p-value, and eta squared from cleaned data. **Action**: Run Repeated-Measures ANOVA on the wide-format data. **Output Schema**: Save results to `data/processed/anova_results.json` with keys: `F_statistic`, `p_value`, `eta_squared`, `degrees_of_freedom`.
- [ ] T026_integrated [US2] Implement conditional pairwise t-tests if ANOVA p < 0.05 using Bonferroni correction and calculate Cohen's d with the corrected p-values. **Action**: Run pairwise t-tests between conditions in `code/analysis/02_pairwise.py`. **Output Schema**: Save results to `data/processed/pairwise_results.json` with keys: `Cohen_d`, `Bonferroni_corrected_p`, `unadjusted_p`. **Dependency**: Requires output from T025a_b (`data/processed/anova_results.json`).
- [ ] T027a_b [US2] Create report script to generate a summary table including ANOVA results, pairwise comparisons, effect sizes, and save it as `data/processed/analysis_results.json`. **Dependency**: Requires outputs from **T025a_b** and **T026_integrated**.
- [ ] T045 [US2] **Create and Execute Power Analysis Script**. Calculate minimum detectable effect size for N=250 using real or mock data. **Action**: Use `statsmodels.stats.power` to calculate power. **Output Schema**: Save to `data/processed/power_analysis_results.json` with keys: `sample_size`, `effect_size`, `power`, `alpha`.
- [ ] T048 [US2] Address reviewer comment: "The p-value correction method (Bonferroni) is conservative and may lead to a loss of statistical power. Consider using a more flexible method, such as Benjamini-Hochberg (FDR), to control the false discovery rate." **Action**: Modify `code/analysis/02_pairwise.py` to add a command-line argument `--correction-method {bonferroni, fdr}`. Default to `bonferroni` to maintain backward compatibility and satisfy Spec US2. Update `data/processed/analysis_results.json` to include the method used and the resulting p-values for both methods if applicable. **Output Schema**: Include keys `bonferroni_p` and `fdr_p`. **Note**: Bonferroni is the primary metric.

**Checkpoint**: Preprocessing scripts ready; data analysis blocked until T024b completes.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [ ] T032_33_35 [US3] Create and execute `code/analysis/03_mixed_effects.py` to run a linear mixed effects model with random intercepts, age/education as covariates, and compare the results to ANOVA findings. Save output to `data/processed/mixed_effects_results.json`.
- [ ] T049 [US3] Address reviewer comment: "The mixed-effects model assumes a normal distribution of residuals. Check the residuals for normality and consider data transformations if necessary." **Action**: Add residual normality checks (Shapiro-Wilk test) to `code/analysis/03_mixed_effects.py`. If the p-value of the Shapiro-Wilk test is < 0.05, log a warning and attempt a log or square-root transformation of the dependent variable (Credibility/Professionalism) and re-run the model. Report both the original and transformed model results in `data/processed/mixed_effects_results.json` with a flag indicating whether transformation was necessary. **Constraint**: Transformations are only applied if the protocol allows; raw data meaning is preserved in the primary report.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [P] T041 Update `README.md` with setup instructions and execution order
- [P] T042 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [X] T043b [P] Verify runtime benchmark: Create `tests/benchmark/test_runtime.py` that asserts the full analysis pipeline completes within 30 minutes on a CPU-only runner using the mock data from T043a.
- [X] T043c [P] Verify file size: Add assertion in `tests/benchmark/test_runtime.py` that `data/raw/submissions.csv` size < 5MB for N=250.
- [P] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md` documenting the exact steps for data collection, cleaning, and analysis to ensure reproducibility by external researchers.

**Checkpoint**: Polish and validation tasks complete.

---

## Phase 8: Revision & Review Resolution

**Purpose**: Address specific concerns raised in prior research-stage reviews to ensure scientific rigor and data integrity.

- [ ] T051 [US2] **Enhance Effect Size Reporting**. Address reviewer concern about the lack of confidence intervals for effect sizes. **Action**: Update `code/analysis/02_pairwise.py` and `code/analysis/03_mixed_effects.py` to calculate and report confidence intervals for Cohen's d and Eta-squared using bootstrapping (1000 iterations, **seed=42**). Store these intervals in `data/processed/analysis_results.json` and `data/processed/mixed_effects_results.json`. <!-- ATOMIZE: requested -->
- [ ] T052 [US3] **Validate Mixed-Effects Model Convergence**. Address reviewer concern about potential convergence warnings in mixed-effects models. **Action**: Add a convergence check in `code/analysis/03_mixed_effects.py`. If the model fails to converge (return code != 1), automatically retry with different optimizers (`'bfgs'`, `'newton'`) or simplified random effects structures. Log all retry attempts and final convergence status in `data/processed/mixed_effects_results.json`. If convergence fails after a predefined number of attempts, flag the result as "UNCONVERGED" in the output JSON.
- [ ] T053 [US1] **Implement Session Integrity Audit**. Address reviewer concern about incomplete or corrupted sessions. **Action**: Create `code/analysis/06_integrity_audit.py`. This script will scan `data/raw/submissions.csv` for sessions with missing ratings (e.g., a participant started but didn't finish all 4 stimuli), inconsistent timestamps, or duplicate entries. It will generate a report `data/processed/integrity_audit.json` listing excluded sessions and reasons for exclusion.

**Checkpoint**: All prior research-stage review concerns have been addressed and verified.