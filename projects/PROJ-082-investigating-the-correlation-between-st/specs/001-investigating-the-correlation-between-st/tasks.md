# Tasks: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` dependencies (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation)
- [X] T006 [P] Setup configuration management: `code/utils/config.py` (seed pinning, path loading)
- [X] T007a [P] Create `contracts/study_record.schema.yaml`: Define schema for study metadata, tract, r, n, and qualitative descriptors.
- [X] T007b [P] Create `contracts/meta_analysis_result.schema.yaml`: Define schema for pooled effect, CI, heterogeneity, and bias metrics.
- [X] T007c [P] Generate `data/config/tract_lexicon.yaml`: Create a configuration file containing the specific list of tract names (e.g., "arcuate", "cingulum", "uncinate") and directional verbs (e.g., "increased", "decreased", "correlated") required for T013 extraction logic. **Output**: `data/config/tract_lexicon.yaml`.
- [X] T008 [P] Implement tract harmonization logic: `code/analysis/tract_mapping.py` (JHU Atlas mapping, string normalization). **Constraint**: This task MUST NOT implement any prioritization or filtering logic. It must only standardize tract names. **Depends on: T007a, T007b**.
- [X] T008c [P] Implement tract counting logic: `code/analysis/tract_counting.py`. **Task**: Read `data/processed/extracted_studies.csv` (output of T013), apply harmonization (T008), and count unique tract names. **Output**: Write `data/processed/tract_count.json` containing `{"k": <count>}`. **Depends on: T008, T013**.
- [X] T009 Setup logging infrastructure: `code/utils/logger.py` (structured logging for convergence warnings, fallbacks)
- [X] T042 [P] [US3] Implement `code/visualization/memory_monitor.py` to wrap plot generation with `tracemalloc` and abort if peak memory exceeds a predefined safe threshold, logging the specific plot causing the overflow. **Output**: Reusable module for T027. **Moved to Phase 2 to ensure library availability.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1) 🎯 MVP

**Goal**: Extract effect sizes from CSV, handle missing data, perform random-effects meta-analysis, and trigger narrative fallback if N < 10.

**Independent Test**: Run extraction script on a small, synthetic CSV of mock studies with known effect sizes and verify the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for extraction logic in `tests/unit/test_extraction.py` (verify r, n parsing)
- [X] T011 [P] [US1] Unit test for meta-analysis calculation in `tests/unit/test_meta_analysis.py` (verify weighted mean within 0.001 tolerance)
- [X] T012 [P] [US1] Unit test for narrative fallback trigger in `tests/unit/test_narrative.py` (verify N < 10 skips aggregation)

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for r, n, tract AND qualitative descriptors. **Extraction Logic**: When direct (r, n) pairs are unavailable, implement specific logic to search for tract names and directional verbs defined in `data/config/tract_lexicon.yaml` (output of T007c) in proximity to extract "neural circuitry" and "preference" descriptors. **Narrative Pool**: If no specific descriptors are found, include the study in the `narrative_pool` list with a `no_qualitative_data` flag set to true. **Output**: Produce an intermediate CSV `data/processed/extracted_studies.csv` containing all studies with a `narrative_pool` boolean column and `qualitative_desc` field. **Depends on: T007a, T007b, T007c**.
- [X] T014 [US1] Implement `code/analysis/meta_analysis.py` Random-Effects model using `statsmodels` (handle convergence failure by falling back to Fixed-Effects with warning); output `study_count` artifact. **Depends on: T013**.
- [X] T015 [US1] Implement `code/analysis/narrative.py` to generate structured text summary if eligible study count < 10. **Input**: Consume `data/processed/extracted_studies.csv` (specifically `qualitative_desc` and `narrative_pool` columns) from T013. **Output Artifact**: Generate `data/derived/narrative_summary.md`. **Structure Requirements**:
  - JSON Metadata Block at the top with keys: `study_count`, `synthesis_mode`, `timestamp`.
  - Section 1: `## Study Overview` (Methodology, References).
  - Section 2: `## Qualitative Themes` (Categorizing recurring themes regarding specific tracts based on `qualitative_desc`).
  - Section 3: `## Limitations` (Explicitly stating N < 10 constraint).
  - **Zero-Studies Handling**: If input CSV is empty, output a specific header `# No studies found` and an empty JSON metadata block.
  - **Depends on: T013**.
- [X] T016 [US1] Implement `code/main.py` entry point logic: load raw CSV, run extraction, check N count. **Gate Logic**: If N < 10, **invoke T015** immediately to generate `data/derived/narrative_summary.md` and set `synthesis_mode` to "narrative" in the final output `data/derived/results.json`. If N >= 10, proceed to quantitative analysis. **Output Artifact**: `data/derived/results.json` with `synthesis_mode` field set to "narrative" or "quantitative". **Depends on: T013, T014**. (Note: T016 *calls* T015 at runtime; T015 is implemented independently).
- [X] T017 [US1] Implement validation and error handling for missing effect sizes in `code/extraction/parser.py`. **Artifact**: Log exclusion reasons to `data/logs/exclusion_log.csv` with columns `study_id`, `reason`, `original_value`. **Constraint**: If Fisher's z conversion is ambiguous, exclude the study and log the reason; do not silently drop data. **Depends on: T013**.
- [X] T018 [US1] Handle zero-studies edge case: **Merged into T015**. T015 now explicitly handles the empty input case.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneity and Bias Assessment (Priority: P2)

**Goal**: Calculate I² statistics and perform Egger's regression test (only if N ≥ 10).

**Independent Test**: Provide a synthetic dataset with high variance and verify I² > 50%; provide skewed data to verify Egger's test p-value < 0.05; verify skip logic for N < 10.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for I² calculation in `tests/unit/test_heterogeneity.py` (verify precision to **exactly two decimal places** as required by SC-002, e.g., 52.34)
- [X] T020 [P] [US2] Unit test for Egger's regression in `tests/unit/test_bias.py` (verify p-value calculation and N < 10 skip logic; verify `egger_skipped_reason` output matches **exact string**: 'Skipped: Insufficient studies (N < 10) for Egger's regression')

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/analysis/bias.py` Egger's linear regression test. **Skip Logic**: Explicitly SKIP if `study_count` (from T014) < 10. **Input Verification**: Read `study_count` from T014 output JSON to determine skip condition. **Output Requirement**: If N >= 10, report the intercept and p-value. If N < 10, output the exact string `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"` as a runtime value in the result JSON. **Depends on: T014**.
- [X] T021b [US2] Implement `code/analysis/heterogeneity.py` I² calculation. **Precision Requirement**: The output MUST report the I² statistic with **exactly two decimal places** (e.g., 52.34) as mandated by **SC-002** and **FR-002**. **Artifact**: Append `i_squared` field to the `MetaAnalysisResult` JSON at `data/derived/results.json`. **Note**: This task is independent of T021 and does not require its results. **Depends on: T014**.
- [X] T022 [US2] Implement `code/analysis/correction.py` for multiple comparison correction. **Decision Logic**:
 1. Apply **Bonferroni correction** ONLY if N ≥ 10 AND k ≥ 2 tracts.
 2. **Strict Requirement**: Read `k` (distinct tract count) from `data/processed/tract_count.json` (output of T008c). **Do NOT** re-count tracts internally.
 3. **Constraint**: Do NOT implement Robust Variance Estimation (RVE). The spec mandates Bonferroni correction only.
 4. Include a mandatory "Limitations" note in the output report acknowledging that Bonferroni is conservative due to tract non-independence.
 5. **Output Requirement**: Report the **adjusted significance threshold** value in the output report. **Depends on: T008c, T014**.
- [X] T023 [US2] Integrate bias assessment into `code/main.py` (run after meta-analysis, update `MetaAnalysisResult` JSON).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate forest plots, funnel plots, and summary correlation plots using `matplotlib` and `seaborn`.

**Independent Test**: Run plotting module on a static dataset and verify PNG files exist, are under a reasonable file size limit, and contain correct axis labels/data points.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_plots.py` (verify file existence, size < 5MB, peak memory < 6GB using tracemalloc, and correct axis labels).

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/visualization/plots.py` to generate all required plots: Forest plot (summary diamond aligns with `weighted_mean_r`), Funnel plot (standard error vs effect size, symmetry line at pooled effect), and Correlation summary plot. **Optimization**: Implement PNG compression settings (optimize=True, dpi=150) to ensure file size < 5MB. **Memory Safety**: Integrate T042 (Memory Monitor) by importing and wrapping generation with `tracemalloc` to abort if peak memory exceeds a predefined threshold. **Retry Logic**: If T031 validation fails, invoke T027b to regenerate with lower resolution. **Artifact**: Save PNGs to `data/derived/`. **Depends on: T042, T027b, T031**.
- [X] T027b [P] [US3] Implement `code/visualization/regenerator.py` to handle plot retry logic. **Task**: If T031 validation fails, regenerate plots with lower DPI (e.g., reduced resolution) and higher compression. **Depends on: T027**.
- [X] T028 [US3] Integrate visualization into `code/main.py` (save PNGs to `data/derived/` after analysis).
- [X] T031 [US3] Implement file size validation logic in `code/utils/validator.py`: Add a function to verify generated PNGs are < 5MB. Integrate this check into the `main.py` pipeline post-generation. **Depends on: T027**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Generate `docs/paper_draft.md` from `MetaAnalysisResult` JSON using Jinja2 template (automated report generation).
- [ ] T033 [P] Run linting (ruff) and fix any violations; refactoring triggered by test failures.
- [ ] T034 [P] Profile total runtime and ensure < 15 mins on CI; optimize bottlenecks if exceeded.
- [ ] T035 [P] Additional unit tests in `tests/unit/` (coverage for p-value conversion edge cases).
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end pipeline execution.
- [ ] T037 Verify `tasks.md` execution order matches data flow (extraction -> analysis -> visualization).
- [X] T038 [P] Create `data/fetcher.py` to retrieve real, public datasets from **PubMed** and **Web of Science** (primary) and **OpenNeuro** (fallback) for dMRI and music preference data. **Constraint**: This task handles "Data Scarcity" (logical pivot). If the extraction phase (T013) yields **zero eligible studies** (N=0) after attempting to fetch, generate `data/raw/narrative_citation_list.json` with links to qualitative review papers to support the narrative synthesis. **Do NOT** use NAB or UCI datasets for this specific data strategy. **Note**: This task does NOT handle network errors; it handles the logical outcome of "no data found".
- [X] T039 [P] Implement `tests/integration/test_real_data_flow.py` to verify the pipeline processes real dataset downloads without memory overflow.
- [X] T040 [P] [US1] Implement `code/extraction/p_value_converter.py` to handle studies reporting only p-values: implement Fisher's z conversion logic and strict exclusion logging if conversion is ambiguous. **Artifact**: Log conversion results to `data/logs/conversion_log.csv`. **Dependency**: Must be integrated into T013 logic before quantitative aggregation.
- [X] T041 [P] [US1] Implement `code/analysis/convergence_handler.py` to detect `statsmodels` non-convergence warnings and automatically trigger the Fixed-Effects fallback with a specific log entry. **Dependency**: Must be called within T014.
- [X] T043 [P] [US1] Create `data/mock_synthetic_data.csv` with a representative set of studies containing known `r`, `n`, and `tract` values for unit test T011, ensuring the `weighted_mean_r` can be manually verified.
- [X] T044 [P] [US2] Create `data/mock_bias_data.csv` with 15 studies engineered to produce I² > 50% and Egger's p < 0.05 for unit test T020.
- [X] T045 [P] [US2] Create `data/mock_small_data.csv` with Several studies to verify the exact skip string in T020 and T021.
- [ ] T046 [P] [US1] Implement `data/streaming_processor.py` to handle large real datasets via `datasets.load_dataset(..., streaming=True)` for online statistics accumulation, ensuring the full dataset contributes to results without exceeding RAM limits. **Constraint**: If streaming is not feasible, task a well-defined real sample (e.g., first N rows) with explicit documentation of the sample size and representativeness limitations. **Depends on: T038**.
- [X] T047 [P] [US1] Implement `code/extraction/parser.py` to strictly fail loudly (raise exception) if **real data fetch fails** (e.g., network error, 404, unreachable URL) before extraction begins. **Constraint**: Ensure no `try/except` block falls back to `generate_synthetic_*()` or mock data for network failures. **Note**: This task handles "Fetch Failure" (technical crash), distinct from T038's "Data Scarcity" (logical pivot). If the network is down, the pipeline crashes. If the network is up but yields no studies, T038 handles the pivot. **Depends on: T013**.
- [X] T048 [P] [US1] Implement `code/main.py` logic to adopt any "VERIFIED REAL DATA SOURCE" injected by the execution stage, replacing any hand-rolled `load_dataset` or guessed URLs with the provided package/recipe. **Constraint**: Ensure the single source of truth for data is the verified source. **Depends on: T038, T046**.