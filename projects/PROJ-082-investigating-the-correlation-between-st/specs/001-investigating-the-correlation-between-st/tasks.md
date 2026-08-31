# Tasks: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after dependencies)
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001-impl [S] Initialize project directory structure: Create a Python script `code/setup/init_dirs.py` that programmatically creates `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/derived/`, `data/logs/`, `paper/`, `contracts/`, AND `state/projects/` directories. **Output**: The script `code/setup/init_dirs.py` and the created directory tree. **Constraint**: Must be runnable via `python code/setup/init_dirs.py`. **Note**: This task MUST create the `state/projects/` directory and a placeholder YAML file `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml` with the following exact structure: `project_id: "PROJ-082-investigating-the-correlation-between-st"`, `updated_at: "2026-07-01T00:00:00Z"`, and `artifact_hashes: {}`. This satisfies Constitution Principle V (Versioning) before T000-verif runs.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T000-script [P] Create Mock Data Generator Script: Create `code/data/generate_mock_data.py`. **Task**: Implement a script that generates mock study data with configurable seed, N, and tract count. **Output**: The script file `code/data/generate_mock_data.py`. **Depends on**: T001-impl.
- [X] T002a [P] Create `requirements.txt`: Create `code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`. **Output**: `code/requirements.txt`. **Constraint**: Must specify `python>=3.11`.
- [X] T002b [P] Create `pyproject.toml`: Create `code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Output**: `code/pyproject.toml`. **Constraint**: Must be runnable via `ruff check.` and `black.`.
- [X] T005 [S] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation). **Input**: Must depend on `data/raw/` directory being present (created by T001-impl). **Output**: `code/utils/checksum.py` with functions `calculate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)`. **Constraint**: Must raise an exception if the file does not exist. **CRITICAL**: This task MUST NOT update the state file. It only provides utility functions for checksum calculation. **Depends on**: T001-impl.
- [X] T006a [P] Create config schema: Define `code/config/config_schema.yaml` with keys `seed` (int), `paths` (dict), `limits` (dict). **Output**: `code/config/config_schema.yaml`.
- [X] T006b [P] Implement config loader: Create `code/utils/config.py` to load `code/config/config.yaml` (if exists) or defaults, validating against `config_schema.yaml`. **Output**: `code/utils/config.py` with `load_config()` function. **Depends on**: T006a.
- [X] T006c [S] Initialize default config: Create `code/config/config.yaml` with default seed values and paths. **Output**: `code/config/config.yaml`. **Constraint**: Must explicitly set `seed: 42` for T000-run fallback, `seed: 43` for default quantitative mock, and `seed: 44` for Bonferroni‑specific mock. **Depends on**: T006a, T006b.
- [X] T000-run [S] Generate Default Mock Dataset: Run `code/data/generate_mock_data.py` with no `--config` argument (defaults to seed 43, N=15, 5 distinct tracts) producing `data/raw/mock_studies.csv`. **Output**: `data/raw/mock_studies.csv`. **Depends on**: T001-impl, T000-script, T006c.
- [X] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata. **Fields**: `author` (string), `year` (integer), `tract` (string), `r` (float, nullable), `n` (integer, nullable), `qualitative_desc` (string, nullable), `narrative_pool` (boolean). **Output**: `contracts/study_record.schema.yaml`.
- [X] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics. **Output**: `contracts/meta_analysis_result.schema.yaml`.
- [X] T007c [S] [US1] Create and Execute Tract Lexicon Generator: Create `code/config/generate_lexicon.py` and run it to produce `code/config/tract_lexicon.yaml`. **Task**: Implement a script that defines a hard‑coded list of tract names (`arcuate fasciculus`, `cingulum bundle`, `uncinate fasciculus`, `inferior longitudinal fasciculus`, `auditory cortex`, `ventral striatum`) and directional verbs (`increased`, `decreased`, `correlated`, `associated with`), then writes this list to `code/config/tract_lexicon.yaml`. **Output**: The script file `code/config/generate_lexicon.py` and the output `code/config/tract_lexicon.yaml`. **Depends on**: T007a, T007b.
- [X] T007d-1 [S] [US1] Define the thematic coding scheme: Create `data/config/narrative_methodology.yaml` with schema `keywords: [list]`, `sentiment_rules: {positive: [list], negative: [list]}`, `exclusion_criteria: [list]`. **Output**: `data/config/narrative_methodology.yaml`. **Depends on**: T007a, T007b.
- [X] T007d-2 [S] [US1] Implement NLP logic: Create `code/extraction/nlp_logic.py` using the scheme from T007d-1 and lexicon from T007c. **Task**: Implement regex patterns to search for tract names (from the lexicon) in proximity (≤5 words) to directional verbs. **Constraint**: This logic MUST ONLY be applied to studies that lack both `r` and `n` values. **Output**: `code/extraction/nlp_logic.py` with function `extract_qualitative_desc(text, lexicon, scheme)`. **Depends on**: T007d-1, T007c.
- [X] T008c [S] [US2] Implement `code/analysis/tract_counter.py` to count distinct tracts. **Task**: Read `data/processed/extracted_studies.csv` (produced by T013) and write `data/derived/tract_count.json` with `{"k": <count>}`. **Constraint**: If input missing, write `{"k": 0}` and log a warning. **Depends on**: T013.
- [ ] T009 [S] [US1] Implement Data Source Adapter: Create `code/data/data_source_adapter.py`. **Logic**:
 1. Check if `data/raw/studies.csv` exists and validates headers.
 2. If `data/raw/studies.csv` is missing, DO NOT copy mock data. Instead, log a warning and proceed to trigger narrative synthesis path.
 3. Compute MD5 checksum of the selected source (if exists) and write to `data/processed/checksum_tmp.json`. **Output**: `data/processed/checksum_tmp.json` (or empty if no source). **Depends on**: T001-impl, T006c, T000-script, T010, T000-run.
- [ ] T009b [S] [US1] Implement Real Data Validator: Create `code/data/real_data_validator.py`. **Task**:
 - Verify `data/raw/studies.csv` exists.
 - Count unique (author, year) pairs → `N`.
 - Write `data/processed/real_data_status.json` with schema `{"valid": bool, "N": int, "mode": "quantitative" | "narrative", "message": str}`.
 - If `N < 10`, set `mode` to `"narrative"` and `valid` to `true` (no error).
 - If `studies.csv` is missing, set `mode` to `"narrative"` and `valid` to `true` (no error), DO NOT copy mock data.
 - **Constraint**: This task MUST NOT raise an error or exception; it must only output the status flag to allow the pipeline to proceed to the narrative path. **Depends on**: T001-impl, T009, T000-run.
- [X] T010 [S] [US1] Generate Config‑Specific Mock Data: Create `code/data/generate_mock_data.py` that supports `--config` values `fallback`, `quant`, `bonferroni`. **Task**: Generate mock data using specific distributions: `r` values from a Normal distribution (mean=0.3, std=0.1), `n` values from a Uniform distribution (min=20, max=200), and `tract_name` from the lexicon. **Output**: Corresponding CSV files (`mock_studies_fallback.csv`, `mock_studies_quant.csv`, `mock_studies_bonferroni.csv`). **Depends on**: T001-impl, T006c, T000-script.
- [ ] T012 [S] [US1] Qualitative Extraction (Narrative Path): Implement `code/analysis/extraction.py` that reads `data/raw/studies.csv` and extracts qualitative descriptors using `nlp_logic.py` for rows lacking both `r` and `n`. Writes `data/processed/qualitative_data.json`. **Depends on**: T009b, T007d-2, T007c.
- [X] T040 [S] [US1] p‑value to r Conversion: `code/analysis/p_to_r.py` implements Fisher's Z conversion. **Formula**: For t-statistic: `r = sqrt(t^2 / (t^2 + df))`. For p-value: Convert p to t using `scipy.stats.t.ppf` (handling one-tailed vs two-tailed flags) then apply t-to-r formula. Raises `DataConversionError` for ambiguous cases. **Output**: Updated `extracted_studies.csv` with `r` column and `conversion_method` flag. **Depends on**: T009b, T009.
- [ ] T013 [S] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for `r`, `n`, `tract` and merge with qualitative data from T012. Generates `data/processed/extracted_studies.csv` with columns including `narrative_pool` and `qualitative_desc`. Logs exclusions to `data/logs/exclusion_log.csv`. **Depends on**: T009b, T012, T040, T007c, T007d-2.
- [X] T014a [S] [US1] Implement `code/analysis/study_counter.py`. **Task**: Count unique (author, year) pairs in `extracted_studies.csv` → `data/processed/study_count.json` (`{"N": <count>}`). **Constraint**: If input missing/empty, write `{"N": 0}`. **Depends on**: T013.
- [ ] T014b [S] [US1] Implement `code/analysis/valid_pair_counter.py`. **Task**: Count rows with both `r` and `n` present → `data/processed/valid_pair_count.json` (`{"N_valid": <count>}`). **Depends on**: T013.
- [ ] T014 [S] [US1] Implement `code/analysis/meta_analysis.py` (Random‑Effects via DerSimonian‑Laird). **Gate Logic**:
 - Read `N` from `study_count.json` (T014a) AND `mode` from `real_data_status.json` (T009b).
 - If `mode` == `"narrative"` OR `N < 10`: write `data/processed/meta_status.json` with `{"status":"skipped","reason":"Insufficient studies","N":N,"egger_skipped_reason":"Skipped: Insufficient studies (N < 10) for Egger's regression"}`. **Do not** invoke narrative tasks directly; the orchestrator (T016) will handle the transition based on this status.
 - If `N >= 10`: run random‑effects model using DerSimonian-Laird estimator; on convergence failure fall back to fixed‑effects; write results to `data/derived/results_meta.json`.
 - If `10 <= N < 20`, invoke T041 (Hartung‑Knapp) after model fit. **Depends on**: T014a, T014b, T009b, T017, T018.
- [ ] T015 [S] [US3] Visualization Orchestrator: After successful quantitative meta‑analysis (`meta_status.json` status == "completed"), invoke plot generators T024, T025, T026. Writes `data/derived/visualization_status.json`. **Depends on**: T014 (quantitative path) and T042 (memory‑safe utilities).
- [ ] T015a [S] [US1] Implement narrative logic: `code/analysis/narrative_logic.py` aggregates qualitative descriptors into thematic counts using `narrative_methodology.yaml`. Output: `data/derived/narrative_themes.json`. **Depends on**: T013, T007d-1.
- [ ] T015b [S] [US1] Narrative Synthesis Engine: `code/analysis/narrative_engine.py` reads `narrative_themes.json` and `study_count.json`; if `mode` is `"narrative"` (from T009b) OR if `meta_status.json` status is "skipped" (from T014), it produces `data/derived/narrative_content.md`. **Depends on**: T015a, T014a, T009b, T014.
- [X] T015c [S] [US1] Generate Narrative Summary: `code/analysis/narrative.py` consumes `narrative_content.md` and produces `data/derived/narrative_summary.md` with JSON metadata block, sections, and explicit "Data Insufficient" disclaimer when `N=0`. **Depends on**: T015b, T007d-1.
- [X] T015d [S] [US1] Pivot Narrative Script: `code/analysis/pivot_narrative.py` orchestrates T015b → T015c based on `mode` flag. **Output**: Callable CLI script. **Depends on**: T015b, T015a.
- [X] T016 [S] [US1] Main Orchestrator (`code/main.py`): Loads `real_data_status.json`, `study_count.json`, `valid_pair_count.json`, and `meta_status.json`.
 - If `mode` == `"narrative"` (from T009b) **OR** `meta_status.json` status == "skipped" (from T014): invoke `pivot_narrative.py` → generate narrative artifacts, set `data/derived/results.json` with `synthesis_mode: "narrative"`.
 - If `status` == `"completed"`: invoke T015 (visualization orchestrator) and then T021 (multiple‑comparison correction). Finally, write final `data/derived/results.json` with `synthesis_mode: "quantitative"`.
 - Handles Hartung‑Knapp flag from T041 automatically. **Note**: T016 is the root orchestrator; it DOES NOT depend on T015 as a prerequisite, but invokes it. **Depends on**: T009b, T014a, T014b, T014, T021, T015d.
- [ ] T017 [S] [US2] Implement Egger's regression (`code/analysis/bias.py`). **Skip** if `N < 10` (read from `study_count.json`). For `10 ≤ N < 20` add low‑power warning. Write results to `data/derived/egger_test.json`. **Depends on**: T014a, T014.
- [ ] T018 [S] [US2] Implement I² calculation (`code/analysis/heterogeneity.py`). Output `i_squared` with exactly two decimal places to `data/derived/i2_stats.json`. **Depends on**: T014a, T014.
- [X] T021 [S] [US2] Multiple Comparisons Correction (`code/analysis/correction.py`):
 1. Read `N` from `study_count.json`; if `N < 10` set `bonferroni_applied: false` and log skip.
 2. Read `k` from `tract_count.json`; if `k ≥ 2` and `N ≥ 10` compute:
 - Standard Bonferroni adjusted α = 0.05 / k.
 3. Write `data/derived/bonferroni_status.json` with `{"bonferroni_applied": <bool>, "adjusted_threshold": <float>}`.
 4. Update `data/derived/results.json` with the adjusted p‑values and a flag indicating which method was applied.
 **Note**: Holm-Bonferroni is NOT included; only Standard Bonferroni per FR-005.
 **Depends on**: T008c, T014a, T014, T014b.
- [ ] T024 [S] [US3] Implement Forest Plot (`code/visualization/plots_forest.py`). Uses `code/visualization/memory_safe_plots.py` (T053) for memory checks. Saves PNG to `data/derived/forest_plot.png`. **Depends on**: T015, T042, T053.
- [X] T025 [S] [US3] Implement Funnel Plot (`code/visualization/plots_funnel.py`). **Depends on**: T015, T042, T053.
- [X] T026 [S] [US3] Implement Correlation Summary Plot (`code/visualization/plots_correlation.py`). **Depends on**: T015, T042, T053.
- [X] T027b [S] Plot File‑Size Validator: Extend `code/utils/validator.py` with `validate_png_size(path, max_bytes=5*1024*1024)`. Returns exit code 0/2 and writes per‑plot status to `data/logs/size_validation.log`. **Constraint**: Validation passes only if `size <= 5 * 1024 * 1024` bytes. **Depends on**: T024, T025, T026.
- [X] T027c [S] Regenerator: `code/visualization/regenerator.py` reads `data/derived/validation_report.json` (produced by T031). If `overall_status` is `"fail"` it retries failed plots ONCE with reduced DPI/compression. Logs failures to `data/logs/regeneration_failure.log`. **Depends on**: T027b, T031.
- [X] T027d [S] Validation Report Check: `code/visualization/check_validation.py` reads `data/derived/validation_report.json`; if `overall_status` is `"fail"` it triggers `regenerator.py` (T027c) and then re-runs T031 to update the report. Max retries: a limited number. **Depends on**: T031, T027c.
- [X] T031 [S] Validation Report Generation: Aggregate results from `size_validation.log` and produce `data/derived/validation_report.json` with schema `{"overall_status":"pass"|"fail","details":{...}}`. **Depends on**: T027b.
- [~] T032 [P] Generate Paper Draft: `code/report/generate_paper.py` uses Jinja2 to render `docs/paper_draft.md` from `results.json`, inserting Bonferroni conservatism note if `bonferroni_applied` is true. **Depends on**: T016, T021, T018, T017. <!-- FAILED: unspecified -->
- [X] T033a [P] Linting: Run `ruff` across `code/` and `tests/`; output log to `data/logs/lint_report.md`. **Depends on**: All code artifacts.
- [X] T034a [P] Runtime Profiling: Profile total pipeline runtime; ensure <15 min; write `data/logs/profile_report.md`. **Depends on**: Entire pipeline execution.
- [X] T035 [P] Additional Unit Tests: Add coverage for p‑value conversion edge cases in `tests/unit/`. **Depends on**: T040.
- [X] T037 [P] Create Bonferroni Test Script: `tests/unit/test_bonferroni.py` verifies correction logic with multiple distinct tracts. **Depends on**: T021.
- [X] T038 [P] Run Bonferroni Verification: Execute `pytest tests/unit/test_bonferroni.py`; capture logs. **Depends on**: T037.
- [X] T041 [S] Hartung‑Knapp Adjustment: `code/analysis/hartung_knapp.py` adjusts CI for low‑power meta‑analysis (10 ≤ N < 20) and writes `hk_adjusted_ci` to `results.json`. **Depends on**: T014 (after successful model fit) and T014a.
- [X] T042 [S] Memory‑Safe Plot Generation: Refactor all plot scripts to use `tracemalloc` and explicit `gc.collect()`; log peak memory to `data/logs/memory_usage.log`. **Constraint**: This task includes the memory monitoring logic previously in T027a. **Depends on**: T002a.
- [X] T043 [S] No‑Studies‑Found Handler: `code/analysis/zero_studies_handler.py` generates `data/derived/narrative_summary.md` with header `# No studies found` and JSON metadata when `N = 0`. **Depends on**: T014a (detect N=0) and T015b (fallback path).
- [X] T044 [S] Tract Independence Checker: `code/analysis/independence_checker.py` scans `extracted_studies.csv` for multiple tracts from same study, logs warnings, and writes `data/derived/independence_status.json` (`{"independence_assumed": bool}`). **Depends on**: T013.

- [X] T000-verif [S] Checksum and Register Artifacts: Create `code/utils/register_artifacts.py`. **Task**: Calculate MD5 checksums for ALL data files in `data/raw/`, `data/processed/`, `data/derived/` AND ALL code files in `code/`, `tests/`, `contracts/`. Update `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml` with the new hashes. **Constraint**: Must run after T010 (Generate) and T009 (Select). **Depends on**: T001-impl, T009, T010.

---

## Phase 6: Review Resolution & Edge Case Hardening (Priority: P1)

**Goal**: Address specific reviewer concerns regarding data flow, error handling, and scientific integrity.

- [X] T040 (already added above) – strict p‑value conversion with error on ambiguous inputs.
- [X] T041 (already added above) – Hartung‑Knapp adjustment.
- [X] T042 (already added above) – memory‑safe plotting.
- [X] T043 (already added above) – zero‑studies handling.
- [X] T044 (already added above) – tract independence warning.

---

## Phase 7: Final Integration & Execution Readiness

**Goal**: Ensure the pipeline is robust, reproducible, and ready for execution on the target runner.

- [X] T049 [P] [US1] Create End-to-End Integration Test: Create `tests/integration/test_full_pipeline.py`. **Task**: Run the entire pipeline from `code/main.py` using the `--use-mock` flag and `--config=quant`. Assert that all expected output files (`results.json`, `plots/*.png`, `narrative_summary.md` if skipped) are generated and valid. **Depends on**: T016, T021, T032.
- [X] T050 [S] [US1] Documentation Update: Update `README.md` and `docs/paper_draft.md` to reflect the new "Real Data First" policy (with graceful fallback), the explicit failure-on-fetch-fail behavior (removed), and the conditions under which mock data is used. **Depends on**: T049.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T051 [S] [US1] Reconcile run-book vs implementation for `code/data/generators.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/generators.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist. <!-- FAILED: unspecified -->

- [ ] T052 [S] [US1] Resolve Data Flow Dependency: Remove this task as it is redundant with T014's existing dependencies on T017/T018. **Depends on**: None.
- [ ] T053 [S] [US1] Resolve Unspecified Visualization Dependency: Implement `code/visualization/memory_safe_plots.py` with explicit `tracemalloc` context managers and `matplotlib` backend switching to `Agg` to prevent display errors in headless CI. **Depends on**: T002a, T042.
- [ ] T054 [S] [US1] Resolve Paper Draft Dependency: Implement `code/report/generate_paper.py` (T032) with a fallback to a minimal text report if Jinja2 templates are missing, ensuring the pipeline does not crash on report generation. **Depends on**: T016, T021.
- [ ] T055 [S] [US1] Resolve Mock Data Consistency: Remove this task as its objective is now covered by T000-run which explicitly generates tract_name from lexicon. **Depends on**: None.