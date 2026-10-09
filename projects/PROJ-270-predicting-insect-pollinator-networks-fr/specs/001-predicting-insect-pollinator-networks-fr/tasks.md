# Tasks: Predicting Insect Pollinator Networks from Floral Trait Data

**Input**: Design documents from `/specs/001-predicting-pollinator-networks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] **Directory Structure**: Execute `mkdir -p code/ data/raw/ data/processed/ tests/ docs/ results/ code/utils/ code/contracts` at repository root. Verify existence with `test_directory_structure` in `tests/test_setup.py` asserting `os.path.exists` for each directory.
- [ ] T001b [P] Create empty `__init__.py` files in `code/`, `tests/`, and `code/utils/` to initialize Python packages.
- [X] T002 Initialize Python 3.11 project with `scikit-learn`, `pandas`, `numpy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `datasets` dependencies in `code/requirements.txt`
- [X] T003 [P] **Linting/Formatting Config**: Create `code/.ruff.toml`, `code/.black.toml`, `code/.mypy.ini` with standard configs. Verify installation with `ruff --version`, `black --version`, `mypy --version`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement data hygiene utilities: checksum verification, raw vs processed directory structure (`data/raw/`, `data/processed/`) in `code/utils/io_utils.py` (Depends on T008 schema)
- [X] T005 [P] Implement reference validation wrapper for the Reference-Validator Agent pre-commit hook in `code/utils/citation_validator.py`
- [X] T006 [P] Create base configuration management (env vars, random seeds) in `code/config.py`
- [X] T007 [P] Setup logging infrastructure with structured JSON output in `code/utils/logger.py`
- [X] T008 [P] Define data schemas and validation logic in `code/contracts/dataset.schema.yaml` and `code/contracts/output.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest bipartite interaction matrices from Web of Life and trait metadata, preprocess into a unified feature matrix.

**Independent Test**: Can be fully tested by running the data ingestion script against a small, fixed set of Web of Life ecosystems and verifying the output feature matrix dimensions and data types match the expected schema (rows: plant-pollinator pairs, columns: encoded traits + binary link label).

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [~] T009 [P] [US1] Unit test for Web of Life downloader in `tests/test_ingestion.py` (mock network calls, verify file structure)
- [~] T010 [P] [US1] Unit test for heuristic mapping logic in `tests/test_ingestion.py` (verify fallback paths: mapping file -> DOI scrape -> Dryad API)
- [~] T011 [P] [US1] Integration test for full ingestion pipeline on 3 sample ecosystems in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/ingestion.py`: Web of Life downloader with error handling (skip ecosystem if no trait data, log warning). **Must return the count of valid ecosystems retrieved.**
- [~] T013 [P] [US1] Implement `code/ingestion.py`: Heuristic mapping strategy (Mapping file -> DOI scrape -> Dryad API search). **Runs in parallel with T012.**
- [~] T012b [US1] **Strict Real-Data Fetch**: Refactor `code/ingestion.py` to **remove any** `try/except` blocks or conditional logic that falls back to `generate_synthetic_*()`, `mock_*()`, or placeholder data when a real fetch fails. If a download or API call fails for a specific ecosystem, the script MUST log a warning and **skip that ecosystem**, proceeding with the remaining valid data. It must NOT halt the entire pipeline (unless no ecosystems are found at all). Add `test_strict_fetch_failure` in `tests/test_ingestion.py` to assert that a simulated network error for one ecosystem results in a warning and skip, not a synthetic fallback or pipeline abort.
- [~] T012c [US1] **Streaming Implementation**: Implement `stream_dataset()` in `code/ingestion.py` using `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(..., chunksize=...)`. **Trigger Condition**: Only enable streaming if `profile_memory_usage()` (T026b) detects RAM usage approaching 7GB or if the dataset size exceeds available memory. Ensure the pipeline processes data in chunks to stay within 7GB RAM limits without loading the full dataset into memory. Add `test_streaming_memory` in `tests/test_ingestion.py` to verify memory usage remains stable while processing a large simulated stream.
- [~] T012d [US1] **Sample Definition & Limitation**: If a real dataset is too large to stream efficiently or a specific ecosystem lacks data, implement `define_sample()` in `code/preprocessing.py` to explicitly select a well-defined subset (e.g., `itertools.islice` first N rows or a fixed-seed random sample). The code MUST log and report the exact sample size, selection criteria, and a limitation statement regarding representativeness. Add `test_sample_definition` in `tests/test_preprocessing.py` to assert that any sampling logic is deterministic and explicitly logged.
- [~] T012e [US1] **Verified Source Adoption**: Implement `adopt_verified_source()` in `code/ingestion.py` to detect and use a "VERIFIED REAL DATA SOURCE" block if provided by the execution stage (e.g., an installable package + access recipe). The script must prioritize this verified source over any hard-coded URLs or guessed dataset IDs. If no verified source is provided, fall back to the default heuristic mapping strategy (T013) to ensure graceful handling. Add `test_verified_source_priority` in `tests/test_ingestion.py` to assert that a verified source overrides default fetch logic.
- [~] T012f [US1] **Real Result Verification**: Add `test_real_result_only` in `tests/test_model.py` to assert that the final `results/metrics.json` is generated from real data inputs (checked via data hash or source ID) and not from synthetic or placeholder datasets. The test must fail if the metrics are derived from a known synthetic source.
- [~] T012a [US1] **Chunked Reading**: Implement `process_in_chunks` in `code/ingestion.py` to handle large datasets. Algorithm: Read CSV in chunks of **configurable size (default [deferred] rows)** during the download/parse phase in T012, process, and append to final dataframe. Verify `data/processed/feature_matrix.csv` is generated without OOM error on large input.
- [~] T014a [US1] **Temporal Metadata Check**: Implement `check_temporal_metadata()` in `code/preprocessing.py`. Validate presence of `start_date` and `end_date` fields in ecosystem metadata. **Log warning if missing, do not block execution.**
- [~] T015a [US1] **Negative Sample Generation**: Implement `generate_negative_samples()` in `code/preprocessing.py`. Algorithm: <!-- FAILED: unspecified -->
 1. Generate Cartesian product of plant and pollinator species in the ecosystem, excluding observed links.
 2. **Primary Proxy**: Use spatial co-occurrence (species appearing in the same ecosystem file) as the sufficient condition for negative sampling.
 3. **Optional Filter**: If temporal metadata is explicitly provided, apply temporal overlap as an additional filter.
 4. Ensure the final set satisfies the co-occurrence constraint. **Note**: Spatial co-occurrence is sufficient; temporal is an optional enhancement, not a requirement.
- [~] T015b [US1] **Negative Sample Validation**: Implement `validate_negative_samples()` in `tests/test_preprocessing.py`. Assert all negative pairs exist in the co-occurrence matrix derived from T014 and satisfy the co-occurrence constraint (spatial primary, temporal optional). <!-- FAILED: unspecified -->
- [~] T016a [US1] **Imputation Logic**: Implement `median_imputation()` in `code/preprocessing.py`. Apply to all continuous columns in `feature_matrix`. <!-- FAILED: unspecified -->
- [~] T016b [US1] **Missingness Flagging**: Implement `flag_missingness()` in `code/preprocessing.py`. Flag ecosystem if missingness > 15% and log warning.
- [~] T017a [US1] **Winsorization**: Implement `winsorize_outliers()` in `code/preprocessing.py` at extreme percentiles.
- [~] T017b [US1] **Normalization**: Implement `z_score_normalize()` in `code/preprocessing.py` after winsorization.
- [~] T018a [US1] **Categorical Encoding**: Implement `one_hot_encode()` in `code/preprocessing.py`. Strategy: One-hot encode categorical columns, drop unknown categories, and add "unknown" column if specified in schema.
- [~] T018b [US1] **Effort Extraction**: Implement `extract_sampling_effort()` in `code/preprocessing.py`. <!-- FAILED: unspecified -->
- [~] T019a [US1] **Matrix Assembly**: Implement `assemble_feature_matrix()` in `code/preprocessing.py`. Schema: Rows: plant-pollinator pairs; Columns: [trait_1,..., trait_n, sampling_effort, link_label].
- [~] T019b [US1] **ID Exclusion**: Implement `exclude_species_ids()` in `code/preprocessing.py` to ensure no species/ID columns in final matrix.
- [~] T020 [US1] **Validation & Threshold Enforcement**: Implement `validate_ecosystem_count()` in `code/ingestion.py`. If valid_count < 8, **log a warning** stating the count and **proceed with available data** (do NOT abort). Add `test_validate_count` in `tests/test_ingestion.py` to assert pipeline **continues execution** when count < 8 and verifies a warning was logged.
- [~] T021 [US1] Create `code/main.py` orchestrator to run ingestion and preprocessing sequentially (depends on T020 validation logic).
- [~] T022 [US1] **Schema Validation**: Implement `validate_schema()` in `code/utils/schema_validator.py`. Add `tests/test_schema_validation.py` to assert output matches `code/contracts/dataset.schema.yaml`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with stratified k-fold CV and calculate permutation importance.

**Independent Test**: Can be fully tested by training the model on a subset of the data (e.g., 1 ecosystem) and verifying that the cross-validation loop completes, produces consistent AUC-ROC scores across folds, and that the model object is serializable.

### Tests for User Story 2

- [~] T023 [P] [US2] Unit test for stratified split generation in `tests/test_model.py`
- [~] T024 [P] [US2] Unit test for permutation importance calculation in `tests/test_model.py`
- [~] T025 [P] [US2] Integration test for training loop on sample data in `tests/integration/test_training_flow.py`

### Implementation for User Story 2

- [~] T026a [US2] **Chunked Processing**: Implement `process_in_chunks()` in `code/model_training.py`. Algorithm: Process data in manageable chunks; merge results after each chunk.
- [~] T026b [US2] **Memory Profiling**: Implement `profile_memory_usage()` in `code/model_training.py` to detect OOM risks.
- [~] T027 [US2] **Logging Setup**: Implement `log_cv_metrics()` in `code/model_training.py`. Verify `results/metrics.json` contains keys `auc_mean`, `auc_std`, `precision_mean`, `recall_mean`.
- [~] T028a [US2] **Class Weight Config**: Implement `set_class_weights()` in `code/model_training.py` (class_weight='balanced').
- [~] T028b [US2] **CV Setup**: Implement `setup_stratified_kfold()` in `code/model_training.py`.
- [~] T029a [US2] **CV Loop**: Implement `run_cross_validation()` in `code/model_training.py`.
- [~] T029b [US2] **Metric Aggregation**: Implement `aggregate_cv_metrics()` in `code/model_training.py` to calculate mean/std.
- [~] T030a [US2] **Importance Calculation**: Implement `calculate_permutation_importance()` in `code/model_training.py`.
- [~] T030b [US2] **Ranking Logic**: Implement `rank_traits()` in `code/model_training.py` to identify top 3 traits.
- [~] T031 [US2] **Model Serialization**: Implement `save_model()` in `code/model_training.py` to save to `data/processed/model.pkl`. Add `test_model_serialization` in `tests/test_model.py` to assert file exists and loads without error.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generalization Validation and Reporting (Priority: P3)

**Goal**: Evaluate model using LOEO cross-validation, compare against null models, and generate visualizations.

**Independent Test**: Can be fully tested by running the evaluation script on a single held-out ecosystem and verifying that an AUC-ROC score is generated, a network comparison plot is saved, and the results are logged to a summary report.

### Tests for User Story 3

- [~] T032 [P] [US3] Unit test for LOEO loop logic in `tests/test_validation.py`
- [~] T033 [P] [US3] Unit test for Trait-Shuffled Null Model in `tests/test_validation.py`
- [~] T034 [P] [US3] Unit test for Degree-Preserving Null Model in `tests/test_validation.py`
- [~] T035 [P] [US3] Unit test for NetworkX visualization generation in `tests/test_visualization.py`

### Implementation for User Story 3

- [~] T036a [US3] **LOEO Loop**: Implement `run_loeo_cv()` in `code/validation.py`. Algorithm: Iterate over all ecosystems, train on N-1, test on 1; repeat for all N ecosystems.
- [~] T036b [US3] **Trait-Shuffled Null**: Implement `trait_shuffled_null()` in `code/validation.py`. Add `test_trait_shuffled_null` in `tests/test_validation.py`.
- [~] T036c [US3] **Comparison Logic**: Implement `compare_loeo_to_cv()` in `code/validation.py`.
- [~] T037 [US3] **CV Mean Baseline**: Implement `calculate_cv_baseline()` in `code/validation.py` to compute mean of internal 5-fold CV for SC-003 comparison.
- [~] T039 [US3] **Degree-Preserving Null**: Implement `degree_preserving_null()` in `code/validation.py`. Add verification test.
- [~] T040 [US3] **Permutation Test**: Implement `run_permutation_test()` in `code/validation.py`.
 Algorithm:
 1. **Primary Validation**: Run permutation test with 1000 iterations against the **Trait-Shuffled Null Model (T036b)** to calculate p-value for SC-001 (p < 0.05). This is the primary validation for trait efficacy.
 2. **Secondary Validation**: Run permutation test against Degree-Preserving Null (T039) for topology comparison.
 3. **Fallback**: If runtime > 3h, reduce to 100 iterations, log "approximate", and write results to `results/p_values_approx.json`.
 4. **Success**: Write results to `results/p_values.json`.
 **Artifact**: T045b MUST read `results/p_values.json` (or `results/p_values_approx.json` if fallback triggered) to assert the final p-value. Verify `results/report.md` contains "approximate" if iterations < 1000.
- [~] T041a [US3] **Network Plotting**: Implement `plot_network_discrepancies()` in `code/visualization.py`. Algorithm: Generate NetworkX plot comparing observed vs. predicted links. Assert `results/plots/observed_vs_predicted.png` exists.
- [~] T041b [US3] **Discrepancy Highlighting**: Implement `highlight_discrepancies()` in `code/visualization.py` to mark high-probability missing links.
- [~] T042a [US3] **PR Curves**: Implement `plot_pr_curves()` in `code/visualization.py`. Assert `results/plots/pr_curve.png` exists.
- [~] T042b [US3] **ROC Curves**: Implement `plot_roc_curves()` in `code/visualization.py`. Assert `results/plots/roc_curve.png` exists.
- [~] T043a [US3] **Trait-Only Baseline (Observed Model)**: Implement `train_trait_only_baseline()` in `code/validation.py`.
 **Definition**: This model uses the full set of available *trait* features (**morphology, color, scent, sampling_effort**) and explicitly **excludes** species IDs and ecosystem IDs. This is the "observed model" for the trait gap calculation.
 **Note**: SC-004's "saturated model" definition (using all known interaction features) is unimplementable under the project's generalizability constraints (Constitution Principle VI). This task implements the best possible proxy: the model using all *available trait features*.
 Use same trait features as main model; exclude species IDs. This serves as the baseline for the Trait-Shuffled Null comparison (SC-004).
- [~] T043b [US3] **Trait Gap Calc**: Implement `calculate_trait_gap()` in `code/validation.py`.
 Algorithm: Calculate `trait_gap = AUC_observed (T043a) - AUC_shuffled (T036b)`.
 Store result in `results/metrics.json` under key `trait_gap`.
- [~] T044a [US3] **Sensitivity Re-run**: Implement `sensitivity_analysis_high_confidence()` in `code/validation.py` to re-run eval on high-confidence negatives.
- [~] T044b [US3] **Noise Assessment**: Implement `assess_label_noise_impact()` in `code/validation.py` and log results.
- [~] T045a [US3] **Report Template**: Implement `generate_report_template()` in `code/reporting.py`.
- [~] T045b [US3] **Content Compilation**: Implement `compile_report_content()` in `code/reporting.py`.
 Algorithm: Use `jinja2` template to insert `auc_mean`, `trait_importance_ranking`, and `trait_gap` into `results/report.md`.
 **Format**: Ensure the trait gap is formatted as `Trait Gap: {value:.4f}`.
 Assert `results/report.md` contains `Trait Gap: ` followed by a numeric value.
 **Artifact Source**: Read `results/metrics.json` for `trait_gap` and `results/p_values.json` (or `results/p_values_approx.json`) for p-value.
- [~] T046 [US3] **Citation Validation**: Run `reference-validator --file results/report.md` and assert exit code 0.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T047 [P] **Documentation**: Create `docs/quickstart.md` with execution instructions including `python code/main.py` command.
- [~] T048 [P] **Code Cleanup**: Run `ruff check --fix`, `black.`, `mypy code/` with zero errors. Add `test_code_quality` in `tests/test_setup.py` to verify linting passes.
- [ ] T049 [P] **Performance Verification**: Create `tests/test_memory_usage.py`. Run with 2GB synthetic dataset and assert peak memory < 6.5 GB.
- [ ] T050 [P] **Edge Case Tests**: Add `tests/unit/test_ingestion.py` with `test_empty_ecosystem` (assert pipeline handles empty input gracefully) and `test_missing_metadata` (assert pipeline skips missing metadata and logs warning).
- [~] T051 [P] **Quickstart Validation**: Run `python -m code.main` via `quickstart.md` instructions. Verify dynamic iteration scaling fallback triggers correctly (check logs for "approximate" flag) and produces reproducible results.
- [~] T052 [P] **Reproducibility Check**: Run pipeline twice with same seed. Assert `data/processed/feature_matrix.csv` hashes match.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion/Preprocessing (T012-T022) before Model Training (T026-T031)
- Model Training before Validation/Reporting (T036-T046)
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
# Launch all tests for User Story 1 together:
Task: "Unit test for Web of Life downloader in tests/test_ingestion.py"
Task: "Unit test for heuristic mapping logic in tests/test_ingestion.py"
Task: "Integration test for full ingestion pipeline in tests/integration/test_ingestion_flow.py"

# Launch all preprocessing tasks for User Story 1 together (T012 & T013 parallel, T014-T022 sequential):
Task: "Implement Web of Life downloader in code/ingestion.py"
Task: "Implement Heuristic mapping strategy in code/ingestion.py"
Task: "Implement Strict Real-Data Fetch in code/ingestion.py"
Task: "Implement Streaming Implementation in code/ingestion.py"
Task: "Implement Temporal Metadata Check in code/preprocessing.py"
Task: "Implement Negative Sample Generation in code/preprocessing.py"
Task: "Implement Negative Sample Validation in tests/test_preprocessing.py"
Task: "Implement Imputation Logic in code/preprocessing.py"
Task: "Implement Missingness Flagging in code/preprocessing.py"
Task: "Implement Winsorization in code/preprocessing.py"
Task: "Implement Normalization in code/preprocessing.py"
Task: "Implement Categorical Encoding in code/preprocessing.py"
Task: "Implement Effort Extraction in code/preprocessing.py"
Task: "Implement Matrix Assembly in code/preprocessing.py"
Task: "Implement ID Exclusion in code/preprocessing.py"
Task: "Implement Validation & Threshold Enforcement in code/ingestion.py"
Task: "Implement Schema Validation in code/utils/schema_validator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify feature matrix output and threshold enforcement)
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
 - Developer A: User Story 1 (Ingestion/Preprocessing)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Validation/Reporting)
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
- **Data Integrity**: Never fall back to synthetic data if real fetch fails; use real data sources only. Graceful skipping of missing data is required.
- **Co-occurrence**: Ensure negative samples are derived strictly from the interaction matrix (spatial co-occurrence) with explicit temporal validation. If temporal data is missing, the system must proceed with spatial-only data (no error).
- **LOEO**: Ensure the validation strategy is Leave-One-Ecosystem-Out, not a single held-out test.
- **Null Models**: Prioritize Trait-Shuffled Null Model for SC-001 (trait efficacy); use Degree-Preserving Null Model as secondary for topology.
- **Threshold**: If <8 ecosystems are retrieved, log a warning and proceed with available data (graceful skip).
- **Trait Gap**: Must be calculated as `AUC_observed (Trait-Only) - AUC_shuffled` where "Trait-Only" uses all available trait features.
- **Approximate Results**: If permutation test fallback triggers, explicitly flag the result as approximate in the report.
- **Real Data Only**: Synthetic fallbacks are strictly prohibited; use real data sources only.
- **Streaming**: Large datasets MUST be streamed or sampled with explicit limitation reporting; no loading full datasets into memory.
- **Verified Sources**: If a verified real data source is provided by the execution stage, it MUST be adopted as the single source of truth.
