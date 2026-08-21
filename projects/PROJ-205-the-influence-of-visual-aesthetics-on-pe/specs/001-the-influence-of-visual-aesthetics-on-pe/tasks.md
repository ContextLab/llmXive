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
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. Create `.ruff.toml` with rules E, W, F, I, N, D, UP, C90, B, C4, PT, RUF, SIM, TCH, TID, ARG, UP, W, F. Create `pyproject.toml` with `[tool.black]` and `[tool.isort]` sections.

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
- [X] T011d [US0] Implement verification logic in `code/survey/app.py` to validate `data/consent/irb_approved.txt`. **Action**: Check if the file contains `<<INSERT_IRB_APPROVED_TEXT_HERE>>`. If found and `MODE=production`, raise a fatal error (fail loudly). If `MODE=development`, log a warning and allow execution for testing purposes.
- [ ] T011e [US0] **MANDATORY**: Insert IRB-Approved Text. **Action**: Before any production data collection, manually replace the placeholder in `data/consent/irb_approved.txt` with the actual IRB-approved text. This task must be marked complete before US0 can be considered "Production Ready". <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

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

**Independent Test**: Simulate a participant session; verify 4 stimuli load in a valid sequence, 8 ratings are captured, and the CSV export contains all fields.

### Implementation for User Story 1

- [X] T016a [US1] Define the Latin Square sequences as a hardcoded constant list in `code/survey/app.py`. The list MUST contain tuples (verified as a valid Latin Square for the specified conditions):
 1. ["Professional", "Minimalist", "Low-Quality", "Neutral"]
 2. ["Minimalist", "Low-Quality", "Neutral", "Professional"]
 3. ["Low-Quality", "Neutral", "Professional", "Minimalist"]
 4. ["Neutral", "Professional", "Minimalist", "Low-Quality"]
- [X] T016b [US1] Implement random selection logic in `code/survey/app.py` that selects ONE sequence from the hardcoded list in T016a per participant (strict lookup, no generative algorithm)
- [X] T016c [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square for 4 conditions (each condition appears exactly once in each position and follows every other condition exactly once). **Note**: This test must pass before T016b is considered complete.
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py` to display HTML files sequentially
- [X] T018 [US1] Create multi-point Likert rating inputs for Credibility and Professionalism in `code/survey/app.py`
- [X] T019 [US1] Implement validation logic to block submission if < 8 ratings are present (FR-008). Display `st.error("Please rate all stimuli.")` and disable the submit button if `len(ratings) < 8`. **Note**: Verify 4 stimuli * 2 ratings = 8.
- [X] T020 [US1] Implement client-side state management: Use **in-memory only** (Streamlit session state) to track progress. Implement `st.session_state.clear()` in the submit handler and on session expiration to ensure no PII persists.
- [X] T021 [US1] Implement submission handler to record Participant ID, Stimulus Condition, Ratings, Timestamp, Device Info in `code/survey/app.py`
- [X] T022a [US1] Implement session initialization in `code/survey/app.py`: Generate a unique `participant_id` (UUID v4) at the start of the session and store it in `st.session_state`. **This ID must persist for the entire session and be written to every row of the CSV.**
- [ ] T022b_1 [US1] **Implement IP Header Extraction & Rejection**. **Action**: In `code/survey/app.py`, extract IP using `st.context.headers.get('X-Forwarded-For')` or `st.experimental_request.headers.get('X-Forwarded-For')`. **Logic**: If the IP cannot be captured via either method, display `st.error("IP capture failed: X-Forwarded-For header missing. Please contact support.")` and call `st.stop()` to terminate the session immediately. **Do NOT** proceed without an IP.
- [ ] T022b [US1] **Implement Session Rejection Logic**. **Action**: Use the result from T022b_1. If IP capture fails (as handled in T022b_1), the session is rejected. **Note**: This task is dependent on T022b_1.
- [X] T022c [US1] Implement immediate IP hashing in `code/survey/app.py`: Call `helpers.hash_ip()` on the raw IP variable immediately upon capture. **NEVER** write the raw IP to disk, logs, or the CSV. Write ONLY the hashed value.
- [X] T022d [US1] Implement duplicate flagging: Check if the hashed IP exists in `data/raw/submissions.csv` (read file). **Action**: This check must occur **before** the append operation of T022h. Write `1` if duplicate, `0` if unique to the `duplicate_flag` column. **Note**: This check is for audit purposes only; hashed IPs are NOT stored as persistent identifiers for re-identification.
- [X] T022e_ui [US1] Render the demographic input form in `code/survey/app.py`: Implement a dropdown for Education with options: [High School, Bachelor's, Master's, PhD] and a number input for Age (years). Ensure validation enforces the ordinal structure.
- [X] T022f [US1] Implement demographic data collection: Write Age (integer) and Education (integer code) to `data/raw/submissions.csv` columns. **Mapping**: High School, Bachelor's, Master's, PhD. Reference data collected in T022e_ui.
- [X] T022g [US1] Implement metadata truncation: Truncate `user_agent` strings to a fixed safe length (a predefined maximum character limit). to prevent excessively long entries. Exclude large binary blobs. Ensure `data/raw/submissions.csv` remains manageable.
- [X] T022h [US1] Implement CSV export logic to append to `data/raw/submissions.csv`. **Schema**: `participant_id, stimulus_id, credibility, professionalism, timestamp, hashed_ip, age, education, duplicate_flag, session_status, submission_status`. **Action**:
 1. Read current session flags from `st.session_state` (`session_status`, `submission_status`).
 2. Iterate through the `st.session_state.ratings` list (which contains one entry per stimulus).
 3. For EACH entry, write ONE ROW to the CSV containing the `participant_id`, the specific `stimulus_id` (e.g., "Professional"), the ratings, and the session flags.
 **Note**: This long-format structure (multiple rows per participant) is critical for the Repeated-Measures ANOVA in US2.
- [X] T023f_heartbeat [US1] Implement session timeout detection in `code/survey/app.py`: Use `st.on_change` on a hidden widget or form to update `st.session_state.last_active` with `time.time()`. On page load or widget interaction, check if `time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD` (e.g., a configurable session timeout duration). If exceeded, set `session_status='timeout'` and `submission_status='incomplete'` in the session state. If the user submits successfully before timeout, set `submission_status='complete'` and `session_status='active'`. **This mechanism generates the flags used in T024.**
- [X] T028d [US1] Implement post-hoc duplicate detection in `code/survey/app.py` or a separate script. **Action**: After data collection, read `data/raw/submissions.csv` and flag any rows where `hashed_ip` appears more than once. Log these to `data/raw/duplicate_audit.csv`. **Do NOT** perform this check in real-time during submission to avoid race conditions and PII persistence concerns.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [ ] T024a_1 [US2] **Create Preprocess Script (Loader)**. **Action**: Create `code/analysis/01_preprocess.py`. **Logic**: Import `pandas`. Define function `load_raw_data()` that checks for `data/raw/submissions.csv`. If missing/empty, raise `FileNotFoundError` (Fail Loudly) unless `MODE=development`. If `MODE=development` and missing, generate `data/processed/no_data_report.json` and exit gracefully.
- [ ] T024a_2 [US2] **Create Preprocess Script (Filtering)**. **Action**: In `code/analysis/01_preprocess.py`, implement `filter_complete_sessions(df)` to remove rows where `submission_status != 'complete'` OR `session_status == 'timeout'`. Log excluded rows to `data/processed/excluded_audit.csv`.
- [ ] T024a_3 [US2] **Create Preprocess Script (Audit)**. **Action**: In `code/analysis/01_preprocess.py`, implement `generate_audit_log(excluded_rows)` to write `data/processed/excluded_audit.csv`.
- [ ] T024a [US2] **Create Preprocess Script (Reshape)**. **Action**: In `code/analysis/01_preprocess.py`, implement `reshape_to_wide(df)` to convert long-format data to wide-format using `participant_id` as index. **Output**: `data/processed/cleaned_data.csv`. **Schema**: `participant_id, age, education, credibility_Professional, credibility_Minimalist, credibility_Low-Quality, credibility_Neutral, professionalism_Professional,...`. **Verification**: Add assertion `assert all(col in df.columns for col in ['credibility_Professional', 'credibility_Minimalist', 'credibility_Low-Quality', 'credibility_Neutral'])`.
- [ ] T024b [US2] **Execute Preprocess & Reshape**. **Action**: Run `python code/analysis/01_preprocess.py`. **Verification**: Assert `data/processed/cleaned_data.csv` exists. Assert schema matches T024a. **Exit**: Exit with non-zero code if file is missing or schema mismatch. **Note**: This task produces the artifact required by T025a/T027a.
- [ ] T025a_1 [US2] **Create ANOVA Script (Setup)**. **Action**: Create `code/analysis/01_anova.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. Import `pandas`, `scipy.stats`, `numpy`, `statsmodels`.
- [ ] T025a_2 [US2] **Create ANOVA Script (Function)**. **Action**: In `code/analysis/01_anova.py`, implement `run_rm_anova(df)` that accepts wide-format dataframe. **Logic**: Use `statsmodels.stats.anova.anova_rm` (or equivalent) to calculate F-statistic and p-value. **DO NOT** use `scipy.stats.f_oneway`.
- [ ] T025a_3 [US2] **Create ANOVA Script (Verification)**. **Action**: In `code/analysis/01_anova.py`, add assertion that `run_rm_anova` returns a dictionary with keys `['f_stat', 'df', 'p_val', 'eta_sq']`.
- [X] T025b [US2] **Implement Partial η² Calculation**. **Action**: In `code/analysis/01_anova.py`, calculate `eta_sq = SS_effect / (SS_effect + SS_error)`.
- [X] T026 [US2] **Implement Conditional Pairwise Trigger**. **Action**: In `code/analysis/01_anova.py`, if p < 0.05, trigger pairwise t-tests (call T027a).
- [ ] T027a_1 [US2] **Create Pairwise Script (Setup)**. **Action**: Create `code/analysis/02_pairwise.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. Import `scipy.stats`, `numpy`.
- [ ] T027a_2 [US2] **Create Pairwise Script (Function)**. **Action**: In `code/analysis/02_pairwise.py`, implement `run_pairwise_tests(df)`. **Logic**: Use `scipy.stats.ttest_rel` for all pairs. Apply Bonferroni correction (`p_adj = p_raw * n_comparisons`). Calculate Cohen's d (`d = (mean1 - mean2) / pooled_std`).
- [ ] T027a_3 [US2] **Create Pairwise Script (Verification)**. **Action**: In `code/analysis/02_pairwise.py`, add assertion that `run_pairwise_tests` returns a list of dictionaries with keys `['comparison', 'p_val', 'raw_p_val', 'cohens_d']`.
- [ ] T028a_1 [US2] **Create Report Script (Setup)**. **Action**: Create `code/analysis/03_report.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. Import `json`, `pandas`.
- [ ] T028a_2 [US2] **Create Report Script (Logic)**. **Action**: In `code/analysis/03_report.py`, load results from `01_anova.py` and `02_pairwise.py`. Generate summary table schema: `{ "f_stat": float, "df": list, "n": int, "p_val": float, "eta_sq": float, "bonferroni_factor": float, "pairwise": [{ "comparison": str, "p_val": float, "raw_p_val": float, "bonferroni_factor": float, "cohens_d": float, "df_pairwise": int }] }`.
- [ ] T028a_3 [US2] **Create Report Script (Save)**. **Action**: In `code/analysis/03_report.py`, save results to `data/processed/analysis_results.json`.
- [X] T045 [US2] **MANDATORY**: Implement "Fail Loudly" Data Loader. **Action**: In `code/analysis/01_preprocess.py` (T024a_1), if `data/raw/submissions.csv` is missing/empty, raise `FileNotFoundError` with message "No real data found. Please collect real participant data before running analysis." **BUT**: If `MODE=development`, generate `data/processed/no_data_report.json` with message "No data found - development mode" and exit gracefully (code 0). **Do NOT** generate mock data.

**Checkpoint**: Primary hypothesis test results are generated and saved.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [ ] T032_1 [US3] **Create Mixed-Effects Script (Setup)**. **Action**: Create `code/analysis/04_mixed_effects.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. Import `statsmodels.formula.api`, `pandas`.
- [ ] T032_2 [US3] **Create Mixed-Effects Script (Model)**. **Action**: In `code/analysis/04_mixed_effects.py`, implement `run_lmm(df)`. **Formula**: `credibility ~ condition + age + education + (1|participant_id)`. Use `statsmodels` or `linearmodels`. **Note**: Ensure `participant_id` (from T022a/T024) is used as grouping variable.
- [ ] T032_3 [US3] **Create Mixed-Effects Script (Convergence)**. **Action**: In `code/analysis/04_mixed_effects.py`, implement convergence check. If model fails to converge, log warning to `data/processed/mixed_effects_warnings.log` and set `convergence_failed: true` in output. **Note**: This addresses T047, moving it to Phase 6.
- [X] T033 [US3] **Execute Mixed-Effects Model**. **Action**: Run `python code/analysis/04_mixed_effects.py`. Verify output.
- [ ] T035_1 [US3] **Create Robustness Report Script (Setup)**. **Action**: Create `code/analysis/05_robustness_report.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. Import `json`, `pandas`.
- [ ] T035_2 [US3] **Create Robustness Report Script (Logic)**. **Action**: In `code/analysis/05_robustness_report.py`, compare ANOVA results (from T028a) with LMM results (from T032). **Logic**: 'consistent' if condition coefficient p-value < 0.05 in LMM and magnitude difference < 10%, else 'divergent'.
- [ ] T035_3 [US3] **Create Robustness Report Script (Save)**. **Action**: In `code/analysis/05_robustness_report.py`, save to `data/processed/robustness_results.json`. Schema: `{ "anova_f": float, "anova_p": float, "lmm_condition_coef": float, "lmm_condition_p": float, "r_squared_change": float, "coef_magnitude_diff": float, "comparison": "consistent" | "divergent" }`.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [P] T038 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py`. **Function**: `test_latin_square_sequences_are_valid()`. **Assertion**: `len(sequences) == 4` and `all(len(s) == 4)`.
- [P] T039 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`.
- [P] T040 [P] Add contract test for CSV schema validation (including hashed IP and flags) in `tests/contract/test_csv_schema.py`.
- [P] T041 Update `README.md` with setup instructions and execution order
- [P] T042 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [ ] T046a [US2] **Create Power Analysis Script**. **Action**: Create `code/analysis/06_power_analysis.py`. **Action**: Insert `numpy.random.seed(42)` and `random.seed(42)` at lines 1-2. **Input**: If `data/raw/submissions.csv` exists, use real data. Else, use `data/processed/mock_data.csv` (from T043a) for benchmarking. **Logic**: Calculate minimum detectable effect size for N=250. **Output Schema**: `{ "n": int, "alpha": float, "power": float, "min_effect_size": float, "observed_variance": float, "input_source": "real" | "mock" }`. <!-- FAILED: unspecified -->
- [ ] T046b [US2] **Execute Power Analysis**. **Action**: Run `python code/analysis/06_power_analysis.py`. **Verification**: Assert `data/processed/power_analysis.json` exists and matches schema. **Note**: This is MANDATORY before final reporting. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [P] T043a [P] Generate mock data for benchmarking: Create a script `code/utils/generate_mock_data.py` to generate a synthetic `data/raw/submissions.csv` with N=250 participants. **Schema**: `participant_id` (UUID), `stimulus_id` (categorical), `credibility` (int 1-7), `professionalism` (int 1-7), `timestamp`, `hashed_ip` (SHA256), `age` (int 18-80), `education` (int 1-4), `duplicate_flag` (int 0/1). **Distribution**: Uniform distribution for stimuli, normal distribution for ratings (mean=4, std=1.5) with clamping to 1-7.
- [P] T043b [P] Verify runtime benchmark: Create `tests/benchmark/test_runtime.py` that asserts the full analysis pipeline (T024-T036) completes within 30 minutes on a CPU-only runner using the mock data from T043a.
- [P] T043c [P] Verify file size: Add assertion in `tests/benchmark/test_runtime.py` that `data/raw/submissions.csv` size < 5MB for N=250.
- [P] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md` documenting the exact steps for data collection, cleaning, and analysis to ensure reproducibility by external researchers. This addresses the need for clear documentation of the research pipeline.

**Checkpoint**: Polish and validation tasks complete.

---

## Phase 8: Revision & Validation (Post-Analysis Fixes)

**Purpose**: Address specific reviewer concerns from the initial analysis pass regarding data integrity and statistical rigor.

### Implementation for Revision Concerns

- [P] T048 [US1] Add data export validation in `code/survey/app.py`. **Action**: Before appending to `data/raw/submissions.csv`, verify that the `participant_id` is a valid UUID v4 and that `credibility`/`professionalism` ratings are integers between 1 and 7. Reject and log invalid rows to `data/raw/rejected_rows.csv` instead of corrupting the main dataset.
- [P] T049 [US2/US3] Implement result reproducibility verification in `tests/unit/test_reproducibility.py`. **Action**: Run the full analysis pipeline twice with the same seed and verify that `analysis_results.json` and `robustness_results.json` are byte-identical. Assert that `numpy.random.seed` and `random.seed` are correctly applied in all scripts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US0 (P0)**: Must complete before US1 can collect data.
 - **US1 (P1)**: Must complete before US2 can analyze data.
 - **US2 (P2)**: Must complete before US3 can run robustness checks.
 - **US3 (P3)**: Depends on US2 results.
- **Polish (Phase 7)**: Depends on all desired user stories being complete
- **Revision (Phase 8)**: Depends on Phase 7 completion and initial analysis pass

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational. Blocks US1.
- **User Story 1 (P1)**: Can start after US0. Blocks US2.
- **User Story 2 (P2)**: Can start after US1. Blocks US3.
- **User Story 3 (P3)**: Can start after US2.

### Within Each User Story

- Models/Helpers before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks (T005-T008) marked [P] can run in parallel (creating the 4 stimulus HTML files).
- All tests for a user story marked [P] can run in parallel.

### Specific Artifact Flow

- **T023f_heartbeat** (Phase 4) -> **T024b** (Phase 5): T024b depends on the session flags generated by T023f_heartbeat.
- **T022a** (Phase 4) -> **T024b** (Phase 5): T024b depends on the `participant_id` generated by T022a.
- **T022h** (Phase 4) -> **T024b** (Phase 5): T024b depends on the CSV export generated by T022h.
- **T024a** (Phase 5) -> **T024b** (Phase 5): T024b depends on the script created by T024a.
- **T024b** (Phase 5) -> **T025a/T027a** (Phase 5): T025a/T027a depend on `data/processed/cleaned_data.csv` produced by T024b.
- **T032** (Phase 6) -> **T035** (Phase 6): T035 depends on LMM results from T032.
- **T046a** (Phase 7) -> **T046b** (Phase 7): T046b depends on script from T046a.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All analysis tasks must run on CPU-only runners (no GPU, no 8-bit quantization).
- **Critical Constraint**: No fake data generation; all analysis must use real data from `data/raw/`.
- **Critical Constraint**: IP addresses must be hashed immediately; raw IPs are strictly forbidden in storage.
- **Critical Constraint**: Session flags (timeout, status) must be generated in Phase 4 via heartbeat (T023f_heartbeat) to support filtering in Phase 5.
- **Critical Constraint**: No client-side storage (localStorage/sessionStorage) for PII or partial data (except as explicitly allowed for retry in T020).
- **Critical Constraint**: All stimuli and consent content must be generated inline or version-controlled within the repository; no external file dependencies.
- **Critical Constraint**: `participant_id` (UUID) must be generated at session start (T022a) and preserved in all CSV outputs (T022h) and reshaped datasets (T024) to enable Mixed-Effects modeling.
- **Critical Constraint**: Session timeout must be detected via `st.on_change` heartbeat mechanism (T023f_heartbeat), not browser close events.
- **Critical Constraint**: IRB consent file must be a template with a placeholder marker; actual text must be inserted from an external approved protocol (T011e).
- **Critical Constraint**: Data loaders must fail loudly on missing real data; no synthetic fallbacks allowed (T045).
- **Critical Constraint**: Statistical power must be validated before drawing conclusions (T046a/T046b is MANDATORY).
- **Critical Constraint**: Model convergence must be explicitly checked and reported (T032_3).
- **Reproducibility Checkpoint**: The Plan's Constitution Check lists Principle I (Reproducibility) as "PASS". This status is contingent upon the successful completion of T025a_1, T027a_1, T028a_1, T032_1, and T035_1 (seed pinning steps).