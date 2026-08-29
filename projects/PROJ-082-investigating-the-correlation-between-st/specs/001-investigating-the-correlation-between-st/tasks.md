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

- [X] T001-impl [S] Initialize project directory structure: Create a Python script `code/setup/init_dirs.py` that programmatically creates `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/derived/`, `data/logs/`, `paper/`, `contracts/`, AND `state/projects/` directories. **Output**: The script `code/setup/init_dirs.py` and the created directory tree. **Constraint**: Must be runnable via `python code/setup/init_dirs.py`. **Note**: This task MUST create the `state/projects/` directory and a placeholder YAML file `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml` with an empty `artifact_hashes` map to satisfy Constitution Principle V (Versioning) before T000-verif runs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `requirements.txt`: Create `code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`. **Output**: `code/requirements.txt`. **Constraint**: Must specify `python>=3.11`.
- [X] T002b [P] Create `pyproject.toml`: Create `code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Output**: `code/pyproject.toml`. **Constraint**: Must be runnable via `ruff check.` and `black.`.
- [X] T005 [S] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation). **Input**: Must depend on `data/raw/` directory being present (created by T001-impl). **Output**: `code/utils/checksum.py` with functions `calculate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)`. **Constraint**: Must raise an exception if the file does not exist. **CRITICAL**: This task MUST NOT update the state file. It only provides utility functions for checksum calculation. **Depends on: T001-impl**.
- [X] T006a [P] Create config schema: Define `code/config/config_schema.yaml` with keys `seed` (int), `paths` (dict), `limits` (dict). **Output**: `code/config/config_schema.yaml`.
- [X] T006b [P] Implement config loader: Create `code/utils/config.py` to load `code/config/config.yaml` (if exists) or defaults, validating against `config_schema.yaml`. **Output**: `code/utils/config.py` with `load_config()` function. **Depends on: T006a**.
- [X] T006c [S] Initialize default config: Create `code/config/config.yaml` with default seed values (42, 43, 44) and paths. **Output**: `code/config/config.yaml`. **Constraint**: Must explicitly set `seed: 42` for T000-gen, `seed: 43` for T000b-gen, and `seed: 44` for T000c-gen. **Depends on: T006a, T006b**.
- [X] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata. **Fields**: `author` (string), `year` (integer), `tract` (string), `r` (float, nullable), `n` (integer, nullable), `qualitative_desc` (string, nullable), `narrative_pool` (boolean). **Output**: `contracts/study_record.schema.yaml`.
- [X] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics. **Output**: `contracts/meta_analysis_result.schema.yaml`.
- [X] T007c-1 [S] [US1] Create Tract Lexicon Generator Script: Create `code/config/generate_lexicon.py`. **Task**: Implement a script that defines a hardcoded list of tract names and directional verbs, then writes this list to `code/config/tract_lexicon.yaml`. **Output**: The script `code/config/generate_lexicon.py`. **Constraint**: This task ONLY creates the script; it does NOT produce the YAML file. **Depends on: T007a, T007b**.
- [X] T007c-2 [S] [US1] Generate Tract Lexicon: Execute `code/config/generate_lexicon.py`. **Task**: Run the script created in T007c-1 to produce `code/config/tract_lexicon.yaml`. **Content**: Must include specific tract names (`arcuate fasciculus`, `cingulum bundle`, `uncinate fasciculus`, `inferior longitudinal fasciculus`, `auditory cortex`, `ventral striatum`) and directional verbs (`increased`, `decreased`, `correlated`, `associated with`). **Schema**: Output must be a valid YAML file with keys `tracts: [list of strings]` and `verbs: [list of strings]`. **Output**: `code/config/tract_lexicon.yaml`. **Constraint**: This task MUST run after T007c-1. **Depends on: T007c-1**.
- [X] T007d-1 [S] [US1] Define the thematic coding scheme: Create `data/config/narrative_methodology.yaml` with the exact schema: `keywords: [list of strings]`, `sentiment_rules: {positive: [list], negative: [list]}`, `exclusion_criteria: [list of strings]`. **Task**: Define the coding rules (e.g., keyword frequency, sentiment analysis) to be used by T015b. **Output**: `data/config/narrative_methodology.yaml`. **Depends on: T007a, T007b**.
- [X] T007d-2 [S] [US1] Implement NLP logic: Create `code/extraction/nlp_logic.py` using the scheme from T007d-1 and lexicon from T007c-2. **Task**: Implement regex patterns to search for tract names (from T007c-2) in proximity to directional verbs. **Output**: `code/extraction/nlp_logic.py` with function `extract_qualitative_desc(text, lexicon, scheme)`. **Depends on: T007d-1, T007c-2**.
- [X] T008c [S] [US2] Implement `code/analysis/tract_counter.py` to count distinct tracts. **Task**: Read `data/processed/extracted_studies.csv` (from T013) and count unique tract names. **Output**: Write `data/derived/tract_count.json` containing `{"k": <count>}`. **Constraint**: This task MUST run after T013. **Constraint**: If `data/processed/extracted_studies.csv` is missing or empty, this task must create `data/derived/tract_count.json` with `{"k": 0}` and log a warning, rather than failing. **Depends on: T013**.
- [X] T010 [S] [US1] Generate Mock Data: Create `code/data/generate_mock_data.py` to produce three mock datasets based on a config file. **Logic**: Read a config argument `--config` which specifies the seed and constraints (e.g., `fallback`, `quant`, `bonferroni`).
 - **Default Behavior**: If `--config` is omitted, default to `quant` (seed 43, N=15).
 - If `--config=fallback`: Use seed 42, generate N=5, output `data/raw/mock_studies_fallback.csv`.
 - If `--config=quant`: Use seed 43, generate N=15, output `data/raw/mock_studies_quant.csv`.
 - If `--config=bonferroni`: Use seed 44, generate N=15 with **exactly 5 distinct tracts** (enforced via a fixed list of 5 tract names in the code), output `data/raw/mock_studies_bonferroni.csv`.
 **Constraint**: If `code/config/config.yaml` is missing, use default seeds and write them to the file. **Output**: Three CSV files as specified. **Constraint**: This task is strictly for **Unit Test Data Generation** to verify the pipeline's logic. **Note**: This task does NOT validate the scientific decision logic; it only tests the code paths. **Depends on: T001-impl, T006c**.
- [X] T009 [S] [US1] Implement Data Source Adapter: Create `code/data/data_source_adapter.py` to handle both mock data and real data. **Task**:
 1. Check for real data: Look for `data/raw/studies.csv`. If present, validate it has headers ['author', 'year', 'r', 'n']. If valid, proceed with real data.
 2. If real data is missing or invalid, check for mock data files generated by T010.
 3. **Copy Logic**:
    - If `--config` (or default) implies `fallback`: Copy `data/raw/mock_studies_fallback.csv` to `data/raw/studies.csv`.
    - If `--config` (or default) implies `quant`: Copy `data/raw/mock_studies_quant.csv` to `data/raw/studies.csv`.
    - If `--config` (or default) implies `bonferroni`: Copy `data/raw/mock_studies_bonferroni.csv` to `data/raw/studies.csv`.
 4. **Constraint**: This task MUST explicitly calculate the MD5 checksum of the selected data source (real or mock) and write it to `data/processed/checksum_tmp.json`. It MUST NOT update the state file directly.
 5. **Constraint**: This task is the single entry point for data availability. It MUST NOT depend on T000-verif if real data is present. **Output**: `data/raw/studies.csv` (populated) and `data/processed/checksum_tmp.json`. **Depends on: T001-impl, T006c, T010**.
- [X] T009b [S] [US1] Implement Real Data Validator: Create `code/data/real_data_validator.py`. **Task**: If real data is detected (via `data/raw/studies.csv` populated by T009), count the number of studies. If N < 10, raise a specific warning or error to trigger early narrative mode, ensuring Constitution Principle VII is respected before T013 runs. **Output**: A status file `data/processed/real_data_status.json` with schema `{"valid": boolean, "n": integer, "message": "string"}`. **Constraint**: This task MUST validate the existence of `data/raw/studies.csv`. **Constraint**: The implementation MUST be complete and non-truncated. **Depends on: T001-impl, T009**.
- [X] T000-verif [S] [US1] Checksum and Register Generated Data: Create `code/data/verify_data.py` to calculate MD5 checksums for `data/raw/mock_studies_fallback.csv`, `data/raw/mock_studies_quant.csv`, `data/raw/mock_studies_bonferroni.csv` (generated by T010) AND `data/raw/studies.csv` (selected by T009). **Logic**: Read the generated/selected files, compute MD5 hashes, and write/update the `artifact_hashes` map in `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml`. **YAML Schema**: The state file must contain a key `artifact_hashes` which is a dictionary mapping relative file paths to their MD5 hash strings. **Constraint**: This task is the **Single Source of Truth** for updating the state file. It MUST complete and update the state file BEFORE T013 is invoked. If the state file or directory does not exist, create it with an empty map first. **Constraint**: This task MUST depend on T009 to ensure the real data source is selected before registering checksums.

## Phase 3: User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1) 🎯 MVP

**Goal**: Extract effect sizes from CSV, handle missing data, perform random-effects meta-analysis, and trigger narrative fallback if N < 10.

**Independent Test**: Run extraction script on a small, synthetic CSV of mock studies with known effect sizes and verify the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` logic.

### Implementation for User Story 1

- [X] T013 [S] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for r, n, tract AND qualitative descriptors. **Extraction Logic**:
 1. If direct (r, n) pairs are available, keep the study in the **quantitative pool**.
 2. If (r, n) is missing, use `code/extraction/nlp_logic.py` (T007d-2) and `code/config/tract_lexicon.yaml` (T007c-2) to search for tract names and directional verbs.
 3. If no (r, n) and no qualitative descriptor found, **INCLUDE** the study in the `narrative_pool` with a `qualitative_desc` of "no_descriptor_found".
 4. **Constraint**: Studies with valid (r, n) must NOT be forced into the narrative pool just because they lack a qualitative descriptor.
 5. Log exclusion reasons to `data/logs/exclusion_log.csv` with specific values: `missing_r`, `missing_n`, `no_descriptor`.
 6. **Schema**: `exclusion_log.csv` must have columns `study_id`, `reason`, `original_value`. Valid `reason` strings are strictly: `missing_r`, `missing_n`, `no_descriptor`.
 7. **Pre-flight Check**: This task MUST verify that `code/config/tract_lexicon.yaml`, `code/extraction/nlp_logic.py`, and `data/processed/real_data_status.json` (from T009b) exist before execution.
 8. **Dependency Note**: This task depends on T009 (Data Source Adapter) to ensure `data/raw/` is populated and T009b to ensure validation. **Output**: Produce an intermediate CSV `data/processed/extracted_studies.csv` containing all studies with a `narrative_pool` boolean column and `qualitative_desc` field. **Depends on: T009, T009b, T007a, T007b, T007c-2, T007d-2**.
- [X] T014a [S] [US1] Implement `code/analysis/study_counter.py`. **Task**: Read `data/processed/extracted_studies.csv` and count unique (Author, Year) pairs. **Output**: Write `data/processed/study_count.json` containing `{"N": <count>}`. **Constraint**: This task MUST run regardless of N value. **Constraint**: If the input file is empty or missing, this task MUST create `data/processed/study_count.json` with `{"N": 0}` to prevent downstream errors. **Depends on: T013**.
- [X] T014b [S] [US1] Implement `code/analysis/valid_pair_counter.py`. **Task**: Read `data/processed/extracted_studies.csv` and count studies with valid (r, n) pairs. **Output**: Write `data/processed/valid_pair_count.json` containing `{"N_valid": <count>}`. **Constraint**: This task distinguishes between 'Data Insufficient' (N_valid = 0) and 'Narrative Fallback' (N_valid < 10). **Note**: This task is for diagnostic purposes and specific 'Data Insufficient' handling. **Depends on: T013**.
- [X] T014 [S] [US1] Implement `code/analysis/meta_analysis.py` Random-Effects model using `statsmodels` (handle convergence failure by falling back to Fixed-Effects with warning). **Gate Logic**: **MUST** read `N` from `data/processed/study_count.json` (T014a) at runtime.
 - **N < 10 Gate**: If N < 10, **MUST NOT** attempt Fixed-Effects or Random-Effects models. Immediately set `status: "skipped"`, `reason: "Insufficient studies"`, and include `N` in the output. **CRITICAL**: If N < 10, this task MUST explicitly set `status: "skipped"` to signal the orchestrator (T016) to invoke T015b immediately. **Exact Output**: `{"status": "skipped", "reason": "Insufficient studies", "N": <count>, "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"}`.
 - If N >= 10: Set `status: "completed"`, run model. **Constraint**: If `statsmodels` fails to converge, attempt Fixed-Effects fallback ONLY IF N >= 10. If convergence fails and N >= 10, output `{"model_type": "fixed_effects_fallback", "reliability": "unreliable"}`.
 - **Error Handling**: If `study_count.json` is missing, assume N=0 (per T014a guarantee) and trigger skipped status immediately. **Depends on: T014a, T013**.
- [X] T015a [S] [US1] Implement narrative logic: Create `code/analysis/narrative_logic.py` to perform thematic aggregation. **Task**: Read `data/processed/extracted_studies.csv` (T013) and `data/config/narrative_methodology.yaml` (T007d-1). Aggregate `qualitative_desc` fields by theme (e.g., "auditory-reward pathway", "frontal connectivity") and count frequency. **Logic**: Implement keyword frequency counting and sentiment rule mapping as defined in `narrative_methodology.yaml` to convert raw text into structured theme counts. **Constraint**: If `qualitative_desc` is "no_descriptor_found", group these under a "Unknown" theme or exclude them from frequency counts. **Output**: Write `data/derived/narrative_themes.json`. **Depends on: T013, T007d-1**.
- [X] T015b [S] [US1] Implement Narrative Synthesis Engine: Create `code/analysis/narrative_engine.py`. **Task**: Read `data/derived/narrative_themes.json` (T015a) and `data/processed/study_count.json` (T014a). **Pivot Logic**: If N < 10, generate the structured text content for the narrative review. **Output**: Write `data/derived/narrative_content.md`. **Constraint**: This task implements the core 'pivot' mechanism and text assembly logic. **Depends on: T015a, T014a**.
- [X] T015c [S] [US1] Implement `code/analysis/narrative.py` to generate structured text summary if eligible study count < 10. **Input**: Consume `data/derived/narrative_content.md` (from T015b) and `data/config/narrative_methodology.yaml` from T007d-1. **Output Artifact**: Generate `data/derived/narrative_summary.md`. **Structure Requirements**:
 - JSON Metadata Block at the top with keys: `study_count`, `synthesis_mode`, `timestamp`.
 - **Timestamp Format**: ISO 8601 ('YYYY-MM-DDTHH:MM:SSZ') or JSON `null` for N=0.
 - Section 1: `## Study Overview` (Methodology, References).
 - Section 2: `## Qualitative Themes` (Categorizing recurring themes regarding specific tracts based on `qualitative_desc` and the coding scheme from T007d-1).
 - Section 3: `## Limitations` (Explicitly stating N < 10 constraint).
 - **Zero-Studies Handling**: If input CSV is empty (N=0), output a specific header `# No studies found` and a JSON metadata block: `{"study_count": 0, "synthesis_mode": "narrative", "timestamp": null}`. **CRITICAL**: For N=0, the system must NOT attempt a "narrative synthesis" (which implies content aggregation). Instead, it must output a "Data Insufficient" report stating "No studies found to perform analysis". **Constraint**: This task MUST explicitly include a "Data Insufficient" disclaimer and the "Systematic Review Fallback" structure as mandated by Constitution Principle VII. **Depends on: T015b, T007d-1**.
- [X] T015d [S] [US1] Implement `code/analysis/pivot_narrative.py` as the explicit script entry point for the N < 10 pivot. **Task**: This script wraps T015b and T015c, ensuring they are called in the correct order when the gate logic (T016) detects N < 10. **Output**: A standalone script `code/analysis/pivot_narrative.py` callable via CLI. **Rationale**: Matches Plan.md requirement for a distinct `pivot_narrative.py`. **Depends on: T015b, T015c**.
- [X] T016 [S] [US1] Implement `code/main.py` Gate Logic. **Task**: Load `data/processed/study_count.json` (T014a), `data/processed/valid_pair_count.json` (T014b), and `data/processed/meta_status.json` (T014).
 - **Gate Logic**:
 - If `N_valid` (from T014b) == 0: **invoke T015c** immediately to generate "Data Insufficient" report. Set `synthesis_mode` to "narrative" and `data_insufficient` to true in `data/derived/results.json`.
 - If N < 10: **invoke `narrative_engine.generate()` from `code/analysis/narrative_engine.py` (T015b)** immediately to generate `data/derived/narrative_content.md`, then invoke T015c to generate `data/derived/narrative_summary.md`. Set `synthesis_mode` to "narrative" in the final output `data/derived/results.json`.
 - If N >= 10: **invoke T022 (Bonferroni)**, T023b (Holm-Bonferroni), T024 (MLM), and T027a/b/c (Visualization).
 - **Fallback**: If `bonferroni_status.json` (T022) is missing, assume `bonferroni_applied: false` and proceed.
 - **Output Artifact**: `data/derived/results.json` with `synthesis_mode` field set to "narrative" or "quantitative". **Constraint**: This task is the sole orchestrator for the mode switch. It conditionally invokes T015b/T015c based on the status flags from T014a, T014b, and T014. **Constraint**: This task MUST validate the existence and integrity of `valid_pair_count.json` before proceeding. **Depends on: T013, T014a, T014b, T014**.
- [X] T017 [S] [US2] Implement `code/analysis/bias.py` Egger's linear regression test. **Skip Logic**: Explicitly SKIP if `N` (from `data/processed/study_count.json`) < 10. **Input Verification**: Read `N` from `data/processed/study_count.json` (T014a) to determine skip condition. **Output Requirement**:
 - If N < 10: Output `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"`.
 - If 10 <= N < 20: Run test, output result, AND append `warning: "Low Power: Egger's test may be unreliable with N < 20"`. **This aligns with the Plan's reliability threshold.**
 - If N >= 20: Run test, output result.
 **Artifact**: Append `egger_test` object to `MetaAnalysisResult` JSON at `data/derived/results.json`. **Depends on: T014a, T014**.
- [X] T018 [S] [US2] Implement `code/analysis/heterogeneity.py` I² calculation. **Precision Requirement**: The output MUST report the I² statistic with **exactly two decimal places** (e.g., a precise numerical value) using **round half to even** rounding as mandated by **SC-002** and **FR-002**. **Artifact**: Append `i_squared` field to the `MetaAnalysisResult` JSON at `data/derived/results.json`. **Note**: This task is independent of T017 and does not require its results. **Depends on: T014a, T014**.
- [X] T021 [S] [US2] Implement `code/analysis/correction.py` for multiple comparison correction. **Decision Logic**:
 1. **Check N**: Read `N` from `data/processed/study_count.json` (T014a). If N < 10, **skip immediately**, log "Bonferroni skipped: N < 10", and set `bonferroni_applied: false` in `data/derived/bonferroni_status.json`.
 2. **Check k**: If N >= 10, read `k` (distinct tract count) from `data/derived/tract_count.json` (T008c).
 3. **Execute ONLY if** k ≥ 2 tracts AND N ≥ 10.
 4. **Constraint**: Do NOT implement Robust Variance Estimation (RVE). The spec mandates Bonferroni correction only.
 5. **Implementation**: If k < 2 or if `tract_count.json` is missing (indicating T013/T008c failure), log a warning "Bonferroni correction skipped: k < 2 or extraction failed" and set `bonferroni_applied: false` in the output. If k >= 2, calculate the adjusted threshold and set `bonferroni_applied: true`.
 6. **Output Requirement**: Generate `data/derived/bonferroni_status.json` containing `{"bonferroni_applied": <bool>, "adjusted_threshold": <float>}`. **Constraint**: This task MUST NOT generate narrative text (e.g., "Limitations" notes). The narrative note regarding Bonferroni conservatism must be generated by T032 (Report Generation) based on this status. **Constraint**: This task MUST explicitly verify N >= 10 as a hard gate within the task logic. **Depends on: T008c, T014a**.
- [X] T022 [S] [US2] Implement Multilevel Meta-Analysis (MLM): Create `code/analysis/mlm.py` to perform a robustness check. **Task**: Use `statsmodels` mixed linear models (or `rpy2` if necessary) to model `effect_size ~ 1` with `study_id` as a random effect. **Goal**: Validate the independence assumption by comparing MLM results to Bonferroni-corrected results. **Output**: Write `data/derived/mlm_results.json` containing `pooled_effect`, `confidence_interval`, and `divergence_flag` (true if MLM CI does not overlap with Bonferroni CI). **Constraint**: This task runs only if N >= 10. **Depends on: T014, T022**.
- [X] T023 [S] [US2] Implement Bonferroni correction (Conservative). **Task**: Implement the standard Bonferroni procedure to adjust p-values for multiple comparisons. **Output**: Update `data/derived/results.json` with adjusted p-values and a flag indicating whether adjustment was applied. **Note**: This serves as the conservative comparison per Plan.md.
- [X] T023b [S] [US2] Implement Holm-Bonferroni correction. **Task**: Implement the Holm-Bonferroni procedure (step-down) to adjust p-values for multiple comparisons. **Output**: Update `data/derived/results.json` with adjusted p-values and a flag indicating whether adjustment was applied. **Note**: This is the primary correction method per Plan.md.
- [X] T024 [S] [US3] Implement `code/visualization/plots_forest.py` to generate the **Forest Plot**. **Requirement**: Summary diamond must align with `weighted_mean_r` from `data/derived/results.json`. **Artifact**: Save PNG to `data/derived/forest_plot.png`. **Constraint**: This task MUST use the memory threshold from T042's config and the validation trigger from T031. **Depends on: T042**.
- [X] T025 [P] [US3] Implement `code/visualization/plots_funnel.py` to generate the **Funnel Plot**. **Requirement**: Plot standard error vs effect size; render vertical symmetry line at pooled effect. **Artifact**: Save PNG to `data/derived/funnel_plot.png`. **Constraint**: This task MUST use the memory threshold from T042's config and the validation trigger from T031. **Depends on: T042**.
- [X] T026 [P] [US3] Implement `code/visualization/plots_correlation.py` to generate the **Correlation Summary Plot**. **Artifact**: Save PNG to `data/derived/correlation_summary.png`. **Constraint**: This task MUST use the memory threshold from T042's config and the validation trigger from T031.
- [X] T027a [P] [US3] Implement `code/visualization/memory_monitor.py` to wrap plot generation with `tracemalloc` and abort if peak memory exceeds a predefined safe threshold, logging the specific plot causing the overflow. **Output**: Reusable module for T027a/b/c. **Constraint**: This task is now in Phase 2 to ensure dependency availability before Phase 5 visualization tasks. **Constraint**: This task ensures dependency availability for T027a/b/c. **Depends on: T002a**.
- [X] T027b [P] [US3] Implement file size validation logic in `code/utils/validator.py`: Add a function to verify generated PNGs are < 5MB. **Execution**: This task runs **immediately after** T027a generates the plots. It validates the output and generates a validation report. **Constraint**: If validation fails, write `overall_status: "fail"` to `data/derived/validation_report.json` and **return exit code 2** (non-fatal) to allow the orchestrator (T027c) to invoke T025d for retry logic. If validation passes, return a successful exit code.
- [X] T027c [S] [US3] Implement `code/visualization/regenerator.py` to handle plot retry logic. **Task**: Read `data/derived/validation_report.json` (from T025). **Fallback**: **If the file is missing, assume validation passed and skip retry logic.** If `overall_status` is "fail", regenerate the specific failed plot(s) with **DPI=100 and compression=6**. **Constraint**: **Max retries = 2**. If validation still fails after 2 retries, **raise an exception** and log to `data/logs/regeneration_failure.log`. **Depends on: T027b**.
- [X] T031 [P] [US3] Integrate visualization into `code/main.py` (save PNGs to `data/derived/` after analysis).
- [X] T032 [P] Generate `docs/paper_draft.md` from `MetaAnalysisResult` JSON using Jinja2 template (automated report generation). **Constraint**: This task MUST generate the "Limitations" note regarding Bonferroni conservatism if `bonferroni_applied` is true in `data/derived/bonferroni_status.json`. It MUST NOT rely on hardcoded strings in analysis tasks.
- [X] T033a [P] Run linting (ruff) and fix any violations; save log to `data/logs/lint_report.md`. **Replaces rejected T033**.
- [X] T034a [P] Profile total runtime and ensure <15 mins on CI; optimize bottlenecks if exceeded; save report to `data/logs/profile_report.md`. **Replaces rejected T034**.
- [X] T035 [P] Additional unit tests in `tests/unit/` (coverage for p-value conversion edge cases).
- [X] T038a [P] [US3] Create Bonferroni Test Script: Create `tests/unit/test_bonferroni.py`. **Task**: Implement unit tests for the Bonferroni and Holm-Bonferroni correction logic, verifying SC-004 (5 distinct tracts) and threshold calculations. **Output**: `tests/unit/test_bonferroni.py`. **Depends on: T021, T023, T023b**.
- [X] T038 [P] Run Bonferroni Verification: Execute `pytest tests/unit/test_bonferroni.py` to verify SC-004. **Output**: Test logs and failure evidence. **Depends on: T038a**.

## Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
- [ ] T010 [P] [US1] Unit test for extraction logic in `tests/unit/test_extraction.py` (verify r, n parsing). **Output**: Test logs and failure evidence. **Depends on: T013**.
- [ ] T011 [P] [US1] Unit test for meta-analysis calculation in `tests/unit/test_meta_analysis.py` (verify weighted mean within 0.001 tolerance). **Output**: Test logs and failure evidence. **Depends on: T014**.
- [ ] T012 [P] [US1] Unit test for narrative fallback trigger in `tests/unit/test_narrative.py` (verify N < 10 skips aggregation). **Output**: Test logs and failure evidence. **Depends on: T015b**.

## Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️
- [ ] T019 [P] [US2] Unit test for I² calculation in `tests/unit/test_heterogeneity.py` (verify precision to **exactly two decimal places** as required by SC-002, e.g., 52.34)
- [ ] T020 [P] [US2] Unit test for Egger's regression in `tests/unit/test_bias.py` (verify p-value calculation and N < 10 skip logic; verify `egger_skipped_reason` output matches **exact string**: 'Skipped: Insufficient studies (N < 10) for Egger's regression')