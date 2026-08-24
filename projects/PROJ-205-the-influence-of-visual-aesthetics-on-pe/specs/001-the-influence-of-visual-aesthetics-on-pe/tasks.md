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
- [X] T011d [US0] Implement verification logic in `code/survey/app.py` to validate `data/consent/irb_approved.txt`. **Action**: Check if the file contains `<<INSERT_IRB_APPROVED_TEXT_HERE>>`. If found and `MODE=production`, raise a fatal error (fail loudly). If `MODE=development`, log a warning and allow execution for testing purposes.
- [X] T011e [US0] **MANDATORY**: Insert IRB-approved Text. **Action**: Before any production data collection, manually replace the placeholder in `data/consent/irb_approved.txt` with the actual IRB-approved text. **Verification Gate**: The system MUST implement a strict check in `code/survey/app.py` that raises a fatal error if the file contains the placeholder AND `MODE=production`. This task must be marked complete before US0 can be considered "Production Ready". **Note**: This is a manual administrative step. The system must not run data collection without this verification.

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
- [X] T022b [US1] Implement IP extraction, hashing, and session rejection logic in `code/survey/app.py`: Extract IP using `st.context.headers.get('X-Forwarded-For')`. If missing in production, display error and call `st.stop()`. Hash the IP with `helpers.hash_ip()` immediately after extraction. **This single task covers both extraction and rejection.**
- [X] T022c [US1] Implement demographic input form in `code/survey/app.py`: Implement a dropdown for Education with options: [High School, Bachelor's, Master's, PhD] and a number input for Age (years). Ensure validation enforces the ordinal structure.
- [ ] T022d [US1] Implement demographic data collection: Write Age (integer) and Education (integer code) to `data/raw/submissions.csv` columns. **Mapping**: High School, Bachelor's, Master's, PhD. Reference data collected in the UI.
- [X] T022e_ui [US1] Render the demographic input form in `code/survey/app.py`: Implement a dropdown for Education with options: [High School, Bachelor's, Master's, PhD] and a number input for Age (years). Ensure validation enforces the ordinal structure.
- [X] T022f [US1] Implement metadata truncation: Truncate `user_agent` strings to a maximum length suitable for standard database fields.
- [ ] T022g [US1] Implement CSV export logic to append to `data/raw/submissions.csv`. **Schema**: `participant_id, stimulus_id, credibility, professionalism, timestamp, hashed_ip, age, education, duplicate_flag, session_status, submission_status`. **Constraint**: Truncate `user_agent` to 255 characters before writing.
- [ ] T022h [US1] Implement post-hoc duplicate detection in `code/survey/app.py` or a separate script. **Action**: After data collection, read `data/raw/submissions.csv` and flag any rows where `hashed_ip` appears more than once. Log these to `data/raw/duplicate_audit.csv`.
- [X] T023f_heartbeat [US1] Implement session timeout detection in `code/survey/app.py`: Use `st.on_change` on a hidden widget or form to update `st.session_state.last_active` with `time.time()`. On page load or widget interaction, check if `time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD` (e.g., a configurable session timeout duration). If exceeded, set `session_status='timeout'` and `submission_status='incomplete'` in the session state.
- [X] T028e [US1] Implement Latin Square sequences as a hardcoded constant list.
- [X] T016a [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square for 4 conditions.
- [X] T016b [US1] Implement random selection logic.
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py` to display HTML files sequentially
- [X] T018 [US1] Create multi-point Likert rating inputs for Credibility and Professionalism in `code/survey/app.py`
- [X] T019 [US1] Implement validation logic to block submission if < 8 ratings are present.
- [X] T020 [US1] Implement client-side state management: Use **in-memory only** (Streamlit session state) to track progress.
- [X] T021 [US1] Implement submission handler to record Participant ID, Stimulus Condition, Ratings, Timestamp, Device Info in `code/survey/app.py`

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [ ] T024a_b [US2] Create and execute preprocess script to load data, filter complete sessions, audit excluded rows, and reshape the dataframe into wide format (`data/processed/cleaned_data.csv`). **Artifact**: `data/processed/cleaned_data.csv` must be generated.
- [X] T025a_b [US2] Create and execute ANOVA script using `statsmodels` to calculate F-statistic, p-value, and eta squared from cleaned data. Save results to `data/processed/anova_results.json`.
- [X] T026_integrated [US2] Implement conditional pairwise t-tests if ANOVA p < 0.05 using Bonferroni correction and calculate Cohen's d with the corrected p-values.
- [X] T027a_b [US2] Create report script to generate a summary table including ANOVA results, pairwise comparisons, effect sizes, and save it as `data/processed/analysis_results.json`.
- [ ] T028d [US2] Implement post-hoc duplicate detection (Audit). **Action**: After data collection, read `data/raw/submissions.csv` and flag any rows where `hashed_ip` appears more than once. Log these to `data/raw/duplicate_audit.csv`. **Note**: Real-time flagging is removed; this is the sole duplicate detection mechanism.
- [X] T045 [US2] **Create and Execute Power Analysis Script**. Calculate minimum detectable effect size for N=250 using real or mock data.

**Checkpoint**: Preprocessing scripts ready; data analysis blocked until T024b completes.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [X] T032_33_35 [US3] Create and execute `code/analysis/04_mixed_effects.py` to run a linear mixed effects model with random intercepts, age/education as covariates, and compare the results to ANOVA findings. Save output to `data/processed/mixed_effects_results.json`.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [P] T038 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py`.
- [P] T039 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`.
- [P] T040 [P] Add contract test for CSV schema validation (including hashed IP and flags) in `tests/contract/test_csv_schema.py`.
- [P] T041 Update `README.md` with setup instructions and execution order
- [P] T042 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [X] T043a [P] Generate mock data for benchmarking: Create a script `code/utils/generate_mock_data.py` to generate a synthetic `data/raw/submissions.csv` with N=250 participants, normal distribution (mean=4, std=1.5) for ratings and all required fields.
- [X] T043b [P] Verify runtime benchmark: Create `tests/benchmark/test_runtime.py` that asserts the full analysis pipeline completes within 30 minutes on a CPU-only runner using the mock data from T043a.
- [ ] T043c [P] Verify file size: Add assertion in `tests/benchmark/test_runtime.py` that `data/raw/submissions.csv` size < 5MB for N=250.
- [X] T046a [US2] Create and execute Power Analysis Script. **Action**: Calculate minimum detectable effect size for N=250. **Reproducibility**: Use `numpy.random.seed(42)`. **Fallback**: If mock data is missing, generate it using T043a logic or fail with a clear error message. Output must match the schema in `data/processed/power_analysis_results.json`.
- [P] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md` documenting the exact steps for data collection, cleaning, and analysis to ensure reproducibility by external researchers.

**Checkpoint**: Polish and validation tasks complete.
