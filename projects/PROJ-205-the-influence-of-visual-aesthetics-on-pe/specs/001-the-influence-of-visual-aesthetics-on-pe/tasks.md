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
- [X] T003 [P] Configure linting (ruff/flake8) and formatting tools. Create `.ruff.toml` with rules E, W, F, I, N, D, UP, C90, B, C4, PT, RUF, SIM, TCH, TID, ARG. Create `pyproject.toml` with `[tool.black]` and `[tool.isort]` sections.

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
- [X] T010 Create `code/utils/helpers.py` for CSV export formatting, ID generation, and IP hashing (`hash_ip` function). **Action**: Implement `hash_ip(ip_address, salt="project_salt_2024")` using **SHA-256** (not MD5) to ensure security and prevent reverse lookup. The function must return a hexdigest.
- [X] T011e [US0] **MANDATORY: Manual IRB Text Insertion (Human Operator)**. **Action**: This is a manual administrative step. The human operator MUST replace the placeholder in `data/consent/irb_approved.txt` with the actual IRB-approved text before any production data collection. **Verification Gate**: The system MUST implement a strict check in `code/survey/app.py` that raises a fatal error if the file contains the placeholder AND `MODE=production`. This task must be marked complete before US0 can be considered "Production Ready". **Note**: This is a manual step. The system must not run data collection without this verification.
- [X] T011g [US0] **Verify Production Ready State**. **Action**: Create a verification script `code/utils/verify_consent.py` that checks `data/consent/irb_approved.txt` for the absence of placeholders and the presence of text > 500 chars. This task provides the automated verification step required to confirm Te is complete, resolving the traceability gap for "Production Ready" status.
- [X] T011d [US0] **Implement Verification Logic**. **Action**: Create verification logic in `code/survey/app.py` to validate `data/consent/irb_approved.txt`. **Action**: Check if the file contains the exact string literals `<!-- PLACEHOLDER: INSERT IRB APPROVED TEXT BELOW -->` OR `<!-- END PLACEHOLDER -->`. If found, raise a **fatal error** immediately **IF** `MODE=production`. In **Development Mode**, the system may log a warning but must NOT crash, allowing the developer to test the form logic. Additionally, verify that the file contains substantial text (e.g., > 500 characters) excluding the placeholder header. If the text is insufficient or missing in Production, raise a fatal error. **Constraint**: Development mode exception is allowed for testing; Production mode must strictly block. **Note**: This task runs AFTER T011e to ensure the file has been updated.
- [X] T011f [US0] **Enforce Runtime Blocking**. **Action**: Modify `code/survey/app.py` to run the verification logic from T011d **immediately on app startup** (before any UI is rendered). If the check fails in Production, the app must terminate with a clear error message: "FATAL: IRB Consent text is missing or invalid. Please update data/consent/irb_approved.txt." This ensures no data collection can occur without valid text, satisfying Constitution Principle VI. **Note**: This task runs AFTER T011e to ensure the file has been updated.
- [X] T054 [US0] **Add Consent Form Versioning**. Address reviewer concern about tracking consent form changes. **Action**: Modify `code/utils/helpers.py` to compute a SHA-256 hash of `data/consent/irb_approved.txt` for backend version tracking. **Crucial**: The hash is ONLY for internal logging and version tracking. The full, readable text of the consent form MUST be displayed to the participant. **Do NOT** display the hash to the participant. Update `data/consent/irb_approved.txt` to include a version header comment. Ensure `code/survey/app.py` logs the version hash with every consent decision.
- [X] T011h [US0] **Implement Automated CI/CD Gate for IRB**. **Action**: Create a pre-commit hook or CI script `scripts/check_irb.py` that runs automatically before any commit or deployment. The script MUST fail the build if `data/consent/irb_approved.txt` contains placeholder strings (`<!-- PLACEHOLDER... -->`). This enforces Constitution Principle I and VI by preventing manual errors from blocking the pipeline. **Dependency**: Requires T011e to be completed by the human operator first.
- [X] T016c [P] Create `code/utils/file_lock.py` for file-based locking mechanism to persist state across sessions. **Action**: Implement a thread-safe file lock utility using `fcntl` (Linux) or `msvcrt` (Windows) to allow atomic read/write of a counter file.
- [X] T043a [P] **Generate Mock Data Script (Skeleton)**. **Action**: Create the skeleton script `code/utils/generate_mock_data.py` with the necessary imports and function structure. **Action**: Ensure `numpy.random.seed(42)` is set at the start to guarantee reproducibility. **Note**: This task creates the script structure; implementation of the generation logic is in T043a_impl.
- [X] T043a_impl [P] **Implement Mock Data Generation Logic**. **Action**: Implement the data generation logic in `code/utils/generate_mock_data.py` to generate a synthetic `data/raw/submissions.csv` with N=250 participants. **Schema**: Must include `participant_id` (UUID), `stimulus_id`, `credibility_rating` (1-7), `professionalism_rating` (1-7), `timestamp`, `hashed_ip`, `age`, `education`, `session_status`, `submission_status`, `hashed_user_agent`. **Distribution**: Use normal distribution (mean=4, std=1.5) for ratings, truncated to 1-7. **Action**: Ensure `numpy.random.seed(42)` is set at the start. **Constraint**: This data is **strictly for structural validation only**. The statistical parameters are arbitrary and do not constitute a "ground truth" for effect size verification. **Note**: This task runs after T043a.
- [X] T043a_run [P] **Execute Mock Data Generation**. **Action**: Run `python code/utils/generate_mock_data.py` to generate the initial `data/raw/submissions.csv` artifact. **Verification**: Confirm the file exists and contains 250 rows. **Purpose**: This task creates the required input artifact for T024a and T057, unblocking the analysis pipeline. **Dependency**: Requires T043a and T043a_impl to be complete.
- [X] T043b [P] **Mock Data Checksum & Seed**. **Action**: Add logic to `code/utils/generate_mock_data.py` (T043a_impl) to compute the SHA-256 checksum of the generated `data/raw/submissions.csv` and record it in `state/projects/PROJ-205-...yaml` under `artifact_hashes` (Constitution Principle III). **Action**: Ensure `numpy.random.seed()` is set at the start to guarantee reproducibility.
- [X] T043d [P] **Verify Mock Data Separation**. **Action**: Create a test in `tests/unit/test_data_integrity.py` that asserts `data/raw/submissions.csv` generated by the experimental task is flagged as "TEST_DATA" in the filename or metadata and is explicitly excluded from the final analysis pipeline (e.g., by checking that the analysis script `00_preprocess.py` rejects files with "test" in the name or by checking a specific metadata flag). **Purpose**: Enforce Constitution Principle II (Verified Accuracy) by ensuring synthetic data is never used for final results.

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
- [X] T023f_heartbeat [US1] Implement session timeout detection in `code/survey/app.py`: Use `st.on_change` on a hidden widget or form to update `st.session_state.last_active` with `time.time()`. On page load or widget interaction, check if `time.time() - st.session_state.last_active > TIMEOUT_THRESHOLD` (e.g., a configurable session timeout duration). If exceeded, set `session_status='timeout'` and `submission_status='incomplete'` in the session state. **Action**: This must run **immediately after T022a** to establish the timeout mechanism before any form rendering or data capture occurs.
- [X] T022b [US1] Implement IP extraction, hashing, and session rejection logic in `code/survey/app.py`: Extract IP using `st.context.headers.get('X-Forwarded-For')`. If missing in production, display error "Session Rejected: Unable to verify identity." and call `st.stop()`. Hash the IP with `helpers.hash_ip()` immediately after extraction. **This single task covers both extraction and rejection.**
- [X] T022c [US1] **Define Form Schema**: Define the schema for demographic input (Age, Education) and the CSV export structure in `code/survey/constants.py`. **Action**: Define a dictionary `DEMOGRAPHIC_SCHEMA` with keys `age` (type: int, validation: > 18), `education` (type: str, validation: in ['High School', 'Bachelor', 'Master', 'PhD']). Define `CSV_SCHEMA` as a list of column names: `['participant_id', 'stimulus_id', 'credibility', 'professionalism', 'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag', 'session_status', 'submission_status', 'hashed_user_agent']`. **Update**: Added `hashed_user_agent` to schema to match T022f and T022g_impl.
- [X] T022g_schema [US1] **Define Export Function Signature**. **Action**: Define the function signature `export_to_csv(data_list)` in `code/utils/helpers.py`. **Action**: Ensure the function accepts a list of data dictionaries and prepares to append them to `data/raw/submissions.csv`. **Schema**: Use the `CSV_SCHEMA` from T022c. **Return**: None. **Edge Case**: If `data_list` is empty, create an empty CSV file with headers only. **Note**: This task defines the interface; implementation of file handling is in T022g_impl.
- [X] T022d [US1] **Render Form**. **Action**: Render the demographic input form in `code/survey/app.py` using the schema defined in T022c. **Note**: This task depends on T022c and T022g_schema for function existence.
- [X] T022e [US1] **Capture Data**. **Action**: On form submission (triggered by T022d), append a row to `data/raw/submissions.csv` with columns `participant_id`, `age`, `education`, `timestamp`, `hashed_ip`. **Action**: Use the `export_to_csv()` function defined in **T022g_impl**. **Note**: This task depends on T022g_impl for the function existence and T022c for schema.
- [X] T022f [US1] Implement metadata sanitization. **Action**: Hash the `user_agent` string using **SHA-256** (not just truncate) before writing to CSV in `code/survey/app.py` to prevent PII leakage (device fingerprinting). **Code**: `hashlib.sha256(user_agent.encode()).hexdigest()`. **Constraint**: Do not store the raw user_agent.
- [X] T022g_impl [US1] **Implement Export Logic**. **Action**: Implement the file handling logic in `code/utils/helpers.py` for `export_to_csv()`. **Action**: Use file mode `'a'` (append) and create the file if it doesn't exist (`os.makedirs` for directories). **Action**: If the file is new (does not exist), **write the header row defined in CSV_SCHEMA** before appending data. **Action**: Store the full SHA-256 hexdigest for `hashed_user_agent`; **do NOT truncate**. **Note**: This function is called by T021 (Submission Handler).
- [X] T022g_test [US1] Verify CSV schema. **Action**: Run `pytest tests/contract/test_csv_schema.py` to verify header matches schema. **Note**: This task depends on T022g_impl creating the file.
- [X] T022h [US1] Implement post-hoc duplicate detection. **Action**: Create script `code/analysis/05_audit.py`. Read `data/raw/submissions.csv`, flag rows where `hashed_ip` appears more than once, and log to `data/raw/duplicate_audit.csv`. **Verification**: Run `python code/analysis/05_audit.py` and verify `duplicate_audit.csv` content. **Note**: This task depends on the output artifact `data/raw/submissions.csv` from T043a_run or live survey.
- [X] T028e [US1] Implement Latin Square sequences as a hardcoded constant list in `code/survey/constants.py`. **Content**: Define a list of lists `LATIN_SQUARE_MATRIX` with the following permutations (Professional, Minimalist, Low-Quality, Neutral):
 1. `['Professional', 'Minimalist', 'Low-Quality', 'Neutral']`
 2. `['Minimalist', 'Low-Quality', 'Neutral', 'Professional']`
 3. `['Low-Quality', 'Neutral', 'Professional', 'Minimalist']`
 4. `['Neutral', 'Professional', 'Minimalist', 'Low-Quality']`
 **Action**: Write these exact permutations to `code/survey/constants.py` as a constant list `LATIN_SQUARE_MATRIX`.
- [X] T016a [US1] Verify Latin Square validity: Add a unit test in `tests/unit/test_randomization.py` that mathematically verifies the hardcoded sequences form a balanced Latin Square for the specified number of conditions.
- [X] T016b [US1] Implement balanced Latin Square selection logic. **Action**: In `code/survey/app.py`, implement a function `get_stimulus_order(participant_id: str) -> list` that uses `hash(participant_id) % 4` to select a row index from `LATIN_SQUARE_MATRIX`. **Crucial**: This is a **stateless** selection mechanism. Do NOT use file locking or server-side counters. The hash of the participant ID ensures a consistent, balanced distribution across the cohort without requiring persistent state, adhering to the Streamlit architecture defined in T020. **Output**: Return the specific order of stimuli for the current participant.
- [X] T016c [US1] **Verify Latin Square Runtime Selection**. **Action**: Create an integration test `tests/integration/test_latin_square_runtime.py` that simulates multiple participants, collects their assigned orders, and verifies that the distribution of orders matches the Latin Square matrix (i.e., each condition appears equally often in each position across the cohort). **Purpose**: Verify the *implementation* of T016b against the spec requirement for counterbalanced order.
- [X] T017 [US1] Implement stimulus rendering loop in `code/survey/app.py` to display HTML files sequentially based on the order returned by T016b.
- [X] T018 [US1] Create multi-point Likert rating inputs for Credibility and Professionalism in `code/survey/app.py`.
- [X] T019 [US1] Implement validation logic to block submission if < 4 stimuli rated (8 total ratings). **Action**: In the submit handler of `app.py`, check if all 4 stimuli have been rated (8 total ratings: 4 stimuli * 2 scales). If not, display error "Please rate all stimuli before submitting." and block submission. **Constraint**: Use the constant `MIN_STIMULI = 4` defined in `code/survey/constants.py`. **Note**: This explicitly enforces the 4-stimuli requirement.
- [X] T020 [US1] Implement client-side state management: Use **in-memory only** (Streamlit session state) to track progress.
- [X] T021 [US1] Implement submission handler to record Participant ID, Stimulus Condition, Ratings, Timestamp, Device Info in `code/survey/app.py`. **Action**: This handler aggregates all data (demographics, ratings) and calls the `export_to_csv()` function defined in **T022g_impl** to write the row.
- [X] T057 [US1] **Implement Data Integrity Checksums**. **Action**: Extend `code/utils/helpers.py` to compute a SHA-256 checksum of the `data/raw/submissions.csv` file **only when the session ends and the file is finalized**. **Action**: Store the checksum in `state/projects/PROJ-205-...yaml` under `data_checksums`. **Trigger**: Compute checksum via a cron job or end-of-batch script (e.g., `scripts/compute_checksum.py`) after data collection batches. **Verification**: Add a check in `code/analysis/00_preprocess.py` to verify the checksum of the input file before processing. If the checksum mismatches, raise a fatal error. **Constraint**: This ensures the "Single Source of Truth" principle (Constitution Principle IV) is maintained for the raw data. **Dependency**: Requires T043a_run to generate the file first.
- [X] T038 [P] Add unit tests for Latin Square lookup logic in `tests/unit/test_randomization.py`.
- [X] T039 [P] Add integration test for full survey flow (Consent → Stimuli → Submit) in `tests/integration/test_survey_flow.py`.
- [X] T040 [P] Add contract test for CSV schema validation (including hashed IP and hashed user_agent) in `tests/contract/test_csv_schema.py`.

**Checkpoint**: User Story 1 is fully functional; data can be collected and exported.

---

## Phase 5: User Story 2 - Statistical Analysis Pipeline (Priority: P2) 📊

**Goal**: Execute Repeated-Measures ANOVA and conditional Bonferroni-corrected pairwise t-tests.

**Independent Test**: Run analysis on a sample CSV (N=50); verify ANOVA F-stat, p-value, η², and conditional pairwise comparisons with effect sizes.

### Implementation for User Story 2

- [X] T024a [US2] Create preprocess script `code/analysis/00_preprocess.py`. **Action**: Load `data/raw/submissions.csv` using **chunked reading** (streaming) to handle large datasets. Filter **complete sessions** (those with the full set of rows corresponding to the stimuli and scales), audit excluded rows, and reshape the dataframe into **wide format** (one row per participant, columns for each condition's rating) specifically for `statsmodels` Repeated-Measures ANOVA. **Artifact**: Generate `data/processed/cleaned_data.csv`. **Dependency**: Requires T043a_run to generate the input file. **Note**: For CI/CD execution and reproducibility verification, this script MUST successfully process the mock data from T043a to generate the artifact. Real data collection is an external operational phase, but the pipeline must be verified against the mock dataset to prove reproducibility (Constitution Principle I). **Note**: This script processes mock data for testing and real data for production. **Dependency**: Requires T057 for checksum verification.
- [X] T024b [US2] Execute preprocess script and verify output. **Action**: Run `python code/analysis/preprocess.py` and verify output file exists.
- [X] T045 [US2] **Create and Execute Power Analysis Script** (Required: Sensitivity Analysis). Calculate minimum detectable effect size for N=250 using real or mock data. **Action**: Use `statsmodels.stats.power` to calculate power. **Parameters**: Target power=0.8, alpha=0.05, effect size metric= Cohen's f. **Output Schema**: Save to `data/processed/power_analysis_results.json` with keys: `sample_size`, `effect_size`, `power`, `alpha`. **Dependency**: Requires `data/processed/cleaned_data.csv` from T024a_b. **Note**: This is a required sensitivity analysis task to validate statistical power.
- [X] T048 [US2] Address reviewer comment: "The p-value correction method (Bonferroni) is conservative and may lead to a loss of statistical power. Consider using a more flexible method, such as Benjamini-Hochberg (FDR), to control the false discovery rate." **Action**: Modify `code/analysis/02_pairwise.py` (created in T026_integrated) to add a command-line argument `--correction-method {bonferroni, fdr}`. **Constraint**: **Default must be `bonferroni`** to satisfy Spec US2. FDR is only for sensitivity analysis. Update `data/processed/analysis_results.json` to include the method used and the resulting p-values for both methods if applicable. **Output Schema**: Include keys `bonferroni_p` and `fdr_p` (optional). **Note**: Bonferroni is the primary metric.
- [X] T025a_b [US2] Create and execute ANOVA script using `statsmodels` to calculate F-statistic, p-value, and eta squared from cleaned data. **Action**: Run Repeated-Measures ANOVA on the wide-format data using `statsmodels.stats.anova.AnovaRM`. **Column Names**: Dependent variable `rating`, Independent variable `condition`, Subject `participant_id`. **Output Schema**: Save results to `data/processed/anova_results.json` with keys: `F_statistic`, `p_value`, `eta_squared`, `degrees_of_freedom`.
- [X] T026_integrated [US2] Implement conditional pairwise t-tests if ANOVA p < 0.05 using Bonferroni-corrected tests and calculate Cohen's d. **Action**: Create `code/analysis/02_pairwise.py`. Run pairwise t-tests between conditions using `scipy.stats.ttest_rel`. **Correction**: Apply Bonferroni correction manually (`p_value * number_of_comparisons`). **Effect Size**: Calculate Cohen's d using `pingouin.compute_effsize` (requires `pingouin` from T002) or manual formula `(mean1 - mean2) / pooled_std`. **Input**: Requires `data/processed/cleaned_data.csv` (T024a) and `data/processed/anova_results.json` (T025a_b). **Output Schema**: Save results to `data/processed/pairwise_results.json` with keys: `Cohen_d`, `Bonferroni_corrected_p`, `unadjusted_p`. **Dependency**: Requires completion of T025a_b and T002.
- [X] T027a_b [US2] Create report script to generate a summary table including ANOVA results, pairwise comparisons, effect sizes, and save it as `data/processed/analysis_results.json`. **Dependency**: Requires outputs from **T025a_b** and **T026_integrated** (including T048 updates). **Output Format**: JSON with keys `anova_summary`, `pairwise_summary`, `effect_sizes`. **Note**: This task is moved after T026_integrated to respect producer-consumer dependency.
- [X] T026_verify [US2] **Verify Statistical Output**. **Action**: Create `tests/contract/test_anova_schema.py` to verify `data/processed/anova_results.json` and `data/processed/pairwise_results.json` contain all required keys and valid numeric ranges (e.g., p-value between 0 and 1). **Purpose**: Explicitly validate the correctness of the ANOVA and pairwise test results against the spec's acceptance criteria.
- [X] T051a [US2] **Update Pairwise Script for Bootstrapping**. Address reviewer concern about the lack of confidence intervals for effect sizes. **Action**: Update `code/analysis/02_pairwise.py` to calculate and report confidence intervals for Cohen's d using bootstrapping (1000 iterations, **seed=42**). **Method**: Resample **participants** (rows) with replacement. Use `scipy.stats.bootstrap` or manual implementation.

**Checkpoint**: Preprocessing scripts ready; data analysis blocked until T024b completes.

---

## Phase 6: User Story 3 - Robustness and Validation Checks (Priority: P3) 🔬

**Goal**: Run Mixed-Effects models with age/education covariates to verify design effects persist.

**Independent Test**: Run mixed-effects model on the same dataset; verify design condition coefficient is reported with covariates and converges without warnings.

### Implementation for User Story 3

- [X] T032 [US3] Create `code/analysis/03_mixed_effects.py` script. **Action**: Initialize the script structure for mixed effects modeling.
- [X] T033 [US3] Implement mixed effects model logic. **Action**: Use `statsmodels` `MixedLM`. **Formula**: `Credibility ~ Condition + Age + Education + (|Participant)`. **Input**: Requires `data/processed/cleaned_data.csv` from T024a. **Output**: Save to `data/processed/mixed_effects_results.json` with keys: `coefficients`, `p_values`, `convergence_status`. **Note**: This task implements the full MixedLM logic.
- [X] T035 [US3] Implement comparison logic and save output. **Action**: Explicitly compare the `Condition` coefficient and p-value with the ANOVA results from T025a_b and log the comparison (e.g., "ANOVA p=0.03, MixedEffects p=0.04; consistent") to the JSON file. **Output**: Save to `data/processed/mixed_effects_results.json`. **Dependency**: Requires completion of T033.
- [X] T049 [US3] Address reviewer comment: "The mixed-effects model assumes a normal distribution of residuals. Check the residuals for normality and consider data transformations if necessary." **Action**: Add residual normality checks (Shapiro-Wilk test) to the analysis script for mixed-effects modeling using `scipy.stats.shapiro`. If the p-value < 0.05, log a warning and attempt a log or square-root transformation of the dependent variable (Credibility/Professionalism) and re-run the model. Report both the original and transformed model results in `data/processed/mixed_effects_results.json` with a flag indicating whether transformation was necessary. **Constraint**: Transformations are only applied if the protocol allows; raw data meaning is preserved in the primary report. **Output Schema**: Include keys `transformation_applied` (boolean) and `transformation_method` (string).
- [X] T052 [US3] **Validate Mixed-Effects Model Convergence**. **Action**: Add a convergence check in `code/analysis/03_mixed_effects.py`. If the model fails to converge (return code != 1), automatically retry with different optimizers (`'bfgs'`, `'newton'`, `'cg'`) or simplified random effects structures. Log all retry attempts and final convergence status in `data/processed/mixed_effects_results.json`. If convergence fails after a predetermined number of attempts, flag the result as "UNCONVERGED".
- [X] T051b [US3] **Update Mixed Effects Script for Bootstrapping**. **Action**: Update `code/analysis/03_mixed_effects.py` to calculate and report confidence intervals for the **Condition coefficient** using bootstrapping (1000 iterations, **seed=42**). **Note**: Calculate CI for the primary effect size metric (Condition coefficient), not Eta-squared (which is ANOVA-specific).
- [X] T051c [US2/US3] **Update JSON Schemas**. **Action**: Update `data/processed/analysis_results.json` and `data/processed/mixed_effects_results.json` to include the confidence interval keys (`ci_lower`, `ci_upper`). **Dependency**: Requires completion of T051a and T051b.

**Checkpoint**: Robustness checks are complete; findings are validated against demographics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [P] T041 Update `README.md` with setup instructions and execution order
- [P] T042 Run `quickstart.md` validation (if available) to ensure all paths are correct
- [X] T043b [P] Verify runtime benchmark: Create `tests/benchmark/test_runtime.py` that asserts the full analysis pipeline completes within 30 minutes on a CPU-only runner using the mock data from T043a.
- [X] T043c [P] **Verify File Size**. **Action**: Add assertion in `tests/benchmark/test_runtime.py` that `data/raw/submissions.csv` size < 5MB for N=250. **Dependency**: Requires `data/raw/submissions.csv` to exist (from T043a execution).
- [P] T044 [P] Add a comprehensive `CONTRIBUTING.md` and `DATA_PROCEDURE.md` documenting the exact steps for data collection, cleaning, and analysis to ensure reproducibility by external researchers.

**Checkpoint**: Polish and validation tasks complete.

---

## Phase 8: Revision & Review Resolution

**Purpose**: Address specific concerns raised in prior research-stage reviews to ensure scientific rigor and data integrity.

- [X] T055 [US1] **Implement Data Streaming for Large Datasets**. Address reviewer concern that the current CSV loading approach (`pd.read_csv`) will fail on large datasets. **Action**: Modify `code/analysis/00_preprocess.py` to support chunked reading using `pandas.read_csv(..., chunksize=...)` to iterate over the CSV in chunks. **Constraint**: The script must compute running statistics (mean, sum, count) online to avoid loading the full dataset into memory. **Fallback**: If the full dataset cannot be processed, the script must **FAIL LOUDLY** (raise an exception) rather than logging a limitation. This preserves the 'Verified Accuracy' principle. **Dependency**: This task must be completed before `T024a` is considered robust for production-scale data.
- [X] T056 [US2] **Add Sensitivity Analysis for Effect Size**. Address reviewer concern regarding the power of the study with N=250. **Action**: Extend `code/analysis/04_power.py` (created in T045) to calculate the minimum detectable effect size (MDES) for the specific design (within-subjects, 4 conditions) at 80% power and alpha=0.05. **Output**: Save the MDES to `data/processed/sensitivity_analysis.json`. **Constraint**: If the observed effect size is smaller than the MDES, the script must flag the result as "Underpowered" in the final report. **Dependency**: Requires `data/processed/cleaned_data.csv` from T024a and T045.
- [ ] T060 [US1] **Implement Real Data Streaming Fallback**. Address reviewer concern about handling datasets that exceed memory limits during the initial load phase. **Action**: Modify `code/analysis/00_preprocess.py` to explicitly implement a streaming fallback mechanism using `datasets.load_dataset(..., streaming=True)` or manual chunked iteration if `pandas.read_csv(chunksize=...)` fails due to schema complexity. **Constraint**: The script must **NOT** fall back to synthetic data or a smaller static sample if streaming fails; it must **FAIL LOUDLY** with a clear error message indicating the real data source is inaccessible or the chunking logic is insufficient. **Dependency**: Requires T055 to be complete.
- [ ] T061 [US2] **Add Robustness Check for Outlier Influence**. Address reviewer concern about the sensitivity of ANOVA to outliers. **Action**: Create `code/analysis/06_outlier_sensitivity.py` to run the ANOVA and Mixed-Effects models on the dataset after removing top/bottom 1% of ratings (winsorization) and compare results to the full dataset. **Output**: Save comparison metrics to `data/processed/outlier_sensitivity.json`. **Constraint**: The primary analysis results (T025a_b, T033) must remain based on the unmodified data; this task is strictly for sensitivity reporting. **Dependency**: Requires T024a and T033.
- [ ] T062 [US0] **Implement Participant Withdrawal Data Purge**. Address reviewer concern about GDPR/CCPA compliance for participants who withdraw after data submission. **Action**: Create a script `code/utils/purge_participant.py` that accepts a `participant_id` and removes all associated rows from `data/raw/submissions.csv` and `consent_log.csv`, then updates the checksums in `state/projects/PROJ-205-...yaml`. **Constraint**: This script must be idempotent and log the action to a separate audit trail (`data/raw/purge_log.csv`) without modifying the original raw data file in place (use atomic rename). **Dependency**: Requires T057 for checksum management.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
