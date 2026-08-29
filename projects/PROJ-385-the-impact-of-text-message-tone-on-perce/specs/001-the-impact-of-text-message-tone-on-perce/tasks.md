# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-the-impact-of-text-message-tone-on-perce/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data-model.md`, `contracts/`

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

## Phase 0: Research & Design (covers implementation plan sub‑steps 0.1‑0.5)

- [X] T090 [P] Define cue‑intensity weighting schemes. Store in `data/processed/cue_intensity_weights.json`. **Script**: `code/00_define_weights.py`. **Verification**: JSON file exists with EXACT numeric weights for three schemes: (1) Primary: `{ "emoji": 0.4, "punctuation": 0.3, "length": 0.3 }` (2) Emoji‑Dominant: `{ "emoji": 0.6, "punctuation": 0.2, "length": 0.2 }` (3) Punctuation‑Dominant: `{ "emoji": 0.2, "punctuation": 0.6, "length": 0.2 }`.
- [ ] T090a [P] Generate synthetic datasets for power analysis simulation. **Script**: `code/00_generate_synthetic_power_data.py`. **Output**: `data/processed/synthetic_power_datasets.zip`. **Verification**: Zip file contains multiple CSVs with correct schema and N=60 per dataset.
- [ ] T091 [P] Perform simulation‑based power analysis for the LMM using the synthetic datasets from T090a. **Script**: `code/00_run_power_simulation.py`. **Output**: `data/processed/power_analysis_results.json`. **Verification**: JSON includes `estimated_power`, `target_N`, and `method`. **Depends on**: T090a.
- [ ] T091-Check [P] Validate power analysis results. **Verification**: Run `code/00_validate_power.py` which exits with error if `estimated_power` < 0.80 **or** `target_N` < 60. **Depends on**: T091.
- [ ] T050 [P] Compute SHA‑256 checksum for `data/raw/stimuli.csv` and record in `data/checksums.json`. **Verification**: JSON entry exists.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`). **Verification**: `ls -R` matches expected tree, `README.md` present.
- [X] T002 Initialize Python project with pinned dependencies in `code/requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scipy>=1.10.0, statsmodels>=0.14.0, pyyaml>=6.0, pytest>=7.0.0). **Verification**: `pip check` succeeds.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in repository root (`ruff.toml`, `pyproject.toml`). **Verification**: `ruff check.` exits 0.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 Define data model in `specs/001-the-impact-of-text-message-tone-on-perce/data-model.md` (Stimulus, Participant, Rating, AnalysisResult). **Verification**: grep finds all entities.
- [X] T005 Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`. **Verification**: directories exist with `.gitkeep`.
- [X] T006 [P] Define and validate JSON/YAML schemas in `specs/001-the-impact-of-text-message-tone-on-perce/contracts/` (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_ready.schema.yaml`, `lmm_summary.schema.yaml`, `analysis_result.schema.yaml`). **Verification**: `yamllint` passes; schema tests exist.
- [X] T007 Create base configuration management for random seed pinning and path resolution in `code/config.py`. **Verification**: Import asserts `RANDOM_SEED` set.
- [X] T008 [P] Setup logging infrastructure via `code/logging_config.py` writing to `data/pipeline.log`. **Verification**: Import creates log file.

### Stimulus Generation & Validation

- [X] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py`. **Output** `data/raw/stimuli.csv` with columns `id,text,emoji_count,punctuation_type,length_category,scenario_id,cue_intensity`. **Verification**: `python code/01_generate_stimuli.py --verify` exits 0 with log message.
- [ ] T013-Verify [US1] Contract test `tests/contract/test_stimulus_uniqueness.py` that loads `data/raw/stimuli.csv` and asserts that each combination of `emoji_count`, `punctuation_type`, and `length_category` is unique. **Verification**: `pytest` passes.
- [ ] T014 [US1] Counterbalancing task `code/02_counterbalance.py` that creates `data/processed/counterbalanced_trials.csv` assigning every stimulus to both relationship contexts (friend & acquaintance) for each participant. **Verification**: CSV contains rows for each stimulus‑context pair per participant.
- [ ] T014-Verify [US1] Test `tests/contract/test_counterbalance.py` ensuring that for each participant each stimulus appears exactly twice (once per context).
- [ ] T015 [US1] Random presentation order generator `code/03_random_order.py` producing `data/processed/presentation_orders.csv` with a shuffled trial order per participant. **Verification**: Each participant's order list is a permutation of their trial set.
- [ ] T015-Verify [US1] Test `tests/contract/test_random_order.py` confirming per‑participant permutation and reproducibility given the fixed seed.
- [ ] T010a [US1] Create contract test `tests/contract/test_stimulus_schema.py` that loads `data/raw/stimuli.csv` and validates against `stimulus.schema.yaml`. **Verification**: `pytest` passes.

### Rating Data (Real & Verification)

- [ ] T015b-Real [US1] Implement real data ingestion logic in `code/02_collect_real_data.py`. **Verification**: Generates `data/raw/real_ratings.csv` with proper columns.
- [ ] T015b-Verify [US1] **Automated** Verify presence of `data/raw/real_ratings.csv` using `code/02_validate_data.py`. Check N≥60 unique participants, valid Prolific ID format, and absence of simulated data. **Verification**: Script exits 0 if valid, 1 if invalid.
- [ ] T015b-ContextCheck [US1] Verify that each participant has ratings for both relationship contexts. **Verification**: Script fails if any participant missing a context.
- [ ] T015c-Guard [US1] Add guard to primary analysis pipeline to strictly reject `data/raw/real_ratings.csv` if it matches mock patterns. **Verification**: Pipeline aborts with clear error if mock data detected in primary path.
- [ ] T015c-Verify [US1] **Automated** Verify presence and validity of real consent records in `data/consent/`. **Verification**: Script exits 0 if valid, 1 if invalid.
- [ ] T015c-VerifyPrimary [US1] **Build Step** Verify that no mock data artifacts exist in the primary analysis path (`data/raw/`, `data/processed/`) before analysis tasks run. **Verification**: Script exits 0 if clean, 1 if mock data found.
- [ ] T051 [P] Anonymise `data/raw/real_ratings.csv` (hash Prolific IDs, strip PII) and write to `data/processed/anonymised_ratings.csv`. **Verification**: No raw IDs remain. **Depends on**: T015b-Real.
- [ ] T086 [US1] Validate Participant entity: ensure `data/processed/anonymised_ratings.csv` contains a non‑null `participant_id` column matching the Participant schema. **Verification**: Test fails if column missing or malformed. **Depends on**: T051.
- [ ] T101 [P] Pre‑analysis guard `code/99_preanalysis_guard.py` aborts pipeline when `data/processed/anonymised_ratings.csv` is absent, fails schema validation against `rating.schema.yaml`, or contains PII. **Verification**: Pipeline stops with clear error; test T125 confirms non‑zero exit on failure.
- [X] T102 [P] CI check `ci/check_real_data.yml` aborts pipeline when `data/raw/real_ratings.csv` is absent. **Verification**: CI job fails with informative message.
- [ ] T054 [P] Compute SHA‑256 checksum for `data/raw/real_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T052 [P] Compute SHA‑256 checksum for `data/processed/anonymised_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists.

### Data Cleaning & Straight‑lining Detection

- [ ] T016a [US1] Implement straight‑lining detector in `code/03_clean_data.py` that flags participants with zero variance across all stimuli and writes excluded IDs to `data/processed/excluded_participants.csv`. **Verification**: Log shows flagged participants, file created.
- [ ] T016b [US1] Implement listwise deletion of any participant flagged by T016a or with missing ratings. Output cleaned dataset to `data/processed/cleaned_ratings.csv`. **Verification**: File created without excluded rows.
- [ ] T122 [US1] Unit test `tests/unit/test_listwise_deletion.py` that runs the cleaning script and checks that `data/processed/cleaned_ratings.csv` is created and validates against the schema. **Verification**: Test passes.
- [X] T123 [US1] Document listwise‑deletion options in `docs/data_cleaning.md`, including guidance on when to use it. **Verification**: Documentation file exists and contains section "Listwise Deletion".

## Phase 3: User Story 1 – Stimulus Generation & Data Collection (Priority: P1)

- [ ] T037a [P] Implement CLI entry point `code/run_pipeline.py` supporting `--mode real`. **Verification**: `--help` displays options. **Note**: `--mode mock` is REMOVED; primary analysis strictly requires `--mode real`.
- [ ] T058 [P] Benchmark full pipeline (`--benchmark`). **Verification**: Outputs `total_duration_seconds`; fails if >21600.

## Phase 4: User Story 2 – Statistical Analysis Pipeline (Priority: P2)

- [ ] T020 [US2] Data preprocessing in `code/04_fit_lmm.py` (listwise deletion, reads `data/processed/anonymised_ratings.csv` via pre‑analysis guard). **Output** `data/processed/analysis_ready.csv`. **Verification**: File created. **Depends on**: T051, T101, T015c-Guard.
- [ ] T084a [US2] Create `analysis_ready.schema.yaml` defining required columns and types for `analysis_ready.csv`. **Verification**: Schema file exists under `contracts/`.
- [ ] T084 [US2] Validate `analysis_ready.schema.yaml` against `data/processed/analysis_ready.csv`. **Verification**: Test passes.
- [ ] T021 [US2] **PRIMARY** LMM script `code/04_fit_lmm.py` fits model using `statsmodels.MixedLM` (Wald‑Z) as mandated by the Plan (Phase 3, Step 3.3). **Output** `data/results/lmm_summary.csv` with `df_Wald` column. **Verification**: Summary file created with required columns. **Depends on**: T020.
- [ ] T021-Verify [US2] Test `tests/contract/test_lmm_wald.py` confirming that the summary exists, `df_Wald > 0 [UNRESOLVED-CLAIM: c_9260a024 — status=not_enough_info] `, and {{claim:c_1409b017}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value). **Verification**: Test passes.
- [ ] T085 [US2] Validate `lmm_summary.schema.yaml` against `data/results/lmm_summary.csv`. **Verification**: Tests pass.
- [ ] T022 [US2] Document Methodological Limitation in `data/results/methodological_limitations.md` explaining that `statsmodels.MixedLM` uses Wald‑Z statistics (primary) and that {{claim:c_2ca977bd}}, citing Plan Phase 3 Step 3.3 as the reason for this deviation from the Spec's mention of Satterthwaite. **Verification**: File contains string "statsmodels.MixedLM uses Wald-Z statistics (primary)" and "Plan Phase 3 Step 3.3".
- [ ] T023a [US2] Log warning if stimulus variance component <0.001 and generate transient exclusion object. **Verification**: Log entry created.
- [ ] T023b [US2] Unit test for low‑variance warning logic. **Verification**: Test passes.
- [ ] T024 [US2] Implement Tukey‑corrected post‑hoc pairwise comparisons (triggered on significant interaction in the primary model). **Output** `data/results/posthoc_tukey.csv` always generated; includes `significant` flag column indicating whether each comparison is significant. **Verification**: File created regardless of p‑value.
- [ ] T025 [US2] Serialize final results to `data/results/analysis_results.json`, merging exclusion summary. **Verification**: JSON includes `exclusion_summary`.
- [ ] T111 [P] Validate `posthoc_tukey.schema.yaml` against `data/results/posthoc_tukey.csv`. **Verification**: Test passes.
- [ ] T107 [P] Compute SHA‑256 checksum for `data/results/lmm_summary.csv` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T108 [P] Compute SHA‑256 checksum for `data/results/posthoc_tukey.csv` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T109 [P] Compute SHA‑256 checksum for `data/results/analysis_results.json` and record in `data/checksums.json`. **Verification**: Entry exists.

#### New tasks to solidify analysis safeguards

- [ ] T124 [P] T101a – Implement the full pre‑analysis guard in `code/99_preanalysis_guard.py` to (a) confirm existence of `data/processed/anonymised_ratings.csv`, (b) validate it against `rating.schema.yaml`, and (c) abort with a clear error message if any check fails.
- [ ] T125 [P] T101b – Add contract test `tests/contract/test_preanalysis_guard.py` that deliberately removes `data/processed/anonymised_ratings.csv` and verifies that the guard script exits with a non‑zero status.

## Phase 5: User Story 3 – Methodological Robustness & Sensitivity Reporting (Priority: P3)

- [ ] T027 [US3] Sensitivity analysis engine `code/05_sensitivity_analysis.py` reads definitions from `data/processed/cue_intensity_weights.json` (output of T090) and re‑runs LMM by **importing the fitting function from `code/04_fit_lmm.py` (T021)** to ensure single source of truth. **Verification**: Runs without error. **Depends on**: T090, T021.
- [ ] T029 [US3] Compute stability metrics and store in `data/processed/sensitivity_metrics.csv`. **Columns**: `scheme`, `beta_interaction`, `abs_beta` (magnitude = |beta|), `p_value`, `significant`, `direction` (positive/negative based on sign of beta), `stability_score` (calculated as variance of beta_interaction across the three schemes). **Verification**: CSV contains all required columns. **Depends on**: T027.
- [ ] T030 [US3] Generate `data/processed/sensitivity_report.md` summarising stability. **Verification**: Non‑empty report file.
- [ ] T056 [P] Compute SHA‑256 checksum for `data/processed/sensitivity_report.md` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T110 [P] Compute SHA‑256 checksum for `data/processed/sensitivity_metrics.csv` and record in `data/checksums.json`. **Verification**: Entry exists.

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T033 [P] Update `quickstart.md` with sections on power analysis, benchmarking, and CLI usage. **Verification**: Commands present.
- [ ] T035 [P] Run full pipeline with fixed seed; compute SHA‑256 of `analysis_results.json` and verify deterministic hash. **Verification**: Hash matches recorded value.
- [ ] T036 [P] Add edge‑case unit tests `tests/unit/test_edge_cases.py` (missing data handling, PID format). **Verification**: Tests pass.
- [ ] T038 [P] Run quickstart integration test. **Verification**: `pytest` passes.
- [ ] T099 [P] Align performance documentation: update `plan.md` and `README.md` to state {{claim:c_14d2dab3}} **and verify** that both files contain the exact phrase "≤ 6 hours". **Verification**: Script scans the files and fails if the phrase is missing.
- [ ] T040-Generate [P] Generate final feature‑folder `README.md` with usage and results sections via `code/README_generator.py`. **Verification**: README contains sections "CLI Usage", "Results Overview", and "Reproducibility".
- [ ] T040-Verify [P] Test `tests/unit/test_readme_contents.py` asserting the presence of the above sections in the generated README.
- [ ] T042 [P] Verify deterministic pipeline output by comparing SHA‑256 of `analysis_results.json` and `sensitivity_report.md` across two runs. **Verification**: Hashes identical.
- [ ] T043 [P] Ensure no GPU‑specific imports exist. **Verification**: `tests/unit/test_no_gpu_imports.py` scans codebase.
- [ ] T043a [P] Add CI step to run `tests/unit/test_no_gpu_imports.py` and fail the pipeline if any GPU import is detected. **Verification**: CI job fails on detection.
- [ ] T044 [P] Document CPU‑only constraint in `quickstart.md` under "Environment Requirements". **Verification**: Section present.

## Phase N+1: Additional Verification & Determinism

- [ ] T045 [P] Verify every dataset file listed in `data/checksums.json` exists and matches recorded SHA‑256. **Verification**: Automated script passes.
- [ ] T046 [P] Verify `data/processed/anonymised_ratings.csv` contains no raw Prolific IDs (regex check). **Verification**: Test passes.

## Phase N+2: Final Review & Compliance Tasks

- [ ] T100 [P] Manifest generation script `code/99_manifest.py` writes `data/manifest.json` after each artifact creation; validation via `utils/validate_manifest.py`. **Verification**: CI step runs script and validates manifest before downstream tasks.
- [ ] T103 [P] Static‑analysis test `tests/unit/test_no_gpu_imports.py` scans all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`). **Verification**: Test fails if any such import is found.
- [ ] T104 [P] Document in `report.md` that `statsmodels.MixedLM` uses Wald‑Z statistics (primary) and that {{claim:c_2ca977bd}}. **Verification**: Search finds disclaimer string.
- [ ] T105 [P] Validate `data/processed/sensitivity_report.md` includes columns `scheme,beta_interaction,abs_beta,p_value,significant,direction,stability_score` via schema test. **Verification**: Test passes.
- [ ] T106 [P] Integration test `tests/integration/test_full_pipeline_mock.py` runs entire pipeline and asserts completion ≤ 21600 seconds. **Verification**: Test passes within time budget.
- [ ] T112 [P] Contract test for straight‑lining detector: load `data/processed/cleaned_ratings.csv` and verify that flagged participants list matches expectations based on zero variance. **Verification**: Test passes.
- [ ] T113 [P] Contract test for power‑analysis JSON: ensure `data/processed/power_analysis_results.json` contains keys `estimated_power`, `target_N`, and `method`. **Verification**: Test passes.
- [ ] T126 [P] Add test `tests/unit/test_mock_guard.py` to confirm that the pipeline **fails** if any mock data is detected in the primary path (verifying the guard logic).
- [ ] T127 [P] Add unit test `tests/unit/test_no_fallback.py` that asserts all data-loading scripts (`code/01_generate_stimuli.py`, `code/02_collect_real_data.py`, `code/03_clean_data.py`) raise explicit errors on fetch or validation failures and contain no silent fallback to synthetic data. **Verification**: Test passes.
- [ ] T128 [P] Add CI step that runs `ruff` and `black --check` to enforce code style compliance across the entire repository.

## Phase N+3: Manifest Finalization (post‑artifact)

- [ ] T093 [P] Generate project manifest `data/manifest.json` **after** all artifact‑creation tasks have completed (stimuli, ratings, processed files, analysis results, sensitivity reports, checksums). **Verification**: Manifest includes SHA‑256 hashes for every file and passes `utils/validate_manifest.py` before any downstream consumption.