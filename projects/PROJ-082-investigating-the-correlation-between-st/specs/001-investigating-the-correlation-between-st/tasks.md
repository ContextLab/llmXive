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

- [X] T000-run [S] Generate Mock Data: Create `code/data/generate_mock_data.py` and run it to produce `data/raw/mock_studies.csv` (N=15, 5+ tracts) AND `data/raw/mock_studies_fallback.csv` (N=5). **Task**: Implement a script that generates mock study data with configurable seed, N, and tract count. **Function Signatures**: The script MUST include `generate_studies(seed, n, tract_count, output_path)` and `generate_fallback(seed, output_path)`. **Constraint**: Must support generating a specific N=5 dataset (`mock_studies_fallback.csv`) for testing the N<10 narrative pivot. **Output**: The script file `code/data/generate_mock_data.py` and the output files `data/raw/mock_studies.csv` and `data/raw/mock_studies_fallback.csv`. **Depends on**: T001-impl, T006c.
- [X] T002a [P] Create `requirements.txt`: Create `code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`. **Output**: `code/requirements.txt`. **Constraint**: Must specify `python>=3.11`.
- [X] T002b [P] Create `pyproject.toml`: Create `code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Output**: `code/pyproject.toml`. **Constraint**: Must be runnable via `ruff check.` and `black.`.
- [X] T005 [S] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation). **Input**: Must depend on `data/raw/` directory being present (created by T001-impl). **Output**: `code/utils/checksum.py` with functions `calculate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)`. **Constraint**: Must raise an exception if the file does not exist. **CRITICAL**: This task MUST NOT update the state file. It only provides utility functions for checksum calculation. **Depends on**: T001-impl.
- [X] T006a [P] Create config schema: Define `code/config/config_schema.yaml` with keys `seed` (int), `paths` (dict), `limits` (dict). **Output**: `code/config/config_schema.yaml`.
- [X] T006b [P] Implement config loader: Create `code/utils/config.py` to load `code/config/config.yaml` (if exists) or defaults, validating against `config_schema.yaml`. **Output**: `code/utils/config.py` with `load_config()` function. **Depends on**: T006a.
- [X] T006c [S] Initialize default config: Create `code/config/config.yaml` with default seed values and paths. **Output**: `code/config/config.yaml`. **Constraint**: Must explicitly set `seed: 42` for T000-run fallback, `seed: 43` for default quantitative mock, and `seed: 44` for Bonferroni‑specific mock. **Depends on**: T006a, T006b.
- [X] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata. **Fields**: `author` (string), `year` (integer), `tract` (string), `r` (float, nullable), `n` (integer, nullable), `qualitative_desc` (string, nullable), `narrative_pool` (boolean). **Output**: `contracts/study_record.schema.yaml`.
- [X] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics. **Output**: `contracts/meta_analysis_result.schema.yaml`.
- [X] T007c [S] [US1] Generate Tract Lexicon: Create `code/config/generate_lexicon.py` and run it to produce `code/config/tract_lexicon.yaml`. **Task**: Implement a script that defines a hard‑coded list of tract names (`arcuate fasciculus`, `cingulum bundle`, `uncinate fasciculus`, `inferior longitudinal fasciculus`, `auditory cortex`, `ventral striatum`) and directional verbs (`increased`, `decreased`, `correlated`, `associated with`), then writes this list to `code/config/tract_lexicon.yaml`. **Output**: The script file `code/config/generate_lexicon.py` and the output `code/config/tract_lexicon.yaml`. **Depends on**: T007a, T007b.
- [X] T007d-1 [S] [US1] Define the thematic coding scheme: Create `data/config/narrative_methodology.yaml` with schema `keywords: [list]`, `sentiment_rules: {positive: [list], negative: [list]}`, `exclusion_criteria: [list]`. **Output**: `data/config/narrative_methodology.yaml`. **Depends on**: T007a, T007b.
- [X] T007d-2 [S] [US1] Implement NLP logic: Create `code/extraction/nlp_logic.py` using the scheme from T007d-1 and lexicon from T007c. **Task**: Implement regex patterns to search for tract names (from the lexicon) in proximity (≤5 words) to directional verbs. **Constraint**: This logic MUST ONLY be applied to studies that lack both `r` and `n` values. **Output**: `code/extraction/nlp_logic.py` with function `extract_qualitative_desc(text, lexicon, scheme)`. **Depends on**: T007d-1, T007c.
- [X] T008c [S] [US2] Implement `code/analysis/tract_counter.py` to count distinct tracts. **Task**: Read `data/processed/extracted_studies.csv` (produced by T013) and write `data/derived/tract_count.json` with `{"k": <count>}`. **Constraint**: If input missing, write `{"k": 0}` and log a warning. **Depends on**: T013.
- [X] T010 [S] [US1] Generate Config‑Specific Mock Data: Create `code/data/generate_mock_data.py` that supports `--config` values `fallback`, `quant`, `bonferroni`. **Task**: Generate mock data using specific distributions: `r` values from a Normal distribution (mean=0.3, std=0.1), `n` values from a Uniform distribution (min=20, max=200), and `tract_name` from the lexicon. **Output**: Corresponding CSV files (`mock_studies_fallback.csv`, `mock_studies_quant.csv`, `mock_studies_bonferroni.csv`). **Depends on**: T001-impl, T006c, T000-run.
- [X] T040 [S] [US1] p‑value to r Conversion: `code/analysis/p_to_r.py` implements Fisher's Z conversion. **Formula**: For t-statistic: `r = sqrt(t^2 / (t^2 + df))`. For p-value: Convert p to t using `scipy.stats.t.ppf` (handling one-tailed vs two-tailed flags) then apply t-to-r formula. Raises `DataConversionError` for ambiguous cases. **Output**: Updated `extracted_studies.csv` with `r` column and `conversion_method` flag. **CRITICAL**: This task MUST depend on T013 (Parser) which produces the initial `extracted_studies.csv`. **Depends on**: T013.
- [X] T056 [S] [US1] Re-implement Unified Data Loader: Create `code/data/loader.py`. **Task**: Implement a single function `load_study_data(input_path, allow_fallback=False)` that: 1) Validates the file exists and has correct headers (author, year, tract, r, n), 2) If `input_path` is `data/raw/studies.csv` and missing, AND `allow_fallback=True`, attempts to load `data/raw/mock_studies.csv` (or `mock_studies_fallback.csv` if testing N<10) and COPIES it to `data/raw/studies.csv` to ensure T012 has the file, 3) If `allow_fallback=False` and file is missing, raises `FileNotFoundError`. **CRITICAL**: If `allow_fallback=True` and the source file from T000-run is missing, this function MUST raise `FileNotFoundError` to prevent silent failure. **Output**: The script file `code/data/loader.py`. **Depends on**: T001-impl, T006c, T000-run.
- [X] T012 [S] [US1] Qualitative Extraction (Narrative Path): Implement `code/analysis/extraction.py`. **Task**: Read `data/raw/studies.csv` (ensured by T056) and extract qualitative descriptors using `nlp_logic.py` for rows lacking both `r` and `n`. Writes `data/processed/qualitative_data.json`. **CRITICAL**: Output MUST include `author`, `year`, `tract`, and `qualitative_desc` fields to satisfy the Narrative Engine contract. **Output**: The script file `code/analysis/extraction.py`. **Depends on**: T056, T007d-2, T007c.
- [X] T013 [S] [US1] Implement Parser: Create `code/extraction/parser.py`. **Task**: Parse CSV/JSON inputs for `r`, `n`, `tract` and merge with qualitative data from T012. Generates `data/processed/extracted_studies.csv` with columns including `narrative_pool` and `qualitative_desc`. Logs exclusions to `data/logs/exclusion_log.csv`. **CRITICAL**: This task MUST perform initial p-value to r conversion if `r` is missing but `p` or `t` is present. **Output**: The script file `code/extraction/parser.py`. **Depends on**: T056, T012, T007c, T007d-2.
- [X] T014a [S] [US1] Implement `code/analysis/study_counter.py`. **Task**: Count unique (author, year) pairs in `extracted_studies.csv` → `data/processed/study_count.json` (`{"N": <count>}`). **Constraint**: If input missing/empty, write `{"N": 0}`. **Depends on**: T013.
- [X] T014b [S] [US1] Implement `code/analysis/valid_pair_counter.py`. **Task**: Count rows with both `r` and `n` present → `data/processed/valid_pair_count.json` (`{"N_valid": <count>}`). **Depends on**: T013.
- [X] T057 [S] [US1] Re-implement Quantitative Gatekeeper: Create `code/analysis/gatekeeper.py`. **Task**: Read `study_count.json` and `valid_pair_count.json`. If `N < 10` OR `N_valid < 10`, write `data/derived/gate_result.json` with `{"status": "narrative_required", "reason": "Insufficient valid studies", "synthesis_mode": "narrative"}`. If `N >= 10`, write `{"status": "quantitative_ok", "synthesis_mode": "quantitative"}`. **Constraint**: This task MUST explicitly set the `synthesis_mode` flag to ensure downstream tasks (T014, T015b) know the correct path. **Output**: The script file `code/analysis/gatekeeper.py`. **Depends on**: T014a, T014b.
- [X] T014 [S] [US1] Implement Meta-Analysis Model: Create `code/analysis/meta_analysis.py`. **Task**: Run Random-Effects Model (DerSimonian-Laird) on `extracted_studies.csv`. **Gate Logic**: Read `gate_result.json` (T057). If `status` == `narrative_required`, write `data/derived/meta_status.json` with `{"status":"skipped","reason":"Insufficient studies"}`. If `status` == `quantitative_ok`: run model; on convergence failure log divergence explicitly and fall back to fixed-effects; write base results to `data/derived/meta_results.json`. **Constraint**: If `10 <= N < 20`, set flag `hk_adjustment_needed` in output. **Output**: The script file `code/analysis/meta_analysis.py`. **Depends on**: T014a, T014b, T057.
- [X] T017 [S] [US2] Implement Egger's regression: Create `code/analysis/bias.py`. **Task**: Read `meta_results.json` (T014). If `N < 10`, skip and write `data/derived/egger_test.json` with `{"skipped": true, "reason": "N < 10"}`. Else, run Egger's test and write results to `data/derived/egger_test.json`. **Output**: The script file `code/analysis/bias.py`. **Depends on**: T014, T014a.
- [X] T018 [S] [US2] Implement I² calculation: Create `code/analysis/heterogeneity.py`. **Task**: Read `meta_results.json` (T014). Calculate I² and write to `data/derived/heterogeneity_results.json` with exactly two decimal places. **Output**: The script file `code/analysis/heterogeneity.py`. **Depends on**: T014, T014a.
- [X] T053 [S] [US3] Implement Memory-Safe Plot Module: Create `code/visualization/memory_safe_plots.py`. **Task**: Implement utility functions using `tracemalloc` and `matplotlib` backend `Agg` to ensure memory safety and headless compatibility. **Output**: The script file `code/visualization/memory_safe_plots.py`. **Depends on**: T002a.
- [X] T051-Create [S] [US1] Create Run-Book Entry Point: Create `code/data/generators.py` as a wrapper script that invokes `code/data/generate_mock_data.py`. **Output**: The script file `code/data/generators.py`. **Depends on**: T000-run.
- [X] T051-Update [S] [US1] Update Quickstart: Update `docs/quickstart.md` to invoke `python code/data/generators.py` instead of the missing script. **Output**: The updated file `docs/quickstart.md`. **Depends on**: T051-Create.

## Phase 3: Narrative Synthesis (Fallback Path)

**Purpose**: Handle cases where N < 10

- [X] T015a [S] [US1] Implement Narrative Logic: Create `code/analysis/narrative_logic.py`. **Task**: Aggregate qualitative descriptors into thematic counts using `narrative_methodology.yaml`. Output: `data/derived/narrative_themes.json`. **Output**: The script file `code/analysis/narrative_logic.py`. **Depends on**: T013, T007d-1.
- [X] T015b [S] [US1] Narrative Synthesis Engine: Create `code/analysis/narrative_engine.py`. **Task**: Read `narrative_themes.json` and `gate_result.json` (T057); if `synthesis_mode` is `"narrative"`, it produces `data/derived/narrative_content.md`. **CRITICAL**: Depends on T057, NOT T014, to ensure it runs even if T014 is skipped. **Output**: The script file `code/analysis/narrative_engine.py`. **Depends on**: T015a, T014a, T057.
- [X] T015c [S] [US1] Generate Narrative Summary: Create `code/analysis/narrative.py`. **Task**: Consume `narrative_content.md` and produce `data/derived/narrative_summary.md` with JSON metadata block, sections, and explicit "Data Insufficient" disclaimer when `N=0`. **Output**: The script file `code/analysis/narrative.py`. **Depends on**: T015b, T007d-1.
- [X] T015d [S] [US1] Pivot Narrative Script: Create `code/analysis/pivot_narrative.py`. **Task**: Orchestrates T015b → T015c based on `mode` flag. **Output**: The script file `code/analysis/pivot_narrative.py`. **Depends on**: T015b, T015a.
- [X] T043 [S] [US1] No‑Studies‑Found Handler: Create `code/analysis/zero_studies_handler.py`. **Task**: Generates `data/derived/narrative_summary.md` with header `# No studies found` and JSON metadata when `N = 0`. **Output**: The script file `code/analysis/zero_studies_handler.py`. **Depends on**: T014a, T015b.

## Phase 4: Quantitative Analysis & Visualization

**Purpose**: Core meta-analysis and plotting

- [X] T021 [S] [US2] Multiple Comparisons Correction: Create `code/analysis/correction.py`. **Task**: Read `N` from `study_count.json`; if `N < 10` set `bonferroni_applied: false`. Read `k` from `tract_count.json` (T008c) OR count directly from `data/processed/extracted_studies.csv`; if `k ≥ 2` AND `N ≥ 10` compute adjusted α. **CRITICAL**: Must explicitly verify that `k` (distinct tracts) is at least 5 to satisfy SC-004, and report the adjusted threshold. Write `data/derived/bonferroni_status.json`. Update `data/derived/results.json` with adjusted p‑values. **Output**: The script file `code/analysis/correction.py`. **Depends on**: T008c, T014a, T014, T014b.
- [X] T041 [S] Hartung‑Knapp Adjustment: Create `code/analysis/hartung_knapp.py`. **Task**: Adjust CI for low‑power meta‑analysis (10 ≤ N < 20) and writes `hk_adjusted_ci` to `results.json`. **Output**: The script file `code/analysis/hartung_knapp.py`. **Depends on**: T014, T014a.
- [X] T015 [S] [US3] Visualization Orchestrator: Create `code/visualization/orchestrator.py`. **Task**: After successful quantitative meta‑analysis (`meta_status.json` status == "completed"), invoke plot generators T024, T025, T026. Writes `data/derived/visualization_status.json`. **Output**: The script file `code/visualization/orchestrator.py`. **Depends on**: T014, T042, T053.
- [X] T042 [S] Memory‑Safe Plot Generation: Refactor all plot scripts to use `tracemalloc` and explicit `gc.collect()`. **Task**: This task includes the memory monitoring logic previously in T027a. **Output**: Updated plot scripts (T024, T025, T026). **Depends on**: T002a, T053.
- [X] T058 [S] [US3] Fix Visualization Orchestration: Update `code/visualization/plots_forest.py`, `plots_funnel.py`, and `plots_correlation.py`. **Task**: Explicitly depend on `data/derived/gate_result.json` (T057). If `gate_result.json` status is `narrative_required`, these scripts must exit gracefully with code 0 and log "Skipped: Narrative mode active". **CRITICAL**: This task depends on T024, T025, and T026 being created first so it can update them. **Output**: Updated files `code/visualization/plots_forest.py`, `code/visualization/plots_funnel.py`, `code/visualization/plots_correlation.py`. **Depends on**: T024, T025, T026, T057.
- [X] T024 [S] [US3] Implement Forest Plot: Create `code/visualization/plots_forest.py`. **Task**: Uses `code/visualization/memory_safe_plots.py` (T053) for memory checks. Saves PNG to `data/derived/forest_plot.png`. **Output**: The script file `code/visualization/plots_forest.py`. **Depends on**: T014, T042, T053.
- [X] T025 [S] [US3] Implement Funnel Plot: Create `code/visualization/plots_funnel.py`. **Output**: The script file `code/visualization/plots_funnel.py`. **Depends on**: T014, T042, T053.
- [X] T026 [S] [US3] Implement Correlation Summary Plot: Create `code/visualization/plots_correlation.py`. **Output**: The script file `code/visualization/plots_correlation.py`. **Depends on**: T014, T042, T053.
- [X] T027b [S] Plot File‑Size Validator: Extend `code/utils/validator.py` with `validate_png_size(path, max_bytes=5*1024*1024)`. Returns exit code 0/2 and writes per‑plot status to `data/logs/size_validation.log`. **Constraint**: Validation passes only if `size <= 5 * 1024 * 1024` bytes. **Output**: The updated file `code/utils/validator.py`. **Depends on**: T024, T025, T026.
- [X] T027c [S] Regenerator: Create `code/visualization/regenerator.py`. **Task**: Reads `data/derived/validation_report.json` (produced by T031). If `overall_status` is `"fail"` it retries failed plots ONCE with reduced DPI/compression. Logs failures to `data/logs/regeneration_failure.log`. **Output**: The script file `code/visualization/regenerator.py`. **Depends on**: T027b, T031.
- [X] T027d [S] Validation Report Check: Create `code/visualization/check_validation.py`. **Task**: Reads `data/derived/validation_report.json`; if `overall_status` is `"fail"` it triggers `regenerator.py` (T027c) and then re-runs T031 to update the report. Max retries: a configurable limit. **Output**: The script file `code/visualization/check_validation.py`. **Depends on**: T031, T027c.
- [X] T031 [S] Validation Report Generation: Aggregate results from `size_validation.log` and produce `data/derived/validation_report.json` with schema `{"overall_status":"pass"|"fail","details":{...}}`. **Output**: The script file `code/visualization/validator.py` (or update existing). **Depends on**: T027b.

## Phase 5: Reporting & Integration

**Purpose**: Final outputs and testing

- [X] T032 [S] Generate Paper Draft: Create `code/report/generate_paper.py`. **Task**: Uses Jinja2 to render `docs/paper_draft.md` from `results.json`, inserting Bonferroni conservatism note if `bonferroni_applied` is true. Falls back to minimal text if Jinja2 missing. **Output**: The script file `code/report/generate_paper.py`. **Depends on**: T016, T021, T018, T017.
- [X] T033a [P] Linting: Run `ruff` across `code/` and `tests/`; output log to `data/logs/lint_report.md`. **Depends on**: All code artifacts.
- [X] T034a [P] Runtime Profiling: Profile total pipeline runtime; ensure <15 min; write `data/logs/profile_report.md`. **Depends on**: Entire pipeline execution.
- [X] T035 [P] Additional Unit Tests: Add coverage for p‑value conversion edge cases in `tests/unit/`. **Depends on**: T040.
- [X] T037 [P] Create Bonferroni Test Script: Create `tests/unit/test_bonferroni.py` verifies correction logic with multiple distinct tracts. **Depends on**: T021.
- [X] T038 [P] Run Bonferroni Verification: Execute `pytest tests/unit/test_bonferroni.py`; capture logs. **Depends on**: T037.
- [X] T044 [S] Tract Independence Checker: Create `code/analysis/independence_checker.py`. **Task**: Scans `extracted_studies.csv` for multiple tracts from same study, logs warnings, and writes `data/derived/independence_status.json` (`{"independence_assumed": bool}`). **Output**: The script file `code/analysis/independence_checker.py`. **Depends on**: T013.
- [X] T000-verif [S] Checksum and Register Artifacts: Create `code/utils/register_artifacts.py`. **Task**: Calculate MD5 checksums for ALL data files in `data/raw/`, `data/processed/`, `data/derived/` AND ALL code files in `code/`, `tests/`, `contracts/`. Update `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml` with the new hashes. **Constraint**: Must run after T010 (Generate) and T056 (Select). **Output**: The script file `code/utils/register_artifacts.py`. **Depends on**: T001-impl, T056, T010.

## Phase 6: Review Resolution & Edge Case Hardening (Priority: P1)

**Goal**: Address specific reviewer concerns regarding data flow, error handling, and scientific integrity.

- [X] T040 (already added above) – strict p‑value conversion with error on ambiguous inputs.
- [X] T041 (already added above) – Hartung‑Knapp adjustment.
- [X] T042 (already added above) – memory‑safe plotting.
- [X] T043 (already added above) – zero‑studies handling.
- [X] T044 (already added above) – tract independence warning.

## Phase 7: Final Integration & Execution Readiness

**Goal**: Ensure the pipeline is robust, reproducible, and ready for execution on the target runner.

- [X] T049 [P] [US1] Create End-to-End Integration Test: Create `tests/integration/test_full_pipeline.py`. **Task**: Run the entire pipeline from `code/main.py` using the `--use-mock` flag and `--config=quant`. Assert that all expected output files (`results.json`, `plots/*.png`, `narrative_summary.md` if skipped) are generated and valid. **Output**: The test file `tests/integration/test_full_pipeline.py`. **Depends on**: T016, T021, T032.
- [X] T050 [S] [US1] Documentation Update: Update `README.md` and `docs/paper_draft.md` to reflect the new "Real Data First" policy (with graceful fallback), the explicit failure-on-fetch-fail behavior (removed), and the conditions under which mock data is used. **Output**: Updated `README.md`, `docs/paper_draft.md`. **Depends on**: T049.
- [X] T016 [S] [US1] Main Orchestrator: Create `code/main.py`. **Task**: Loads `gate_result.json` (T057), `study_count.json`, `valid_pair_count.json`, and `meta_status.json` (T014).
 - If `gate_result.json` status == `"narrative_required"`: invoke `pivot_narrative.py` (T015d) → generate narrative artifacts, set `data/derived/results.json` with `synthesis_mode: "narrative"`.
 - If `gate_result.json` status == `"quantitative_ok"`: invoke T014 (Meta-Analysis), then T017/T018 (Bias/Heterogeneity), then T021 (Correction), then T015 (Visualization). Finally, write final `data/derived/results.json` with `synthesis_mode: "quantitative"`.
 - Handles Hartung‑Knapp flag from T041 automatically.
 **Output**: The script file `code/main.py`. **Depends on**: T057, T014a, T014b, T014, T021, T015d, T017, T018, T015.

## Phase 8: Data Source Verification & Streaming Hardening (Priority: P1)

**Goal**: Ensure strict adherence to "Real Data First" principles, prevent synthetic fallbacks, and implement streaming for large datasets as required by the Tasker Agent rules.

- [ ] T060 [S] [US1] Implement Real Data Fetcher: Create `code/data/fetch_real_data.py`. **Task**: Implement a function `fetch_real_data(source_id, output_path)` that attempts to download real study data from verified sources (e.g., `https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/...` or specific neuroimaging repositories if available). **Constraint**: Must NOT use `try/except` to fall back to synthetic data. If the download fails, it MUST raise a `DataFetchError` with a clear message indicating the source URL and failure reason. **Output**: The script file `code/data/fetch_real_data.py`. **Depends on**: T001-impl, T056.
- [ ] T061 [S] [US1] Implement Streaming Data Loader: Create `code/data/stream_loader.py`. **Task**: Implement a function `stream_study_data(source_path, chunk_size=100)` that processes large datasets in chunks to avoid memory overflow on the 7GB runner. Uses `datasets.load_dataset(..., streaming=True)` or manual line-by-line parsing. **Constraint**: Must accumulate statistics (N, sum_r, sum_r2) online without loading the full dataset into RAM. **Output**: The script file `code/data/stream_loader.py`. **Depends on**: T060, T013.
- [ ] T062 [S] [US1] Update Gatekeeper for Streaming: Modify `code/analysis/gatekeeper.py` (T057) to accept `streaming_mode` flag. **Task**: If `streaming_mode` is active, the gatekeeper must read the pre-computed `streaming_stats.json` (produced by T061) instead of counting lines in a full file. **Output**: Updated `code/analysis/gatekeeper.py`. **Depends on**: T057, T061.
- [ ] T063 [S] [US1] Create Data Source Registry: Create `code/config/data_sources.yaml`. **Task**: Define a registry of verified real data sources with their URLs, expected formats, and access methods. **Constraint**: This file MUST be the single source of truth for data fetching; `fetch_real_data.py` (T060) must read from this file, not hard-coded URLs. **Output**: The file `code/config/data_sources.yaml`. **Depends on**: T006a.
- [ ] T064 [S] [US1] Implement Data Source Validator: Create `code/data/validate_source.py`. **Task**: Verify that a data source in `data_sources.yaml` is reachable and returns valid data before the pipeline starts. **Constraint**: If validation fails, the pipeline must abort with an error message suggesting the use of mock data via `--use-mock` flag. **Output**: The script file `code/data/validate_source.py`. **Depends on**: T063, T060.
- [ ] T065 [S] [US1] Update Mock Data Generation for Streaming Test: Modify `code/data/generate_mock_data.py` (T000-run) to support `--streaming-test` flag. **Task**: Generate a large mock CSV (e.g., 100k rows) to test the streaming logic in T061 without exceeding disk limits. **Output**: Updated `code/data/generate_mock_data.py`. **Depends on**: T000-run, T061.
- [ ] T066 [S] [US1] Integration Test for Streaming: Create `tests/integration/test_streaming_pipeline.py`. **Task**: Run the pipeline with `--use-mock --streaming-test` and verify that `streaming_stats.json` is generated correctly and the gatekeeper processes it without memory errors. **Output**: The test file `tests/integration/test_streaming_pipeline.py`. **Depends on**: T061, T062, T065.
