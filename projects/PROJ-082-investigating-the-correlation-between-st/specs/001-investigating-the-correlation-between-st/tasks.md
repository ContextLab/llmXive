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
- [X] T005 [S] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation). **Input**: Must depend on `data/raw/` directory being present (created by T001-impl). **Output**: `code/utils/checksum.py` with functions `calculate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)`. **Constraint**: Must raise an exception if the file does not exist. **CRITICAL**: This task MUST **NOT** update the state file. It only provides utility functions for checksum calculation. **Depends on: T001-impl**.
- [X] T006a [P] Create config schema: Define `code/config/config_schema.yaml` with keys `seed` (int), `paths` (dict), `limits` (dict). **Output**: `code/config/config_schema.yaml`.
- [X] T006b [P] Implement config loader: Create `code/utils/config.py` to load `code/config/config.yaml` (if exists) or defaults, validating against `config_schema.yaml`. **Output**: `code/utils/config.py` with `load_config()` function. **Depends on: T006a**.
- [X] T006c [S] Initialize default config: Create `code/config/config.yaml` with default seed values (42, 43, 44) and paths. **Output**: `code/config/config.yaml`. **Constraint**: Must explicitly set `seed: 42` for T000-gen, `seed: 43` for T000b-gen, and `seed: 44` for T000c-gen. **Depends on: T006a, T006b**.
- [X] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata. **Fields**: `author` (string), `year` (integer), `tract` (string), `r` (float, nullable), `n` (integer, nullable), `qualitative_desc` (string, nullable), `narrative_pool` (boolean). **Output**: `contracts/study_record.schema.yaml`. **Constraint**: Must include `narrative_pool` and `qualitative_desc` fields to match T013 output.
- [X] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics. **Output**: `contracts/meta_analysis_result.schema.yaml`.
- [X] T007c [S] Create tract lexicon: Create `code/config/generate_lexicon.py` to produce `data/config/tract_lexicon.yaml`. **Content**: Must include specific tract names (`arcuate fasciculus`, `cingulum bundle`, `uncinate fasciculus`, `inferior longitudinal fasciculus`, `auditory cortex`, `ventral striatum`) and directional verbs (`increased`, `decreased`, `correlated`, `associated with`). **Output**: `data/config/tract_lexicon.yaml`. **Constraint**: This task MUST NOT implement any prioritization or filtering logic. It must only standardize tract names. **Prerequisite**: T007c must complete before T007d-2 executes to ensure the NLP logic has the lexicon. **Depends on: T007a, T007b**.
- [X] T007d-1 [S] [US1] Define the thematic coding scheme: Create `data/config/narrative_methodology.yaml` with the exact schema: `keywords: [list of strings]`, `sentiment_rules: {positive: [list], negative: [list]}`, `exclusion_criteria: [list of strings]`. **Task**: Define the coding rules (e.g., keyword frequency, sentiment analysis) to be used by T015b. **Output**: `data/config/narrative_methodology.yaml`. **Depends on: T007a, T007b**.
- [X] T007d-2 [S] [US1] Implement NLP logic: Create `code/extraction/nlp_logic.py` using the scheme from T007d-1 and lexicon from T007c. **Task**: Implement regex patterns to search for tract names (from T007c) in proximity to directional verbs. **Output**: `code/extraction/nlp_logic.py` with function `extract_qualitative_desc(text, lexicon, scheme)`. **Depends on: T007d-1, T007c**.
- [X] T008 [P] Implement tract harmonization logic: `code/analysis/tract_mapping.py` (JHU Atlas mapping, string normalization). **Constraint**: This task MUST NOT implement any prioritization or filtering logic. It must only standardize tract names. **Depends on: T007a, T007b**.
- [X] T008c [S] [US1] Implement `code/analysis/tract_counter.py` to count distinct tracts. **Task**: Read `data/processed/extracted_studies.csv` (from T013) and count unique tract names. **Output**: Write `data/derived/tract_count.json` containing `{"k": <count>}`. **Constraint**: This task MUST run after T013. **Depends on: T013**.
- [X] T009 [S] [US1] Implement Data Source Adapter: Create `code/data/data_source_adapter.py` to handle both mock data and real data. **Task**:
 1. Check for real data: Look for `data/raw/studies.csv`. If present, validate it has headers ['author', 'year', 'r', 'n']. If valid, proceed with real data.
 2. If real data is missing or invalid, check for mock data files (`data/raw/mock_studies_*.csv`).
 3. If mock data exists, copy the appropriate file to `data/raw/studies.csv`.
 4. **Constraint**: This task MUST explicitly calculate the MD5 checksum of the selected data source (real or mock) and update `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml` with the hash BEFORE proceeding.
 5. **Constraint**: This task is the single entry point for data availability. It MUST NOT depend on T000-verif if real data is present. **Depends on: T001-impl, T006c, T005**.
- [ ] T009b [S] [US1] Implement Real Data Validator: Create `code/data/real_data_validator.py`. **Task**: If real data is detected, count the number of studies. If N < 10, raise a specific warning or error to trigger early narrative mode, ensuring Constitution Principle VII is respected before T013 runs. **Output**: A status file `data/processed/real_data_status.json` with `{"valid": true/false, "n": <count>}`. **Constraint**: This task breaks the dependency loop for real data paths. **Depends on: T001-impl**.
- [X] T009c [P] Setup logging infrastructure: `code/utils/logger.py` (structured logging for convergence warnings, fallbacks)
- [X] T042 [S] [US3] Implement `code/visualization/memory_monitor.py` to wrap plot generation with `tracemalloc` and abort if peak memory exceeds a predefined safe threshold, logging the specific plot causing the overflow. **Output**: Reusable module for T027a/b/c. **Constraint**: This task is now in Phase 2 to ensure library availability before Phase 5 visualization tasks. **Depends on: T002a**.
- [X] T040 [P] Implement P-value converter: `code/extraction/p_value_converter.py` to convert p-values to r-values using Fisher's z. **Output**: `code/extraction/p_value_converter.py`. **Depends on: T002a**.
- [ ] T000-gen [S] [US1] Generate mock data for Fallback Testing (N=5): Create `code/data/generate_mock_data.py` to produce `data/raw/mock_studies_fallback.csv` with synthetic studies containing `author`, `year`, `tract`, `r`, `n`, and `qualitative_desc` columns. **Logic**: Read the random seed from `code/config/config.yaml` (default value 42). **Constraint**: If `code/config/config.yaml` is missing, use default seed 42 and **write** `seed: 42` to the file to ensure reproducibility. **Output**: `data/raw/mock_studies_fallback.csv`. **Constraint**: This task is strictly for **Unit Test Data Generation** to verify the pipeline's fallback logic. It does not represent the scientific output. The pipeline must pivot to narrative synthesis if real data is insufficient. **Note**: This task does NOT validate the scientific decision logic (which requires variable N inputs); it only tests the code paths. **Constraint**: This task does NOT depend on T000-verif. **Depends on: T001-impl, T006c**.
- [ ] T000b-gen [S] [US1] Generate mock data for Quantitative Testing (N=15): Create `code/data/generate_mock_data.py` to produce `data/raw/mock_studies_quant.csv` with a set of synthetic studies containing `author`, `year`, `tract`, `r`, `n`, and `qualitative_desc` columns. **Logic**: Read the random seed from `code/config/config.yaml` (default value 43). **Constraint**: If `code/config/config.yaml` is missing, use default seed 43 and **write** `seed: 43` to the file to ensure reproducibility. **Output**: `data/raw/mock_studies_quant.csv`. **Constraint**: This task is strictly for **Unit Test Data Generation** to verify the quantitative path. It does not represent the scientific output. **Note**: This task does NOT validate the scientific decision logic (which requires variable N inputs); it only tests the code paths. **Constraint**: Generate random r values within a suitable positive range. **Constraint**: This task does NOT depend on T000-verif. **Depends on: T001-impl, T006c**.
- [ ] T000c-gen [S] [US1] Generate mock data for Bonferroni Verification (N=15, k=5): Create `code/data/generate_mock_data.py` to produce `data/raw/mock_studies_bonferroni.csv` with synthetic studies containing `author`, `year`, `tract`, `r`, `n`, and `qualitative_desc` columns. **Logic**: Use seed 44. **Constraint**: If `code/config/config.yaml` is missing, use default seed 44 and **write** `seed: 44` to the file to ensure reproducibility. **Constraint**: Ensure exactly 5 distinct tract names are used across the 15 studies to satisfy SC-004. **Output**: `data/raw/mock_studies_bonferroni.csv`. **Constraint**: This task is strictly for **Unit Test Data Generation** to verify Bonferroni correction logic. **Depends on: T001-impl, T006c**.
- [ ] T000-verif [S] [US1] Checksum and Register Generated Data: Create `code/data/verify_data.py` to calculate MD5 checksums for `data/raw/mock_studies_fallback.csv`, `data/raw/mock_studies_quant.csv`, and `data/raw/mock_studies_bonferroni.csv` (generated by T000-gen, T000b-gen, T000c-gen). **Logic**: Read the generated files, compute MD5 hashes, and write/update the `artifact_hashes` map in `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml`. **YAML Schema**: The state file must contain a key `artifact_hashes` which is a dictionary mapping relative file paths (e.g., `data/raw/mock_studies_fallback.csv`) to their MD5 hash strings (e.g., `{"data/raw/mock_studies_fallback.csv": "abc123..."}`). **Constraint**: This task is the **Single Source of Truth** for updating the state file. It MUST complete and update the state file BEFORE T013 is invoked. If the state file or directory does not exist, create it with an empty map first. **Depends on: T000-gen, T000b-gen, T000c-gen, T001-impl**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1) 🎯 MVP

**Goal**: Extract effect sizes from CSV, handle missing data, perform random-effects meta-analysis, and trigger narrative fallback if N < 10.

**Independent Test**: Run extraction script on a small, synthetic CSV of mock studies with known effect sizes and verify the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` logic.

### Implementation for User Story 1

- [X] T013 [S] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for r, n, tract AND qualitative descriptors. **Extraction Logic**:
 1. If direct (r, n) pairs are available, keep the study in the **quantitative pool**.
 2. If (r, n) is missing, use `code/extraction/nlp_logic.py` (T007d-2) and `data/config/tract_lexicon.yaml` (T007c) to search for tract names and directional verbs.
 3. If no (r, n) and no qualitative descriptor found, **INCLUDE** the study in the `narrative_pool` with a `qualitative_desc` of "no_descriptor_found".
 4. **Constraint**: Studies with valid (r, n) must NOT be forced into the narrative pool just because they lack a qualitative descriptor.
 5. Log exclusion reasons to `data/logs/exclusion_log.csv` with specific values: `missing_r`, `missing_n`, `no_descriptor`.
 6. **Schema**: `exclusion_log.csv` must have columns `study_id`, `reason`, `original_value`. Valid `reason` strings are strictly: `missing_r`, `missing_n`, `no_descriptor`.
 7. **Pre-flight Check**: This task MUST verify that `data/config/tract_lexicon.yaml` and `code/extraction/nlp_logic.py` exist before execution.
 8. **Dependency Note**: This task depends on T009 (Data Source Adapter) to ensure `data/raw/` is populated.
 9. **Output**: Produce an intermediate CSV `data/processed/extracted_studies.csv` containing all studies with a `narrative_pool` boolean column and `qualitative_desc` field. **Depends on: T009, T007a, T007b, T007c, T007d-2, T040**.
- [X] T014a [S] [US1] Implement `code/analysis/study_counter.py`. **Task**: Read `data/processed/extracted_studies.csv` and count unique (Author, Year) pairs. **Output**: Write `data/processed/study_count.json` containing `{"N": <count>}`. **Constraint**: This task MUST run regardless of N value. **Depends on: T013**.
- [X] T014b [S] [US1] Implement `code/analysis/valid_pair_counter.py`. **Task**: Read `data/processed/extracted_studies.csv` and count studies with valid (r, n) pairs. **Output**: Write `data/processed/valid_pair_count.json` containing `{"N_valid": <count>}`. **Constraint**: This task distinguishes between 'Data Insufficient' (N_valid = 0) and 'Narrative Fallback' (N_valid < 10). **Depends on: T013**.
- [ ] T014 [S] [US1] Implement `code/analysis/meta_analysis.py` Random-Effects model using `statsmodels` (handle convergence failure by falling back to Fixed-Effects with warning). **Gate Logic**: **MUST** read `N` from `data/processed/study_count.json` (T014a) at runtime.
 - **ALWAYS** write `data/processed/meta_status.json`.
 - If N < 10: Set `status: "skipped"`, `reason: "Insufficient studies"`, and include `N` in the output. **CRITICAL**: If N < 10, this task MUST explicitly set `status: "skipped"` to signal the orchestrator (T016) to invoke T015b immediately. **Exact Output**: `{"status": "skipped", "reason": "Insufficient studies", "N": <count>, "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"}`.
 - If N >= 10: Set `status: "completed"`, run model, and output `data/derived/results.json` (which MUST include `i_squared` and `egger_p` if N>=10).
 - **Constraint**: If Fixed-Effects fallback is triggered, the output JSON MUST include a flag `"model_type": "fixed_effects_fallback"` and `"reliability": "unreliable"`.
 - **Error Handling**: If `study_count.json` is missing, raise a `FileNotFoundError` with exact message "Missing study count. Run T014a first". T016 must catch this exception and trigger narrative mode.
 - **Note**: This task runs unconditionally. It does NOT assume N>=10. It reads N and sets status accordingly. **Depends on: T013, T014a**.
- [X] T016 [S] [US1] Implement `code/main.py` Gate Logic. **Task**: Load `data/processed/study_count.json` (T014a), `data/processed/valid_pair_count.json` (T014b), and `data/processed/meta_status.json` (T014).
 - **Gate Logic**:
 - If `N_valid` (from T014b) == 0: **invoke T015c** immediately to generate "Data Insufficient" report. Set `synthesis_mode` to "narrative" and `data_insufficient` to true in `data/derived/results.json`.
 - If `meta_status.status` (from T014) == "skipped" (N < 10): **invoke `narrative_engine.generate()` from `code/analysis/narrative_engine.py` (T015b)** immediately to generate `data/derived/narrative_content.md`, then invoke T015c to generate `data/derived/narrative_summary.md`. Set `synthesis_mode` to "narrative" in the final output `data/derived/results.json`.
 - If `meta_status.status` (from T014) == "completed": **invoke T022 (Bonferroni)** and T027a/b/c (Visualization).
 - **Fallback**: If `bonferroni_status.json` (T022) is missing, assume `bonferroni_applied: false` and proceed.
 - **Output Artifact**: `data/derived/results.json` with `synthesis_mode` field set to "narrative" or "quantitative". **Constraint**: This task is the sole orchestrator for the mode switch. It conditionally invokes T015b/T015c based on the status flags from T014a, T014b, and T014. **Constraint**: This task MUST validate the existence and integrity of `valid_pair_count.json` before proceeding. **Depends on: T013, T014a, T014b, T014, T015a, T015b, T015c**.
- [X] T015a [S] [US1] Implement narrative logic: Create `code/analysis/narrative_logic.py` to perform thematic aggregation. **Task**: Read `data/processed/extracted_studies.csv` (T013) and `data/config/narrative_methodology.yaml` (T007d-1). Aggregate `qualitative_desc` fields by theme (e.g., "auditory-reward pathway", "frontal connectivity") and count frequency. **Logic**: Implement keyword frequency counting and sentiment rule mapping as defined in `narrative_methodology.yaml` to convert raw text into structured theme counts. **Constraint**: If `qualitative_desc` is "no_descriptor_found", group these under a "Unknown" theme or exclude them from frequency counts. **Output**: Write `data/derived/narrative_themes.json`. **Depends on: T013, T007d-1**.
- [X] T015b [S] [US1] Implement Narrative Synthesis Engine: Create `code/analysis/narrative_engine.py`. **Task**: Read `data/derived/narrative_themes.json` (T015a) and `data/processed/study_count.json` (T014a). **Pivot Logic**: If N < 10, generate the structured text content for the narrative review. **Output**: Write `data/derived/narrative_content.md`. **Constraint**: This task implements the core 'pivot' mechanism and text assembly logic. **Depends on: T015a, T014a**.
- [X] T015c [S] [US1] Implement `code/analysis/narrative.py` to generate structured text summary if eligible study count < 10. **Input**: Consume `data/derived/narrative_content.md` (from T015b) and `data/config/narrative_methodology.yaml` from T007d-1. **Output Artifact**: Generate `data/derived/narrative_summary.md`. **Structure Requirements**:
 - JSON Metadata Block at the top with keys: `study_count`, `synthesis_mode`, `timestamp`.
 - **Timestamp Format**: ISO 8601 ('YYYY-MM-DDTHH:MM:SSZ') or JSON `null` for N=0.
 - Section 1: `## Study Overview` (Methodology, References).
 - Section 2: `## Qualitative Themes` (Categorizing recurring themes regarding specific tracts based on `qualitative_desc` and the coding scheme from T007d-1).
 - Section 3: `## Limitations` (Explicitly stating N < 10 constraint).
 - **Zero-Studies Handling**: If input CSV is empty (N=0), output a specific header `# No studies found` and a JSON metadata block: `{"study_count": 0, "synthesis_mode": "narrative", "timestamp": null}`. **CRITICAL**: For N=0, the system must NOT attempt a "narrative synthesis" (which implies content aggregation). Instead, it must output a "Data Insufficient" report stating "No studies found to perform analysis". **Constraint**: Must explicitly include a "Data Insufficient" disclaimer and the "Systematic Review Fallback" structure as mandated by Constitution Principle VII. **Depends on: T015b, T007d-1**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneity and Bias Assessment (Priority: P2)

**Goal**: Calculate I² statistics and perform Egger's regression test (only if N ≥ 10).

**Independent Test**: Provide a synthetic dataset with high variance and verify I² > 50%; provide skewed data to verify Egger's test p-value < 0.05; verify skip logic for N < 10.

### Implementation for User Story 2

- [X] T021 [S] [US2] Implement `code/analysis/bias.py` Egger's linear regression test. **Skip Logic**: Explicitly SKIP if `N` (from `data/processed/study_count.json`) < 10. **Input Verification**: Read `N` from `data/processed/study_count.json` (T014a) to determine skip condition. **Output Requirement**: If N >= 10, report the intercept and p-value. If N < 10 or `meta_status.status` is "skipped", output the exact string `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"` as a runtime value in the result JSON. **Depends on: T014a, T014**.
- [X] T021b [S] [US2] Implement `code/analysis/heterogeneity.py` I² calculation. **Precision Requirement**: The output MUST report the I² statistic with **exactly two decimal places** (e.g., a precise numerical value) using **round half to even** rounding as mandated by **SC-002** and **FR-002**. **Artifact**: Append `i_squared` field to the `MetaAnalysisResult` JSON at `data/derived/results.json`. **Note**: This task is independent of T021 and does not require its results. **Depends on: T014a, T014**.
- [X] T022 [S] [US2] Implement `code/analysis/correction.py` for multiple comparison correction. **Decision Logic**:
 1. **Check N**: Read `N` from `data/processed/study_count.json` (T014a). If N < 10, **skip immediately**, log "Bonferroni skipped: N < 10", and set `bonferroni_applied: false` in `data/derived/bonferroni_status.json`.
 2. **Check k**: If N >= 10, read `k` (distinct tract count) from `data/derived/tract_count.json` (T008c).
 3. **Execute ONLY if** k ≥ 2 tracts AND N ≥ 10.
 4. **Constraint**: Do NOT implement Robust Variance Estimation (RVE). The spec mandates Bonferroni correction only.
 5. **Implementation**: If k < 2 or if `tract_count.json` is missing (indicating T013/T008c failure), log a warning "Bonferroni correction skipped: k < 2 or extraction failed" and set `bonferroni_applied: false` in the output. If k >= 2, calculate the adjusted threshold and set `bonferroni_applied: true`.
 6. **Output Requirement**: Generate `data/derived/bonferroni_status.json` containing `{"bonferroni_applied": <bool>, "adjusted_threshold": <float>}`. **Constraint**: This task MUST NOT generate narrative text (e.g., "Limitations" notes). The narrative note regarding Bonferroni conservatism must be generated by T032 (Report Generation) based on this status. **Constraint**: This task must explicitly verify N >= 10 as a hard gate within the task logic. **Depends on: T008c, T014a, T016**.
- [X] T023 [P] [US2] Integrate bias assessment into `code/main.py` (run after meta-analysis, update `MetaAnalysisResult` JSON).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate forest plots, funnel plots, and summary correlation plots using `matplotlib` and `seaborn`.

**Independent Test**: Run plotting module on a static dataset and verify PNG files exist, are under a reasonable file size limit, and contain correct axis labels/data points.

### Implementation for User Story 3

- [X] T027a [P] [US3] Implement `code/visualization/plots_forest.py` to generate the **Forest Plot**. **Requirement**: Summary diamond must align with `weighted_mean_r` from `data/derived/results.json`. **Artifact**: Save PNG to `data/derived/forest_plot.png`. **Depends on: T042**.
- [X] T027b [P] [US3] Implement `code/visualization/plots_funnel.py` to generate the **Funnel Plot**. **Requirement**: Plot standard error vs effect size; render vertical symmetry line at pooled effect. **Artifact**: Save PNG to `data/derived/funnel_plot.png`. **Depends on: T042**.
- [X] T027c [P] [US3] Implement `code/visualization/plots_correlation.py` to generate the **Correlation Summary Plot**. **Artifact**: Save PNG to `data/derived/correlation_summary.png`. **Depends on: T042**.
- [X] T027d [S] [US3] Implement `code/visualization/regenerator.py` to handle plot retry logic. **Task**: Read `data/derived/validation_report.json` (from T031). If `overall_status` is "fail", regenerate the specific failed plot(s) with **DPI=100 and compression=6**. **Constraint**: **Max retries = 2**. If validation still fails after 2 retries, **raise an exception** and log to `data/logs/regeneration_failure.log`. **Readability Check**: After regeneration, verify that axis labels and font sizes are > 8pt by checking `matplotlib` text properties to ensure scientific clarity. **Trigger Condition**: Retry only if memory > 6GB or file size > 5MB. **Pre-flight Check**: This task MUST check if `data/derived/validation_report.json` exists before attempting to read it. **Depends on: T027a, T027b, T027c, T031**.
- [X] T027e [S] [US3] Implement `code/main.py` Validation Loop Orchestrator. **Task**: Implement the retry loop that catches exit code 2 from T031 and invokes T027d up to 2 times. **Constraint**: This task is the explicit orchestrator for the validation loop. It does NOT depend on T031 for data flow, but only for exit code handling. It **invokes** T031, so it does not depend on T031 as a prerequisite. **Depends on: T027d**.
- [X] T028 [P] [US3] Integrate visualization into `code/main.py` (save PNGs to `data/derived/` after analysis).
- [X] T031 [P] [US3] Implement file size validation logic in `code/utils/validator.py`: Add a function to verify generated PNGs are < 5MB. **Execution**: This task runs **immediately after** T027a/b/c generates the plots. It validates the output and generates a validation report. **Constraint**: If validation fails, write `overall_status: "fail"` to `data/derived/validation_report.json` and **return exit code 2** (non-fatal) to allow the orchestrator (T027e) to invoke T027d for retry logic. If validation passes, return a successful exit code. **Depends on: T027a, T027b, T027c**.
- [X] T038 [P] [US2] Implement `code/analysis/validate_bonferroni.py` to verify SC-004. **Task**: Run a test case with multiple distinct tracts (using `data/raw/mock_studies_bonferroni.csv` from T000c-gen) by executing `pytest tests/unit/test_bonferroni.py` and verify that `bonferroni_applied` is true and `adjusted_threshold` is reported correctly. **Output**: `data/logs/bonferroni_validation_report.md`. **Constraint**: This task explicitly verifies the "5 distinct tracts" scenario required by SC-004. **Depends on: T022, T000c-gen**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Generate `docs/paper_draft.md` from `MetaAnalysisResult` JSON using Jinja2 template (automated report generation). **Constraint**: This task MUST generate the "Limitations" note regarding Bonferroni conservatism if `bonferroni_applied` is true in `data/derived/bonferroni_status.json`. It MUST NOT rely on hardcoded strings in analysis tasks. **Depends on: T016**.
- [X] T033a [P] Run linting (ruff) and fix any violations; save log to `data/logs/lint_report.md`. **Replaces rejected T033**.
- [X] T034a [P] Profile total runtime and ensure <15 mins on CI; optimize bottlenecks if exceeded; save report to `data/logs/profile_report.md`. **Replaces rejected T034**.
- [X] T035 [P] Additional unit tests in `tests/unit/` (coverage for p-value conversion edge cases).
- [X] T036a [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution; save log to `data/logs/quickstart_report.md`. **Replaces rejected T036**.
- [X] T037 [P] Verify `tasks.md` execution order matches data flow (extraction -> analysis -> visualization). **Verification Method**: This task involves generating a dependency graph from the task list and confirming no circular dependencies exist, specifically checking the data flow from T006c -> T000-gen -> T009 -> T013 -> T014a -> T016.
- [X] T039 [P] Implement `tests/integration/test_real_data_flow.py` to verify the pipeline processes real dataset downloads without memory overflow.
- [X] T041 [P] [US1] Implement `code/analysis/convergence_handler.py` to detect `statsmodels` non-convergence warnings and automatically trigger the Fixed-Effects fallback with a specific log entry. **Dependency**: Must be called within T014.
- [X] T048 [P] [US1] Implement `code/main.py` logic to adopt any "VERIFIED REAL DATA SOURCE" injected by the execution stage, replacing any hand-rolled `load_dataset` or guessed URLs with the provided package/recipe. **Constraint**: Ensure the single source of truth for data is the verified source. **Mechanism**: Check environment variable `VERIFIED_DATA_SOURCE_PATH` or file `data/verified_source.yaml` for the source location. **Note**: Data ingestion is handled via external scripts or manual CSV preparation, not the core pipeline. **Path Update**: Ensure state file path matches `state/projects/PROJ-082-investigating-the-correlation-between-st.yaml`. **Depends on: T013**.

## Re-plan Section

**Rejected Tasks**: The following tasks were previously marked as "Repeatedly-unverifiable" or "Rejected" and have been replaced:
- **T001** (Initialize directory structure): Replaced by **T001-impl** (create dirs script).
- **T003** (Configure linting): Replaced by **T003-impl** (create pyproject.toml).
- **T033** (Linting): Replaced by **T033a** (Run linting and save log).
- **T034** (Profiling): Replaced by **T034a** (Profile and save report).
- **T036** (Quickstart): Replaced by **T036a** (Run quickstart validation and save log).
- **T035, T037**: Retained but verified for executability.
- **T038** (Data Fetcher): **Removed** (Scope Creep). The project assumes input CSVs are provided.
- **T046** (Streaming Processor): **Removed** (Scope Creep).
- **T047** (Fetch Failure Handler): **Removed** (Orphan task). No network fetch logic required by spec.
- **T049** (Data Source Registry): **Removed** (Scope Creep). No dynamic registry required by spec.
- **T052** (Validation Report MD): **Removed** (Redundant). JSON report (T031) is sufficient.
- **T007d** (Coarse Task): **Split** into T007d-1 (Config) and T007d-2 (Code).
- **T016** (Main Entry): **Merged** into T016 (Gate Logic) to resolve circular dependencies and split logic.
- **T027** (Generic Plotter): **Split** into T027a (Forest), T027b (Funnel), T027c (Correlation), T027d (Regenerator), and T027e (Orchestrator).
- **T049** (Fetch versions): **Removed** (Reproducibility violation).
- **T043, T044, T045** (Mock Data): **Merged** into T000-gen/T000b-gen/T000c-gen to ensure deterministic generation.

**Restored Tasks**: The following tasks were incorrectly marked as "REMOVED" in previous drafts and are now **ACTIVE**:
- **T013** (Parser): Retained. Essential for extracting qualitative descriptors and populating the narrative pool.
- **T014a** (Study Counter): Retained. Essential for generating `study_count.json` required by the gate logic.
- **T014** (Meta-Analysis): Retained. Essential for generating `meta_status.json` and performing the statistical analysis.
- **T008c** (Tract Counting): Retained. Essential for generating `tract_count.json` required for Bonferroni correction.
- **T021** (Egger's Test): Retained. Essential for bias assessment and skip logic.
- **T016** (Gate Logic): Retained. Essential for orchestrating the mode switch between quantitative and narrative paths.
- **T015a** (Narrative Logic): Retained. Essential for thematic aggregation.
- **T015b** (Narrative Engine): Retained. Essential for text generation.
- **T015c** (Narrative Summary): Retained. Essential for final summary.
- **T021b** (Heterogeneity): Retained. Essential for I² calculation.
- **T027a** (Forest Plot): Retained. Essential for visualization.
- **T000c-gen** (Bonferroni Mock Data): Retained. Essential for SC-004 verification.

**New Deliverables**:
- **T000-gen**: Added to generate initial mock data (N=5 for fallback), resolving the producer-consumer gap.
- **T000b-gen**: Added to generate mock data (N=15 for quantitative).
- **T000c-gen**: Added to generate mock data (N=15 with 5 tracts) for Bonferroni verification.
- **T000-verif**: Added to checksum and register generated data before use, resolving Data Hygiene concerns.
- **T015a**: Added to implement core narrative logic, distinct from summary generation.
- **T015b**: Added to implement the Narrative Synthesis Engine (pivot logic).
- **T015c**: Added to generate the final summary.
- **T027a/b/c**: Split T027 to ensure granular coverage of specific plot requirements.
- **T027d**: Renumbered regenerator with specific retry logic (DPI 100, compression 6) and readability check.
- **T027e**: Added to orchestrate the validation loop.
- **T002a/b, T006a/b**: Split coarse tasks for executability.
- **T006c**: Added to initialize default config.
- **T007c**: Updated with specific content to ensure determinism.
- **T031**: Updated to non-fatal (exit code 2) on failure to support T027e retry logic.
- **T042**: Moved to Phase 2 to resolve ordering violations.
- **T048**: Updated to specify mechanism for real data source injection.
- **T016**: Merged T016a/T016b to resolve gate logic ordering and removed visualization dependencies.
- **T009b**: Added to validate real data thresholds before T013.
- **T014b**: Added to count valid (r, n) pairs for specific pivot logic.
- **T038**: Added to validate Bonferroni correction against 5+ tracts.
- **T008c**: Added to count distinct tracts for Bonferroni logic.

**Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️**
- [ ] T010 [P] [US1] Unit test for extraction logic in `tests/unit/test_extraction.py` (verify r, n parsing). **Output**: Test logs and failure evidence. **Depends on: T013**.
- [ ] T011 [P] [US1] Unit test for meta-analysis calculation in `tests/unit/test_meta_analysis.py` (verify weighted mean within 0.001 tolerance). **Output**: Test logs and failure evidence. **Depends on: T014**.
- [ ] T012 [P] [US1] Unit test for narrative fallback trigger in `tests/unit/test_narrative.py` (verify N < 10 skips aggregation). **Output**: Test logs and failure evidence. **Depends on: T015b**.

**Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️**
- [ ] T019 [P] [US2] Unit test for I² calculation in `tests/unit/test_heterogeneity.py` (verify precision to **exactly two decimal places** as required by SC-002, e.g., 52.34)
- [ ] T020 [P] [US2] Unit test for Egger's regression in `tests/unit/test_bias.py` (verify p-value calculation and N < 10 skip logic; verify `egger_skipped_reason` output matches **exact string**: 'Skipped: Insufficient studies (N < 10) for Egger's regression')

**Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️**
- [ ] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_plots.py` (verify file existence, size < 5MB, peak memory < 6GB using tracemalloc, and correct axis labels).