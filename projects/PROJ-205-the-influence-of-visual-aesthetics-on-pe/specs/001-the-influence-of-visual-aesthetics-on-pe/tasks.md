# Tasks: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

**Input**: Design documents from `/specs/001-visual-aesthetics-credibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per `projects/PROJ-205-.../` in `plan.md` <!-- FAILED: unspecified -->
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/stimuli/text_content.txt` with the fixed neutral text source (source: paste content from `docs/NEUTRAL_TEXT_V1.txt`) <!-- FAILED: unspecified -->
- [X] T005 [P] Create `code/stimuli/professional.html` (High-fidelity CSS, serif fonts, balanced layout; source: `docs/STIMULI_DESIGN_V1.json`)
- [X] T006 [P] Create `code/stimuli/minimalist.html` (Low-fidelity CSS, sans-serif, sparse layout; source: `docs/STIMULI_DESIGN_V1.json`)
- [X] T007 [P] Create `code/stimuli/low_quality.html` (Broken CSS, mismatched fonts, cluttered layout; source: `docs/STIMULI_DESIGN_V1.json`)
- [X] T008 [P] Create `code/stimuli/neutral.html` (Standard default browser styling, plain text; source: `docs/STIMULI_DESIGN_V1.json`)
- [ ] T009 Setup `data/raw/` and `data/processed/` directory structure
- [X] T010 Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function)
- [ ] T011b [US0] Create `data/consent/irb_approved.txt` with the full, verbatim IRB-approved consent text (source: paste content from `docs/IRB_PROTO_V1.txt`) <!-- FAILED: unspecified -->
- [~] T011c [US0] Define `IRB_PROTOCOL_ID` environment variable and ensure it is captured in every consent log entry (Constitution Principle VI compliance)
- [ ] T011 [US0] Configure environment variables to point to `data/consent/irb_approved.txt` for the consent form source
- [ ] T011a [US0] Implement verification logic to validate `docs/IRB_PROTO_V1.txt` content against the `IRB_PROTOCOL_ID` before use

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Informed Consent Workflow (Priority: P0) 🛡️

**Goal**: Present IRB-approved Informed Consent and block access until accepted.

**Independent Test**: Simulate a new user session; verify consent form appears, survey is blocked, and a consent record is logged upon "I Agree".

### Implementation for User Story 0

- [~] T012 [US0] Implement consent modal in `code/survey/app.py` displaying IRB text from `data/consent/irb_approved.txt` and including the `IRB_PROTOCOL_ID` in the header
- [X] T013 [US0] Implement "I Agree" / "I Do Not Agree" logic in `code/survey/app.py`
- [X] T014 [US0] Create consent logging function in `code/utils/helpers.py` to write `consent_log.csv` (timestamp, user_id, decision, IRB_PROTOCOL_ID)
- [~] T015 [US0] Implement redirect logic to withdrawal page on "I Do Not Agree"

**Checkpoint**: User Story 0 is functional; no data collection can occur without consent.

---

## Phase 4: User Story 1 - Participant Survey Data Collection (Priority: P1) 🎯 MVP

**Goal**: Deliver 4 stimuli in Latin Square order, collect 8 ratings, and export CSV.

**Independent Test**: Simulate a participant session; verify 4 stimuli load in a valid sequence, 8 ratings are captured, and the CSV export contains all fields.

### Implementation for User Story 1

- [X] T016a [US1] Define the EXACT 4 Latin Square sequences as a hardcoded constant list in `code/survey/app.py` (DO NOT generate). The list MUST contain exactly these tuples:
 1. ["Professional", "Minimalist", "Low-Quality", "Neutral"]
 2. ["Minimalist", "Low-Quality", "Neutral", "Professional"]
 3. ["Low-Quality", "Neutral", "Professional", "Minimalist"]
 4. ["Neutral", "Professional", "Minimalist", "Low-Quality"]
- [X] T016b [US1] Implement random selection logic in `code/survey/app.py` that selects ONE sequence from the hardcoded list in T016a per participant (strict lookup, no generative algorithm)
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py` to display HTML files sequentially
- [X] T018 [US1] Create 7-point Likert rating inputs for Credibility and Professionalism in `code/survey/app.py`
- [~] T019 [US1] Implement validation logic to block submission if < 8 ratings are present (FR-008)
- [~] T020 [US1] Implement client-side state management: Use **in-memory only** (Streamlit session state) to track progress. **FORBIDDEN**: Do NOT use `sessionStorage`, `localStorage`, or cookies to store partial ratings or PII. Implement logic to clear all in-memory state immediately upon successful submission or user abandonment to ensure no PII persists on the client device (Constitution Principle III & VI). **Exception**: Allow `sessionStorage` for partial data retry ONLY if network failure is detected (Spec Edge Case #3). Define 'user abandonment' as 'session state expiration' and 'successful submission' as 'Streamlit form submit event'.
- [X] T021 [US1] Implement submission handler to record Participant ID, Stimulus Condition, Ratings, Timestamp, Device Info in `code/survey/app.py`
- [ ] T022 [US1] Implement CSV export logic to append to `data/raw/submissions.csv` using `helpers.py`
- [X] T023a [US1] Implement raw IP address capture in `code/survey/app.py` (capture from request headers into a volatile variable ONLY)
- [X] T023b [US1] Implement immediate IP hashing in `code/survey/app.py`: Call `helpers.hash_ip()` on the raw IP variable immediately upon capture. **NEVER** write the raw IP to disk, logs, or the CSV. Write ONLY the hashed value.
- [ ] T023c [US1] Implement duplicate flagging: Check if the hashed IP exists in previous submissions. Write the hashed IP and a `duplicate_flag` to `data/raw/submissions.csv`.
- [ ] T023d_ui [US1] Render the demographic input form in `code/survey/app.py`: Implement a dropdown for Education with options: [High School, Bachelor's, Master's, PhD] and a number input for Age (years). Ensure validation enforces the ordinal structure.
- [ ] T023d [US1] Implement demographic data collection: Write Age (integer) and Education (integer code 1-4) to `data/raw/submissions.csv` columns, referencing data collected in T023d_ui.
- [ ] T023e_calc [US1] Implement metadata truncation calculation: Calculate the maximum safe `user_agent` truncation length to ensure `data/raw/submissions.csv` remains < 5MB for N=250. Implement a runtime check and fallback mechanism (truncation or warning) if the limit is exceeded.
- [ ] T023e [US1] Implement metadata truncation: Truncate `user_agent` strings to the calculated length from T023e_calc. Exclude large binary blobs. Ensure `data/raw/submissions.csv` remains < 5MB (SC-005).
- [~] T023f [US1] Implement session state flagging logic: detect 'browser close' (missing timestamp) and 'network failure' (partial submission) and write `session_timeout` and `submission_status` flags to CSV. Mark partial records as `submission_status='excluded'` to ensure they are not retained for analysis.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [~] T024 [US2] Create `code/analysis/01_preprocess.py` to load `data/raw/submissions.csv`. Filter rows where: `submission_status != 'complete'` OR `session_timeout == true` OR `rating_count < 8`. Log all excluded rows to `data/processed/excluded_audit.csv` for transparency. Reshape valid data to wide format for ANOVA.
- [X] T025 [US2] Implement Repeated-Measures ANOVA in `code/analysis/01_anova.py` (factor: design condition, DV: credibility)
- [ ] T026 [US2] Implement partial η² calculation in `code/analysis/01_anova.py`
- [ ] T027 [US2] Implement conditional logic in `code/analysis/01_anova.py`: if p < 0.05, trigger pairwise t-tests
- [ ] T028 [US2] Implement Bonferroni-corrected pairwise t-tests in `code/analysis/02_pairwise.py` (comparisons)
- [ ] T029 [US2] Implement Cohen's d calculation for pairwise comparisons in `code/analysis/02_pairwise.py`
- [ ] T030 [US2] Create `code/analysis/03_report.py` to generate a summary table (F-stat, df, p, η², pairwise p-values, effect sizes) and save to `data/processed/analysis_results.json`
- [ ] T031 [US2] Add seed pinning to ALL analysis scripts: `numpy.random.seed`, `random.seed`, `statsmodels` (via global numpy seed), and `scipy` optimization parameters. Ensure reproducibility for Mixed-Effects models (US-3) and ANOVA.

**Checkpoint**: Primary hypothesis test results are generated and saved.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [ ] T032 [US3] Create `code/analysis/04_mixed_effects.py` to load `data/processed/` data including demographic columns (Age, Education) collected in T023d
- [ ] T033 [US3] Implement Mixed-Effects Linear Model (LMM) in `code/analysis/04_mixed_effects.py` with fixed effects: condition, age, education; random intercept: participant_id
- [ ] T034 [US3] Implement convergence check and warning handling in `code/analysis/04_mixed_effects.py` (Depends on T023d for demographic data)
- [ ] T035 [US3] Generate robustness report comparing Mixed-Effects coefficients to ANOVA results in `code/analysis/05_robustness_report.py`
- [ ] T036 [US3] Save robustness results to `data/processed/robustness_results.json`

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py` (Verify only the 4 specific sequences are used)
- [ ] T038 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`
- [ ] T039 [P] Add contract test for CSV schema validation (including hashed IP and flags) in `tests/contract/test_csv_schema.py`
- [ ] T040 Update `README.md` with setup instructions and execution order
- [ ] T041 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [ ] T042 Verify all analysis scripts complete within 30 minutes on CPU-only runner (mock N=250) AND verify `data/raw/submissions.csv` size < 5MB for N=250

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
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
- **Critical Constraint**: Session flags (timeout, status) must be generated in Phase 4 to support filtering in Phase 5.
- **Critical Constraint**: No client-side storage (localStorage/sessionStorage) for PII or partial data (except as explicitly allowed for retry in T020).