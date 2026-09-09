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

- [X] T001 Create project structure: Create the following directory structure at `projects/PROJ-082-investigating-the-correlation-between-st/`: `code/`, `data/raw/`, `data/processed/`, `data/derived/`, `tests/unit/`, `tests/integration/`. **Output**: The directory structure.
- [X] T002 Create `requirements.txt` and `pyproject.toml`: Create `projects/PROJ-082-investigating-the-correlation-between-st/code/requirements.txt` with pinned versions for `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`. Create `projects/PROJ-082-investigating-the-correlation-between-st/code/pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. **Output**: `code/requirements.txt`, `code/pyproject.toml`. **Constraint**: Must specify `python>=3.11`.
- [X] T005 Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation). **Input**: Must depend on the existence of the directories created by T001. **Output**: `code/utils/checksum.py` with functions `calculate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)`. **Constraint**: Must raise an exception if the file does not exist. **CRITICAL**: This task MUST NOT update the state file. It only provides utility functions for checksum calculation. **Depends on**: T001.
- [X] T006 Create Config System: Create `code/config/config_schema.yaml`, `code/utils/config.py`, and `code/config/config.yaml`. **Output**: `code/config/config_schema.yaml`, `code/utils/config.py`, `code/config/config.yaml`. **Constraint**: Must explicitly set `seed: 42` for default mock, `seed: 43` for quantitative mock, and `seed: 44` for Bonferroni-specific mock. **Depends on**: T001.
- [X] T007 Define Schemas and Lexicon: Create `contracts/study_record.schema.yaml`, `contracts/meta_analysis_result.schema.yaml`, `code/config/generate_lexicon.py`,  `code/config/tract_lexicon.yaml`, and `data/config/narrative_methodology.yaml`. **Output**: Schema files, `code/config/tract_lexicon.yaml`, `data/config/narrative_methodology.yaml`. **Depends on**: T001, T006.
- [X] T007c-2 Generate Tract Lexicon: Run `code/config/generate_lexicon.py`. **Output**: `code/config/tract_lexicon.yaml`. **Depends on**: T007.
- [X] T007d Implement NLP Logic: Create `code/extraction/nlp_logic.py`. **Task**: Implement regex patterns to search for tract names (from the lexicon) in proximity (≤5 words) to directional verbs. Generate `nlp_logic.py`. **Constraint**: This logic MUST ONLY be applied to studies that lack both `r` and `n` values. **Output**: `code/extraction/nlp_logic.py` with function `extract_qualitative_desc(text, lexicon, scheme)`. **Depends on**: T007c-2.
- [X] T007e-integration Integrate Reference Validator: Integrate the Reference-Validator Agent into the NLP extraction process to verify citations found in extracted qualitative descriptors. **Output**: Modified `code/extraction/nlp_logic.py` with citation verification logic. **Depends on**: T007d.
- [X] T010 Generate Mock Data: Create `code/data/generate_mock_data.py` that generates `data/raw/mock_studies.csv` by default (N=15, 5+ tracts). Supports optional `--config` values `fallback`, `quant`, `bonferroni` for specific test scenarios. **Output**: `data/raw/mock_studies.csv`. **Depends on**: T001, T006, T007c-2.
- [X] T012b Handle N=0 Input: Create `code/data/ensure_input.py`. **Task**: Check if `data/raw/studies.csv` exists. If not, copy `data/raw/mock_studies.csv` to `data/raw/studies.csv`. **Constraint**: This task MUST NOT crash if the file is missing; it must create an empty CSV to allow the pipeline to proceed to T012a with N=0. **Output**: `code/data/ensure_input.py`. **Depends on**: T001.
- [X] T012a Implement Qualitative Extraction: Implement `code/analysis/extraction.py` to parse qualitative descriptors if no direct (r, n) pairs exist. **Input**: Requires T007d, T007e-integration. **Output**: `code/analysis/extraction.py`. **Depends on**: T007d, T007e-integration, T012b.
- [X] T013 Implement Parser and Converter: Create `code/extraction/parser.py`. **Task**: Parse CSV/JSON inputs for `r`, `n`, `tract` and merge with qualitative data from T012a. **CRITICAL**: Implement p-value to r-value conversion here (FR-001 Edge Cases) using standard formulas (e.g., Fisher's z) with explicit sign determination logic. **Constraint**: Must handle empty input files gracefully (produce empty output). **Output**: `code/extraction/parser.py`. **Depends on**: T012b, T012a, T007d.

## Phase 2: Core Analysis Logic (Gatekeeper & Models)

**Purpose**: Implement the statistical core and the pivot logic

- [X] T014a Implement Random-Effects Model: Create `code/analysis/meta_analysis.py`. **Task**: Run Random-Effects Model (DerSimonian-Laird) on `extracted_studies.csv`. **Output**: `data/derived/meta_results.json`. **Depends on**: T013.
- [X] T014b Implement Heterogeneity Assessment: Implement I² calculation and Egger's regression in `code/analysis/bias.py`. **Output**: `data/derived/heterogeneity_results.json` and `data/derived/egger_test.json`. **Depends on**: T013.
- [X] T014 Implement Meta-Analysis Model: Orchestrate T014a and T014b. **Output**: `data/derived/meta_results.json`. **Depends on**: T014a, T014b.
- [X] T015a Implement Narrative Synthesis Engine: Create `code/analysis/narrative_engine.py`. **Task**: Generate `data/derived/narrative_content.md`. **Output**: `code/analysis/narrative_engine.py`. **Depends on**: T013.
- [X] T057 Re-implement Quantitative Gatekeeper: Create `code/analysis/gatekeeper.py`. **Task**: Check `study_count.json`. If N < 10, set mode="narrative" and write `gate_result.json`. If N >= 10, set mode="quantitative". **Output**: `data/derived/gate_result.json`. **Depends on**: T013.
- [X] T015b Implement Narrative Summary: Create `code/analysis/narrative.py`. **Task**: Consume `narrative_content.md` and produce `data/derived/narrative_summary.md` with JSON metadata block. **Output**: `code/analysis/narrative.py`. **Depends on**: T015a, T057.
- [X] T015d Implement Narrative Pivot: Create `code/analysis/pivot_narrative.py`. **Task**: Orchestrates T015b based on `mode` flag from `gate_result.json`. **Output**: `code/analysis/pivot_narrative.py`. **Depends on**: T015b, T057.
- [X] T081 Implement Random-Effects Model Convergence Handler: Integrate fallback to Fixed-Effects model in `code/analysis/meta_analysis.py` if `statsmodels` fails to converge. **Output**: Updated `code/analysis/meta_analysis.py`. **Depends on**: T014a.

## Phase 3: Visualization, Reporting & Validation

**Purpose**: Generate outputs and validate them

- [X] T024 Implement Forest Plot: Create `code/visualization/plots_forest.py`. **Output**: `data/derived/forest_plot.png`. **Depends on**: T057, T014.
- [X] T025 Implement Funnel Plot: Create `code/visualization/plots_funnel.py`. **Output**: `data/derived/funnel_plot.png`. **Depends on**: T057, T017b.
- [X] T026 Implement Correlation Summary Plot: Create `code/visualization/plots_correlation.py`. **Output**: `data/derived/correlation_plot.png`. **Depends on**: T057, T014.
- [X] T017b Implement Heterogeneity Assessment: Run I² and Egger's test. **Output**: `data/derived/heterogeneity_results.json`. **Depends on**: T057, T014.
- [X] T018b Implement Visualization: Run `code/viz/plots.py`. **Output**: `data/derived/plots/*.png`. **Depends on**: T057, T024, T025, T026.
- [X] T021b Implement Bonferroni Calculation: Apply Bonferroni correction for multiple tract comparisons. **Output**: `data/derived/bonferroni_status.json`. **Depends on**: T057, T014.
- [X] T031 Validation Report Generation: Aggregate results from `size_validation.log` and produce `data/derived/validation_report.json`. **Output**: The script file `code/visualization/validator.py`. **Depends on**: T027b.
- [X] T027b Plot File‑Size Validator: Extend `code/utils/validator.py` with `validate_png_size`. **Output**: The script file `code/utils/validator.py`. **Depends on**: T024, T025, T026.
- [X] T027c Regenerator: Create `code/visualization/regenerator.py`. **Output**: The script file `code/visualization/regenerator.py`. **Depends on**: T027b, T031.
- [X] T027d Validation Report Check: Create `code/visualization/check_validation.py`. **Output**: The script file `code/visualization/check_validation.py`. **Depends on**: T027b, T027c, T031.
- [X] T032 Generate Paper Draft: Create `code/report/generate_paper.py`. **Output**: The script file `code/report/generate_paper.py`. **Depends on**: T014, T021b, T018b, T017b.
- [X] T042 Implement Memory-Safe Plot Module: Create `code/visualization/memory_safe_plots.py`. **Output**: The script file `code/visualization/memory_safe_plots.py`. **Depends on**: T002.
- [X] T043b Implement Low-Memory Plotting Fallback: Update `code/visualization/memory_safe_plots.py` to detect memory pressure. **Output**: Updated plot scripts. **Depends on**: T042.
- [X] T044b Implement Tract Independence Logic: Create `code/analysis/independence_checker.py`. **Output**: The script file `code/analysis/independence_checker.py`. **Depends on**: T013.
- [X] T049 Create End-to-End Integration Test: Create `tests/integration/test_full_pipeline.py`. **Output**: The test file `tests/integration/test_full_pipeline.py`. **Depends on**: T014, T021b, T032.
- [X] T050 Update Quickstart: Update `README.md` and `docs/paper_draft.md`. **Output**: Updated `README.md`, `docs/paper_draft.md`. **Depends on**: T049.
- [X] T051a Create Run-Book Entry Point: Create `code/data/generators.py`. **Output**: The script file `code/data/generators.py`. **Depends on**: T010.
- [X] T051b Update Quickstart: Update `docs/quickstart.md`. **Output**: The updated file `docs/quickstart.md`. **Depends on**: T051a.
- [X] T053 Implement Memory-Safe Plot Module: Create `code/visualization/memory_safe_plots.py`. **Output**: The script file `code/visualization/memory_safe_plots.py`. **Depends on**: T002.
- [X] T056 Implement Unified Data Loader: Create `code/data/loader.py`. **Output**: The script file `code/data/loader.py`. **Depends on**: T001, T006, T010.
- [X] T056a Enforce Mock Data: Add a task to explicitly set the `--use-mock` flag in the CI pipeline. **Output**: Modified CI configuration. **Depends on**: T056.
- [X] T059 Dataset Size Check: Create `code/data/check_dataset_size.py`. **Output**: The script file `code/data/check_dataset_size.py`. **Depends on**: T001, T056.
- [X] T060 Implement Data Source Validation: Create `code/data/validate_metadata.py`. **Output**: The script file `code/data/validate_metadata.py`. **Depends on**: T013.
- [X] T061 Implement Sensitivity Analysis: Create `code/analysis/sensitivity_analysis.py`. **Output**: The script file `code/analysis/sensitivity_analysis.py`. **Depends on**: T014.
- [X] T062 Implement Plot Accessibility Checks: Update `code/visualization/plots_forest.py`. **Output**: Updated plot scripts. **Depends on**: T024.
- [X] T063 Generate Systematic Review of Absence Report: Create `code/analysis/absence_report.py`. **Output**: The script file `code/analysis/absence_report.py`. **Depends on**: T015b.
- [X] T064 Implement Data Source Audit Trail: Create `code/data/audit_trail.py`. **Output**: The script file `code/data/audit_trail.py`. **Depends on**: T056, T070.
- [X] T065 Generate Data Source Report: Create `code/data/generate_source_report.py`. **Output**: The script file `code/data/generate_source_report.py`. **Depends on**: T076.
- [X] T066 Validate Mock Data Integrity: Create `tests/unit/test_mock_data_integrity.py`. **Output**: The test file `tests/unit/test_mock_data_integrity.py`. **Depends on**: T010.
- [X] T067 Validate Mock Data Tract Diversity: Create `tests/unit/test_tract_diversity.py`. **Output**: The test file `tests/unit/test_tract_diversity.py`. **Depends on**: T010.
- [X] T068 Update Documentation on Data Scarcity: Update `docs/paper_draft.md` and `README.md`. **Output**: Updated `docs/paper_draft.md`, `README.md`. **Depends on**: T063.
- [X] T069 Validate Narrative Synthesis Output: Create `tests/unit/test_narrative_output.py`. **Output**: The test file `tests/unit/test_narrative_output.py`. **Depends on**: T063.
- [X] T070 Implement Data Source Fallback Logic: Update `code/data/loader.py`. **Output**: Updated `code/data/loader.py`. **Depends on**: T056.
- [X] T071 Implement Explicit Pivot Logic: Update `code/analysis/gatekeeper.py`. **Output**: `code/analysis/gatekeeper.py`. **Depends on**: T057, T015b, T070.
- [X] T072 Generate Data Source Report: Create `code/data/generate_source_report.py`. **Output**: The script file `code/data/generate_source_report.py`. **Depends on**: T056, T032, T076.
- [X] T073 Generate Data Source Report: Create `code/data/generate_source_report.py`. **Output**: The script file `code/data/generate_source_report.py`. **Depends on**: T010, T007c-2.
- [X] T073b Implement Data Source Fallback Logic: Update `code/data/loader.py`. **Output**: Updated `code/data/loader.py`. **Depends on**: T010, T007c-2.
- [X] T074 Update Documentation: Update `docs/paper_draft.md` and `README.md`. **Output**: Updated `docs/paper_draft.md`, `README.md`. **Depends on**: T071, T072.
- [X] T075 Run Pivot Logic Test: Execute `pytest tests/unit/test_pivot_logic.py` with assertions for 'No Quantitative Evidence Found' header, missing forest plots, and correct JSON flags. **Output**: The test file `tests/unit/test_pivot_logic.py`. **Depends on**: T071, T017b, T021b, T049.
- [X] T076 Implement Data Hygiene Check: Create `code/data/validate_metadata.py`. **Output**: The script file `code/data/validate_metadata.py`. **Depends on**: T013.
- [X] T077 Implement Data Source Fallback Logic: Update `code/data/loader.py`. **Output**: Updated `code/data/loader.py`. **Depends on**: T010, T073.
- [X] T078 Implement Sensitivity Analysis: Create `code/analysis/sensitivity_analysis.py`. **Output**: The script file `code/analysis/sensitivity_analysis.py`. **Depends on**: T014.
- [X] T079 Implement Plot Export Formats: Update `code/visualization/plots_forest.py`. **Output**: Updated plot scripts. **Depends on**: T024.
- [X] T080 Implement P-Value Conversion Fallback: Integrated into T013.
- [X] T082 Implement Tract Lexicon Expansion: Update `code/config/generate_lexicon.py`. **Output**: Updated `code/config/generate_lexicon.py`. **Depends on**: T007c-2.
- [X] T083 Implement Bonferroni Correction for Dependent Tracts: Update `code/analysis/correction.py`. **Constraint**: Must strictly implement Bonferroni as per FR-005. **Output**: Updated `code/analysis/correction.py`. **Depends on**: T021b, T044b.
- [X] T084 Implement Plot Accessibility Checks: Update `code/visualization/plots_forest.py`. **Output**: Updated plot scripts. **Depends on**: T024, T025, T026.
- [X] T085 Implement Study Metadata Validation: Create `code/data/validate_metadata.py`. **Output**: The script file `code/data/validate_metadata.py`. **Depends on**: T013.
- [X] T086 Implement Heterogeneity Source Analysis: Create `code/analysis/heterogeneity_sources.py`. **Output**: The script file `code/analysis/heterogeneity_sources.py`. **Depends on**: T018b.
- [X] T087 Implement Report Generation Fallback: Update `code/report/generate_paper.py`. **Output**: Updated `code/report/generate_paper.py`. **Depends on**: T032.
- [X] T088 Implement Data Source Audit Trail: Create `code/data/audit_trail.py`. **Output**: The script file `code/data/audit_trail.py`. **Depends on**: T056, T070.
- [X] T089 Implement Data Source Report: Create `code/data/generate_source_report.py`. **Output**: The script file `code/data/generate_source_report.py`. **Depends on**: T056, T032, T076.
- [X] T090 Implement Mock Data Integrity: Create `tests/unit/test_mock_data_integrity.py`. **Output**: The test file `tests/unit/test_mock_data_integrity.py`. **Depends on**: T010.
- [X] T091 Implement Mock Data Tract Diversity: Create `tests/unit/test_tract_diversity.py`. **Output**: The test file `tests/unit/test_tract_diversity.py`. **Depends on**: T010.
- [X] T092 Update Documentation on Data Scarcity: Update `docs/paper_draft.md` and `README.md`. **Output**: Updated `docs/paper_draft.md`, `README.md`. **Depends on**: T063.
- [X] T093 Validate Narrative Synthesis Output: Create `tests/unit/test_narrative_output.py`. **Output**: The test file `tests/unit/test_narrative_output.py`. **Depends on**: T063.
- [X] T094 Implement Data Source Fallback Logic: Update `code/data/loader.py`. **Output**: Updated `code/data/loader.py`. **Depends on**: T056.
- [X] T095 Implement Sensitivity Analysis: Create `code/analysis/sensitivity_analysis.py`. **Output**: The script file `code/analysis/sensitivity_analysis.py`. **Depends on**: T014.
- [X] T096 Implement Plot Export Formats: Update `code/visualization/plots_forest.py`. **Output**: Updated plot scripts. **Depends on**: T024.
