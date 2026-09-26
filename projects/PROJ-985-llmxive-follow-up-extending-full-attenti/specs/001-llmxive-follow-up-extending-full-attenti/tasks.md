# Tasks: llmXive Follow-up: Extending "Full Attention Strikes Back"

**Input**: Design documents from `/specs/001-llmxive-static-sparsification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Research Pipeline**: `code/data/`, `code/models/`, `code/evaluation/`, `code/lib/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create base project directories: `code/`, `tests/`, `data/`, `code/lib/`, `code/data/`, `code/models/`, `code/evaluation/`, `data/results/`, `data/logs/`, `data/intermediate/`, `data/config/`. **Implementation**: Create `code/scripts/init_dirs.sh` with `mkdir -p` commands for all 11 paths. **Verification**: Assert `os.path.isdir(...)` for all paths.
- [X] T001b [P] Verify directory structure and capture `tree` output. **Deliverables**: Create `data/logs/structure_verification.txt` containing the `tree` output. **Verification**: Assert `structure_verification.txt` exists and is non-empty.
- [X] T002a [P] Create base `code/requirements.txt` with unpinned dependencies for: transformers, torch, datasets, scikit-learn, spacy, kenlm, numpy, pandas, bitsandbytes. **Content**: List exact package names one per line without version specifiers.
- [X] T002b [P] Pin versions in `code/requirements.txt` by running `pip freeze` in a clean virtualenv and saving output. **Verification**: Assert `requirements.txt` contains `==` for all packages.
- [X] T003a [P] Configure linting and formatting tools. **Deliverables**: Create `.ruff.toml` (content: `max-line-length = 88`) and `pyproject.toml` (content: `[tool.black]` section with `line-length = 88`). **Verification**: Assert `.ruff.toml` and `pyproject.toml` exist and contain specified content.
- [X] T003b [P] Run linting and formatting checks. **Verification**: Run `ruff check . --exit-zero` and `black --check .` successfully.
- [X] T004 [P] Initialize pytest configuration and create empty test suite structure. **Deliverables**: Create `pyproject.toml` (tool.pytest section) and `code/tests/conftest.py`. **Verification**: Run `pytest --collect-only` and verify 0 errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until T005 and T006 are complete. T007/T008 are optional for debugging but recommended and do NOT block T011/T012 execution.

- [X] T005 [P] Implement memory-efficient data loader in `code/lib/data_loader.py` that streams RULER dataset chunks, enforces GB RAM limit, and includes a **unit test asserting peak memory usage < 7GB** in `tests/unit/test_data_loader.py::test_peak_memory`. **Input Scope**: The test MUST use a **100-document sample** from the RULER validation split using `datasets.load_dataset(..., split='validation')[:100]`. **Verification**: Run `pytest tests/unit/test_data_loader.py::test_peak_memory` and assert it passes.
- [X] T006 [P] Create base data entities (`TokenUnit`, `AttentionMap`, `StaticHeuristic`) in `code/lib/entities.py`.
- [X] T007 [P] [Optional] Implement attention map visualization and debugging utilities in `code/lib/attention_utils.py`.
- [X] T008 [P] [Optional] Setup logging infrastructure to track pipeline stages and memory usage in `code/lib/logging_config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Extraction & Static Feature Computation (Priority: P1) 🎯 MVP

**Goal**: Generate parallel datasets of RTPurbo-selected tokens and static linguistic features for the RULER corpus subset.

**Independent Test**: Run the extraction pipeline on a representative document sample and verify the output CSV contains valid entropy, POS tags, and binary RTPurbo labels without GPU memory errors.

### Tests for User Story 1 (OPTIONAL)

- [X] T009 [P] [US1] Unit test for feature extraction logic in `tests/unit/test_feature_extraction.py`.
- [X] T010 [P] [US1] Integration test for ground truth generation on small sample in `tests/integration/test_ground_truth.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement RULER dataset downloader with streaming support in `code/data/download.py` (FR-001). **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` and **fail loudly** if the real source is unreachable; **NO** synthetic fallbacks or mock data generation.
- [X] T012 [US1] Implement frozen Llama-3-8B Ground Truth Extraction pipeline in `code/data/extract_ground_truth.py` (FR-002). **Requirements**:
 1. Load model with `torch.no_grad()`, `requires_grad=False`, and **8-bit quantization** (`load_in_8bit=True`, `device_map="auto"`) to fit 7GB RAM.
 2. Process a **strictly sampled subset of documents** (from T011) to fit 7GB RAM.
 3. Generate full attention maps and apply RTPurbo to extract ground-truth labels. **Parameters**: Use `k=10` and `threshold=0.05` as defined in `data/config/rtpurbo_params.yaml` (create this file with these defaults). **Implementation**: Reference the canonical RTPurbo implementation from the "Full Attention Strikes Back" paper repo.
 4. Implement anomaly detection: flag documents with zero RTPurbo tokens, log to `data/logs/anomalies.csv`, and **exclude them from the final dataset**.
 5. **Sampling Logic**: Sample a fixed subset of documents first, then apply anomaly exclusion. This ensures the effective sample size for training (T019) is consistent.
 6. **Verification**: Ensure deterministic output by using pinned random seeds for sampling. **Verification**: Assert `data/logs/anomalies.csv` is created and used to filter data in T014.
 7. **Output**: `data/intermediate/rtpurbo_labels.parquet`, `data/intermediate/attention_maps.h5`, and `data/logs/anomalies.csv`.
- [X] T015 [US1] [Implementation] Implement edge case handling for ambiguous tokens (special chars, emojis) in `code/data/compute_features.py` (Edge Case 1). **Requirement**: Must assign default "neutral" category or exclude from heuristic logic. **Verification**: Assert no runtime crashes on input with special characters. **Dependency**: Must be completed before T013.
- [X] T013 [US1] Implement static feature computation (Entropy, POS via spaCy, Position, KenLM perplexity, **local semantic density**) in `code/data/compute_features.py` (FR-003). **Input**: Anomaly list from T012 (to exclude rows) AND Edge Case handling from T015. **Definition**: 'local semantic density' is calculated as the density of unique n-grams (n=3) within a sliding window of size `window_size=10` around the target token. **Verification**: Assert output schema includes `local_semantic_density` column. **Dependency**: T012 (anomaly list) and T015 (edge cases) must complete before T013.
- [X] T014 [US1] Implement dataset merger to join ground truth labels (from T012, filtered by anomaly list) with static features (from T013) into `data/intermediate/merged_dataset.csv`. **Input**: T012 anomaly list to exclude rows. **Dependency**: T012 must complete before T014. **Verification**: Assert row count matches sum of valid inputs and schema is correct (all expected columns present).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **T014 must complete before T019 starts.**

---

## Phase 4: User Story 2 - Static Predictor Training & Heuristic Derivation (Priority: P2)

**Goal**: Train a CPU-based classifier to predict RTPurbo selection and derive a deterministic rule-based heuristic.

**Independent Test**: Train the model on a training split and evaluate on validation; verify the output includes a specific rule set and baseline accuracy metric.

### Tests for User Story 2 (OPTIONAL)

- [X] T017 [P] [US2] Unit test for rule derivation logic in `tests/unit/test_rule_derivation.py`.
- [X] T018 [P] [US2] Integration test for training pipeline with multiple seeds in `tests/integration/test_training.py`.

### Implementation for User Story 2

- [X] T019 [US2] Implement CPU-based classifier training (Decision Tree/Logistic Regression) with **independent random seeds** in `code/models/train_static.py` (FR-004). **Input**: `data/intermediate/merged_dataset.csv` (output of T014). **Output**: trained models saved to `data/intermediate/models/seeds/model_seed_{seed}.pkl`. **Verification**: Run a test to assert model loads and predicts on a dummy input.
- [X] T019b [US2] Implement evaluation of the trained static models on the test set to generate **performance scores** (precision/recall) in `code/models/evaluate_static.py` (FR-004). **Logic**: Iterate over the seed models, evaluate each on the test set, and save results. **Output**: `data/intermediate/static_eval_scores.json` with schema `{seed_id: int, precision: float, recall: float}`. **Verification**: Assert schema matches.
- [X] T019c [US2] Implement aggregation logic to compute **mean, variance, and standard deviation** of the static evaluation scores and save to `data/results/static_aggregated.json`. **Schema**: `{mean_metric, std_metric, variance_metric, n_seeds, seed_values: []}` (FR-004). **Verification**: Assert aggregation logic matches manual calculation on a small subset. **Requirement**: Must include variance/std_dev to satisfy SC-001 stability measurement.
- [X] T020 [US2] Implement rule derivation logic to extract hard thresholds from model importance in `code/models/derive_rules.py` (FR-004). **Output Format**: JSON schema `{"rules": [{"condition": "entropy > X", "pos": ["NOUN", "PROPN"]}]}`. **Method**: Extract decision tree paths or analyze feature importance coefficients to derive deterministic rules. **Verification**: Assert output file exists and matches schema.
- [X] T021 [US2] Implement static heuristic application script to reconstruct RTPurbo tokens using only rules in `code/models/apply_heuristic.py` (FR-004).
- [X] T022 [US2] Add metrics calculation (Precision/Recall) for static predictor against ground truth in `code/lib/metrics.py` (FR-004).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sparsification Evaluation & Statistical Comparison (Priority: P3)

**Goal**: Evaluate static-heuristic sparsification against baselines and perform statistical significance testing.

**Independent Test**: Run evaluation on test set and generate report with perplexity, exact match, and p-values comparing methods.

### Tests for User Story 3 (STRICT PREREQUISITE)

**⚠️ CRITICAL ORDERING**: T023 and T024 MUST be written and verified to fail before any implementation tasks (T025-T032) begin. These are NOT parallel tasks; they are sequential prerequisites to ensure the contract is defined before implementation.

- [X] T023 [US3] Contract test for statistical analysis output format in `tests/contract/test_stats_output.py`. **Verification**: Assert `data/results/statistical_report.txt` contains required fields (p-value, test_type, method_comparison).
- [X] T024 [US3] Integration test for full baseline comparison in `tests/integration/test_baselines.py`. **Verification**: Assert `data/results/full_baseline_metrics.json` exists and contains keys `perplexity`, `exact_match`. **Note**: This test must be written first and verified to fail (artifact missing) before T025 is implemented.

### Implementation for User Story 3

- [X] T025 [US3] Implement full attention baseline runner in `code/evaluation/run_baselines.py` (FR-005). **Output**: `data/results/full_baseline_metrics.json`.
- [X] T026a [US3] Implement learned sparse (RTPurbo) baseline runner to **execute multiple independent random seeds** and save **per-document scores** to `data/intermediate/baseline_seeds/seed_{seed}_per_doc.json` (FR-008/FR-006). **Mechanism**: Use `random.seed={seed}` for each of the 5 iterations. **Seeds**: Use fixed seeds `[42, 123, 456, 789, 101]`. **Constraint**: Must use the **same fixed document subset** (from T014) for all 5 seeds to ensure paired t-test validity. **Output**: Raw per-document results for each seed. **Schema**: `[{document_id, metric_name, value}]`. **Verification**: Assert schema matches T029 requirements for paired t-test.
- [X] T026b [US3] Implement aggregation logic to compute **mean and variance** of the seed results from T026a and save to `data/results/baseline_aggregated.json`. **Schema**: `{mean_metric, std_metric, n_seeds, seed_values: []}` (FR-008). **Verification**: Assert aggregation logic matches manual calculation on a small subset. **Dependency**: T026a must complete before T026b.
- [X] T027 [US3] Implement static heuristic sparsification runner in `code/evaluation/run_baselines.py` (FR-005). **Input**: Rules from T020. **Output**: **Per-document** Perplexity and Exact Match metrics to `data/intermediate/static_per_document.json`. **Schema**: `[{document_id, perplexity, exact_match}]`. **Requirement**: Document IDs must match those in T026a for paired t-test. **Verification**: Assert schema matches T029 requirements and ID alignment.
- [X] T027b [US3] Implement aggregation logic to compute **mean and variance** of the static evaluation results from T027 and save to `data/results/static_eval_aggregated.json`. **Schema**: `{mean_metric, std_metric}`. **Dependency**: T027. **Verification**: Assert aggregation logic matches manual calculation on a small subset.
- [X] T029 [US3] Implement paired t-test/Wilcoxon test for statistical significance in `code/evaluation/stats_analysis.py` (FR-006). **Input**: Raw per-document scores from T026a (`data/intermediate/baseline_seeds/`) and T027 (`data/intermediate/static_per_document.json`). **Logic**: Read all `seed_{seed}_per_doc.json` files, merge them into a single paired dataset using `document_id` as the key (averaging the 5 seeds for the learned baseline per document), then perform a paired t-test on document-level performance differences between Static and Learned Sparse. **Library**: Use `scipy.stats.ttest_rel`. **Missing Data**: Exclude document pairs where either score is missing. **Requirement**: Must perform a **paired t-test on document-level performance differences** between Static and Learned Sparse using the raw per-document data, NOT aggregated means. **Dependency**: T026a and T027 must complete before T029.
- [X] T031a [US3] Create configuration file `data/config/threshold.yaml` defining the performance drop threshold. **Content**: `drop_threshold: 0.01`. **Verification**: Assert `data/config/threshold.yaml` exists and contains `drop_threshold: 0.01`.
- [X] T031 [US3] Implement Falsifiability Check: Calculate the performance drop `(Learned_Mean - Static_Mean) / Learned_Mean` using metrics from T026b and T027b, compare against the threshold read from `data/config/threshold.yaml`, and log the boolean result and exact drop percentage to `data/results/metrics.csv`. **Safeguard**: Include a **zero-division guard**: if `Learned_Mean` is near zero (< 1e-6), log an error and skip the calculation to prevent pipeline crash. **Dependencies**: T027b, T026b, T031a. **Note**: This task uses aggregated means for the drop check, while T029 uses raw data for the statistical test. **Dependency**: T026b must complete before T031.
- [X] T030 [US3] Generate final evaluation report at `data/results/final_report.md` containing: Perplexity, Exact Match, P-values, and Statistical Significance (SC-002, SC-004). **Required Sections**: Executive Summary, Methodology, Results Table, Statistical Significance. **Dependencies**: T025, T026b, T027b, T029, T031, T032b.
- [X] T032 [US3] Implement pipeline timing instrumentation to log start/end timestamps to `data/results/timing_report.json`.
- [X] T032b [US3] Implement post-execution check script in `code/evaluation/check_timing.py` that reads `timing_report.json` and asserts duration < 21600s (6 hours). **Scope**: The duration MUST include **total pipeline time (including data download)** as per SC-005. Log result to `data/results/timing_report.json`. **Verification**: Assert script exits with code 0 if duration < 21600s.
- [X] T033a [US3] [FR-008] [SC-006] Implement **Gemma-2 Ground Truth Generator** in `code/evaluation/cross_model_gt.py`. **Input**: RULER sample (from T011). **Sampling**: Use a **fixed sample of N=50 documents** to fit RAM. **Output**: `data/intermediate/gemma2_attention_maps.h5`. **Constraint**: Sample an initial subset of documents to fit RAM. **Dependency**: T011, T012 (pattern). **Note**: Does NOT depend on T020 (Rules) for generation.
- [X] T033 [US3] [FR-008] [SC-006] Implement **Cross-Model Validation** runner in `code/evaluation/cross_model_eval.py` to apply the derived static rules (from T020) to a **Gemma-2-9B** attention map subset (from T033a) and record performance drop (FR-008, SC-006). **Constraint**: Must use the sampled subset; must explicitly log generalizability metrics. **Dependency**: T020, T033a.
- [X] T034 [US3] Implement **Cross-Model Aggregation** script in `code/evaluation/cross_model_stats.py` to compare Llama-3-8B vs Gemma-2 static performance and log the cross-model stability metric to `data/results/cross_model_report.json`. **Metric Formula**: `mean(|Perplexity_Llama - Perplexity_Gemma|)`. **Schema**: `{mean_diff, std_diff, n_docs}`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `quickstart.md` and `research.md`.
- [ ] T036 Code cleanup and refactoring of data loading logic.
- [ ] T037 Performance optimization for streaming pipeline.
- [ ] T038 [P] Additional unit tests for edge cases in `tests/unit/`.
- [ ] T039 Run quickstart.md validation to ensure reproducibility on free tier.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **T005/T006 block all user stories**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/intermediate/merged_dataset.csv` from T014)
- **User Story 3 (P3)**: Depends on US1 and US2 completion (requires derived rules and baselines)

### Within Each User Story

- **Test-Implementation Order**: For US3 specifically, T023 and T024 (Tests) are strict prerequisites. They must be written, run, and verified to fail before T025-T032 (Implementation) begin. This ensures the contract is defined before coding. For US1 and US2, tests are optional parallel tasks.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T007/T008 in Phase 2 can run in parallel with T005/T006 (but T005/T006 are critical path)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for US1 and US2 marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T033a and T033 (Cross-Model) are NOT parallel with T020 (Rules) due to explicit dependency.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for feature extraction logic in tests/unit/test_feature_extraction.py"
Task: "Integration test for ground truth generation on small sample in tests/integration/test_ground_truth.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement RULER dataset downloader with streaming support in code/data/download.py"
Task: "Implement static feature computation in code/data/compute_features.py"
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Evaluation + Cross-Model)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except US3 tests which are sequential)
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Flow**: T011 -> T012 -> T015 -> T013 -> T014 -> T019 -> T019b -> T019c -> T020 -> T027 -> T027b -> T029 -> T031 -> T030.
- **Learned Baseline Flow**: T011 -> T012 -> T026a (5 seeds) -> T026b (Aggregate) -> T029 (Raw pairing) / T031 (Mean comparisons).
- **Static Evaluation Flow**: T020 -> T027 (Per-doc) -> T027b (Aggregate) -> T029 (Raw pairing) / T031 (Mean comparisons).
- **Cross-Model Flow**: T011 -> T033a (Gemma GT) -> T020 (Rules) -> T033 (Eval) -> T034 (Aggregate).
- **Dependencies**:
 - T013 depends on T012 (anomaly exclusion) and T015 (edge cases).
 - T014 depends on T012 (anomaly exclusion).
 - T019 depends on T014 (merged dataset).
 - T029 depends on T026a (raw learned) and T027 (raw static) for paired t-test. **T029 also depends on T026a and T027 completion** to ensure raw data is available.
 - T031 depends on T026b (learned mean), T027b (static mean), and T031a (threshold config). **T031 must complete before T030**.
 - T030 depends on T029 (p-value), T031 (drop check), T032b (timing).
 - **T033a depends on T011/T012 (pattern)**. T033 depends on T020 and T033a.
 - **T025-T032 depend on T023 and T024 being written and failing.**
 - **T031a must be completed before T031**.
 - **T024 must be written and verified to fail before T025 begins.**