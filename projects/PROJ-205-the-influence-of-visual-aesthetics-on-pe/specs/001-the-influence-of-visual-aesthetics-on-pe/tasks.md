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
- [X] T005 [P] Create `code/stimuli/professional.html`. **Design**: High-fidelity CSS, serif fonts (Georgia/Times New Roman), balanced layout, professional color palette (navy #003366, white #FFFFFF, gray #F0F0F0), clean typography, no clutter. **CSS Rules**: `body { font-family: Georgia, serif; background: #FFFFFF; color: #333333; } h1 { color: #003366; } .container { max-width: 800px; margin: 0 auto; padding: 20px; }`.
- [X] T006 [P] Create `code/stimuli/minimalist.html`. **Design**: Low-fidelity CSS, sans-serif fonts (Arial/Helvetica), sparse layout, high contrast black (#000000) / white (#FFFFFF), minimal decoration, simple structure, no images. **CSS Rules**: `body { font-family: Arial, sans-serif; background: #FFFFFF; color: #000000; } h1 { font-weight: normal; } .container { max-width: 600px; margin: 0 auto; }`.
- [X] T007 [P] Create `code/stimuli/low_quality.html`. **Design**: Broken CSS, mismatched fonts (Comic Sans MS / Times New Roman mix), cluttered layout, jarring colors (neon green #39FF14, red #FF0000), broken alignment, visual noise, overlapping elements. **CSS Rules**: `body { font-family: 'Comic Sans MS', 'Times New Roman', serif; background: #000000; color: #39FF14; } h1 { color: #FF0000; font-size: 40px; } .container { margin: -20px; }`.
- [X] T008 [P] Create `code/stimuli/neutral.html`. **Design**: Standard default browser styling, plain text, no custom CSS, minimal formatting, Times New Roman, black text on white background. **CSS Rules**: No custom CSS file; relies on browser defaults.
- [X] T009 Setup `data/raw/` and `data/processed/` directory structure. Execute: `touch data/raw/.gitkeep data/processed/.gitkeep`
- [X] T010 Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function)
- [X] T011a [US0] Create `data/consent/irb_approved.txt` as a **template structure**. **Action**: Write a file containing the following sections as placeholders: `# Introduction`, `# Risks`, `# Benefits`, `# Confidentiality`, `# Consent Checkbox`. Include a header comment explaining that the actual IRB-approved text must be manually inserted from an external approved protocol before production use. **Do NOT** generate legal text or simulate approval.
- [X] T011b [US0] Define `IRB_PROTOCOL_ID` environment variable and ensure it is captured in every consent log entry (Constitution Principle VI compliance).
- [X] T011c [US0] Configure environment variables to point to `data/consent/irb_approved.txt` for the consent form source.
- [X] T011d [US0] Implement verification logic in `code/survey/app.py` to validate `data/consent/irb_approved.txt`. **Action**: Check if the file contains `<<INSERT_IRB_APPROVED_TEXT_HERE>>`. If found and `MODE=production`, raise a fatal error (fail loudly). If `MODE=development`, log a warning and allow execution for testing purposes.
- [X] T023f_heartbeat [US1] Implement session timeout detection in `code/survey/app.py`: Use `st.on_change` on a hidden widget or form to update `st.session_state.last_active` with `time.time()`. On page load or widget interaction, check if `time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD` (e.g., 30 mins). If exceeded, set `session_status='timeout'` and `submission_status='incomplete'` in the session state. If the user submits successfully before timeout, set `submission_status='complete'` and `session_status='active'`. **This mechanism generates the flags used in T024.**
- [X] T031 [P] Add seed pinning to ALL analysis scripts: `numpy.random.seed(42)`, `random.seed(42)` at the top of `01_anova.py`, `02_pairwise.py`, `03_report.py`, `04_mixed_effects.py`, and `05_robustness_report.py`. **Note**: Moved to Phase 2 to ensure reproducibility before any analysis logic is written.
- [X] T045 [P] Implement "Fail Loudly" data loader in `code/analysis/01_preprocess.py`. **Action**: If `data/raw/submissions.csv` is missing or empty, raise a `FileNotFoundError` with a clear message: "No real data found. Please collect real participant data before running analysis." **BUT**: If `MODE=development` is set, generate a `data/processed/no_data_report.json` with a message "No data found - development mode" and exit gracefully (do not crash). **Do NOT** generate mock data.

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

**Goal**: Deliver 4 stimuli in Latin Square order, collect 8 ratings, and export CSV.

**Independent Test**: Simulate a participant session; verify 4 stimuli load in a valid sequence, 8 ratings are captured, and the CSV export contains all fields.

### Implementation for User Story 1

- [X] T016a [US1] Define the Latin Square sequences as a hardcoded constant list in `code/survey/app.py`. The list MUST contain exactly these tuples (verified as a valid Latin Square for 4 conditions):
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
- [X] T022b [US1] Implement raw IP address capture in `code/survey/app.py`: Use `st.context.headers.get('X-Forwarded-For')` or `st.experimental_request.headers.get('X-Forwarded-For')` to capture the IP. **Action**: If the IP cannot be captured via either method, the session MUST be rejected (display an error and terminate the session) to comply with the 'IP hashing mandatory' requirement. Do not proceed without an IP.
- [X] T022c [US1] Implement immediate IP hashing in `code/survey/app.py`: Call `helpers.hash_ip()` on the raw IP variable immediately upon capture. **NEVER** write the raw IP to disk, logs, or the CSV. Write ONLY the hashed value.
- [X] T022d [US1] Implement duplicate flagging: Check if the hashed IP exists in `data/raw/submissions.csv` (read file). Write `1` if duplicate, `0` if unique to the `duplicate_flag` column. **Note**: This check is for audit purposes only; hashed IPs are NOT stored as persistent identifiers for re-identification.
- [X] T022e_ui [US1] Render the demographic input form in `code/survey/app.py`: Implement a dropdown for Education with options: [High School, Bachelor's, Master's, PhD] and a number input for Age (years). Ensure validation enforces the ordinal structure.
- [X] T022f [US1] Implement demographic data collection: Write Age (integer) and Education (integer code 1-4) to `data/raw/submissions.csv` columns. **Mapping**: 1=High School, 2=Bachelor's, 3=Master's, 4=PhD. Reference data collected in T022e_ui.
- [X] T022g [US1] Implement metadata truncation: Truncate `user_agent` strings to a fixed safe length (255 chars) to prevent excessively long entries. Exclude large binary blobs. Ensure `data/raw/submissions.csv` remains manageable.
- [X] T022h [US1] Implement CSV export logic to append to `data/raw/submissions.csv`. **Schema**: `participant_id, stimulus_id, credibility, professionalism, timestamp, hashed_ip, age, education, duplicate_flag, session_status, submission_status`. **Action**: 
  1. Read current session flags from `st.session_state` (`session_status`, `submission_status`).
  2. Iterate through the `st.session_state.ratings` list (which contains one entry per stimulus).
  3. For EACH entry, write ONE ROW to the CSV containing the `participant_id`, the specific `stimulus_id` (e.g., "Professional"), the ratings, and the session flags.
  **Note**: This long-format structure (multiple rows per participant) is critical for the Repeated-Measures ANOVA in US2.
- [X] T028d [US1] Implement post-hoc duplicate detection in `code/survey/app.py` or a separate script. **Action**: After data collection, read `data/raw/submissions.csv` and flag any rows where `hashed_ip` appears more than once. Log these to `data/raw/duplicate_audit.csv`. **Do NOT** perform this check in real-time during submission to avoid race conditions and PII persistence concerns.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [X] T024 [US2] Create `code/analysis/01_preprocess.py` to load `data/raw/submissions.csv`. Filter rows where: `submission_status != 'complete'` OR `session_status == 'timeout'` (flags generated by **T023f_heartbeat**). **Justification**: This filtering is a necessary data quality gate to ensure the Repeated-Measures ANOVA (US2) is run only on complete, valid sessions, preventing bias from incomplete data. Log all excluded rows to `data/processed/excluded_audit.csv` for transparency. **Reshape valid data to wide format** using `participant_id` (from **T022a**) as the index. **Output**: Save as `data/processed/cleaned_data.csv`. **Schema**: `participant_id, age, education, credibility_Professional, credibility_Minimalist, credibility_Low-Quality, credibility_Neutral, professionalism_Professional, ...`. **Note**: Ensure `participant_id` is preserved as the index/column for downstream Mixed-Effects models.
- [X] T025a [US2] Create `code/analysis/01_anova.py`. **Action**: Import `pandas`, `scipy.stats`, `numpy`, `statsmodels`. Load `data/processed/cleaned_data.csv`.
- [X] T025b [US2] Implement Repeated-Measures ANOVA in `code/analysis/01_anova.py`. **Action**: Use `statsmodels.stats.anova.anova_rm` (or equivalent repeated-measures implementation) to calculate F-statistic and p-value for the effect of condition on credibility. **DO NOT** use `scipy.stats.f_oneway` (one-way ANOVA) as it is statistically invalid for within-subjects data.
- [X] T025c [US2] Implement partial η² calculation in `code/analysis/01_anova.py`. **Action**: Calculate effect size using `eta_sq = SS_effect / (SS_effect + SS_error)`.
- [X] T026 [US2] Implement conditional logic in `code/analysis/01_anova.py`: if p < 0.05, trigger pairwise t-tests
- [X] T027a [US2] Create `code/analysis/02_pairwise.py`. **Action**: Import `scipy.stats`, `numpy`. Load `data/processed/cleaned_data.csv`.
- [X] T027b [US2] Implement Bonferroni-corrected pairwise t-tests in `code/analysis/02_pairwise.py`. **Action**: Use `scipy.stats.ttest_rel` for all pairs. Apply Bonferroni correction to p-values (`p_adj = p_raw * n_comparisons`).
- [X] T027c [US2] Implement Cohen's d calculation for pairwise comparisons in `code/analysis/02_pairwise.py`. **Action**: Calculate `d = (mean1 - mean2) / pooled_std`.
- [X] T028a [US2] Create `code/analysis/03_report.py`. **Action**: Import `json`, `pandas`. Load results from `01_anova.py` and `02_pairwise.py`.
- [X] T028b [US2] Generate a summary table in `code/analysis/03_report.py`. **Schema**: `{ "f_stat": float, "df": list, "n": int, "p_val": float, "eta_sq": float, "bonferroni_factor": float, "pairwise": [{ "comparison": str, "p_val": float, "raw_p_val": float, "bonferroni_factor": float, "cohens_d": float, "df_pairwise": int }] }`.
- [X] T028c [US2] Save results to `data/processed/analysis_results.json`. **Action**: Write the summary table JSON to file.

**Checkpoint**: Primary hypothesis test results are generated and saved.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [X] T032 [US3] Create `code/analysis/04_mixed_effects.py`. **Action**: Import `statsmodels.formula.api`, `pandas`. Load `data/processed/cleaned_data.csv`. **Ensure `participant_id` (generated in T022a and preserved in T024) is used as the grouping variable.**
- [X] T033 [US3] Implement Mixed-Effects Linear Model (LMM) in `code/analysis/04_mixed_effects.py`. **Action**: Define formula `credibility ~ condition + age + education + (1|participant_id)`. Use `statsmodels` or `linearmodels` to fit the model.
- [X] T034 [US3] Implement convergence check and warning handling in `code/analysis/04_mixed_effects.py`. **Action**: Log warnings to `data/processed/mixed_effects_warnings.log`.
- [X] T035 [US3] Generate robustness report comparing Mixed-Effects coefficients to ANOVA results in `code/analysis/05_robustness_report.py`. **Action**: Compare `condition` coefficient and p-value. **Logic**: The comparison is 'consistent' if the condition coefficient p-value remains < 0.05 in the Mixed-Effects model and the magnitude difference is < 10%, otherwise 'divergent'.
- [X] T036 [US3] Save robustness results to `data/processed/robustness_results.json`. **Schema**: `{ "anova_f": float, "anova_p": float, "lmm_condition_coef": float, "lmm_condition_p": float, "r_squared_change": float, "coef_magnitude_diff": float, "comparison": "consistent" | "divergent" }`.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py`. **Function**: `test_latin_square_sequences_are_valid()`. **Assertion**: `len(sequences) == 4` and `all(len(s) == 4)`.
- [X] T039 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`.
- [X] T040 [P] Add contract test for CSV schema validation (including hashed IP and flags) in `tests/contract/test_csv_schema.py`.
- [X] T041 Update `README.md` with setup instructions and execution order
- [X] T042 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [X] T043a [P] Generate mock data for benchmarking: Create a script to generate a synthetic `data/raw/submissions.csv` with N=250 participants and specific distribution to test performance. **Action**: Use `numpy.random` with fixed seeds to generate ratings and demographics.
- [X] T043b [P] Verify all analysis scripts complete within 30 minutes on CPU-only runner (mock N=250) AND verify `data/raw/submissions.csv` size < 5MB for N=250. **Action**: Create `tests/benchmark/test_runtime.py` that asserts runtime < 30m.
- [X] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md` documenting the exact steps for data collection, cleaning, and analysis to ensure reproducibility by external researchers. This addresses the need for clear documentation of the research pipeline.
- [X] T046 [Optional] [US2] Implement statistical power analysis in `code/analysis/06_power_analysis.py`. **Action**: Calculate the minimum detectable effect size for the target N=250 given observed variance (or simulated variance based on literature values if real data is not available). Save results to `data/processed/power_analysis.json` to validate the study's ability to detect meaningful effects. **Note**: This is a post-hoc analysis or simulation; it is not a prerequisite for data collection.

---

## Phase 8: Revision & Validation (Post-Analysis Fixes)

**Purpose**: Address specific reviewer concerns from the initial analysis pass regarding data integrity and statistical rigor.

### Implementation for Revision Concerns

- [X] T047 [US3] Enhance Mixed-Effects model robustness check in `code/analysis/04_mixed_effects.py`. **Action**: Add a check for model convergence warnings. If the model fails to converge, log a warning to `data/processed/mixed_effects_warnings.log` and output a flag `convergence_failed: true` in `robustness_results.json`. Do not silently proceed with a failed model.
- [X] T048 [US1] Add data export validation in `code/survey/app.py`. **Action**: Before appending to `data/raw/submissions.csv`, verify that the `participant_id` is a valid UUID v4 and that `credibility`/`professionalism` ratings are integers between 1 and 7. Reject and log invalid rows to `data/raw/rejected_rows.csv` instead of corrupting the main dataset.
- [X] T049 [US2/US3] Implement result reproducibility verification in `tests/unit/test_reproducibility.py`. **Action**: Run the full analysis pipeline twice with the same seed and verify that `analysis_results.json` and `robustness_results.json` are byte-identical. Assert that `numpy.random.seed` and `random.seed` are correctly applied in all scripts.

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

- **T023f_heartbeat** (Phase 2) -> **T024** (Phase 5): T024 depends on the session flags generated by T023f_heartbeat.
- **T022a** (Phase 4) -> **T024** (Phase 5): T024 depends on the `participant_id` generated by T022a.
- **T022h** (Phase 4) -> **T024** (Phase 5): T024 depends on the CSV export generated by T022h.
- **T031** (Phase 2) -> **All Analysis Scripts**: Seed pinning must be applied before any analysis logic is written.
- **T045** (Phase 2) -> **T024** (Phase 5): T024 depends on the "Fail Loudly" logic implemented in T045.

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
- **Critical Constraint**: Session flags (timeout, status) must be generated in Phase 2 via heartbeat (T023f_heartbeat) to support filtering in Phase 5.
- **Critical Constraint**: No client-side storage (localStorage/sessionStorage) for PII or partial data (except as explicitly allowed for retry in T020).
- **Critical Constraint**: All stimuli and consent content must be generated inline or version-controlled within the repository; no external file dependencies.
- **Critical Constraint**: `participant_id` (UUID) must be generated at session start (T022a) and preserved in all CSV outputs (T022h) and reshaped datasets (T024) to enable Mixed-Effects modeling.
- **Critical Constraint**: Session timeout must be detected via `st.on_change` heartbeat mechanism (T023f_heartbeat), not browser close events.
- **Critical Constraint**: IRB consent file must be a template with a placeholder marker; actual text must be inserted from an external approved protocol.
- **Critical Constraint**: Data loaders must fail loudly on missing real data; no synthetic fallbacks allowed (T045).
- **Critical Constraint**: Statistical power must be validated before drawing conclusions (T046).
- **Critical Constraint**: Model convergence must be explicitly checked and reported (T047).