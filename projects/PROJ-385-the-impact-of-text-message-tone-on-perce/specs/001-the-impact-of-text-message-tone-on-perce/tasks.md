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

- [ ] T090 [P] Define cue‑intensity weighting schemes. Store in `data/processed/cue_intensity_weights.json`. **Verification**: JSON file exists with four scheme objects: () Primary (0.4/0.3/0.3), (2) Equal (0.33/0.33/0.33), (3) Emoji-Dominant (0.6/0.2/0.2), (4) Punctuation-Dominant (0.2/0.6/0.2).
- [ ] T091 [P] Perform simulation‑based power analysis for the LMM using a large set of synthetic datasets. Write results to `data/processed/power_analysis_results.json`. **Verification**: JSON includes `estimated_power` and `target_N`.
- [ ] T091-Check [P] Validate power analysis results. **Verification**: Script exits with error if `estimated_power` < 0.80 or `target_N` < 60.
- [ ] T092 [P] Guard task: Verify that the LMM script (`code/04_fit_lmm.py`) reads directly from `data/processed/anonymised_ratings.csv`. The script must exit with error if it attempts to load any raw file. **Verification**: CI step runs the guard and fails on incorrect path usage.
- [ ] T093 [P] Generate project manifest `data/manifest.json` after every artifact creation (stimuli, ratings, cleaned data, analysis results, sensitivity report). **Verification**: Manifest contains SHA‑256 hashes for all listed files and passes validation script `utils/validate_manifest.py`.

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

- [X] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py`. **Output** `data/raw/stimuli.csv` with columns `id,text,emoji_count,punctuation_type,length_category,scenario_id,cue_intensity`. **Verification**: `python code/01_generate_stimuli.py --verify` exits 0 with log message "{{claim:c_2b08411c}} (OEIS A000142, https://oeis.org/A000142)".
- [ ] T050 [P] Compute SHA‑256 checksum for `data/raw/stimuli.csv` and record in `data/checksums.json`. **Verification**: JSON entry exists.
- [ ] T010a [US1] Create contract test `tests/contract/test_stimulus_schema.py` that loads `data/raw/stimuli.csv` and validates against `stimulus.schema.yaml`. **Verification**: `pytest` passes.

### Rating Data (Real & Verification)

- [ ] T015a-Stub [US1] Define Prolific API interface stub in `code/stubs/prolific_api_client.py`. **Verification**: Stub defines required methods.
- [ ] T015a-Real [US1] Implement real Prolific API client in same file. **Verification**: Unit test `tests/unit/test_prolific_client.py` validates request/response handling.
- [ ] T015b-Code [US1] Implement real data ingestion logic in `code/02_collect_real_data.py`. **Verification**: Generates `data/raw/real_ratings.csv` with proper columns.
- [ ] T015b-Verify [US1] **Automated** Verify presence of `data/raw/real_ratings.csv`. Check N≥60 unique participants, valid Prolific ID format, and absence of simulated data. **Verification**: Script exits 0 if valid, 1 if invalid.
- [ ] T015c-Mock [US1] Generate mock consent records (`--mode mock`) under `data/consent/mock/`. **Verification**: Files created.
- [ ] T015c-Verify [US1] **Automated** Verify presence and validity of real consent records in `data/consent/`. **Verification**: Script exits 0 if valid, 1 if invalid.
- [ ] T041 [P] Verify presence of `data/raw/real_ratings.csv` before any downstream analysis. **Verification**: Script exits with error if missing.

- [ ] T051 [P] Anonymise `data/raw/real_ratings.csv` (hash Prolific IDs, strip PII) and write to `data/processed/anonymised_ratings.csv`. **Verification**: No raw IDs remain.
- [ ] T054 [P] Compute SHA‑256 checksum for `data/raw/real_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T052 [P] Compute SHA‑256 checksum for `data/processed/anonymised_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists.
- [ ] T086 [US1] Validate Participant entity: ensure `data/processed/anonymised_ratings.csv` contains a non‑null `participant_id` column matching the Participant schema. **Verification**: Test fails if column missing or malformed. **Depends on**: T051.

### Data Cleaning & Straight‑lining Detection

- [ ] T016 [US1] Implement straight‑lining detector and missing‑data handler in `code/03_clean_data.py`. **Verification**: Logs exclusions, outputs `data/processed/cleaned_ratings.csv`.
- [ ] T055 [P] Compute SHA‑256 checksum for `data/processed/cleaned_ratings.csv` and record in `data/checksums.json`. **Verification**: Entry exists.

## Phase 3: User Story 1 – Stimulus Generation & Data Collection (Priority: P1)

*Note: Tasks T015a-Stub, T015a-Real, T015b-Code, T015b-Verify, T015c-Mock, T015c-Verify are located in Phase 2. This phase focuses on execution and validation.*

- [ ] T037a [P] Implement CLI entry point `code/run_pipeline.py` supporting `--mode` (`real`/`mock`) and `--benchmark`. **Verification**: `--help` displays options.
- [ ] T058 [P] Benchmark full pipeline (`--benchmark --mode mock`). **Verification**: Outputs `total_duration_seconds`; fails if >21600.

## Phase 4: User Story 2 – Statistical Analysis Pipeline (Priority: P2)

- [ ] T020 [US2] Data preprocessing in `code/04_fit_lmm.py` (listwise deletion, reads `data/processed/anonymised_ratings.csv` via pre‑analysis guard). **Output** `data/processed/analysis_ready.csv`. **Verification**: File created. **Depends on**: T051.
- [ ] T084 [US2] Validate `analysis_ready.schema.yaml` against `data/processed/analysis_ready.csv`. **Verification**: Test passes.
- [ ] T021 [US2] Primary LMM script `code/04_fit_lmm.py` fits model `rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)` using `statsmodels.MixedLM`. **Output** `data/results/lmm_summary.csv`. **Verification**: Summary file created.
- [ ] T085 [US2] Validate `lmm_summary.schema.yaml` against `data/results/lmm_summary.csv`. **Verification**: Test passes.
- [ ] T022 [US2] Document Methodological Deviation: Write `data/results/methodological_limitations.md` explaining why Wald-Z is used instead of Satterthwaite (statsmodels limitation) and citing theoretical equivalence for large N. **Verification**: File contains string "Satterthwaite approximation not available; using Wald-Z".
- [ ] T023a [US2] Log warning if stimulus variance component <0.001 and generate transient exclusion object. **Verification**: Log entry created.
- [ ] T023b [US2] Unit test for low‑variance warning logic. **Verification**: Test passes.
- [ ] T024 [US2] Implement Tukey‑corrected post‑hoc pairwise comparisons (triggered on significant interaction). **Output** `data/results/posthoc_tukey.csv`. **Verification**: File created when p < 0.05.
- [ ] T025 [US2] Serialize final results to `data/results/analysis_results.json`, merging exclusion summary. **Verification**: JSON includes `exclusion_summary`.

## Phase 5: User Story 3 – Methodological Robustness & Sensitivity Reporting (Priority: P3)

- [ ] T027 [US3] Sensitivity analysis engine `code/05_sensitivity_analysis.py` reads definitions from `data/processed/cue_intensity_weights.json` (output of T090) and re‑runs LMM. **Verification**: Runs without error. **Depends on**: T090.
- [ ] T028 [US3] Re‑execute LMM for each definition (Equal, Emoji-Dominant, Punctuation-Dominant). **Verification**: Three LMM runs logged.
- [ ] T029 [US3] Compute stability metrics (variation in beta & p‑value) and store in `data/processed/sensitivity_metrics.csv`. **Verification**: CSV contains columns `scheme,beta_interaction,p_value,significant`.
- [ ] T030 [US3] Generate `data/processed/sensitivity_report.csv` summarising stability. **Verification**: Non-empty report file.
- [ ] T056 [P] Compute SHA‑256 checksum for `data/processed/sensitivity_report.csv` and record in `data/checksums.json`. **Verification**: Entry exists.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T033 [P] Update `quickstart.md` with sections on power analysis, benchmarking, and CLI usage. **Verification**: Commands present.
- [ ] T035 [P] Run full pipeline with fixed seed; compute SHA‑256 of `analysis_results.json` and verify deterministic hash. **Verification**: Hash matches recorded value.
- [ ] T036 [P] Add edge‑case unit tests `tests/unit/test_edge_cases.py` (missing data handling, PID format). **Verification**: Tests pass.
- [ ] T038 [P] Run quickstart integration test. **Verification**: `pytest` passes.
- [ ] T099 [P] Align performance documentation: update `plan.md` and `README.md` to state pipeline must complete ≤ 6 hours. **Verification**: Text present.
- [ ] T040 [P] Generate final feature‑folder `README.md` with usage and results sections. **Depends on**: T041, T025, T031.
- [ ] T042 [P] Verify deterministic pipeline output by comparing SHA‑256 of `analysis_results.json` and `sensitivity_report.csv` across two runs. **Verification**: Hashes identical.
- [ ] T043 [P] Ensure no GPU‑specific imports exist. **Verification**: `tests/unit/test_no_gpu_imports.py` scans codebase.
- [ ] T044 [P] Document CPU‑only constraint in `quickstart.md` under “Environment Requirements”. **Verification**: Section present.

## Phase N+1: Additional Verification & Determinism

- [ ] T045 [P] Verify every dataset file listed in `data/checksums.json` exists and matches recorded SHA‑256. **Verification**: Automated script passes.
- [ ] T046 [P] Verify `data/processed/anonymised_ratings.csv` contains no raw Prolific IDs (regex check). **Verification**: Test passes.

## Phase N+2: Final Review & Compliance Tasks

- [ ] T100 [P] Manifest generation script `code/99_manifest.py` writes `data/manifest.json` after each artifact creation; validation via `utils/validate_manifest.py`. **Verification**: CI step runs script and validates manifest before downstream tasks.
- [ ] T101 [P] Pre‑analysis guard script `code/99_preanalysis_guard.py` aborts if `data/processed/anonymised_ratings.csv` missing or fails schema validation. **Verification**: Pipeline stops with clear error.
- [ ] T102 [P] CI check `ci/check_real_data.yml` aborts pipeline in real mode when `data/raw/real_ratings.csv` is absent. **Verification**: CI job fails with informative message.
- [ ] T103 [P] Static‑analysis test `tests/unit/test_no_gpu_imports.py` scans all `.py` files for disallowed imports (`torch`, `tensorflow`, `jax`). **Verification**: Test fails if any such import is found.
- [ ] T104 [P] Document in `report.md` that `statsmodels.MixedLM` uses Wald‑Z statistics (no true Satterthwaite). **Verification**: Search finds disclaimer string.
- [ ] T105 [P] Validate `data/processed/sensitivity_report.csv` includes columns `scheme,beta_interaction,p_value,significant` via schema test. **Verification**: Test passes.
- [ ] T106 [P] Integration test `tests/integration/test_full_pipeline_mock.py` runs entire pipeline in mock mode and asserts completion ≤ 21600 seconds. **Verification**: Test passes within time budget.