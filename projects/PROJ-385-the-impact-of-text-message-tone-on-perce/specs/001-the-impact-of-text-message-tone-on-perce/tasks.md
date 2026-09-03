# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-the-impact-of-text-message-tone-on-perce/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md` (MUST EXIST), `contracts/` (MUST EXIST)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`

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

## Phase 0: Setup & Research Design

- [ ] T004 **(Data Model Validation)** Validate the existing `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` against the current spec requirements for Stimulus, Participant, Rating, AnalysisResult entities.
 - **PRECONDITION**: The file `data-model.md` MUST exist as per Prerequisites. If missing, this task FAILS immediately.
 - **Action**: Compare the content of `data-model.md` with the entities defined in `spec.md`. If it matches, mark as complete. If it deviates, update `data-model.md` to match the spec exactly.
 - Create `code/verify_data_model.py` that validates the markdown against a reference schema.
 - **Verification**: Run `pytest tests/contract/test_data_model_schema.py` which imports the verification script. *Maps to FR‑001*.

- [ ] T004-Verify **(Data Model Validation Execution)** Run `pytest tests/contract/test_data_model_schema.py` to ensure the data‑model file matches its schema. **Depends on: T004**.

- [ ] T001 **(Project Structure)** Create project directory hierarchy (`code/`, `data/`, `tests/`, `README.md`). **Verification**: `ls -R` matches expected tree and `README.md` exists. *Maps to FR‑001, SC‑001*.

- [X] T002 **(Dependencies)** Initialize `code/requirements.txt` with pinned versions of all required packages. **Verification**: `pip install -r code/requirements.txt` succeeds without conflicts. *Maps to FR‑007*.

- [X] T003 **(Linting & Formatting)** Add `ruff.toml` and `pyproject.toml` for `ruff` and `black`. **Verification**: `ruff check.` and `black --check.` return zero exit codes. *Maps to FR‑007*.

- [ ] T003-ConsentVerify **(Consent Verification)** Implement `code/00_verify_consent.py` to check `data/consent/provenance.json`. It MUST verify the existence of keys: `irb_number`, `expiration_date`, `consent_form_version`, `participant_count_limit`. If the file is missing, it MUST generate a template `provenance.json` with placeholders for these fields and exit with a warning code (not fatal, but logged). **Verification**: Script exits 0 if file valid, 1 if missing (after generating template), 2 if invalid keys. *Maps to Plan 0.3*.

- [ ] T005 **(Directory Creation)** Create data sub‑directories `data/raw/`, `data/processed/`, `data/consent/` each containing a `.gitkeep`. **Verification**: Directories exist and contain `.gitkeep`. *Maps to FR‑001*.

- [ ] T006 **(Schema Definitions)** Verify existence of JSON/YAML schema files in `specs/001-the-impact-of-text-message-tone-on-perce/contracts/`:
 - `stimulus.schema.yaml`
 - `rating.schema.yaml`
 - `analysis_ready.schema.yaml`
 - `lmm_summary.schema.yaml`
 - `analysis_result.schema.yaml`
 If any are missing, create them based on the `data-model.md`.
 **Verification**: `pytest tests/contract/test_schema_validation.py` passes. *Maps to FR‑001, FR‑002*. **Depends on: T004-Verify**.

- [X] T007 **(Configuration Management)** Implement `code/config.py` with deterministic random seed and base data path constants. **Verification**: Importing the module asserts `RANDOM_SEED` is an integer and `BASE_DATA_PATH` points to `data/`. *Maps to FR‑007*.

- [ ] T008 **(Logging Infrastructure)** Set up `code/logging_config.py` to write logs to `data/pipeline.log`. **Verification**: Importing creates the log file with a startup message. *Maps to FR‑007*.

- [ ] T090 **(Cue‑Intensity Weighting Schemes)** Create `data/processed/cue_intensity_weights.json` containing three weighting dictionaries with **exact** numeric values:
 1. Equal: `{"emoji": 0.33, "punctuation": 0.33, "length": 0.34}`
 2. Emoji-Dominant: `{"emoji": 0.6, "punctuation": 0.2, "length": 0.2}`
 3. Punctuation-Dominant: `{"emoji": 0.2, "punctuation": 0.6, "length": 0.2}`
 **Verification**: JSON file exists with exact numeric weights as specified. *Maps to FR‑005*.

- [ ] T090b **(Synthetic Power‑Analysis Datasets)** Generate synthetic datasets for power analysis (`data/processed/synthetic_power_datasets.zip`). **Depends on: T090**. **Verification**: Zip contains datasets with N=60, effect size 0.25, random‑effects structure (Participant, Stimulus). *Supports FR‑002*.

- [ ] T091 **(Run Power‑Analysis Simulation)** Execute `code/00_run_power_simulation.py` using the synthetic datasets to produce `data/processed/power_analysis_results.json`. **Depends on: T090b**. **Verification**: JSON includes keys `estimated_power`, `target_N`, `method` and `estimated_power` ≥ 0.80. *Maps to FR‑002*.

- [ ] T091-ValidateScript **(Power‑Analysis Validation Script)** Implement `code/00_validate_power.py` that checks the JSON for required keys and thresholds. **Verification**: Script exits with error if `estimated_power` < 0.80 or `target_N` < 60.

- [ ] T091-Check **(Validate Power‑Analysis Results)** Run `code/00_validate_power.py` against the JSON. **Depends on: T091, T091-ValidateScript**. **Verification**: CI fails if thresholds not met.

- [ ] T099-CLI **(Primary Pipeline CLI)** Add `code/run_pipeline.py` providing a unified CLI (`--mode real` or `--mode mock`). **GUARD CLAUSE**: The `--mode mock` flag MUST be strictly disabled for the primary analysis path. If `--mode mock` is used and the final report generation is triggered, the script MUST exit with a fatal error (code 1) stating "Mock mode is not allowed for primary analysis; real data is required." **Verification**: `python code/run_pipeline.py --mode mock --generate-report` fails with specific error. *Maps to overall workflow*.

## Phase 1: Stimulus Generation & Data Collection (User Story 1 – P1)

- [~] T013 **(Stimulus Generation)** Implement factorial generator `code/01_generate_stimuli.py` producing `data/raw/stimuli.csv` with columns `id,text,emoji_count,punctuation_type,length_category,scenario_id,cue_intensity`. **Depends on: T001, T005, T090**. **Verification**: `python code/01_generate_stimuli.py --verify` exits 0 confirming uniqueness of all feature combinations.

- [ ] T014 **(Counterbalancing)** Create `code/02_counterbalance.py` that assigns **every** stimulus to **both** relationship contexts ("friend" and "acquaintance") for **every** participant, ensuring a fully within-subjects design. Output `data/processed/counterbalanced_trials.csv`. **Depends on: T013**. **Verification**: Row counts per stimulus per context are correct; test `tests/contract/test_counterbalance.py` passes, explicitly checking that the number of rows corresponds to the product of N_participants, N_stimuli, and the required trial structure per participant.

- [ ] T015 **(Random Presentation Order)** Implement `code/03_random_order.py` to shuffle trial order per participant, saving `data/processed/presentation_orders.csv`. **Depends on: T014**. **Verification**: Each participant's order is a permutation of their trials and reproducible with the fixed seed; test `tests/contract/test_random_order.py` validates.

- [ ] T010a **(Stimulus Schema Test)** Add `tests/contract/test_stimulus_schema.py` to validate `data/raw/stimuli.csv` against `stimulus.schema.yaml`. **Depends on: T013**.

- [ ] T015b-Recruit **(External Recruitment)** **EXTERNAL TASK**: Manually deploy survey via Prolific and collect `data/raw/real_ratings.csv`. This task is not implemented in code; it is a manual step. The pipeline assumes this file exists. **Verification**: File `data/raw/real_ratings.csv` exists with required columns. *Maps to FR‑002*.

- [ ] T015b-Real **(Real Data Ingestion)** Write `code/02_collect_real_data.py --mode ingest` to verify and ingest `data/raw/real_ratings.csv` (Prolific export) with required columns. **Depends on: T015b-Recruit**. **Verification**: Errors out if file missing, empty, or contains mock patterns.

- [ ] T015b-FallbackCI **(CI Fallback Behavior)** Implement `code/02_collect_real_data.py` logic to handle missing `data/raw/real_ratings.csv` in CI. If the file is missing, the script MUST raise a `FileNotFoundError` with the specific message "Real data file 'data/raw/real_ratings.csv' is missing. Recruitment step T015b-Recruit has not been completed. Pipeline aborted." and exit with code 1. **NO** synthetic data generation is allowed. **Depends on: T015b-Real**. **Verification**: CI fails with code 1 and specific message if file missing.

- [ ] T015b-Verify **(Real Data Verification)** Run `code/02_validate_data.py` to check schema compliance and basic quality of `data/raw/real_ratings.csv`. **Depends on: T015b-Real**.

- [ ] T015b-ContextCheck **(Relationship Context Check)** Ensure each participant has ratings for both `friend` and `acquaintance`. **Depends on: T015b-Verify**.

- [ ] T016a **(Straight‑Lining Detection)** Implement detector in `code/03_clean_data.py` that flags participants with zero variance across all stimuli, outputting `data/processed/excluded_participants.csv`. **Depends on: T015b-Real**. **Verification**: Test `tests/contract/test_straightlining.py` confirms flagged IDs have zero variance. **Note**: This MUST run BEFORE anonymization to preserve ID linkage.

- [ ] T016b **(Listwise Deletion)** Extend cleaning script to remove flagged participants and any rows with missing data, producing `data/processed/cleaned_ratings.csv`. **Depends on: T016a**. **Verification**: Schema validated by `tests/contract/test_cleaned_schema.py`.

- [ ] T051 **(Anonymisation)** Transform `data/processed/cleaned_ratings.csv` to `data/processed/anonymised_ratings.csv` by hashing Prolific IDs and stripping PII. **Depends on: T016b**. **Verification**: No raw IDs remain; `participant_id` column contains SHA‑256 hashes. **Note**: Runs AFTER cleaning to ensure exclusion flags are applied to raw data first.

- [ ] T052 **(Checksum for Anonymised Ratings)** Compute SHA‑256 of `data/processed/anonymised_ratings.csv` and record in `data/checksums.json`. **Depends on: T051**.

- [ ] T054 **(Checksum for Raw Ratings)** Compute SHA‑256 of `data/raw/real_ratings.csv` and record in `data/checksums.json`. **Depends on: T015b-Real**.

- [ ] T112 **(Straight‑Lining Contract Test)** Load `data/processed/excluded_participants.csv` and assert each listed ID has zero variance in the original ratings. **Depends on: T016a**.

- [ ] T015c-Guard **(Primary Pipeline Guard)** Modify `code/99_preanalysis_guard.py` to abort if `data/raw/real_ratings.csv` contains mock data patterns. **Verification**: Pipeline stops with clear error when mock data detected.

- [ ] T015c-VerifyPrimaryScript **(Guard Verification Script)** Implement `code/guard_no_mock_data.py` that scans primary data paths for mock artifacts. **Verification**: Exits 0 when clean, non‑zero otherwise.

- [ ] T015c-Verify **(Guard Verification)** Run `code/guard_no_mock_data.py` to confirm absence of mock data before analysis. **Depends on: T015c-Guard, T015c-VerifyPrimaryScript**.

## Phase 2: Data Pre‑processing (User Story 1 – continuation)

- [ ] T020 **(Analysis‑Ready Merge)** Merge stimuli metadata with cleaned, anonymised ratings to create `data/processed/analysis_ready.csv`. **Depends on: T016b, T015b-ContextCheck, T051**. **Verification**: File created; schema validated by `tests/contract/test_analysis_ready_schema.py`.

## Phase 3: Statistical Analysis Pipeline (User Story 2 – P2)

- [ ] T021-AmendPlan **(Plan Amendment: LMM Method)** Update `plan.md` (Phase 3) and `spec.md` (FR-003/US2) to explicitly state that the analysis uses the **Wald-Z approximation** for degrees of freedom, acknowledging that `statsmodels.MixedLM` does not support Satterthwaite and that R/rpy2 is outside the approved Python-only stack. This amendment resolves the contradiction between the original requirement and the technical feasibility. **Depends on: T021** (conceptually, but logically precedes implementation verification). **Verification**: `plan.md` and `spec.md` contain the updated text.

- [ ] T021 **(Primary LMM Fit)** Fit a Linear Mixed‑Effects Model using `statsmodels.MixedLM` in `code/04_fit_lmm.py` with formula `rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)`. **Method**: Use **Wald-Z** approximation for degrees of freedom as `statsmodels` does not support Satterthwaite. This is the standard Python-native approach for this stack, as now formally amended in the plan. Output `data/results/lmm_summary.csv` containing `fixed_effect,estimate,stderr,z_value,p_value`. **Depends on: T020**. **Verification**: CSV present; test `tests/contract/test_lmm_summary_schema.py` passes.

- [ ] T021-DocumentMethod **(Methodological Limitation Document)** Create `data/results/methodological_limitations.md` explicitly stating: "The analysis uses the Wald-Z approximation for degrees of freedom. [UNRESOLVED-CLAIM: c_40a089ae — status=not_enough_info] The original Spec (FR-003) and Plan (Phase 3) requested Satterthwaite approximation; however, the Python-only stack (Plan Phase 3) restricts us to `statsmodels`, which only provides Wald-Z. The Plan and Spec have been formally amended to reflect this constraint." **Depends on: T021-AmendPlan, T021**.

- [ ] T024 **(Tukey‑Corrected Post‑hoc)** Implement `code/05_posthoc.py` to run Tukey HSD on interaction marginal means when the interaction term is significant (p < 0.05). Always generate `data/results/posthoc_tukey.csv` with a `significant` flag. **Depends on: T021**. **Verification**: Schema validated by `tests/contract/test_posthoc_schema.py`.

- [ ] T025 **(Result Serialization)** Combine LMM summary, post‑hoc results, and exclusion summary into `data/results/analysis_results.json`. **Depends on: T024**.

- [ ] T084a **(Analysis‑Ready Schema)** Add `contracts/analysis_ready.schema.yaml` defining required columns/types for `analysis_ready.csv`. **Verification**: Schema file exists.

- [ ] T084 **(Validate Analysis‑Ready Schema)** Run `pytest tests/contract/test_analysis_ready_schema.py` to ensure `analysis_ready.csv` conforms. **Depends on: T020**.

- [ ] T085 **(Validate LMM Summary Schema)** Ensure `lmm_summary.schema.yaml` matches `lmm_summary.csv`. **Verification**: Test passes.

- [ ] T107 **(Checksum LMM Summary)** Record SHA‑256 of `data/results/lmm_summary.csv` in `data/checksums.json`. **Depends on: T021**.

- [ ] T108 **(Checksum Post‑hoc)** Record SHA‑256 of `data/results/posthoc_tukey.csv` in `data/checksums.json`. **Depends on: T024**.

- [ ] T109 **(Checksum Analysis Results)** Record SHA‑256 of `data/results/analysis_results.json` in `data/checksums.json`. **Depends on: T025**.

## Phase 4: Sensitivity Analysis (User Story 3 – P3)

- [ ] T027 **(Sensitivity Engine)** Run `code/05_sensitivity_analysis.py` which reads `cue_intensity_weights.json` and re‑fits the LMM for each weighting scheme using the fitting function from `code/04_fit_lmm.py`. Produce intermediate CSVs `data/results/sensitivity_{scheme}.csv`. **Depends on: T090, T021**.

- [ ] T029 **(Stability Metrics)** Compute stability metrics from the three runs and save `data/processed/sensitivity_metrics.csv` with columns `scheme,beta_interaction,abs_beta,p_value,significant,direction,stability_score`. **Depends on: T027**. **Verification**: Test `tests/contract/test_sensitivity_metrics.py` validates.

- [ ] T030 **(Sensitivity Report)** Generate `data/processed/sensitivity_report.md` summarising the stability table and interpreting results. **Depends on: T029**.

- [ ] T056 **(Checksum Sensitivity Report)** Record SHA‑256 of `data/processed/sensitivity_report.md` in `data/checksums.json`. **Depends on: T030**.

- [ ] T110 **(Checksum Sensitivity Metrics)** Record SHA‑256 of `data/processed/sensitivity_metrics.csv` in `data/checksums.json`. **Depends on: T029**.

- [ ] T105 **(Validate Sensitivity Report Schema)** Ensure `sensitivity_report.md` contains required sections via a schema test. **Verification**: Test `tests/contract/test_sensitivity_report_schema.py` passes.

## Phase 5: Polishing & Cross‑Cutting Concerns

- [ ] T033 **(Quickstart Update)** Revise `quickstart.md` with sections on power analysis, benchmarking, and CLI usage (`python code/run_pipeline.py --mode real`). **Verification**: Test `tests/contract/test_quickstart_commands.py` finds the command strings.

- [ ] T035 **(Determinism Verification)** Add `code/verify_determinism.py` that compares current hash of `analysis_results.json` to the value recorded in `data/manifest.json`. **Verification**: Script exits 0 when hashes match.

- [ ] T036 **(Edge‑Case Unit Tests)** Add `tests/unit/test_edge_cases.py` covering missing data handling and participant ID format checks. **Verification**: Tests pass.

- [ ] T038 **(Quickstart Integration Test)** Implement `tests/integration/test_quickstart.py` that runs the quickstart flow end‑to‑end. **Verification**: Test passes.

- [ ] T099 **(Performance Documentation Alignment)** Update `plan.md` and `README.md` to state "≤ 6 hours". **Verification**: `code/check_performance_phrase.py` scans both files for the exact phrase.

- [ ] T040-Generate **(README Generation)** Create `code/README_generator.py` to produce a project `README.md` containing sections "CLI Usage", "Results Overview", and "Reproducibility". **Verification**: Generated README includes all sections.

- [ ] T040-Verify **(README Content Test)** Add `tests/unit/test_readme_contents.py` asserting presence of the three sections.

- [ ] T042 **(Deterministic Output Comparison)** Implement `code/compare_hashes.py` to compare SHA‑256 of `analysis_results.json` and `sensitivity_report.md` across two runs; test `tests/contract/test_hash_determinism.py` ensures equality.

- [ ] T043 **(No GPU Imports Test)** Add `tests/unit/test_no_gpu_imports.py` scanning all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`). **Verification**: CI fails if any are found.

- [ ] T043a **(CI GPU‑Import Guard)** CI step to run the above test and abort on failure.

- [ ] T044 **(CPU‑Only Constraint Documentation)** Document the CPU‑only requirement in `quickstart.md` under "Environment Requirements". **Verification**: Test `tests/contract/test_cpu_constraint.md` checks for phrase "CPU-only".

- [ ] T045 **(Checksum Verification)** Implement `code/verify_checksums.py` to ensure every file listed in `data/checksums.json` exists and matches its recorded SHA‑256. **Verification**: Script exits 0 on success.

- [ ] T046 **(No Raw IDs Verification)** Add `tests/contract/test_no_raw_ids.py` to regex‑check that `data/processed/anonymised_ratings.csv` contains no raw Prolific IDs.

- [ ] T100 **(Manifest Generation)** Write `code/99_manifest.py` that creates `data/manifest.json` after all artifacts are produced, recording SHA‑256 hashes. **Verification**: `utils/validate_manifest.py` validates before downstream consumption.

- [ ] T104 **(Methodological Limitation Note in Report)** Ensure `report.md` includes a paragraph referencing `data/results/methodological_limitations.md` that explains the **Wald-Z approximation** used for the LMM (instead of Satterthwaite), citing the Python stack constraint. **Depends on: T021-DocumentMethod**.

- [ ] T106 **(Full Pipeline Mock Integration Test)** Add `tests/integration/test_full_pipeline_mock.py` that runs the entire pipeline on mock data and asserts completion ≤ 21600 seconds.

- [ ] T113 **(Power‑Analysis JSON Contract Test)** Implement `tests/contract/test_power_analysis_json.py` to verify required keys in `power_analysis_results.json`. **Depends on: T091**.

- [ ] T124 **(Pre‑analysis Guard Implementation)** Extend `code/99_preanalysis_guard.py` to (a) confirm existence of `data/processed/anonymised_ratings.csv`, (b) validate against `rating.schema.yaml`, and (c) abort with clear error if checks fail. **Verification**: `pytest tests/contract/test_preanalysis_guard.py` ensures non‑zero exit when conditions violated.

- [ ] T125 **(Pre‑analysis Guard Test)** Add `tests/contract/test_preanalysis_guard.py` that deliberately removes `data/processed/anonymised_ratings.csv` and checks that the guard script exits with non‑zero status. **Depends on: T124**.

- [ ] T126 **(Mock‑Guard Test)** Add `tests/unit/test_mock_guard.py` confirming that the pipeline fails when mock data is present, relying on T124 and T125. **Depends on: T124, T125**.

- [ ] T127 **(No‑Fallback Test)** Add `tests/unit/test_no_fallback.py` asserting that all data‑loading scripts raise explicit errors on fetch/validation failures and contain no silent synthetic fallback. **Depends on: T015b-Real, T015c-Guard**.

- [ ] T128 **(CI Style Enforcement)** CI step to run `ruff` and `black --check` across the repository.

- [ ] T093 **(Final Manifest Generation)** After all artifacts are created, run `code/99_manifest.py` again to ensure the manifest is up‑to‑date. **Verification**: `utils/validate_manifest.py` passes.

- [ ] T129 **(Missing Values Check)** Implement `code/02_validate_ratings.py` to ensure `data/raw/real_ratings.csv` has no missing values in `stimulus_id`, `relationship_type`, or `rating`. **Verification**: Script exits 0 on clean data.

- [ ] T130 **(Relationship Value Validation)** Extend the same script to confirm `relationship_type` contains only `"friend"` or `"acquaintance"`.

- [ ] T131 **(Cue‑Intensity Consistency Check)** Add `code/01_verify_cue_intensity.py` that recomputes cue intensity from stimulus features and asserts equality with values in `data/raw/stimuli.csv` using the primary weighting scheme from `cue_intensity_weights.json`. **Verification**: Script exits 0 on match.

- [ ] T132 **(Power‑Analysis Section in Report)** Extend `code/07_generate_report.py` to include a "Power Analysis" section summarising estimated power, target sample size, and methodology.

- [ ] T133 **(Effect‑Size Computation)** Update `code/04_fit_lmm.py` to calculate Cohen's f for the interaction term and add column `cohens_f_interaction` to `data/results/lmm_summary.csv`. **Verification**: Column present and non-negative.

- [ ] T134 **(Effect‑Size Unit Test)** Add `tests/unit/test_effect_size.py` confirming that `cohens_f_interaction` is computed correctly and ≥ 0.

- [ ] T135 **(Runtime Benchmark)** Add `code/benchmark_runtime.py` that measures total pipeline runtime and fails if > 21600 seconds. **Verification**: CI step runs this benchmark; fails on excess time.

## Phase 6: Final Verification & Documentation (Revision)

- [ ] T140 **(Data Flow Ordering Verification)** Review and update `code/run_pipeline.py` to ensure strict execution order: Stimulus Generation → Counterbalancing → Random Order → Real Data Ingestion → Cleaning → Preprocessing → LMM → Post-hoc → Sensitivity. **Depends on: T099**. **Verification**: Unit test `tests/integration/test_execution_order.py` asserts that each step's output file exists before the next step begins.

- [ ] T141 **(Real Data Source Documentation)** Update `quickstart.md` and `README.md` to explicitly state that `data/raw/real_ratings.csv` MUST be a Prolific export and that the pipeline will fail if synthetic data is detected. **Verification**: `grep` check in CI confirms presence of "Prolific" and "fail" warnings.

- [ ] T142 **(Wald-Z vs Satterthwaite Clarification)** Ensure `data/results/methodological_limitations.md` (created by T021-DocumentMethod) clearly distinguishes between the Wald-Z approximation (used via statsmodels) and the Satterthwaite approximation (requested originally but unavailable), justifying the choice of Wald-Z as the standard Python-native method and confirming the Spec/Plan amendment. **Verification**: Document contains both terms and the rationale.

- [ ] T143 **(Sensitivity Analysis Theoretical Basis)** Add a section to `data/processed/sensitivity_report.md` citing theoretical hypotheses for the three weighting schemes (Equal, Emoji-Dominant, Punctuation-Dominant) to justify the sensitivity analysis design. **Verification**: Report includes citations or theoretical references.

- [ ] T144 **(Final End-to-End Validation)** Run the complete pipeline with `--mode real` (using a valid mock dataset for CI) to ensure all tasks complete in order and all checksums are recorded. **Verification**: CI passes with `--mode real` using a small, pre-generated dataset.

- [ ] T145 **(Constitutional Principle Checklist)** Add `tests/contract/test_constitutional_principles.py` to verify that all six constitutional principles (Reproducibility, Verified Accuracy, Data Hygiene, Single Source of Truth, Versioning Discipline, Human-Subject Anonymity) are met by the generated artifacts. **Verification**: Test suite passes.