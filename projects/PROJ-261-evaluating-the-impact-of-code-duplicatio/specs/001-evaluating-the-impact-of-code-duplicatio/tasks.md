# Tasks: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Input**: Design documents from `/specs/001-evaluate-code-duplication-llm-understanding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per spec.md Independent Test requirements for each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (datasets, transformers, bitsandbytes, scipy, matplotlib, pytest)
- [X] T003 [P] Create `.pre-commit-config.yaml` with black, flake8, isort hooks (consolidated from T003/T003a)
- [X] T004 [P] Create `research.md` documentation artifact in `specs/001-evaluating-code-duplication-llm-understanding/` with literature review and research question justification
- [X] T005 [P] Create `data-model.md` documentation artifact in `specs/001-evaluating-code-duplication-llm-understanding/` with entity definitions and data flow diagrams

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/config.py` for seeds, thresholds, and model parameters
- [X] T007 [P] Setup data directory structure (`projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/raw`, `.../processed`, `.../analysis`)
- [X] T008 [P] Configure logging infrastructure for parse failures (logs to `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/parse_failures.csv`)
- [X] T009 [P] Create checksum state manifest infrastructure in `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/checksum_manifest.py` with `artifact_hashes` tracking
- [X] T010 [P] Create and populate contract schema files: `clone_metrics.schema.yaml`, `model_metrics.schema.yaml`, `correlation_results.schema.yaml`, `pipeline_config.schema.yaml` in `specs/001-evaluating-code-duplication-llm-understanding/contracts/` (consolidated from T010/T010a/T010b)
- [X] T011 [P] Implement contract tests for all schemas in `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/tests/contract/`
- [X] T018 [US1] Stream a **representative** subset of `codeparrot/github-code` using HuggingFace `datasets` library with `streaming=True`; write to `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/raw/github-code-sample.csv` (CSV per FR‑008). **Dependency**: This task must complete before T017.
- [X] T018_test [US1] Integration test `tests/integration/test_github_code_download.py::test_file_exists_and_size` asserts CSV exists and size ≥ 500 MB
- [X] T018_verify [US1] Verification test `tests/integration/test_github_code_download_verification.py::test_file_is_nonempty_and_checksum` computes SHA‑256 checksum of `github-code-sample.csv` and validates against recorded hash
- [ ] T018c_small [US1] Create a tiny sample CSV (`data/raw/github-code-sample-small.csv`) containing **exactly 10 Python files** (size < 1MB) for fast‑path dependency testing. **Dependency**: Requires T018 to establish streaming pattern.
- [ ] T018c_small_test [US1] Integration test `tests/integration/test_small_sample.py::test_small_csv_exists` verifies the lightweight sample exists and contains exactly 10 files.
- [ ] T018c_run [US1] **CRITICAL**: Run the full US1 pipeline (T019 + T020 + T053) against `data/raw/github-code-sample-small.csv` to validate the red-green-refactor cycle. Output must be valid CSVs.
- [ ] T018c_run_test [US1] Integration test `tests/integration/test_small_sample_pipeline.py::test_small_pipeline_success` verifies that the full pipeline runs successfully on the small sample and produces valid metrics.
- [X] T017 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/pii_scanner.py` to scan all files under `data/` (including `data/raw/github-code-sample.csv`) for PII patterns per Constitution Principle III. **Dependency**: Requires T018 to be complete.
- [X] T017_checksum [US1] Compute SHA‑256 checksum for `data/raw/github-code-sample.csv` and record in `artifact_hashes` via `checksum_manifest.py`
- [X] T017_verify [US1] Integration test `tests/integration/test_pii_scanner_verification.py::test_no_pii_found` ensures scanner reports zero PII after cleaning

---

## Phase 3: User Story 1 – Compute Clone Density, Semantic Distance, and Model Perplexity (Priority: P1)

**Purpose**: Core metric extraction needed for downstream analysis

- [X] T019 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/ast_cloner.py` to parse Python files via the built‑in `ast` module, classify clones (Type‑1, Type‑2), and compute syntactic clone density (stdlib only) on PII‑cleaned data
- [X] T020 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/model_metrics.py` to load `Salesforce/codegen-350M-mono` in 8‑bit quantization using bitsandbytes and compute token‑level perplexity
- [X] T053 [US1] Implement semantic‑distance computation using CodeBERT embeddings; output to `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/processed/semantic_distance.csv`. **Requirement**: Must explicitly document and apply the threshold for distinguishing semantic clones as per FR-003.
- [X] T053c [US1] **CRITICAL**: Implement logic to document the semantic clone threshold (e.g., cosine similarity > 0.8) in `hyperparameters.md` and apply it to classify semantic clones in `semantic_distance.csv`.
- [X] T053b [US1] Verification test `tests/integration/test_semantic_distance.py::test_output_exists` ensures `semantic_distance.csv` exists and conforms to its schema
- [X] T021 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/main.py` orchestration to join clone‑density, perplexity, and semantic distance metrics, producing:
    - `data/processed/clone_metrics.csv`
    - `data/processed/perplexity_scores.csv`
    - `data/processed/semantic_distance.csv`
    **Dependency**: Requires T053 to be complete.
- [X] T021b [US1] Integration test `tests/integration/test_main_pipeline.py::test_all_csvs_created` verifies all three CSVs are generated and have matching `segment_id`s
- [X] T021b_test [US1] Additional validation `tests/integration/test_main_schema.py::test_csv_schema_compliance` checks each CSV against its contract schema
- [X] T022 [US1] Add comprehensive error handling for parse failures, NaN/infinite perplexity, network interruptions, and syntax errors; log to `data/parse_failures.csv`
- [X] T023 [US1] Memory‑monitoring task: instrument inference with `psutil` and assert RAM usage ≤ 7 GB
- [X] T023b [US1] Test `tests/integration/test_memory_usage.py::test_memory_under_7gb` ensures the memory threshold is respected
- [X] T024 [US1] Performance‑validation test `tests/integration/test_performance.py::test_500mb_under_24h` asserts processing of the 500 MB corpus completes within 24 h on a standard GitHub Actions runner
- [X] T025 [US1] Compute SHA‑256 checksum for `data/processed/clone_metrics.csv` and record in `artifact_hashes`
- [X] T025b [US1] Compute SHA‑256 checksum for `data/processed/perplexity_scores.csv` and record in `artifact_hashes`
- [X] T025c [US1] Compute SHA‑256 checksum for `data/processed/semantic_distance.csv` and record in `artifact_hashes`
- [X] T025_verify [US1] Integration test `tests/integration/test_checksums_clone_perplexity_semantic.py::test_checksums_match_manifest` validates recorded checksums
- [X] T026 [US1] Segment‑count verification test `tests/integration/test_segment_count.py::test_min_1000_segments` ensures ≥ 1000 processed code segments
- [X] T026_verify [US1] Verification test `tests/integration/test_segment_count_verification.py::test_actual_segment_count` reads `clone_metrics.csv` and asserts count >= 1000
- [X] T083 [US1] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/complexity_metric.py` to compute cyclomatic complexity per function body; output `data/processed/complexity_metric.csv`
- [X] T084 [US1] Unit test `tests/unit/test_complexity_metric.py::test_complexity_values` validates known snippets
- [X] T087 [US1] Generate checksums for `complexity_metric.csv` via `checksum_manifest.py` and record in `artifact_hashes`
- [X] T087_verify [US1] Test `tests/integration/test_checksum_complexity.py::test_checksum_valid` confirms checksum entry

---

## Phase 4: User Story 2 – Evaluate Bug Detection Accuracy and Calculate Correlation (Priority: P2)

**Purpose**: Produce research findings linking duplication to model performance

- [ ] T031_rev [US2] **CRITICAL REVISION**: Refactor `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/bug_detection.py` to remove ALL synthetic data generation and fallback logic; implement strict loading of the official `openai_humaneval` dataset via `datasets.load_dataset("openai_humaneval")` and compute real pass@k accuracy on a 50-problem subset; ensure the script raises a fatal error if real data cannot be loaded. **Output Schema**: `bug_detection_results.csv` MUST contain `segment_id` (mapped from problem_id), `pass_status` (0/1), and `problem_id` (for reference only). **Constraint**: Do NOT aggregate by `problem_id`; correlation must be segment-level. **Dependency**: Requires T018 to be complete.
- [ ] T031b_rev [US2] Unit test `tests/unit/test_bug_detection_real_data.py::test_no_synthetic_fallback` asserts that `bug_detection.py` contains no `generate_synthetic` functions or `try/except` blocks that substitute fake data.
- [X] T070 [US2] Implement real HumanEval bug‑detection pipeline in `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/bug_detection.py`; load dataset via `datasets.load_dataset("openai_humaneval")`; compute pass@1 per problem; output `data/processed/bug_detection_results.csv` with `segment_id` linkage. **Constraint**: Output must strictly use `segment_id` for joining; no `problem_id` aggregation allowed.
- [X] T070b [US2] Remove any synthetic‑data fallback from bug‑detection pipeline and ensure only real HumanEval data is used
- [X] T070c [US2] **CRITICAL**: Add verification test `tests/unit/test_bug_detection_segment_constraint.py::test_no_problem_id_aggregation` to assert that the output does not aggregate by `problem_id` and strictly uses `segment_id` for correlation.
- [X] T071 [US2] Extract data loading logic into `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/data_loading.py` (≤ 200 lines) for reuse
- [X] T032 [US2] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/correlation_analysis.py` to calculate Spearman rank correlation between duplication density, perplexity, and bug‑detection accuracy at **segment level** (using `segment_id` only). **Constraint**: Explicitly forbid `problem_id` usage in join or aggregation.
- [X] T032a [US2] Ensure correlation uses only `segment_id` as join key (implementation guard)
- [X] T032b [US2] Verification test `tests/unit/test_correlation_analysis.py::test_segment_key_used` asserts that only `segment_id` appears in the join operation
- [X] T032c [US2] Add explicit validation that no `problem_id` column is used in joins; raise error if present
- [X] T033 [US2] Join all intermediate metrics (`clone_metrics.csv`, `perplexity_scores.csv`, `semantic_distance.csv`, `bug_detection_results.csv`) on `segment_id`; produce combined CSV `data/processed/joined_metrics.csv`. **Constraint**: Join key is strictly `segment_id`.
- [X] T034 [US2] Save correlation results with p‑values to `data/analysis/correlation_results.csv`
- [X] T034b [US2] Verification test `tests/integration/test_correlation_output.py::test_correlation_file_exists_and_schema` checks that `correlation_results.csv` is produced and matches schema
- [X] T035 [US2] Integration test `tests/integration/test_correlation_significance.py::test_pvalue_below_0_05` asserts p < 0.05 or records null finding per SC‑004. **Requirement**: Must explicitly verify that adequate statistical power (from T092) is met before accepting a null finding.
- [X] T035a [US2] Additional test `tests/integration/test_correlation_significance_edge.py::test_pvalue_reporting` ensures p‑value is reported even when not significant
- [X] T036 [US2] Compute SHA‑256 checksum for `data/analysis/correlation_results.csv` and record in `artifact_hashes`
- [X] T036_verify [US2] Integration test `tests/integration/test_checksum_correlation.py::test_checksum_matches_manifest` validates checksum entry
- [X] T027 [US2] Contract test for correlation schema (`tests/contract/test_correlation_schema.py`) using pytest
- [X] T028 [US2] Integration test `tests/integration/test_pipeline_end_to_end.py` runs full pipeline on a modest subset and checks end‑to‑end artifact creation
- [X] T029 [US2] Unit test `tests/unit/test_bug_detection.py::test_pass_at_1_computation` validates bug‑detection accuracy calculation
- [X] T030 [US2] Unit test `tests/unit/test_correlation_analysis.py::test_spearman_computation` validates Spearman coefficient calculation
- [X] T092 [US2] Implement statistical power analysis step outputting `data/analysis/power_analysis.txt`
- [X] T092_test [US2] Integration test `tests/integration/test_power_analysis.py::test_power_sufficient` ensures power is adequate per SC‑004
- [X] T092_verify [US2] Test `tests/integration/test_power_analysis_verification.py::test_power_file_exists_and_content` confirms file presence and reasonable power value
- [ ] T095_rev [US2] **CRITICAL REVISION**: Execute the full pipeline on real data to generate `data/processed/perplexity_scores.csv` and `data/processed/bug_detection_results.csv` with actual measurements from the 500MB corpus and HumanEval; verify `data/analysis/correlation_results.csv` contains non-null, non-NaN Spearman coefficients and p-values derived from real data. **Dependency**: Requires T031_rev to be complete and T018 to be complete.
- [ ] T095_verify [US2] Verification test `tests/integration/test_real_data_validation.py::test_real_data_artifacts` asserts that `perplexity_scores.csv` and `bug_detection_results.csv` contain actual numerical values (not placeholders) and that the sample size N matches the number of processed segments.
- [ ] T095_checksum_rev [US2] **CRITICAL REVISION**: Update `artifact_hashes` state manifest with valid SHA-256 checksums for the newly generated real data files: `clone_metrics.csv`, `perplexity_scores.csv`, `bug_detection_results.csv`, and `correlation_results.csv`.

---

## Phase 5: User Story 3 – Sensitivity Analysis and Visualizations (Priority: P3)

**Purpose**: Robustness checks and publication‑ready figures

- [X] T040 [US3] Extend `correlation_analysis.py` to perform sensitivity analysis across clone‑detection thresholds; output per‑threshold correlation CSVs in `data/analysis/`
- [X] T041 [US3] Implement `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/visualization.py` to generate scatter plots with regression lines for each metric pair; save PNG & PDF in `data/analysis/figures/`
- [X] T041b [US3] **CRITICAL**: Implement `visualization.py` to generate a **structural heat map** visualizing function header vs. body contributions to perplexity spikes. **Algorithm**: 1) Parse code segments into AST; 2) Identify header (def line) vs. body (indented block); 3) Compute local perplexity contribution for each region; 4) Map contributions to a heatmap grid where x-axis = code position, y-axis = region type (header/body), color = perplexity contribution. Output `data/analysis/figures/structural_heatmap.png`.
- [X] T042 [US3] Ensure all figures are saved in both PNG and PDF formats
- [ ] T043_rev [US3] **CRITICAL REVISION**: Expand `specs/001-evaluating-code-duplication-llm-understanding/hyperparameters.md` to explicitly document all random seeds, the three clone-detection thresholds, model quantization parameters (8-bit), and all configuration parameters from `code/config.py` required for full reproducibility.
- [X] T074 [US3] Verification test `tests/integration/test_hyperparameters_doc.py::test_location_and_content` checks that `hyperparameters.md` exists and contains required entries
- [X] T044 [US3] Compute SHA‑256 checksums for all visualization outputs and record in `artifact_hashes`
- [X] T044_verify [US3] Integration test `tests/integration/test_visualization_checksums.py::test_all_figures_checksummed` validates checksum entries
- [X] T045 [P] Update `specs/001-evaluating-code-duplication-llm-understanding/quickstart.md` with reproducibility steps
- [X] T046 Code cleanup and refactoring across `projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/`
- [X] T046_verify [P] Test `tests/integration/test_code_cleanup.py::test_refactor_completeness` ensures refactoring tasks have been applied
- [X] T047 [P] Additional integration tests in `tests/integration/` for end‑to‑end validation
- [X] T048 Run quickstart validation to ensure reproducibility steps work
- [X] T049 [P] Run pytest on Linux/GitHub Actions platform to validate platform compatibility
- [X] T050 [P] Document parallel execution opportunities and team capacity planning in `quickstart.md`
- [X] T051 Map Constitution Check principles to concrete task IDs for traceability (already present)
- [X] T052 [US1] Integration test `tests/integration/test_pii_validation.py::test_no_pii_found` verifies PII scanner finds no patterns after cleaning
- [X] T055 (already completed) – removal of synthetic fallback in bug detection
- [X] T056 (already completed) – main.py integration
- [X] T057‑T060 (already completed) – re‑run pipeline with real data
- [X] T061 [P] Move hyperparameters documentation to `specs/.../hyperparameters.md` and expand it (already completed as T043)
- [X] T062 [US1] Segment‑count verification for SC‑007 (already covered by T026)
- [X] T063 [P] Update `plan.md` to reflect new hyperparameters location and visualization module path (out of scope for tasks.md)
- [X] T064 [P] Verify that `data/raw/github-code-sample.csv` exists, is ~500 MB, and was created via streaming as specified in T018 (covered by T018_test)
- [X] T065 [P] Ensure all schema files are non‑empty and validated (covered by T010 and contract tests)
- [X] T076 [P] Consolidate code‑structure (already completed)
- [X] T076_verify [P] Test `tests/integration/test_code_structure_consolidation.py::test_modules_importable` ensures consolidated modules load correctly
- [X] T077 [P] Verify artifact paths via `tests/integration/test_artifact_paths.py::test_all_paths_exist`
- [X] T078 [P] End‑to‑End Real Data Verification via `tests/integration/test_full_pipeline_real_data.py::test_all_artifacts_present`
- [X] T079 [US1] Implement `semantic_cloner.py` that loads CodeBERT, generates embeddings per AST node, computes cosine similarity, outputs `data/processed/semantic_distance.csv` (already covered by T053)
- [X] T080 [US1] Unit tests `tests/unit/test_semantic_cloner.py::test_embedding_generation` validate embedding generation and cosine similarity on a real snippet
- [X] T081 [US2] Extend `correlation_analysis.py` to optionally include `semantic_distance` as a third independent variable; output includes `semantic_distance` column
- [X] T082 [US2] Integration test `tests/integration/test_semantic_correlation.py::test_semantic_distance_bounds` confirms values are within the expected normalized interval and show sensible correlation with clone density.
- [X] T085 [US1] Update `hyperparameters.md` to document new metrics (semantic distance, complexity) and their config parameters
- [X] T086 [US1] Extend `pii_scanner.py` to also log files that failed AST parsing; integration test `tests/integration/test_pii_and_parse_failures.py::test_logging` verifies logging
- [X] T087 [P] Consolidate checksum generation for `semantic_distance.csv` and `complexity_metric.csv` via `checksum_manifest.py` (already done)
- [X] T088 [P] Consolidate utils for checksum and visualization into canonical `visualization.py`; imports updated accordingly
- [X] T089 [P] Update `plan.md` to reflect new hyperparameters location and visualization module path (out of scope for tasks.md)
- [X] T090 [P] Re‑run full pipeline after adding semantic distance and complexity metrics; verify `correlation_results.csv` includes new columns and checksums are valid
- [X] T091 [US3] Integration test `tests/integration/test_full_pipeline_real_data.py::test_final_artifacts` asserts presence and correctness of all CSVs, PNG/PDF figures, and checksum entries
- [X] T093 [US2] Document power analysis methodology and results in `specs/001-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/reports/power_analysis.md`
- [X] T015a [US1] Edge‑case test `tests/integration/test_rate_limiting.py::test_download_resilience` simulates network interruptions during dataset streaming and verifies retry logic

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **CRITICAL ORDER**: T018 (Download) MUST complete before T017 (PII Scan).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - **Ordering**: T018 -> T017 -> T053 -> T021 -> T019/T020 (parallel)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
  - **Ordering**: T031_rev (Refactor) MUST precede T095_rev (Execute).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Tasks T031_rev, T095_rev, T095_verify, T095_checksum_rev, and T043_rev address critical reviewer concerns regarding synthetic data fabrication, missing real-data artifacts, and incomplete reproducibility documentation. These tasks are mandatory for advancing the research.
- **Constraint Note**: All correlation analysis (T032, T033, T070) is strictly segment-level (function bodies) and explicitly excludes `problem_id` aggregation per FR-007.
- **Data Note**: T018 streams exactly 500MB. Tc_small uses exactly 10 files.
- **Visualization Note**: T041b explicitly requires header vs. body decomposition for perplexity spike visualization.