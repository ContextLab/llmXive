# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-the-impact-of-text-message-tone-on-perce/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md` (MUST EXIST), `contracts/` (MUST EXIST)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if tests requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T004 **(Data Model Validation)** Validate `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` against `spec.md` entities (Stimulus, Participant, Rating, AnalysisResult).  
  **Action**: Run `code/verify_data_model.py` → generates `data/validation/data_model_report.txt`.  
  **Verification**: `pytest tests/contract/test_data_model_report.py` checks report existence and content. *Maps to FR‑001*.

- [ ] T004-Report-Validate **(Data Model Report Test)** Run `pytest tests/contract/test_data_model_report.py` to ensure the validation report matches expected entity definitions. *Depends on: T004*.

- [ ] T001 **(Project Structure)** Create project directory hierarchy (`code/`, `data/`, `tests/`, `README.md`).  
  **Verification**: `tests/contract/test_project_structure.py` checks that directories exist, `README.md` contains sections *Project Overview*, *CLI Usage*, *Reproducibility*. *Maps to FR‑001, SC‑001*.

- [X] T002 **(Dependencies)** Initialize `code/requirements.txt` with pinned versions of all required packages. **Verification**: `pip install -r code/requirements.txt` succeeds without conflicts. *Maps to FR‑007*.

- [X] T003 **(Linting & Formatting)** Add `ruff.toml` and `pyproject.toml` for `ruff` and `black`. **Verification**: `ruff check.` and `black --check.` return zero exit codes. *Maps to FR‑007*.

- [ ] T003-ConsentVerify **(Consent Verification)** Implement `code/00_verify_consent.py` to check `data/consent/provenance.json`. It MUST verify the existence of keys: `irb_number`, `expiration_date`, `consent_form_version`, `participant_count_limit`. If missing, generate a template and exit with warning. **Verification**: Script exits 0 if valid, 1 if missing (after generating template), 2 if invalid keys. *Maps to Plan 0.3*.

- [ ] T005 **(Directory Creation)** Create data sub‑directories `data/raw/`, `data/processed/`, `data/consent/` each containing a `.gitkeep`. **Verification**: Directories exist and contain `.gitkeep`. *Maps to FR‑001*.

- [ ] T006 **(Schema Definitions)** Verify existence of JSON/YAML schema files in `specs/001-the-impact-of-text-message-tone-on-perce/contracts/`:
  - `stimulus.schema.yaml`
  - `rating.schema.yaml`
  - `analysis_ready.schema.yaml`
  - `lmm_summary.schema.yaml`
  - `analysis_result.schema.yaml`  
  **If missing**, create them based on `data-model.md`.  
  **Verification**: `pytest tests/contract/test_schema_validation.py` passes. *Maps to FR‑001, FR‑002*. **Depends on: T004-Report-Validate**.

- [X] T007 **(Configuration Management)** Implement `code/config.py` with deterministic random seed and base data path constants. **Verification**: Importing the module asserts `RANDOM_SEED` is an integer and `BASE_DATA_PATH` points to `data/`. *Maps to FR‑007*.

- [ ] T008 **(Logging Infrastructure)** Set up `code/logging_config.py` to write logs to `data/pipeline.log`. **Verification**: Importing creates the log file with a startup message. *Maps to FR‑007*.

- [ ] T090 **(Cue‑Intensity Weighting Schemes)** Create `data/processed/cue_intensity_weights.json` containing three weighting dictionaries with exact numeric values:  
  1. Equal: `{"emoji": 0.33, "punctuation": 0.33, "length": 0.34}`  
  2. Emoji‑Dominant: `{"emoji": 0.6, "punctuation": 0.2, "length": 0.2}`  
  3. Punctuation‑Dominant: `{"emoji": 0.2, "punctuation": 0.6, "length": 0.2}`  
  **Verification**: `code/validate_cue_weights.py` checks existence and exact values; `pytest tests/contract/test_cue_weights.py` validates. *Maps to FR‑005*.

- [ ] T090-Validate-Script **(Cue Weights Validation Script)** Implement `code/validate_cue_weights.py` that exits 0 when JSON matches required schema, non‑zero otherwise.

- [ ] T090-Validate-Test **(Cue Weights Validation Test)** Run `pytest tests/contract/test_cue_weights.py` to confirm JSON correctness. **Depends on: T090, T090-Validate-Script**.

- [ ] T090b **(Synthetic Power‑Analysis Datasets)** Generate synthetic datasets for power analysis (`data/processed/synthetic_power_datasets.zip`).  
  **Verification**: `tests/contract/test_synthetic_zip.py` checks zip contains CSVs with N=60, effect size 0.25, and correct schema; checksum recorded in `data/checksums.json`. **Depends on: T090**.

- [ ] T090b-Validate-Checksum **(Synthetic Zip Checksum Test)** Ensure zip checksum matches entry in `data/checksums.json`.

- [ ] T091 **(Run Power‑Analysis Simulation)** Execute `code/00_run_power_simulation.py` using synthetic datasets to produce `data/processed/power_analysis_results.json`.  
  **Verification**: `tests/contract/test_power_analysis_json.py` checks keys `estimated_power`, `target_N`, `method` and that `estimated_power` ≥ 0.80. **Depends on: T090b**.

- [ ] T091-ValidateScript **(Power‑Analysis Validation Script)** Implement `code/00_validate_power.py` that checks JSON thresholds.

- [ ] T091-Check **(Validate Power‑Analysis Results)** Run `code/00_validate_power.py` against the JSON. **Depends on: T091, T091-ValidateScript**. **Verification**: CI fails if thresholds not met.

- [ ] T099 **(Primary Pipeline CLI)** Add `code/run_pipeline.py` providing a unified CLI (`--mode real` or `--mode mock`). **GUARD CLAUSE**: `--mode mock` is disabled for primary analysis; invoking it with `--generate-report` exits error code 1 with message “Mock mode is not allowed for primary analysis; real data is required.” **Verification**: `tests/contract/test_cli_guard.py` confirms behavior.

- [ ] T099c **(Performance Documentation Alignment)** Update `plan.md` and `README.md` to state “≤ 6 hours”. **Verification**: `code/check_performance_phrase.py` scans both files for exact phrase. *Depends on: T001*.

- [ ] T013 **(Stimulus Generation)** Implement factorial generator `code/01_generate_stimuli.py` producing `data/raw/stimuli.csv` with columns: `stimulus_id,text,emoji_count,punctuation_type,length_category,scenario_id,cue_intensity`.  
  **Verification**: `pytest tests/contract/test_stimuli_schema.py` validates schema, data types, and uniqueness of all feature combinations. *Depends on: T001, T005, T090*.

- [ ] T013‑Schema‑Test **(Stimulus Schema Test)** Run `pytest tests/contract/test_stimuli_schema.py`. *Depends on: T013*.

- [ ] T014 **(Counterbalancing)** Create `code/02_counterbalance.py` that assigns every stimulus to both relationship contexts (“friend” and “acquaintance”) for every participant. Output `data/processed/counterbalanced_trials.csv`.  
  **Verification**: `tests/contract/test_counterbalance.py` checks correct row counts (N_participants × N_stimuli × 2). *Depends on: T013*.

- [ ] T015 **(Random Presentation Order)** Implement `code/03_random_order.py` to shuffle trial order per participant, saving `data/processed/presentation_orders.csv`.  
  **Verification**: `tests/contract/test_random_order.py` validates each participant’s order is a permutation and reproducible with fixed seed. *Depends on: T014*.

- [ ] T015a **(External Recruitment)** **EXTERNAL TASK**: Deploy survey via Prolific and collect `data/raw/real_ratings.csv`. **Verification**: File existence with required columns. *Maps to FR‑002*.

- [ ] T015b-Real **(Real Data Ingestion)** Write `code/02_collect_real_data.py --mode ingest` to verify and ingest `data/raw/real_ratings.csv`. Errors if file missing or malformed. *Depends on: T015a*.

- [ ] T015b‑ParticipantCount **(Participant Count Verification)** Add check that `real_ratings.csv` contains ≥ 60 unique `participant_id`s. **Verification**: `tests/contract/test_participant_count.py`. *Depends on: T015b-Real*.

- [ ] T015c-Guard **(Primary Pipeline Guard)** Extend `code/99_preanalysis_guard.py` to abort if mock data patterns are present in `data/raw/real_ratings.csv`. **Depends on: T015b-Real, T015b‑ParticipantCount**.

- [ ] T015c‑Guard‑Test **(Guard Verification Test)** Run `pytest tests/contract/test_preanalysis_guard_fail.py` to ensure guard aborts on mock data. *Depends on: T015c-Guard*.

- [ ] T016a **(Straight‑Lining Detection)** Implement detector in `code/03_clean_data.py` that flags participants with zero variance across all stimuli, outputting `data/processed/excluded_participants.csv`.  
  **Verification**: `tests/contract/test_straightlining.py` confirms flagged IDs have zero variance. *Depends on: T015b-Real*.

- [ ] T016b **(Listwise Deletion)** Extend cleaning script to remove flagged participants and rows with missing data, producing `data/processed/cleaned_ratings.csv`.  
  **Verification**: `tests/contract/test_cleaned_schema.py` validates schema. *Depends on: T016a*.

- [ ] T051 **(Anonymisation)** Transform `data/processed/cleaned_ratings.csv` to `data/processed/anonymised_ratings.csv` by hashing Prolific IDs and stripping PII.  
  **Verification**: `tests/contract/test_no_raw_ids.py` ensures no raw IDs remain. *Depends on: T016b*.

- [ ] T052 **(Checksum for Anonymised Ratings)** Compute SHA‑256 of `data/processed/anonymised_ratings.csv` and record in `data/checksums.json`. *Depends on: T051*.

- [ ] T054 **(Checksum for Raw Ratings)** Compute SHA‑256 of `data/raw/real_ratings.csv` and record in `data/checksums.json`. *Depends on: T015b-Real*.

- [ ] T112 **(Straight‑Lining Contract Test)** Load `data/processed/excluded_participants.csv` and assert each listed ID has zero variance in the original ratings. *Depends on: T016a*.

- [ ] T015c‑VerifyPrimaryScript **(Guard Verification Script)** Implement `code/guard_no_mock_data.py` that scans primary data paths for mock artifacts. **Verification**: Exits 0 when clean, non‑zero otherwise.

- [ ] T015c‑Verify **(Guard Verification)** Run `code/guard_no_mock_data.py` before analysis. *Depends on: T015c‑Guard, T015c‑Guard‑Test*.

- [ ] T020 **(Analysis‑Ready Merge)** Merge stimuli metadata with cleaned, anonymised ratings to create `data/processed/analysis_ready.csv`.  
  **Verification**: `tests/contract/test_analysis_ready_schema.py` validates schema. *Depends on: T016b, T015b‑ParticipantCount, T051*.

- [ ] T084a **(Analysis‑Ready Schema)** Add `contracts/analysis_ready.schema.yaml` defining required columns/types for `analysis_ready.csv`. *Verification*: schema file existence.

- [ ] T084 **(Validate Analysis‑Ready Schema)** Run `pytest tests/contract/test_analysis_ready_schema.py`. *Depends on: T020*.

- [ ] T021‑AmendPlan **(Plan Amendment: Satterthwaite via R)** Update `plan.md` and `spec.md` to state that the primary LMM will be fit using R's `lmerTest` (accessed via `rpy2`) to obtain Satterthwaite degrees of freedom. Add note that Wald‑Z is provided as a fallback.  
  **Depends on: T020**  
  **Verification**: `tests/contract/test_plan_amendment.py` diffs the files to confirm amendment presence.

- [ ] T021a **(Primary LMM Fit – Satterthwaite)** Implement `code/04_fit_lmm_r.py` that calls R's `lmerTest::lmer` via `rpy2` with formula `rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)`. Export fixed‑effect table to `data/results/lmm_summary.csv`. *Depends on: T020, T021‑AmendPlan*.

- [ ] T021b **(Export LMM Summary)** Ensure `data/results/lmm_summary.csv` contains columns `fixed_effect,estimate,stderr,z_value,p_value`. **Verification**: `tests/contract/test_lmm_summary_schema.py` passes.

- [ ] T021c **(Fallback Wald‑Z LMM)** Implement `code/04_fit_lmm_wald.py` using `statsmodels.MixedLM` with Wald‑Z approximation; generate `data/results/lmm_summary_wald.csv`. *Optional fallback only*.

- [ ] T021‑DocumentMethod **(Methodological Limitation Document)** Create `data/results/methodological_limitations.md` describing use of Satterthwaite via R, the Wald‑Z fallback, and justification.  
  **Verification**: `tests/contract/test_methodology_doc.py` checks both “Satterthwaite” and “Wald‑Z” appear.

- [ ] T021‑DocumentMethod‑Test **(Methodology Doc Test)** Run `pytest tests/contract/test_methodology_doc.py`. *Depends on: T021‑DocumentMethod*.

- [ ] T024 **(Tukey‑Corrected Post‑hoc)** Implement `code/05_posthoc.py` to run Tukey HSD on interaction marginal means when interaction p < 0.05. Always output `data/results/posthoc_tukey.csv` with a `significant` flag. *Depends on: T021a*.  
  **Verification**: `tests/contract/test_posthoc_schema.py` validates schema.

- [ ] T025 **(Result Serialization)** Combine LMM summary, post‑hoc results, and exclusion summary into `data/results/analysis_results.json`. *Depends on: T024*.

- [ ] T085 **(Validate LMM Summary Schema)** Ensure `contracts/lmm_summary.schema.yaml` matches `lmm_summary.csv`. *Verification*: test passes.

- [ ] T107 **(Checksum LMM Summary)** Record SHA‑256 of `data/results/lmm_summary.csv` in `data/checksums.json`. *Depends on: T021a*.

- [ ] T108 **(Checksum Post‑hoc)** Record SHA‑256 of `data/results/posthoc_tukey.csv` in `data/checksums.json`. *Depends on: T024*.

- [ ] T109 **(Checksum Analysis Results)** Record SHA‑256 of `data/results/analysis_results.json` in `data/checksums.json`. *Depends on: T025*.

- [ ] T027a **(Sensitivity – Equal Weight)** Run `code/06_sensitivity.py --scheme equal` → `data/results/sensitivity_equal.csv`. *Depends on: T090, T021a*.

- [ ] T027b **(Sensitivity – Emoji‑Dominant)** Run `code/06_sensitivity.py --scheme emoji` → `data/results/sensitivity_emoji.csv`. *Depends on: T090, T021a*.

- [ ] T027c **(Sensitivity – Punctuation‑Dominant)** Run `code/06_sensitivity.py --scheme punctuation` → `data/results/sensitivity_punct.csv`. *Depends on: T090, T021a*.

- [ ] T028 **(Aggregate Sensitivity Metrics)** Compute stability metrics from the three runs and save `data/processed/sensitivity_metrics.csv` (`scheme,beta_interaction,abs_beta,p_value,significant,direction,stability_score`). *Depends on: T027a, T027b, T027c*.  
  **Verification**: `tests/contract/test_sensitivity_metrics.py` validates file.

- [ ] T029 **(Sensitivity Report)** Generate `data/processed/sensitivity_report.md` summarising the stability table and interpreting results, including theoretical justification for each weighting scheme. *Depends on: T028*.  
  **Verification**: `tests/contract/test_sensitivity_report_schema.py` checks required sections.

- [ ] T056 **(Checksum Sensitivity Report)** Record SHA‑256 of `data/processed/sensitivity_report.md` in `data/checksums.json`. *Depends on: T029*.

- [ ] T110 **(Checksum Sensitivity Metrics)** Record SHA‑256 of `data/processed/sensitivity_metrics.csv` in `data/checksums.json`. *Depends on: T028*.

- [ ] T105 **(Validate Sensitivity Report Schema)** Ensure `sensitivity_report.md` contains required sections via `tests/contract/test_sensitivity_report_schema.py`. *Depends on: T029*.

- [ ] T033 **(Quickstart Update)** Revise `quickstart.md` with sections on power analysis, benchmarking, and CLI usage (`python code/run_pipeline.py --mode real`). *Verification*: `tests/contract/test_quickstart_commands.py` finds the command strings.

- [ ] T035 **(Determinism Verification)** Add `code/verify_determinism.py` that compares current hash of `analysis_results.json` to the value recorded in `data/manifest.json`. *Verification*: script exits 0 when hashes match.

- [ ] T036 **(Edge‑Case Unit Tests)** Add `tests/unit/test_edge_cases.py` covering missing data handling and participant ID format checks. *Verification*: tests pass.

- [ ] T038 **(Quickstart Integration Test)** Implement `tests/integration/test_quickstart.py` that runs the quickstart flow end‑to‑end. *Verification*: test passes.

- [ ] T040-Generate **(README Generation)** Create `code/README_generator.py` to produce a project `README.md` containing sections "CLI Usage", "Results Overview", and "Reproducibility". *Verification*: generated README includes all sections.

- [ ] T040-Verify **(README Content Test)** Add `tests/unit/test_readme_contents.py` asserting presence of the three sections.

- [ ] T042 **(Deterministic Output Comparison)** Implement `code/compare_hashes.py` to compare SHA‑256 of `analysis_results.json` and `sensitivity_report.md` across two runs; test `tests/contract/test_hash_determinism.py` ensures equality.

- [ ] T043 **(No GPU Imports Test)** Add `tests/unit/test_no_gpu_imports.py` scanning all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`). *Verification*: CI fails if any are found.

- [ ] T043a **(CI GPU‑Import Guard)** CI step runs the above test and aborts on failure.

- [ ] T044 **(CPU‑Only Constraint Documentation)** Document CPU‑only requirement in `quickstart.md` under "Environment Requirements". *Verification*: `tests/contract/test_cpu_constraint.md` checks for phrase "CPU-only".

- [ ] T045 **(Checksum Verification)** Implement `code/verify_checksums.py` to ensure every file listed in `data/checksums.json` exists and matches its recorded SHA‑256. *Verification*: script exits 0 on success.

- [ ] T046 **(No Raw IDs Verification)** Add `tests/contract/test_no_raw_ids.py` to regex‑check that `data/processed/anonymised_ratings.csv` contains no raw Prolific IDs.

- [ ] T100 **(Manifest Generation)** Write `code/99_manifest.py` that creates `data/manifest.json` after all artifacts are produced, recording SHA‑256 hashes. *Verification*: `utils/validate_manifest.py` validates before downstream consumption.

- [ ] T104 **(Methodological Limitation Note in Report)** Ensure `report.md` includes a paragraph referencing `data/results/methodological_limitations.md` that explains the **Wald‑Z** approximation used for the LMM (instead of Satterthwaite), citing the Python stack constraint. *Depends on: T021‑DocumentMethod*.

- [ ] T106 **(Full Pipeline Mock Integration Test)** Add `tests/integration/test_full_pipeline_mock.py` that runs the entire pipeline on mock data and asserts completion ≤ 21600 seconds.

- [ ] T113 **(Power‑Analysis JSON Contract Test)** Implement `tests/contract/test_power_analysis_json.py` to verify required keys in `power_analysis_results.json`. *Depends on: T091*.

- [ ] T124 **(Pre‑analysis Guard Implementation)** Extend `code/99_preanalysis_guard.py` to (a) confirm existence of `data/processed/anonymised_ratings.csv`, (b) validate against `rating.schema.yaml`, and (c) abort with clear error if checks fail. *Verification*: `tests/contract/test_preanalysis_guard.py` ensures non‑zero exit when conditions violated.

- [ ] T124‑Guard‑Test **(Pre‑analysis Guard Test)** Add `tests/contract/test_preanalysis_guard_fail.py` that deliberately removes `data/processed/anonymised_ratings.csv` and checks guard exits non‑zero.

- [ ] T125 **(Pre‑analysis Guard Test)** *Already covered by T124‑Guard‑Test*.

- [ ] T126 **(Mock‑Guard Test)** Add `tests/unit/test_mock_guard.py` confirming pipeline fails when mock data is present, relying on T124 and T125.

- [ ] T127 **(No‑Fallback Test)** Add `tests/unit/test_no_fallback.py` asserting that all data‑loading scripts raise explicit errors on fetch/validation failures and contain no silent synthetic fallback. *Depends on: T015b-Real, T015c‑Guard*.

- [ ] T128 **(CI Style Enforcement)** CI step to run `ruff` and `black --check` across the repository.

- [ ] T093 **(Final Manifest Generation)** After all artifacts are created, run `code/99_manifest.py` again to ensure the manifest is up‑to‑date. *Verification*: `utils/validate_manifest.py` passes.

- [ ] T129 **(Missing Values Check)** Implement `code/02_validate_ratings.py` to ensure `data/raw/real_ratings.csv` has no missing values in `stimulus_id`, `relationship_type`, or `rating`. *Verification*: `tests/contract/test_missing_values_exit.py` asserts non‑zero exit on violation.

- [ ] T130 **(Relationship Value Validation)** Extend the same script to confirm `relationship_type` contains only `"friend"` or `"acquaintance"`. *Verification*: `tests/contract/test_relationship_values.py`.

- [ ] T131 **(Cue‑Intensity Consistency Check)** Add `code/01_verify_cue_intensity.py` that recomputes cue intensity from stimulus features and asserts equality with values in `data/raw/stimuli.csv` using the primary weighting scheme from `cue_intensity_weights.json`. *Verification*: `tests/contract/test_cue_intensity_consistency.py` checks exit codes.

- [ ] T132 **(Power‑Analysis Section in Report)** Extend `code/07_generate_report.py` to include a "Power Analysis" section summarising estimated power, target sample size, and methodology.

- [ ] T133 **(Effect‑Size Computation)** Update `code/04_fit_lmm_r.py` to calculate Cohen's f for the interaction term and add column `cohens_f_interaction` to `data/results/lmm_summary.csv`. *Verification*: column present and non‑negative.

- [ ] T134 **(Effect‑Size Unit Test)** Add `tests/unit/test_effect_size.py` confirming that `cohens_f_interaction` is computed correctly and ≥ 0.

- [ ] T135 **(Runtime Benchmark)** Add `code/benchmark_runtime.py` that measures total pipeline runtime and fails if > 21600 seconds. *Verification*: CI step runs this benchmark; exits 0 on success, 1 on timeout.

- [ ] T140 **(Data Flow Ordering Verification)** Review and update `code/run_pipeline.py` to enforce strict execution order: Stimulus Generation → Counterbalancing → Random Order → Real Data Ingestion → Cleaning → Preprocessing → LMM → Post‑hoc → Sensitivity. *Verification*: `tests/integration/test_execution_order.py` asserts each step's output exists before the next begins.

- [ ] T141 **(Real Data Source Documentation)** Update `quickstart.md` and `README.md` to explicitly state that `data/raw/real_ratings.csv` MUST be a Prolific export and that the pipeline will fail if synthetic data is detected. *Verification*: `grep` check in CI confirms presence of "Prolific" and "fail" warnings.

- [ ] T142 **(Wald‑Z vs Satterthwaite Clarification)** Ensure `data/results/methodological_limitations.md` clearly distinguishes between Wald‑Z (fallback) and Satterthwaite (primary) approximations, justifying the choice and confirming the amendment. *Verification*: document contains both terms and rationale.

- [ ] T143 **(Sensitivity Analysis Theoretical Basis)** Add a section to `data/processed/sensitivity_report.md` citing theoretical hypotheses for the three weighting schemes (Equal, Emoji‑Dominant, Punctuation‑Dominant). *Verification*: report includes citations or theoretical references.

- [ ] T144 **(Final End-to-End Validation)** Run the complete pipeline with `--mode real` (using a valid mock dataset for CI) to ensure all tasks complete in order and all checksums are recorded. *Verification*: CI passes with `--mode real` using a small, pre‑generated dataset.

- [ ] T145 **(Constitutional Principle Checklist)** Add `tests/contract/test_constitutional_principles.py` to verify that all six constitutional principles (Reproducibility, Verified Accuracy, Data Hygiene, Single Source of Truth, Versioning Discipline, Human‑Subject Anonymity) are met by the generated artifacts. *Verification*: test suite passes.
