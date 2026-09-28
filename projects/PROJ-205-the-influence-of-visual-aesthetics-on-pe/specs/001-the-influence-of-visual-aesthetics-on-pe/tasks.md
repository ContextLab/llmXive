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
- [X] T002 Initialize Python project with `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pyyaml, **pingouin**). **Note**: `pingouin` is required for effect size calculations in US2.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting tools. Create `.ruff.toml` with rules E, W, F, I, N, D, UP, C90, B, C4, PT, RUF, SIM, TCH, TID, ARG. Create `pypy.toml` with `[tool.black]` and `[tool.isort]` sections.
- [X] T011e_new [P] **IRB File Requirement**. **Action**: Ensure `data/consent/irb_approved.txt` exists prior to execution. This file must be provided by the researcher and contains the approved IRB text. The code in T012 will read this file. **Note**: This is a prerequisite check, not a manual insertion task.
- [X] T011h_new [P] **Implement Automated CI/CD Gate**. **Action**: Create `.github/workflows/irb_check.yml`. **Logic**: The workflow must check for the existence of `data/consent/irb_approved.txt` and fail the build if missing. **Path**: `.github/workflows/irb_check.yml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/stimuli/text_content.txt` with the fixed neutral text source. **Content**: "The rapid evolution of digital communication has fundamentally altered how individuals perceive and process information. In an era where attention spans are shrinking, the visual presentation of online content plays a critical role in establishing initial trust and credibility. This study examines the psychological mechanisms underlying these perceptions. "
- [X] T005 [P] Create `code/stimuli/professional.html`. **Design**: High-fidelity CSS, serif fonts (Georgia/Times New Roman), balanced layout, professional color palette (navy #003366, white #FFFFFF, gray #F0F0F0), clean typography, no clutter. **CSS Rules**: `body { font-family: Georgia, serif; background: #FFFFFF; color: #333333; } h1 { color: #003366; }.container { max-width: 800px; margin: 0 auto; padding: 20px; }`.
- [X] T006 [P] Create `code/stimuli/minimalist.html`. **Design**: Low-fidelity CSS, sans-serif fonts (Arial/Helvetica), sparse layout, high contrast black (#000000) / white (#FFFFFF), minimal decoration, simple structure, no images. **CSS Rules**: `body { font-family: Arial, sans-serif; background: #FFFFFF; color: #000000; } h1 { font-weight: normal; }.container { max-width: 600px; margin: 0 auto; }`.
- [X] T007 [P] Create `code/stimuli/low_quality.html`. **Design**: Broken CSS, mismatched fonts (Comic Sans MS / Times New Roman mix), cluttered layout, jarring colors (neon green #39FF14, red #FF0000), broken alignment, visual noise, overlapping elements. **CSS Rules**: `body { font-family: 'Comic Sans MS', 'Times New Roman', serif; background: #000000; color: #39FF14; } h1 { color: #FF0000; font-size: 40px; }.container { margin: -20px; }`.
- [X] T008 [P] Create `code/stimuli/neutral.html`. **Design**: Standard default browser styling, plain text, no custom CSS, minimal formatting, Times New Roman, black text on white background. **CSS Rules**: No custom CSS file; relies on browser defaults.
- [X] T009 Setup `data/raw/` and `data/processed/` directory structure. Execute: `touch data/raw/.gitkeep data/processed/.gitkeep`
- [X] T010 [P] Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function). **Note**: The salt for `hash_ip` MUST be loaded from the environment variable `IP_HASH_SALT`. The task must also create a `.env.example` file in the root with `IP_HASH_SALT=your_secure_salt_here` and a comment instructing the user to set this variable. The code must fail loudly if `IP_HASH_SALT` is not set.
- [X] T027c [US2] Create `data/processed/analysis_results.json` which aggregates the results from T025a_b and T026_integrated. Tag with [FR-002] and [US2].
- [ ] T057 [P] **Implement Data Integrity Checksums**. **Action**: Create `code/utils/checksums.py`. **Logic**: Compute a SHA-256 checksum of the `data/raw/submissions.csv` file. **Trigger**: Execute `code/utils/checksums.py` immediately after any write operation in `code/survey/app.py` that appends to `data/raw/submissions.csv`. **Verification**: Add a check in `code/analysis/00_preprocess.py` to verify the checksum of the input file before processing. If the checksum mismatches, raise a fatal error.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Informed Consent Workflow (Priority: P0) 🛡️

**Goal**: Present IRB-approved Informed Consent and block access until accepted.

**Independent Test**: Simulate a new user session; verify consent form appears, survey is blocked, and a consent record is logged upon "I Agree".

### Implementation for User Story 0

- [X] T012 [US0] Implement consent modal in `code/survey/app.py` displaying IRB text from `data/consent/irb_approved.txt` and including the `IRB_PROTOCOL_ID` in the header. **Note**: The ID must be explicitly rendered in the modal title or header text. The file `data/consent/irb_approved.txt` must exist before running.
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
- [X] T022b [US1] Implement IP extraction, hashing, and session rejection logic in `code/survey/app.py`: Extract IP using `st.context.headers.get('X-Forwarded-For')`. If missing in production, display error "Session Rejected: Unable to verify identity." and call `st.stop()`. Hash the IP with `helpers.hash_ip()` immediately after extraction.
- [X] T022c [US1] **Define Form Schema**: Define the schema for demographic input (Age, Education) and the CSV export structure in `code/survey/constants.py`.
- [X] T022d [US1] **Render Form**. **Action**: Render the demographic input form in `code/survey/app.py` using the schema defined in T022c.
- [ ] T022e [US1] **Capture Data**. **Action**: On form submission, append a row to `data/raw/submissions.csv` with columns `participant_id`, `age`, `education`, `timestamp`, `hashed_ip`.
- [X] T022f [US1] Implement metadata sanitization. **Action**: Hash the `user_agent` string using SHA-256 before writing to CSV.
- [ ] T022g_impl [US1] **Implement Export Logic**. **Action**: Implement the file handling logic in `code/utils/helpers.py` for `export_to_csv()`. **Robustness**: Use atomic writes (write to a temporary file first, then rename to `data/raw/submissions.csv`) and handle disk-full exceptions by logging an error and stopping the session.
- [X] T022g_test [US1] Verify CSV schema.
- [X] T022h [US1] Implement post-hoc duplicate detection.
- [X] T028e [US1] Implement Latin Square sequences as a hardcoded constant list in `code/survey/constants.py`.
- [X] T016a [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square.
- [X] T016b [US1] Implement balanced Latin Square selection logic.
- [X] T016c [US1] **Verify Latin Square Runtime Selection**.
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py`.
- [X] T018 [US1] Create multi-point Likert rating inputs for Credibility and Professionalism.
- [X] T019 [US1] Implement validation logic to block submission if < 4 stimuli rated.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [ ] T024a [US2] Create preprocess script `code/analysis/00_preprocess.py`. **Dependency**: This script must call the checksum verification logic from T057 before processing `data/raw/submissions.csv`.
- [X] T025a_b [US2] Create and execute ANOVA script.
- [X] T026_integrated [US2] Implement conditional pairwise t-tests. **Enforcement**: Use `argparse` with `default='bonferroni'` and **do not** expose a `--correction-method` flag. The method is hardcoded to 'bonferroni' to satisfy FR-002.
- [X] T027a_b [US2] Create report script to generate a summary table.
- [X] T026_verify [US2] Verify Statistical Output.
- [X] T033 [US3] Implement mixed effects model logic. **Formula**: `Credibility ~ Condition + Age + Education + (1|Participant)`. **Note**: Explicitly include random intercepts for participants as required by US3.
- [X] T035 [US3] Implement comparison logic and save output.

**Checkpoint**: Preprocessing scripts ready; data analysis blocked until T024a completes.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [X] T032 [US3] Create `code/analysis/03_mixed_effects.py` script.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

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

- [ ] T043a_impl [US1] **Implement Mock Data Generation**. **Action**: Generate synthetic data for testing. **Output Path**: Explicitly write to `data/raw/submissions.csv`. **Note**: This task is for testing only; real data collection is handled by the survey.
- [X] T055 [US1] **Implement Data Streaming for Large Datasets**.
- [X] T056 [US2] **Add Sensitivity Analysis for Effect Size**.
- [X] T060 [US1] **Implement Real Data Streaming Fallback**.
- [X] T061 [US3] **Add Robustness Check for Outlier Influence**.
- [ ] T062_new [US0] **Implement Withdrawal Logging**. **Action**: Create `code/survey/withdrawal_handler.py`. **Logic**: When a participant withdraws, log their `participant_id` and `timestamp` to `data/processed/withdrawal_log.csv`. **Constraint**: Do NOT modify `data/raw/submissions.csv`. This creates a new versioned artifact for audit purposes, satisfying Constitution Principle III.

**Checkpoint**: All prior research-stage review concerns have been addressed and verified.
