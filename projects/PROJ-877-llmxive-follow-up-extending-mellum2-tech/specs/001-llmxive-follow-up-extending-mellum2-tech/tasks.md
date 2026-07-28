# Tasks: llmXive follow-up: extending "Mellum2 Technical Report"

**Input**: Design documents from `/specs/001-llmxive-complexity-loss/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Setup & Feasibility (Blocking Prerequisites)

**Purpose**: Project initialization and feasibility check. **T011 MUST run before T015.**

**⚠️ CRITICAL**: No user story work can begin until T011 completes successfully.

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/` root, `code/`, `data/`, `tests/` directories.
 - **Action**: Create all required directories in one execution.
 - **Artifact**: `project_init.log` containing `ls -R` output of the new directory structure.
- [X] T002 Create `requirements.txt` with exact versions for datasets, transformers, tree-sitter, codeql, scikit-learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm, pwlf, ruptures
- [ ] T003 [P] Create `.gitignore` and `README.md` with project overview
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools
- [X] T005 [P] Implement `code/config.py` with paths, random seeds, and hyperparameter defaults
- [X] T006 [P] Setup `data/` subdirectories (`raw/`, `processed/`, `results/`) with SHA-256 checksumming utilities in `code/data/checksum.py`
- [X] T007 [P] Implement robust error handling and logging infrastructure in `code/utils/logging.py` (must handle parse errors, timeouts, OOMs gracefully as per Edge Cases)
- [ ] T008 Create base entity schemas (`CodeChunk`, `Threshold`, `CorrelationResult`) in `code/contracts/` with explicit field definitions
- [ ] T009 [P] Setup environment configuration management (`.env` handling for HF token)
- [X] T010 [P] Implement timeout enforcement and benchmarking logic in `code/utils/timeout.py` to enforce a fixed per-chunk duration constraint (FR-003); must raise `TimeoutError` on breach.
- [X] T011 [US1] Implement `code/analysis/feasibility.py` (Pilot Sample & Feasibility Check):
 - **Input**: Fetch metadata only (N=50) of code chunks from `codeparrot/github-code` (Python/Java) using `datasets.load_dataset(..., streaming=True).take(50)` to estimate complexity variance WITHOUT downloading full files.
 - **Dependency**: **MUST run BEFORE T015** (Download).
 - **Action**: Estimate effect size and variance from metadata. Compute required sample size N to achieve **0.8 statistical power** within the **-hour total pipeline limit** (Plan Phase 0 summary).
 - **Gate**:
 1. If calculated N > max feasible chunks for 6h limit: **Cap N** to the maximum feasible size.
 2. Write `data/results/feasibility_report.json` with:
 - `status: "capped"`
 - `capped_N: <int>` (the max feasible size)
 - `power_limitation: "Study underpowered; capped to max feasible"`
 - `proceed_flag: true` (signals T015 to proceed)
 3. **DO NOT exit**. Log "WARNING: Study underpowered; capping N to max feasible" and proceed.
 - **Artifact**: `data/results/feasibility_report.json` (with `status: "capped"` or `status: "feasible"`).
 - **Constraint**: **NO full dataset download** in this task. Use metadata estimates only.
 - **Note**: T021 (Orchestration) MUST verify existence of `data/results/feasibility_report.json` before triggering T015.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 1: User Story 1 - Correlation Analysis of Code Complexity and Prediction Loss (Priority: P1) 🎯 MVP

**Goal**: Download code, label with static analysis, run frozen LLM inference, compute correlations, and generate scatter plots.

**Independent Test**: The system can be fully tested by executing the data pipeline on a fixed sample of repositories and verifying that a correlation coefficient (Pearson/Spearman) is computed and a scatter plot is generated, regardless of the specific value of the correlation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Add `tests/unit/test_download.py::test_download_handles_network_timeout` and `tests/unit/test_download.py::test_download_handles_empty_dataset`.
- [X] T013 [P] [US1] Add `tests/unit/test_preprocess.py::test_preprocess_skips_unparseable_files` and `tests/unit/test_preprocess.py::test_preprocess_handles_syntax_errors`.
- [X] T014 [P] [US1] Add `tests/unit/test_inference.py::test_inference_handles_timeout` and `tests/unit/test_inference.py::test_inference_handles_oom`.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/download.py` to fetch `codeparrot/github-code` subset (Python/Java) with streaming to stay within Disk storage constraints.
 - **Dependency**: **T011** (Feasibility passed).
 - **Logic**:
 1. Read `capped_N` from `data/results/feasibility_report.json`.
 2. Fetch dataset based on sample size N.
 3. **Enforce Strict Limit**: `take(capped_N)` from the dataset stream. If fetch returns > capped_N, truncate immediately.
 4. Split immediately into `data/processed/train_python/` and `data/processed/val_java/` based on language metadata.
 - **Constraint**: MUST fail loudly on fetch error. If fetch fails, log "ERROR: Failed to fetch dataset: <reason>" and execute `sys.exit(1)`. No synthetic fallback.
 - **Artifact**: `data/processed/train_python/`, `data/processed/val_java/`.

- [ ] T016 [US1] Implement `code/data/preprocess.py` to run CodeQL and tree-sitter.
 - **Dependency**: **T015** (Download/Split).
 - **Logic**: Create `queries/complexity.ql` for cyclomatic complexity, nesting depth, and repetition ratio. Process files in `data/processed/train_python/` and `data/processed/val_java/`.
 - **Edge Case**: MUST skip unparseable files and log errors (Edge Case 1).
 - **Artifact**: `data/processed/annotated_python.jsonl`, `data/processed/annotated_java.jsonl`.

- [ ] T011b [US1] Implement `code/analysis/variance_check.py` (Variance Detection & Graceful Degradation):
 - **Dependency**: **T015** (Download) and **T016** (Preprocess).
 - **Action**: Load `data/processed/annotated_python.jsonl` and `data/processed/annotated_java.jsonl`. Compute variance of `cyclomatic_complexity` and `nesting_depth`.
 - **Logic**: If variance == 0 for any metric, write `data/results/variance_null_report.json` with `status: "null_variance"`, `metric: <name>`, and `message: "No variance detected; skipping correlation analysis"`. **Log warning but DO NOT exit** (allows T020 to handle the final result).
 - **Artifact**: `data/results/variance_null_report.json` (if null) OR proceed to T018.
 - **Traceability**: Addresses Spec Edge Case: "How does system handle a dataset where the complexity metrics are constant".

- [ ] T018 [US1] Implement `code/data/ngram.py` to build KenLM n-gram model (Producer for T017).
 - **Dependency**: **T016** (Preprocess).
 - **Logic**: Build n-gram model from **ONLY** `data/processed/train_python/` (Training Set) using KenLM. **n-gram order=5**.
 - **Constraint**: **DO NOT** include `data/processed/val_java/` to prevent data leakage. This ensures the validation set remains "held-out" for cross-language consistency checks.
 - **Artifact**: `data/processed/kenlm_model.arpa`.

- [ ] T017 [US1] Implement `code/inference/engine.py` to run frozen LLM (Mistral-7B) with retry logic, n-gram normalization, and OOM fallback.
 - **Dependency**: **T018** (N-Gram model ready - PRIMARY GATE).
 - **Constraint**: MUST load model with **`device='cpu'`** and **`torch.set_num_threads()`** to enforce CPU-only execution (FR-003).
 - **Model Strategy**:
 1. **PRIMARY**: Attempt to load `mistralai/Mistral-7B-v0.1`.
 2. **FALLBACK**: If `RuntimeError` (OOM) occurs, **IMMEDIATELY** log "OOM detected; switching to TinyLlama fallback" and load `TinyLlama/TinyLlama-1.1B-Chat-v1.0` with `device='cpu'` and `max_memory` constraints. **DO NOT** raise `RuntimeError`.
 - **Retry Logic**: On `TimeoutError`, `ConnectionError`, or `OSError` (non-OOM), retry up to 3 times with `backoff_factor=2`. If all retries fail, skip chunk and log failure.
 - **Normalization**:
 1. **LOAD** pre-built kenlm n-gram model from `data/processed/kenlm_model.arpa` (produced by T018). **DO NOT BUILD** here.
 2. **Compute Normalized Loss**: For each token, calculate `normalized_loss = token_loss - ngram_log_prob`, where `token_loss` is the raw loss field from the model output and `ngram_log_prob` is the log-probability of the token sequence derived from the KenLM model.
 3. **Store**: Write `normalized_loss` to the output artifact.
 - **Artifact**: `data/processed/inference_results_python.jsonl`, `data/processed/inference_results_java.jsonl` (fields: `chunk_id`, `token_loss`, `entropy`, `normalized_loss`).

- [ ] T019 [US1] Implement `code/analysis/correlation.py` to compute Pearson/Spearman coefficients.
 - **Dependency**: **T017** (Inference).
 - **Logic**: Use normalized loss from T017. Compute correlations.
 - **Artifact**: `data/results/us1_correlation_stats.json`.

- [ ] T020 [US1] Implement `code/analysis/correlation.py` visualization.
 - **Dependency**: **T019**.
 - **Logic**:
 1. **Variance Check**: Re-check variance of metrics.
 2. **Edge Case Handling**: If variance is zero:
 - Write `data/results/us1_correlation_stats.json` with `status: "no_correlation"`, `message: "No variance detected; no correlation computed"`.
 - Write `data/results/variance_null_report.json` (if not already written by T011b).
 - **Exit with code 0** (graceful degradation).
 3. **Normal Path**: Generate scatter plot with regression line using `seaborn.regplot`.
 - **Artifact**: Save plot to `data/results/us1_correlation_plot.png` (if variance > 0).
 - **Stratification**: Generate separate plots/stats for Python and Java sets.

- [ ] T021 [US1] Implement `code/main.py` pipeline orchestration.
 - **Logic**: Ensure strict order: **Feasibility (T011) -> Download (T015) -> Preprocess (T016) -> Variance Check (T011b) -> N-Gram (T018) -> Inference (T017) -> Correlation (T019) -> Visualization (T020) -> Threshold Detection (T024-T027) -> Statistical Significance (T029-T031) -> Perturbation (T026) -> Output (T032)**.
 - **Dependency**: Must **explicitly wire T010 timeout logic into T017 execution flow**.
 - **Dependency**: Must ensure **T024** (Threshold) runs after **T019** (Correlation).
 - **Dependency**: Must ensure **T029** (Permutation) runs after **T019** (Correlation).
 - **Dependency**: Must ensure **T026** (Perturbation/Sensitivity) runs after **T024** (Threshold Detection) and **T019** (Correlation).
 - **Dependency**: Must ensure **T031** (Validation) runs after **T019** (Correlation).
 - **Dependency**: Must verify existence of `data/results/feasibility_report.json` before triggering T015.

- [ ] T022 [US1] Implement `code/analysis/correlation.py` extension for cross-language validation.
 - **Logic**: Compare correlation coefficients between Python (train) and Java (val) sets.
 - **Artifact**: Append cross-language comparison stats to `data/results/us1_correlation_stats.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Correlation computed, plot generated, held-out validation complete).

---

## Phase 2: User Story 2 - Non-Linear Threshold Detection (Priority: P2)

**Goal**: Identify structural thresholds where complexity/loss relationship shifts and perform sensitivity analysis.

**Independent Test**: The system can be tested by running the change-point detection on the P1 output and verifying that either a threshold value is identified OR a linear model is preferred (AIC/BIC difference > 2), and a sensitivity analysis is performed.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Add `tests/unit/test_threshold.py::test_piecewise_regression_handles_linear_data` and `tests/unit/test_threshold.py::test_piecewise_regression_detects_breakpoint`.

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/analysis/threshold.py` to apply piecewise regression/change-point detection on US1 correlation data (FR-005).
 - **Input**: `data/results/us1_correlation_stats.json`.
 - **Artifact**: `data/results/us2_threshold_candidates.json`.

- [ ] T025 [US2] Implement logic in `code/analysis/threshold.py` to compare linear vs. non-linear models using AIC/BIC and report preference.
 - **Artifact**: Append `model_preference` to `data/results/us2_threshold_candidates.json`.

- [ ] T026 [US2] Implement `code/analysis/threshold.py` sensitivity analysis (SC-002) and threshold sweep (FR-006).
 - **Dependency**: **T024** (Threshold candidates identified).
 - **Logic**:
 1. **Step A: Fixed Perturbation Sweep (SC-002)**:
 - **Import** the threshold detection function from `code/analysis/threshold.py` (T024) to avoid code duplication.
 - Apply a **FIXED perturbation magnitude of 0.05 units** to the complexity metric (e.g., shift threshold by ±0.05).
 - Re-run the threshold detection algorithm from T024 on the perturbed data.
 - Calculate the observed shift in the identified threshold value (delta).
 - **Output**: `threshold_shift_observed` (the delta value) and `perturbation_magnitude_applied: 0.05`.
 2. **Step B: Dataset Perturbation (SC-002)**:
 - **Bootstrap 1000 (2309.06305, https://arxiv.org/abs/2309.06305) samples** of the dataset (resampling chunks with replacement).
 - For each sample, re-run the threshold detection algorithm from T024 (imported function).
 - Calculate the shift in the identified threshold value relative to the original.
 - **Output**: `dataset_perturbation_shifts`.
 - **Constraint**: Report the observed shift magnitude. **DO NOT** derive a dynamic perturbation magnitude; use the fixed 0.05 units as required by SC-002.
 - **Artifact**: Append `threshold_shift_observed`, `perturbation_magnitude_applied: 0.05`, `dataset_perturbation_shifts` to `data/results/us2_threshold_candidates.json`.

- [ ] T027 [US2] Implement `code/analysis/threshold.py` to generate a report.
 - **Format**: Markdown file at `data/results/us2_threshold_report.md`.
 - **Sections**:
 1. `# Threshold Value` (Identified value)
 2. `# Sensitivity Sweep Results` (Table of shifts from bootstrapping)
 3. `# Justification` (Data distribution or community standards)
 - **Artifact**: `data/results/us2_threshold_report.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Thresholds identified, sensitivity report generated).

---

## Phase 3: User Story 3 - Statistical Significance and Power Validation (Priority: P3)

**Goal**: Perform permutation tests, power analysis, and multiple-comparison correction.

**Independent Test**: The system can be tested by running the permutation test (shuffling labels) and verifying that a p-value is calculated and reported, along with a statement on statistical power.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Add `tests/unit/test_stats.py::test_permutation_test_shuffles_labels` and `tests/unit/test_stats.py::test_permutation_test_computes_pvalue`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/stats.py` for cluster-robust permutation test (block permutation at repo level) to compute p-values (FR-007).
 - **Artifact**: `data/results/us3_permutation_pvalue.json`.

- [ ] T030 [US3] Implement `code/analysis/stats.py` for multiple-comparison correction (Bonferroni/FDR) on hypothesis tests (FR-008).
 - **Artifact**: `data/results/us3_corrected_pvalues.json`.

- [ ] T031a [US3] Implement `code/analysis/stats.py` for Power Analysis.
 - **Dependency**: **T019** (Correlation results) and **T029** (Permutation results).
 - **Logic**: Calculate post-hoc statistical power based on observed effect size, sample size, and significance level (alpha=0.05 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics))).
 - **Artifact**: `data/results/us3_power_analysis.json` with `power_value`, `effect_size`, `sample_size`, and `limitation_notes`.

- [ ] T031 [US3] Implement `code/analysis/validation.py` to validate against CodeXGLUE benchmark.
 - **Source**: `codeparrot/codeXGLUE` (split: `test`).
 - **Logic**:
 1. **If CodeXGLUE available**: Load it, compute Pearson r between proxy metrics and CodeXGLUE labels, write to `data/results/us3_validation_result.json` with `status: "validated"`.
 2. **If CodeXGLUE missing**: **HARD REQUIREMENT: Per FR-011, proceed with fallback.** Log "WARNING: CodeXGLUE benchmark unavailable; executing Validation Fallback Phase". Write `data/results/us3_validation_result.json` with `status: "missing_benchmark"`, `limitation: "CodeXGLUE unavailable; relying on internal permutation tests"`, and `proceed_flag: true`. **DO NOT** raise `RuntimeError` or `sys.exit(1)`.
 - **Artifact**: `data/results/us3_validation_result.json`.

- [ ] T031b [US3] Implement `code/analysis/validation.py` to generate limitation report if benchmark is missing.
 - **Dependency**: **T031** (Must detect missing benchmark).
 - **Logic**:
 1. Read `data/results/us3_validation_result.json`.
 2. If `status == "missing_benchmark"`, generate a detailed limitation report in `data/results/us3_limitation_report.md`.
 3. If `status == "validated"`, skip this task.
 - **Artifact**: `data/results/us3_limitation_report.md` (if triggered).

**Checkpoint**: All user stories should now be independently functional (Significance, Power, and Cross-language validation complete).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `README.md` and `docs/`
- [ ] T033a [P] Refactor `code/analysis/correlation.py`: Extract complex correlation logic into a dedicated function `compute_correlation_matrix(...)` to ensure **max cyclomatic complexity < 10**.
- [ ] T033b [P] Refactor `code/analysis/threshold.py`: Simplify threshold detection logic by extracting the AIC/BIC comparison into a separate function `compare_models(...)` to ensure **max cyclomatic complexity < 10**.
- [ ] T034 Performance optimization (ensure the specified latency limit is met with streaming/chunking)
- [ ] T035 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation
- [ ] T037 Update `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with data checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup & Feasibility)**: No dependencies - can start immediately
 - **T011 (Feasibility)**: MUST run BEFORE T015 (Download).
- **Phase 1 (User Story 1)**: Depends on Phase 0 completion
 - **T015**: Depends on T011 (Feasibility passed).
 - **T016**: Depends on T015.
 - **T011b**: Depends on T016 and MUST run BEFORE T018.
 - **T018**: Depends on T016.
 - **T017**: Depends on T018 (N-Gram model ready - PRIMARY GATE).
 - **T019**: Depends on T017.
 - **T020**: Depends on T019.
 - **T021**: Orchestrates all above.
 - **T022**: Depends on T019.
- **Phase 2 (User Story 2)**: Depends on Phase 1 completion (T019 output)
 - **T024**: Depends on T019.
 - **T025**: Depends on T024.
 - **T026**: Depends on T024 (Threshold candidates) and T019 (Correlation data).
 - **T027**: Depends on T026.
- **Phase 3 (User Story 3)**: Depends on Phase 1 completion (T019 output)
 - **T029**: Depends on T019.
 - **T030**: Depends on T029.
 - **T031**: Depends on T019.
 - **T031a**: Depends on T019 and T029.
 - **T031b**: Depends on T031.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 0 (Feasibility passed)
- **User Story 2 (P2)**: Depends on US1 data output (T019)
- **User Story 3 (P3)**: Depends on US1 data output (T019)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] can run in parallel (except T011 which blocks Phase 1)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Add tests/unit/test_download.py::test_download_handles_network_timeout"
Task: "Add tests/unit/test_preprocess.py::test_preprocess_skips_unparseable_files"

# Launch all models for User Story 1 together:
Task: "Create base entity schemas in code/contracts/"
Task: "Setup logging infrastructure in code/utils/logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup & Feasibility (CRITICAL - blocks all stories, includes Feasibility Check T011 and Variance Check T011b)
2. Complete Phase 1: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently (Correlation & Plot)
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Thresholds)
4. Add User Story 3 → Test independently → Deploy/Demo (Significance)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
 - Developer A: User Story 1 (Core Pipeline)
 - Developer B: User Story 2 (Thresholds)
 - Developer C: User Story 3 (Stats)
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
- **Data Integrity**: All data loading tasks MUST fail loudly on real fetch errors; no synthetic fallbacks allowed.
- **Compute Constraints**: All inference tasks must be optimized for CPU-only execution within 6h/GB limits; streaming is mandatory for large datasets.
- **Feasibility**: T011 ensures the sample size is feasible before full inference runs. **Capping** logic implemented if infeasible.
- **Variance**: T011b ensures graceful degradation if complexity metrics lack variance.
- **N-Gram**: T018 uses training data only to prevent leakage.
- **Fallback**: T017 and T031 implement required fallback strategies.
- **Normalization**: T017 uses explicit formula `normalized_loss = token_loss - ngram_log_prob`.
- **Perturbation**: T026 uses fixed 0.05 unit perturbation.
- **Power**: T031a implements post-hoc power analysis.

## Constitution Check (Revised for SC-002 Compliance)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `random.seed()` pinned in all scripts; `requirements.txt` with exact versions; dataset fetched from canonical HF source; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be validated by the **Reference-Validator Agent** against the `# Verified datasets` block before proceeding to implementation. |
| **III. Data Hygiene** | PASS | `data/` files checksummed; raw data immutable; derived data in new files; PII scan in CI. |
| **IV. Single Source of Truth** | PASS | All figures/stats in paper trace to `data/` rows via script output logs. |
| **V. Versioning Discipline** | PASS | A CI job computes **SHA-256** hashes of all files in `data/` and updates `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with these hashes. |
| **VI. Static Analysis Inference Independence** | PASS | Pipeline stages strictly ordered: 1. Feasibility, 2. Download, 3. Static Analysis, 4. N-Gram (Train Only), 5. LLM Inference (frozen). No feedback loop. |
| **VII. Non-Linear Threshold Detection Rigor** | PASS | Plan includes piecewise regression/change-point detection (not just linear) and sensitivity analysis with explicit **fixed 0.05 unit perturbation** (SC-002) and **observed shift reporting**. |