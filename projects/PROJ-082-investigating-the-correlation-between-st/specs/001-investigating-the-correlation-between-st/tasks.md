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

- [ ] T001 [P] Initialize project directory structure: Create `code/`, `tests/`, `data/`, and `docs/` directories in a single step.
- [ ] T002 [P] Initialize a Python 3.x project with `requirements.txt` dependencies (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation)
- [ ] T006 [P] Setup configuration management: `code/utils/config.py` (seed pinning, path loading)
- [ ] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata, tract, r, n, and qualitative descriptors.
- [ ] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics.
- [ ] T007c [P] Generate `data/config/tract_lexicon.yaml`: Create a configuration file containing the specific list of tract names (e.g., "arcuate", "cingulum", "uncinate") and directional verbs (e.g., "increased", "decreased", "correlated") required for T007d-2 extraction logic. **Output**: `data/config/tract_lexicon.yaml`.
- [ ] T007d-1 [S] [US1] Define the thematic coding scheme in `data/config/narrative_methodology.yaml`. **Task**: Define the coding rules (e.g., keyword frequency, sentiment analysis) to be used by T015. **Output**: `data/config/narrative_methodology.yaml`. **Depends on: T007a, T007b, T007c**.
- [ ] T007d-2 [S] [US1] Implement `code/extraction/nlp_logic.py` using the scheme from T007d-1. **Task**: Implement regex patterns to search for tract names (from T007c) in proximity to directional verbs. **Output**: `code/extraction/nlp_logic.py` (functions). **Depends on: T007d-1**.
- [ ] T008 [P] Implement tract harmonization logic: `code/analysis/tract_mapping.py` (JHU Atlas mapping, string normalization). **Constraint**: This task MUST NOT implement any prioritization or filtering logic. It must only standardize tract names. **Depends on: T007a, T007b**.
- [ ] T009 [P] Setup logging infrastructure: `code/utils/logger.py` (structured logging for convergence warnings, fallbacks)
- [ ] T042 [P] [US3] Implement `code/visualization/memory_monitor.py` to wrap plot generation with `tracemalloc` and abort if peak memory exceeds a predefined safe threshold, logging the specific plot causing the overflow. **Output**: Reusable module for T027. **Moved to Phase 2 to ensure library availability.**
- [ ] T040 [P] [US1] Implement `code/extraction/p_value_converter.py` to handle studies reporting only p-values: implement Fisher's z conversion logic and strict exclusion logging if conversion is ambiguous. **Artifact**: Log conversion results to `data/logs/conversion_log.csv`. **Constraint**: This is a utility module used by T013, not a data producer. **Depends on: T007a**.
- [ ] T047 [P] [US1] Implement `code/extraction/fetch_failure_handler.py` to strictly fail loudly (raise exception) if **real data fetch fails** (e.g., network error, 404, unreachable URL) before extraction begins. **Constraint**: Ensure no `try/except` block falls back to `generate_synthetic_*()` or mock data for network failures. **Note**: This task handles "Fetch Failure" (technical crash). **Depends on: T006**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1) 🎯 MVP

**Goal**: Extract effect sizes from CSV, handle missing data, perform random-effects meta-analysis, and trigger narrative fallback if N < 10.

**Independent Test**: Run extraction script on a small, synthetic CSV of mock studies with known effect sizes and verify the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for extraction logic in `tests/unit/test_extraction.py` (verify r, n parsing). **Output**: Test logs and failure evidence.
- [ ] T011 [P] [US1] Unit test for meta-analysis calculation in `tests/unit/test_meta_analysis.py` (verify weighted mean within 0.001 tolerance). **Output**: Test logs and failure evidence.
- [ ] T012 [P] [US1] Unit test for narrative fallback trigger in `tests/unit/test_narrative.py` (verify N < 10 skips aggregation). **Output**: Test logs and failure evidence.

### Implementation for User Story 1

- [ ] T013 [S] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for r, n, tract AND qualitative descriptors. **Extraction Logic**: When direct (r, n) pairs are unavailable, use `code/extraction/nlp_logic.py` (T007d-2) and `data/config/tract_lexicon.yaml` (T007c) to search for tract names and directional verbs. Use `code/extraction/p_value_converter.py` (T040) to convert p-values if needed. **Narrative Pool**: If no specific descriptors are found, **EXCLUDE** the study from the `narrative_pool` and log the exclusion reason to `data/logs/exclusion_log.csv`. **Output**: Produce an intermediate CSV `data/processed/extracted_studies.csv` containing all studies with a `narrative_pool` boolean column and `qualitative_desc` field. **Depends on: T007a, T007b, T007c, T007d-2, T040**.
- [ ] T008c [S] [US1] Implement `code/analysis/tract_counting.py`. **Task**: Read `data/processed/extracted_studies.csv` (output of T013), apply harmonization (T008), and count unique tract names. **Output**: Write `data/processed/tract_count.json` containing `{"k": <count>}`. **Constraint**: This task MUST run AFTER T013. **Depends on: T008, T013**.
- [ ] T014a [S] [US1] Implement `code/analysis/study_counter.py`. **Task**: Read `data/processed/extracted_studies.csv` and count unique (Author, Year) pairs. **Output**: Write `data/processed/study_count.json` containing `{"N": <count>}`. **Constraint**: This task MUST run regardless of N value. **Depends on: T013**.
- [ ] T014 [S] [US1] Implement `code/analysis/meta_analysis.py` Random-Effects model using `statsmodels` (handle convergence failure by falling back to Fixed-Effects with warning). **Gate Logic**: If `N` (from T014a) < 10, skip the model and output `data/processed/meta_status.json` with `status: "skipped"`. If N >= 10, run the model and output `data/derived/results_quant.json`. **Depends on: T013, T014a**.
- [ ] T015 [S] [US1] Implement `code/analysis/narrative.py` to generate structured text summary if eligible study count < 10. **Input**: Consume `data/processed/study_count.json` (from T014a) for `study_count`, `data/processed/extracted_studies.csv` (specifically `qualitative_desc` and `narrative_pool` columns) from T013, and `data/config/narrative_methodology.yaml` from T007d-1. **Output Artifact**: Generate `data/derived/narrative_summary.md`. **Structure Requirements**:
 - JSON Metadata Block at the top with keys: `study_count`, `synthesis_mode`, `timestamp`.
 - Section 1: `## Study Overview` (Methodology, References).
 - Section 2: `## Qualitative Themes` (Categorizing recurring themes regarding specific tracts based on `qualitative_desc` and the coding scheme from T007d-1).
 - Section 3: `## Limitations` (Explicitly stating N < 10 constraint).
 - **Zero-Studies Handling**: If input CSV is empty (N=0), output a specific header `# No studies found` and an empty JSON metadata block.
 - **Depends on: T013, T014a, T007d-1**.
- [ ] T016a [S] [US1] Implement `code/main.py` Gate Logic. **Task**: Load `data/processed/study_count.json` (T014a). **Gate Logic**: If N < 10, **invoke T015** immediately to generate `data/derived/narrative_summary.md` and set `synthesis_mode` to "narrative" in the final output `data/derived/results.json`. If N >= 10, **invoke T016b**. **Output Artifact**: `data/derived/results.json` with `synthesis_mode` field set to "narrative" or "quantitative". **Depends on: T013, T014a, T015**. (Note: T016a *calls* T015 or T016b at runtime; T015 and T016b are implemented independently).
- [ ] T016b [S] [US1] Implement `code/main.py` Quantitative Orchestrator. **Task**: If N >= 10, run T014 (if not already run), then invoke T027 (Visualization) and T031 (Validation). **Output**: Final `data/derived/results.json` with quantitative metrics. **Depends on: T014, T027, T031**.
- [ ] T017 [P] [US1] Implement validation and error handling for missing effect sizes in `code/extraction/parser.py`. **Artifact**: Log exclusion reasons to `data/logs/exclusion_log.csv` with columns `study_id`, `reason`, `original_value`. **Constraint**: If Fisher's z conversion is ambiguous, exclude the study and log the reason; do not silently drop data. **Depends on: T013**.
- [ ] T018 [P] [US1] Handle zero-studies edge case: **Merged into T015**. T015 now explicitly handles the empty input case.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneity and Bias Assessment (Priority: P2)

**Goal**: Calculate I² statistics and perform Egger's regression test (only if N ≥ 10).

**Independent Test**: Provide a synthetic dataset with high variance and verify I² > 50%; provide skewed data to verify Egger's test p-value < 0.05; verify skip logic for N < 10.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for I² calculation in `tests/unit/test_heterogeneity.py` (verify precision to **exactly two decimal places** as required by SC-002, e.g., 52.34)
- [ ] T020 [P] [US2] Unit test for Egger's regression in `tests/unit/test_bias.py` (verify p-value calculation and N < 10 skip logic; verify `egger_skipped_reason` output matches **exact string**: 'Skipped: Insufficient studies (N < 10) for Egger's regression')

### Implementation for User Story 2

- [ ] T021 [S] [US2] Implement `code/analysis/bias.py` Egger's linear regression test. **Skip Logic**: Explicitly SKIP if `study_count` (from T014a) < 10. **Input Verification**: Read `study_count` from `data/processed/study_count.json` (T014a) to determine skip condition. **Output Requirement**: If N >= 10, report the intercept and p-value. If N < 10, output the exact string `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"` as a runtime value in the result JSON. **Depends on: T014a, T014**.
- [ ] T021b [S] [US2] Implement `code/analysis/heterogeneity.py` I² calculation. **Precision Requirement**: The output MUST report the I² statistic with **exactly two decimal places** (e.g., 52.34) as mandated by **SC-002** and **FR-002**. **Artifact**: Append `i_squared` field to the `MetaAnalysisResult` JSON at `data/derived/results.json`. **Note**: This task is independent of T021 and does not require its results. **Depends on: T014a, T014**.
- [ ] T022 [S] [US2] Implement `code/analysis/correction.py` for multiple comparison correction. **Decision Logic**:
 1. Apply **Bonferroni correction** ONLY if N ≥ 10 AND k ≥ 2 tracts.
 2. **Strict Requirement**: Read `k` (distinct tract count) from `data/processed/tract_count.json` (output of T008c) and `N` from `data/processed/study_count.json` (output of T014a). **Do NOT** re-count tracts internally.
 3. **Constraint**: Do NOT implement Robust Variance Estimation (RVE). The spec mandates Bonferroni correction only.
 4. Include a mandatory "Limitations" note in the output report acknowledging that Bonferroni is conservative due to tract non-independence.
 5. **Output Requirement**: **Generate and inject** a mandatory "Limitations" note into the final `data/derived/results.json` acknowledging Bonferroni conservatism. Report the **adjusted significance threshold** value in the output report. **Depends on: T008c, T014a, T014**.
- [ ] T023 [P] [US2] Integrate bias assessment into `code/main.py` (run after meta-analysis, update `MetaAnalysisResult` JSON).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate forest plots, funnel plots, and summary correlation plots using `matplotlib` and `seaborn`.

**Independent Test**: Run plotting module on a static dataset and verify PNG files exist, are under a reasonable file size limit, and contain correct axis labels/data points.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_plots.py` (verify file existence, size < 5MB, peak memory < 6GB using tracemalloc, and correct axis labels).

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/visualization/plots.py` to generate all required plots: Forest plot (summary diamond aligns with `weighted_mean_r`), Funnel plot (standard error vs effect size, symmetry line at pooled effect), and Correlation summary plot. **Optimization**: Implement PNG compression settings (optimize=True, dpi=150) to ensure file size < 5MB. **Memory Safety**: Integrate T042 (Memory Monitor) by importing and wrapping generation with `tracemalloc` to abort if peak memory exceeds a predefined threshold. **Artifact**: Save PNGs to `data/derived/`. **Depends on: T042**.
- [ ] T027b [P] [US3] Implement `code/visualization/regenerator.py` to handle plot retry logic. **Task**: If T031 validation fails, regenerate plots with lower DPI (e.g., reduced resolution) and higher compression. **Constraint**: **Max retries = 2**. If validation still fails after 2 retries, **raise an exception** and log to `data/logs/regeneration_failure.log`. **Depends on: T027**.
- [ ] T028 [P] [US3] Integrate visualization into `code/main.py` (save PNGs to `data/derived/` after analysis).
- [ ] T031 [P] [US3] Implement file size validation logic in `code/utils/validator.py`: Add a function to verify generated PNGs are < 5MB. **Execution**: This task runs **after** T027 generates the plots. It validates the output and generates a validation report. If validation fails, it returns a failure status to `main.py` (T016b) to trigger T027b. **Artifact**: `data/derived/validation_report.json`. **Depends on: T027**.
- [ ] T052 [P] [US3] Generate `data/derived/validation_report.md` from `data/derived/validation_report.json` (T031) to explicitly document file sizes and build status. **Output**: Fails the build if any file > 5MB. **Depends on: T031**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Generate `docs/paper_draft.md` from `MetaAnalysisResult` JSON using Jinja2 template (automated report generation).
- [ ] T033a [P] Run linting (ruff) and fix any violations; save log to `data/logs/lint_report.md`. **Replaces rejected T033**.
- [ ] T034a [P] Profile total runtime and ensure < 15 mins on CI; optimize bottlenecks if exceeded; save report to `data/logs/profile_report.md`. **Replaces rejected T034**.
- [ ] T035 [P] Additional unit tests in `tests/unit/` (coverage for p-value conversion edge cases).
- [ ] T036a [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution; save log to `data/logs/quickstart_report.md`. **Replaces rejected T036**.
- [ ] T037 [P] Verify `tasks.md` execution order matches data flow (extraction -> analysis -> visualization).
- [ ] T039 [P] Implement `tests/integration/test_real_data_flow.py` to verify the pipeline processes real dataset downloads without memory overflow.
- [ ] T041 [P] [US1] Implement `code/analysis/convergence_handler.py` to detect `statsmodels` non-convergence warnings and automatically trigger the Fixed-Effects fallback with a specific log entry. **Dependency**: Must be called within T014.
- [ ] T043 [P] [US1] Create `data/mock_synthetic_data.csv` with a representative set of studies containing known `r`, `n`, and `tract` values for unit test T011, ensuring the `weighted_mean_r` can be manually verified.
- [ ] T044 [P] [US2] Create `data/mock_bias_data.csv` with a body of studies engineered to produce I² > 50% and Egger's p < 0.05 for unit test T020.
- [ ] T045 [P] [US2] Create `data/mock_small_data.csv` with Several studies to verify the exact skip string in T020 and T021.
- [ ] T048 [P] [US1] Implement `code/main.py` logic to adopt any "VERIFIED REAL DATA SOURCE" injected by the execution stage, replacing any hand-rolled `load_dataset` or guessed URLs with the provided package/recipe. **Constraint**: Ensure the single source of truth for data is the verified source. **Note**: Data ingestion is handled via external scripts or manual CSV preparation, not the core pipeline.
- [ ] T049 [P] [US1] Implement `code/utils/data_source_registry.py` to maintain a dynamic list of verified real data sources (packages, URLs, access recipes) and enforce their usage in `data/fetcher.py` (T038 - **Removed**) and `streaming_processor.py` (T046 - **Removed**), preventing the use of unverified or guessed sources. **Depends on: T048**.
- [ ] T050 [P] [US2] Add explicit validation in `code/analysis/bias.py` (T021) to ensure Egger's test is skipped with the exact error string if `study_count` < 10, and log a warning if the test is attempted with insufficient data. **Depends on: T021**.
- [ ] T051 [P] [US3] Implement a unit test in `tests/unit/test_plot_sizes.py` to verify that the PNG compression logic in T027 reliably keeps file sizes under 5MB for standard datasets, and triggers the regeneration logic in T027b if the threshold is exceeded. **Depends on: T027, T031**.

## Re-plan Section

**Rejected Tasks**: The following tasks were previously marked as "Repeatedly-unverifiable" or "Rejected" and have been replaced:
- **T033** (Linting): Replaced by **T033a** (Run linting and save log).
- **T034** (Profiling): Replaced by **T034a** (Profile and save report).
- **T036** (Quickstart): Replaced by **T036a** (Run quickstart validation and save log).
- **T035, T037**: Retained but verified for executability.
- **T038** (Data Fetcher): **Removed** (Scope Creep). The project assumes input CSVs are provided.
- **T046** (Streaming Processor): **Removed** (Scope Creep).
- **T047** (Fetch Failure Handler): **Removed** as T038/T046 were removed.
- **T007d** (Coarse Task): **Split** into T007d-1 (Config) and T007d-2 (Code).
- **T016** (Main Entry): **Split** into T016a (Gate) and T016b (Quant) to resolve circular dependencies.

**New Deliverables**:
- **T007d-1, T007d-2**: Split to define narrative methodology (addressing FR-001).
- **T008c**: Moved to Phase 3 to resolve dependency on T013.
- **T014a**: Added to provide a deterministic `study_count` artifact for all downstream tasks.
- **T016a, T016b**: Split to enforce the fallback protocol and remove circular dependencies.
- **T022**: Updated to explicitly generate the "Limitations" note.
- **T027b**: Updated to include `max_retries` and `fail_build` logic.
- **T052**: Added to generate validation report and fail build (addressing SC-003).
- **T031**: Repositioned as post-processing step to break circular dependency with T027.