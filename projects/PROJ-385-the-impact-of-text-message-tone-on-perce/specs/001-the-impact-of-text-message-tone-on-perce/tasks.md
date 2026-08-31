# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-the-impact-of-text-message-tone-on-perce/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T037a [P] **(CLI Entry Point)** Implement `code/run_pipeline.py` supporting `--mode real`, `--mode benchmark`, and `--help`. **Verification**: `python code/run_pipeline.py --help` displays usage; `--mode real` triggers the full pipeline; `--mode benchmark` runs the benchmark. **Maps to**: FR-001, FR-002 (end-to-end execution).

- [ ] T090 [P] **(Weighting scheme definition)** Define cue-intensity weighting schemes. Store in `data/processed/cue_intensity_weights.json`. **Script**: `code/00_define_weights.py`. **Verification**: JSON file exists with EXACT numeric weights for the three schemes required by FR-005: (1) Equal Weight: `{ "emoji": 0.333, "punctuation": 0.333, "length": 0.333 }` (2) Emoji-Dominant: `{ "emoji": 0.6, "punctuation": 0.2, "length": 0.2 }` (3) Punctuation-Dominant: `{ "emoji": 0.2, "punctuation": 0.6, "length": 0.2 }`. The 'Equal Weight' scheme serves as the baseline.

- [ ] T090b [P] **(Synthetic datasets for power analysis)** Generate synthetic datasets for power analysis simulation. **Script**: `code/00_generate_synthetic_power_data.py`. **Output**: `data/processed/synthetic_power_datasets.zip`. **Verification**: Zip contains synthetic datasets with N=60, effect_size=0.25, and the exact random-effects structure (Participant, Stimulus) used in the LMM. [UNRESOLVED-CLAIM: c_3efbfc20 — status=not_enough_info] **Depends on**: T090.

- [ ] T091 [P] **(Run power analysis)** Perform simulation-based power analysis for the LMM using the synthetic datasets from T090b. **Script**: `code/00_run_power_simulation.py`. **Output**: `data/processed/power_analysis_results.json`. **Verification**: JSON includes keys `estimated_power`, `target_N`, `method`. **Depends on**: T090b.

- [ ] T091-Check [P] **(Validate power analysis results)** Validate power analysis results. **Verification**: Run `code/00_validate_power.py`; it exits with error if `estimated_power` < 0.80 **or** `target_N` < 60. [UNRESOLVED-CLAIM: c_20c0c7d3 — status=not_enough_info] **Depends on**: T091.

- [ ] T004 [P] Define data model in `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` (Stimulus, Participant, Rating, AnalysisResult). **Verification**: File exists; contains the exact entity headings `Stimulus`, `Participant`, `Rating`, `AnalysisResult` (case-sensitive) as verified by a script `code/verify_data_model.py` that parses the markdown and checks for these headings.

- [ ] T004-Verify [P] **(Robust Data Model Verification)** Validate `data-model.md` structure against a schema or hash to avoid brittle markdown parsing. **Verification**: `pytest tests/contract/test_data_model_schema.py` passes. **Depends on**: T004.

- [ ] T005 [P] Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`. **Verification**: Directories exist and each contains a `.gitkeep` file.

- [ ] T006 [P] Define and validate JSON/YAML schemas in `specs/001-the-impact-of-text-message-tone-on-perce/contracts/` (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_ready.schema.yaml`, `lmm_summary.schema.yaml`, `analysis_result.schema.yaml`). **Verification**: Run `pytest tests/contract/test_schema_validation.py` which loads each schema and validates a minimal example file; test must pass. **Depends on**: T004.

- [X] T007 [P] Create base configuration management for random seed pinning and path resolution in `code/config.py`. **Verification**: Importing `code.config` asserts `RANDOM_SEED` is set to an integer constant and `BASE_DATA_PATH` points to `data/`. **Depends on**: T006.

- [ ] T008 [P] Setup logging infrastructure via `code/logging_config.py` writing to `data/pipeline.log`. **Verification**: Importing the module creates `data/pipeline.log` and writes a startup message. **Depends on**: T007.

### Stimulus Generation & Validation

- [ ] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py`. **Output** `data/raw/stimuli.csv` with columns `id,text,emoji_count,punctuation_type,length_category,scenario_id,cue_intensity`. **Verification**: `python code/01_generate_stimuli.py --verify` exits 0 with log message confirming uniqueness of all combinations.

- [ ] T014 [US1] Counterbalancing task `code/02_counterbalance.py` that creates `data/processed/counterbalanced_trials.csv` assigning every stimulus to both relationship contexts (friend & acquaintance) for each participant. **Verification**: CSV contains the appropriate number of rows per stimulus per participant (one per context); the script exits successfully and a pytest test `tests/contract/test_counterbalance.py` confirms the row counts. **Depends on**: T013.

- [ ] T015 [US1] Random presentation order generator `code/03_random_order.py` producing `data/processed/presentation_orders.csv` with a shuffled trial order per participant. **Verification**: Each participant's order list is a permutation of their trial set; reproducible given the fixed seed. Test `tests/contract/test_random_order.py` validates permutation and deterministic seed behavior. **Depends on**: T014.

- [ ] T010a [US1] Create contract test `tests/contract/test_stimulus_schema.py` that loads `data/raw/stimuli.csv` and validates against `stimulus.schema.yaml`. **Verification**: `pytest tests/contract/test_stimulus_schema.py` passes. **Depends on**: T013.

### Rating Data (Real & Verification)

- [ ] T015b-Real [US1] Implement real data ingestion logic in `code/02_collect_real_data.py`. **Verification**: Verifies and ingests `data/raw/real_ratings.csv` (external Prolific export) with columns `participant_id,stimulus_id,relationship_type,rating,timestamp,prolific_id`. Script aborts with error if the source file is missing, empty, or contains mock patterns. **Depends on**: T014 (to know expected stimulus IDs).

- [ ] T015b-Verify [US1] Verify presence and quality of `data/raw/real_ratings.csv` using `code/02_validate_data.py`. {{claim:c_98a6f786}} (Wikidata Q14290457, https://www.wikidata.org/wiki/Q14290457) **Verification**: Script exits 0 on success, 1 on failure.

- [ ] T015b-ContextCheck [US1] Verify each participant has ratings for both relationship contexts. **Verification**: `code/02_check_contexts.py` exits non-zero if any participant missing a context.

- [ ] T015c-Guard [US1] Add guard to primary analysis pipeline to strictly reject `data/raw/real_ratings.csv` if it matches mock patterns. **Verification**: Pipeline aborts with clear error message when mock data detected.

- [ ] T015c-Verify [US1] Verify presence and validity of real consent records in `data/consent/`. **Verification**: `code/verify_consent.py` exits 0 if `provenance.json` exists and contains required fields.

- [ ] T015c-VerifyPrimary [US1] Verify that no mock data artifacts exist in the primary analysis path (`data/raw/`, `data/processed/`) before analysis tasks run. **Verification**: `code/guard_no_mock_data.py` exits 0 if clean, 1 otherwise.

- [ ] T051 [P] Anonymise `data/raw/real_ratings.csv` (hash Prolific IDs, strip PII) and write to `data/processed/anonymised_ratings.csv`. **Verification**: No raw IDs remain; column `participant_id` contains SHA-256 hashes. **Depends on**: T015b-Real.

- [ ] T086 [US1] Validate Participant entity: ensure `data/processed/anonymised_ratings.csv` contains a non-null `participant_id` column matching the Participant schema. **Verification**: Test `tests/contract/test_participant_schema.py` fails if column missing or malformed. **Depends on**: T051.

- [ ] T101 [P] Pre-analysis guard `code/99_preanalysis_guard.py` aborts pipeline when `data/processed/anonymised_ratings.csv` is absent, fails schema validation against `rating.schema.yaml`, or contains PII. **Verification**: Run the guard; it exits 0 on success, non-zero on any failure. **Depends on**: T051, T086, T015c-Guard.

- [ ] T102 [P] CI check `ci/check_real_data.yml` aborts pipeline when `data/raw/real_ratings.csv` is absent. **Verification**: CI job fails with informative message.

- [ ] T054 [P] Compute SHA-256 checksum for `data/raw/real_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists after T015b-Real. **Depends on**: T015b-Real.

- [ ] T052 [P] Compute SHA-256 checksum for `data/processed/anonymised_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists after T051. **Depends on**: T051.

### Data Cleaning & Straight-lining Detection

- [ ] T016a [US1] Implement straight-lining detector in `code/03_clean_data.py` that flags participants with zero variance across all stimuli and writes excluded IDs to `data/processed/excluded_participants.csv`. **Verification**: Script logs flagged IDs; `tests/contract/test_straightlining.py` loads the CSV and asserts that every listed ID has zero variance in the original ratings file. **Depends on**: T051.

- [ ] T016b [US1] Implement listwise deletion of any participant flagged by T016a or with missing ratings. Output cleaned dataset to `data/processed/cleaned_ratings.csv`. **Verification**: File created without excluded rows; schema validated by `tests/contract/test_cleaned_schema.py`. **Depends on**: T016a.

- [ ] T122 [US1] Unit test `tests/unit/test_listwise_deletion.py` that runs the cleaning script and checks that `data/processed/cleaned_ratings.csv` is created and validates against the schema. **Verification**: Test passes.

- [ ] T123 [US1] Document listwise-deletion options in `docs/data_cleaning.md`, including guidance on when to use it. **Verification**: Documentation file exists and contains section "Listwise Deletion".

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Create project structure per implementation plan (`code/`, `data/`, `tests/`). **Verification**: `ls -R` matches expected tree, `README.md` present. **Maps to**: FR-001 (foundation for stimulus generation) and SC-001 (reproducibility). *Infrastructure linked to functional requirements.*

- [ ] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scipy>=1.10.0, statsmodels>=0.14.0, pingouin>=0.5.3, pyyaml>=6.0, pytest>=7.0.0). **Verification**: `pip install -r code/requirements.txt` succeeds; `pip check` passes. **Maps to**: FR-007 (CPU-only, dependency control).

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in repository root (`ruff.toml`, `pyproject.toml`). **Verification**: `ruff check.` exits 0; `black --check.` exits 0. **Maps to**: FR-007 (code quality, reproducibility).

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T004 [X] Define data model in `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` (Stimulus, Participant, Rating, AnalysisResult). **Verification**: File exists; contains the exact entity headings `Stimulus`, `Participant`, `Rating`, `AnalysisResult` (case-sensitive) as verified by a script `code/verify_data_model.py` that parses the markdown and checks for these headings.

- [ ] T005 [X] Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`. **Verification**: Directories exist and each contains a `.gitkeep` file.

- [ ] T006 [X] Define and validate JSON/YAML schemas in `specs/001-the-impact-of-text-message-tone-on-perce/contracts/` (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_ready.schema.yaml`, `lmm_summary.schema.yaml`, `analysis_result.schema.yaml`). **Verification**: Run `pytest tests/contract/test_schema_validation.py` which loads each schema and validates a minimal example file; test must pass.

- [ ] T007 [X] Create base configuration management for random seed pinning and path resolution in `code/config.py`. **Verification**: Importing `code.config` asserts `RANDOM_SEED` is set to an integer constant and `BASE_DATA_PATH` points to `data/`.

- [ ] T008 [X] Setup logging infrastructure via `code/logging_config.py` writing to `data/pipeline.log`. **Verification**: Importing the module creates `data/pipeline.log` and writes a startup message.

## Phase 3: User Story 1 – Stimulus Generation & Data Collection (Priority: P1)

- [ ] T058 [P] Benchmark full pipeline (`--benchmark`). **Verification**: Outputs `total_duration_seconds`; fails if >21600.

## Phase 4: User Story 2 – Statistical Analysis Pipeline (Priority: P2)

- [ ] T020 [US2] Data preprocessing in `code/04_fit_lmm.py` (listwise deletion, reads `data/processed/anonymised_ratings.csv` via pre-analysis guard). **Output** `data/processed/analysis_ready.csv`. **Verification**: File created; schema validated by `tests/contract/test_analysis_ready_schema.py`. **Depends on**: T051, T101, T015c-Guard.

- [ ] T084a [US2] Create `analysis_ready.schema.yaml` defining required columns and types for `analysis_ready.csv`. **Verification**: Schema file exists under `contracts/`.

- [ ] T084 [US2] Validate `analysis_ready.schema.yaml` against `data/processed/analysis_ready.csv`. **Verification**: Test `tests/contract/test_analysis_ready_schema.py` passes.

- [ ] T021 [US2] **PRIMARY** LMM script `code/04_fit_lmm.py` fits model using **statsmodels.MixedLM** with **Wald-Z statistics** (as Satterthwaite is not supported). **Output** `data/results/lmm_summary.csv` with columns `fixed_effect,estimate,stderr,z_value,p_value`. **Verification**: {{claim:c_29a6f505}} (Wikidata Q67272, https://www.wikidata.org/wiki/Q67272) **Depends on**: T020.

- [ ] T021-Doc [US2] Document methodological limitation in `data/results/methodological_limitations.md` explaining why `statsmodels` (Wald-Z) was chosen and that Satterthwaiteis not supported. **Verification**: File contains the required explanatory sentences.

- [ ] T085 [US2] Validate `lmm_summary.schema.yaml` against `data/results/lmm_summary.csv`. **Verification**: Tests pass.

- [ ] T023a [US2] Log warning if stimulus variance component <0.001 and generate transient exclusion object. **Verification**: Log entry created; test `tests/unit/test_low_variance_warning.py` passes.

- [ ] T023b [US2] Unit test for low-variance warning logic. **Verification**: Test passes.

- [ ] T024 [US2] Implement Tukey-corrected post-hoc pairwise comparisons (triggered on significant interaction in the primary model). **Output** `data/results/posthoc_tukey.csv` always generated; includes `significant` flag column. **Verification**: File created; schema validated by `tests/contract/test_posthoc_schema.py`. **Depends on**: T021.

- [ ] T025 [US2] Serialize final results to `data/results/analysis_results.json`, merging exclusion summary. **Verification**: JSON includes `exclusion_summary` key.

- [ ] T111 [P] Validate `posthoc_tukey.schema.yaml` against `data/results/posthoc_tukey.csv`. **Verification**: Test passes.

- [ ] T107 [P] Compute SHA-256 checksum for `data/results/lmm_summary.csv` and record in `data/checksums.json`. **Verification**: Entry exists. **Depends on**: T021.

- [ ] T108 [P] Compute SHA-256 checksum for `data/results/posthoc_tukey.csv` and record in `data/checksums.json`. **Verification**: Entry exists. **Depends on**: T024.

- [ ] T109 [P] Compute SHA-256 checksum for `data/results/analysis_results.json` and record in `data/checksums.json`. **Verification**: Entry exists. **Depends on**: T025.

#### New safeguards

- [ ] T124 [P] Implement the full pre-analysis guard in `code/99_preanalysis_guard.py` to (a) confirm existence of `data/processed/anonymised_ratings.csv`, (b) validate it against `rating.schema.yaml`, and (c) abort with a clear error message if any check fails. **Verification**: `pytest tests/contract/test_preanalysis_guard.py` ensures the script exits non-zero when the file is missing or invalid.

- [ ] T125 [P] Add contract test `tests/contract/test_preanalysis_guard.py` that deliberately removes `data/processed/anonymised_ratings.csv` and verifies that the guard script exits with a non-zero status. **Verification**: Test passes.

## Phase 5: User Story 3 – Methodological Robustness & Sensitivity Reporting (Priority: P3)

- [ ] T027 [US3] Sensitivity analysis engine `code/05_sensitivity_analysis.py` reads definitions from `data/processed/cue_intensity_weights.json` (output of T090) and re-runs LMM by importing the fitting function from `code/04_fit_lmm.py` (T021) to ensure single source of truth. **Verification**: Runs without error and produces intermediate results for the three schemes (Equal, Emoji-Dominant, Punctuation-Dominant). **Depends on**: T090, T021.

- [ ] T029 [US3] Compute stability metrics and store in `data/processed/sensitivity_metrics.csv`. **Columns**: `scheme,beta_interaction,abs_beta,p_value,significant,direction,stability_score`. **Verification**: CSV contains all required columns; test `tests/contract/test_sensitivity_metrics.py` validates content. **Depends on**: T027.

- [ ] T030 [US3] Generate `data/processed/sensitivity_report.md` summarising stability. **Verification**: Non-empty report file; includes a table of the three schemes and their beta/p-value values. **Depends on**: T029.

- [ ] T056 [P] Compute SHA-256 checksum for `data/processed/sensitivity_report.md` and record in `data/checksums.json`. **Verification**: Entry exists. **Depends on**: T030.

- [ ] T110 [P] Compute SHA-256 checksum for `data/processed/sensitivity_metrics.csv` and record in `data/checksums.json`. **Verification**: Entry exists. **Depends on**: T029.

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T033 [P] Update `quickstart.md` with sections on power analysis, benchmarking, and CLI usage. **Verification**: File contains the exact command strings `python code/run_pipeline.py --mode real` and `python code/run_pipeline.py --help`; pytest test `tests/contract/test_quickstart_commands.py` searches for these strings.

- [ ] T035 [P] Run full pipeline with fixed seed; compute SHA-256 of `analysis_results.json` and verify deterministic hash. **Verification**: Script `code/verify_determinism.py` compares current hash to recorded value in `data/manifest.json`.

- [ ] T036 [P] Add edge-case unit tests `tests/unit/test_edge_cases.py` (missing data handling, PID format). **Verification**: Tests pass.

- [ ] T038 [P] Run quickstart integration test. **Verification**: `pytest tests/integration/test_quickstart.py` passes.

- [ ] T099 [P] Align performance documentation: update `plan.md` and `README.md` to state "≤ 6 hours". **Verification**: Script `code/check_performance_phrase.py` scans both files and fails if the exact phrase is missing.

- [ ] T040-Generate [P] Generate final feature-folder `README.md` with usage and results sections via `code/README_generator.py`. **Verification**: Generated README contains sections "CLI Usage", "Results Overview", and "Reproducibility".

- [ ] T040-Verify [P] Test `tests/unit/test_readme_contents.py` asserting the presence of the above sections.

- [ ] T042 [P] Verify deterministic pipeline output by comparing SHA-256 of `analysis_results.json` and `sensitivity_report.md` across two runs. **Verification**: `code/compare_hashes.py` reports identical hashes; test `tests/contract/test_hash_determinism.py` passes.

- [ ] T043 [P] Ensure no GPU-specific imports exist. **Verification**: `tests/unit/test_no_gpu_imports.py` scans all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`); CI fails if any are found.

- [ ] T043a [P] Add CI step to run `tests/unit/test_no_gpu_imports.py` and fail the pipeline if any GPU import is detected. **Verification**: CI job fails on detection.

- [ ] T044 [P] Document CPU-only constraint in `quickstart.md` under "Environment Requirements". **Verification**: Section present; test `tests/contract/test_cpu_constraint.md` checks for phrase "CPU-only".

## Phase N+1: Additional Verification & Determinism

- [ ] T045 [P] Verify every dataset file listed in `data/checksums.json` exists and matches recorded SHA-256. **Verification**: Script `code/verify_checksums.py` exits 0 on success.

- [ ] T046 [P] Verify `data/processed/anonymised_ratings.csv` contains no raw Prolific IDs (regex check). **Verification**: Test `tests/contract/test_no_raw_ids.py` passes.

## Phase N+2: Final Review & Compliance Tasks

- [ ] T100 [P] Manifest generation script `code/99_manifest.py` writes `data/manifest.json` after each artifact creation; validation via `utils/validate_manifest.py`. **Verification**: CI step runs script and validates manifest before any downstream consumption.

- [ ] T103 [P] Static-analysis test `tests/unit/test_no_gpu_imports.py` scans all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`). **Verification**: Test fails if any such import is found.

- [ ] T104 [P] Document in `report.md` that `statsmodels.MixedLM` uses Wald-Z statistics (primary) and reference the plan section. **Verification**: Search finds disclaimer string.

- [ ] T105 [P] Validate `data/processed/sensitivity_report.md` includes columns `scheme,beta_interaction,abs_beta,p_value,significant,direction,stability_score` via schema test. **Verification**: Test passes.

- [ ] T106 [P] Integration test `tests/integration/test_full_pipeline_mock.py` runs entire pipeline and asserts completion ≤ 21600 seconds. **Verification**: Test passes within time budget.

- [ ] T112 [P] Contract test for straight-lining detector: load `data/processed/cleaned_ratings.csv` and verify that flagged participants list matches expectations based on zero variance. **Verification**: Test passes.

- [ ] T113 [P] Contract test for power-analysis JSON: ensure `data/processed/power_analysis_results.json` contains keys `estimated_power`, `target_N`, and `method`. **Verification**: Test passes.

- [ ] T126 [P] Add test `tests/unit/test_mock_guard.py` to confirm that the pipeline **fails** if any mock data is detected in the primary path (verifying the guard logic). **Verification**: Test passes.

- [ ] T127 [P] Add unit test `tests/unit/test_no_fallback.py` that asserts all data-loading scripts raise explicit errors on fetch or validation failures and contain no silent fallback to synthetic data. **Verification**: Test passes.

- [ ] T128 [P] Add CI step that runs `ruff` and `black --check` to enforce code style compliance across the entire repository.

## Phase N+3: Manifest Finalization (post-artifact)

- [ ] T093 [P] Generate project manifest `data/manifest.json` **after** all artifact-creation tasks have completed (stimuli, ratings, processed files, analysis results, sensitivity reports, checksums). **Verification**: Manifest includes SHA-256 hashes for every file and passes `utils/validate_manifest.py` before any downstream consumption.

## Phase N+4: Additional Data Quality Checks

- [ ] T129 [P] Verify that `data/raw/real_ratings.csv` contains no missing values in critical columns (`stimulus_id`, `relationship_type`, `rating`). **Verification**: `code/02_validate_ratings.py` exits 0 if all required fields are present for every row.

- [ ] T130 [P] Verify that `relationship_type` column in `data/raw/real_ratings.csv` contains only the allowed values `"friend"` or `"acquaintance"`. **Verification**: Validation script fails with clear error if any other value is found.

- [ ] T131 [P] Verify that the `cue_intensity` column in `data/raw/stimuli.csv` matches the primary weighting scheme defined in `data/processed/cue_intensity_weights.json`. **Verification**: `code/01_verify_cue_intensity.py` recomputes cue intensity for each stimulus and asserts equality.

- [ ] T132 [P] Add a "Power Analysis" section to `report.md` summarising the estimated power, target sample size, and methodology used. **Verification**: `code/07_generate_report.py` includes this section when generating the final report.

- [ ] T133 [P] Extend `code/04_fit_lmm.py` to compute and output an effect-size metric (Cohen's f) for the interaction term, adding a column `cohens_f_interaction` to `data/results/lmm_summary.csv`. [UNRESOLVED-CLAIM: c_1b45799c — status=not_enough_info] **Verification**: Column present and populated; test `tests/unit/test_effect_size.py` confirms non-negative values.

- [ ] T134 [P] Add unit test `tests/unit/test_effect_size.py` to confirm that `cohens_f_interaction` is correctly calculated and non-negative.

- [ ] T135 [P] Add CI step `code/benchmark_runtime.py` to enforce that the total runtime of the full pipeline (all phases) does not exceed 6 hours on the standard GitHub Actions runner. **Verification**: CI fails if runtime > 21600 seconds.