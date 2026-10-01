---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Moebius: A Lightweight Image Inpainting Framework with Large-Scale Parameters (, https://arxiv.org/abs/2606.19195)"

**Input**: Design documents from `/specs/001-llmxive-moebius-dynamic/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` by executing `mkdir -p projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/{code/{data,models,training,eval,utils},data/{raw,processed,annotations,results},specs/001-llmxive-moebius-dynamic,tests/{unit,integration},docs,paper,state/projects}` and creating empty `__init__.py` files in all Python directories (e.g., `touch projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/__init__.py`).
- [X] T002 Initialize a Python project with PyTorch (CPU-only), scikit-learn, pillow, numpy, pandas, scipy, datasets, lpips, torchmetrics, torchvision dependencies in `projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/requirements.txt`. **Content**: Pin `torch==2.1.0+cpu`, `scikit-learn==1.3.0`, `pillow==10.0.0`, `numpy==1.24.0`, `pandas==2.0.0`, `scipy==1.11.0`, `datasets==2.14.0`, `lpips==0.1.4`, `torchmetrics==1.1.0`, `torchvision==0.16.0+cpu`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [X] T004 Implement `projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/code/config.py` with seeds, paths, hyperparameters, and mode flags. **Schema**: `seed: int = 42`, `mode: str = 'CI'` (options: 'CI', 'RESEARCH'), `dataset_paths: dict`, `hash_registry: dict`, `ram_limit_gb: float = 7.0`, `chunk_size: int = 1024`, `sample_size: int = 500`.
 - [X] T004b [P] [US1] Extend `code/config.py` to include `dataset_paths` (dict) and `hash_registry` (dict) keys for data integrity tracking.
- [X] T005 [P] Implement `code/utils/seed.py` for deterministic seeding across all libraries
- [X] T006 [P] Implement `code/utils/cpu_profiler.py` for CPU-specific timing utilities (`time.perf_counter`)
- [X] T007 Create base data model classes (`MaskedRegion`, `InferenceResult`, `GatingState`) in `code/models/data_models.py`
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [X] T009 [US1] Implement `code/utils/config_validator.py` to validate `dataset_paths` existence and `hash_registry` integrity against `config.py` values. **Dependency**: Must run after T004b.
- [X] T020 [P] [US2] Implement `code/models/moebius_tiny.py` (Simplified CPU version, ≤15M params total) - **Moved to Phase 2 to ensure code availability before gating**.
- [X] T044 [P] [US1] Implement `code/data/streaming_loader.py` to handle large-scale dataset ingestion via `datasets.load_dataset(..., streaming=True)` with chunked processing for memory safety. **Dependency**: T004. **Logic**: **MUST** fetch and checksum the FULL real dataset first (using `datasets.load_dataset` without streaming to verify integrity, then store hash). Sampling (via `itertools.islice`) is ONLY for CI memory constraints. Must explicitly state the sampling rule (e.g., `itertools.islice(first N rows)`) where N is `config.sample_size` (default 500) and log the exact sample size and representativeness limitation in `data/results/streaming_log.txt`. **Constraint**: If the full dataset cannot be processed within RAM, the task must explicitly state this limitation and use the sampled subset ONLY for CI, never replacing the full dataset in Research Mode.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Human Complexity Annotation (Priority: P1) 🎯 MVP

**Goal**: Ingest Places2/CelebA-HQ, generate synthetic masks, and establish ground truth (Human or Decoupled Synthetic Proxy) without circularity.

**Independent Test**: Verify existence of masked dataset and CSV of scores with no model inference used to generate labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for mask generation metrics (gradient variance, entropy) in `tests/unit/test_mask_generator.py`
- [X] T011 [P] [US1] Integration test for data pipeline independence (no model inference in label gen) in `tests/integration/test_data_independence.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/loader.py` to fetch Places365 subset from HuggingFace (`mit-places/Places365`) with checksum verification. **Constraint**: Raise `SystemExit` if real data fetch fails; NO synthetic fallback.
- [X] T013 [P] [US1] Implement `code/data/mask_generator.py` to create synthetic masks with varying complexity; record `gradient_variance` and `texture_entropy`. **Dependency**: T012.
- [X] T014 [US1] Implement `code/data/annotator.py` to provide CLI/JSON interface for crowdsourcing structure
 - [ ] T014a [US1] **CI Mode**: Generate `data/annotations/decoupled_scores.csv` with columns `[image_id, score, mode, seed_used]`. **Dependency**: T013. **Logic**: Verify `data/processed/mask_metrics.json` exists. If missing, raise `FileNotFoundError`. Use `np.random.seed(config.seed)` and generate scores via `np.random.uniform(1, 5, size=50)` strictly decoupled from synthetic mask metrics. **INDEPENDENCE CHECK**: Do NOT compute correlation between generated scores and mask metrics to ensure strict independence. Log the exact `config.seed` value used to `data/results/validation_log.txt` and include it in the CSV header. **Verification**: Log 'Scores generated with decoupled random seed' to `data/results/validation_log.txt`.
 - [X] T014b [US1] **Research Mode**: Implement logic to load external human-annotated CSV. Validate schema and integrity.
 - [ ] T014c [US1] **Research Mode Ingestion**: Implement the specific mechanism to ingest, manage, and validate real human participant data for 'Research Mode' as required by FR-002. **Input**: `data/annotations/human_scores.csv`. **Output**: `data/annotations/validated_scores.csv`. **Implementation**: `code/data/annotator.py::ingest_human_data`. **Validation**: Check schema (image_id, score, rater_id). **Error Handling**: If file missing AND `config.mode == 'RESEARCH'`, log `ERROR: Human annotation file missing. Research mode disabled.` to `data/results/validation_log.txt`, and **RAISE `SystemExit`** with code 1 to halt the pipeline. If `config.mode == 'CI'`, skip this check. **Verification**: Verify that running in RESEARCH mode without human_scores.csv logs the error, raises SystemExit, and prevents downstream tasks. **Warning**: Explicitly state in logs that without human data, the 'Human-Grounded' claim cannot be made.
 - [ ] T014e [US1] **Flow Control**: If CI Mode, skip T015 (IR) and explicitly log `[TIMESTAMP] [CI_MODE] Single-Rater Simulation: Ground truth decoupled from metrics. SIMULATION ONLY - DOES NOT SUPPORT HUMAN-GROUNDED CLAIMS.` to `data/results/validation_log.txt`. **CRITICAL**: Ensure `data/annotations/decoupled_scores.csv` includes a `mode` column set to 'CI_MODE' or 'SIMULATION_ONLY' to satisfy Constitution Principle IV. If Research Mode, **mark T015 as ready to execute** and proceed.
 - [X] T014f [US1] **Logging**: Log the outcome of T014e (mode decision) to `data/results/validation_log.txt`.
- [ ] T015 [US1] **Inter-Rater Reliability & Data Persistence**: Calculate Krippendorff's alpha on multi-rater scores using the `krippendorff` library. **Input**: `data/annotations/validated_scores.csv` (from T014c). **Implementation**: `code/eval/stats.py::calculate_krippendorff`. **Dependency**: T014c (Success). **Conditional**: Only run if `config.mode == 'RESEARCH'` and T014c succeeded. If `config.mode == 'CI'`, skip and log 'N/A'. **Library**: Use `krippendorff` package. **Function**: `krippendorff.alpha(data, level='ordinal')`. **Output**: Persist alpha value AND the raw score distribution (histogram) to `data/annotations/krippendorff_raw.json`. **JSON Schema**: `{ "alpha": float, "histogram": { "bins": [float], "counts": [int] } }`. Use `numpy.histogram` to generate bins/counts and serialize to JSON. Log alpha to `data/results/validation_log.txt`. **Merge**: This task replaces T014d and T015 to avoid redundancy. <!-- FAILED: unspecified -->
- [ ] T016 [US1] Add validation logic in `code/data/annotator.py` that raises an error if sample size < 50 or if label independence check fails. Log result to `data/results/validation_log.txt`.
- [X] T017 [US1] Persist masked images to `data/processed/masked_images/` and scores to `data/annotations/`. **Logic**: Use `os.makedirs(path, exist_ok=True)` to ensure directories exist. Save images as PNG and scores as CSV.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Synthetic Proxy Validation (Priority: P2) ⚠️ GATES US2

**Goal**: Validate that synthetic mask metrics correlate with ground truth BEFORE training the gating mechanism.

**Independent Test**: Compute Pearson correlation; flag if r < 0.7 (for human data) or log expected behavior (CI mode).

### Implementation for User Story 4

- [ ] T035 [P] [US4] Implement correlation analysis in `code/eval/stats.py` (Pearson between synthetic metrics and ground truth). **Implementation**: `code/eval/stats.py::validate_proxy_correlation`. **Dependency**: T014e. **Logic**: Use `scipy.stats.pearsonr` on `gradient_variance`/`texture_entropy` vs `score`. **Gate Logic**: If `config.mode == 'RESEARCH'` and r < 0.7, update `data/results/proxy_validation.json` with `gate_status: BLOCKED` and **raise `SystemExit`** with code 1 and message "GATE BLOCKED: Proxy correlation r < 0.7 in Research Mode." **Blocking Mechanism**: This `SystemExit` must be unconditionally raised to prevent ANY downstream training tasks (T023+) from executing. If `config.mode == 'CI'`, log expected low correlation behavior to `data/results/proxy_validation.json` with `gate_status: EXPECTED_LOW_CORRELATION` and **continue execution** (do not exit). **Note**: The absence of a gate in CI is a deliberate design choice to allow mechanism validation. **Output**: Save `r` value and `gate_status` to `data/results/proxy_validation.json`.
- [X] T037 [US4] **REMOVED**: Redundant task merged into T035.

**Checkpoint**: Proxy validation complete; gating mechanism training can proceed with confidence

---

## Phase 5: User Story 2 - Dynamic Rank Adjustment Mechanism Implementation (Priority: P2)

**Goal**: Implement "Moebius-Dynamic" architecture with lightweight gating head and dynamic rank modulation.

**Independent Test**: Run on single CPU core with low-complexity mask; verify reduced rank output.

**⚠️ GATE ENFORCEMENT**: Phase 5 tasks are BLOCKED until Phase 4 (US4) Gate (T035) passes with exit code 0. **Note**: T020 (Implementation) is now in Phase 2 to ensure code exists before gating.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for gating head output scalar range (lower bound to 5) in `tests/unit/test_gating_head.py`
- [X] T019 [P] [US2] Integration test for dynamic rank modulation logic in `tests/integration/test_dynamic_rank.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/models/gating_head.py` (Lightweight conv head, **≤5M parameters**) to output scalar complexity. **Verification**: Count parameters and fail if > 5M. **Constraint**: This implementation is the SINGLE SOURCE OF TRUTH for the parameter limit; do not duplicate logic elsewhere.
- [X] T022 [US2] Implement `code/models/moebius_dynamic.py` (Deliverable: `code/models/moebius_dynamic.py`) integrating gating head with $L\lambda MI$ linear matrices rank modulation logic. **Dependency**: T020. **Logic**: Map scalar score to rank indices.. **CI Mode**: Implement rank modulation logic specifically for the `Moebius-Tiny` model architecture (from T020). **Research Mode**: Implement rank modulation logic specifically for the full `Moebius 0.2B` model architecture (if memory permits) or a larger variant. **Memory Check**: Implement a check to verify if the model fits within 7GB RAM; if not, fallback to `Moebius-Tiny` and log `WARNING: Memory limit exceeded, falling back to Moebius-Tiny` to `data/results/validation_log.txt`. **Edge Case**: Handle interpolation for score=3 and fallback to static high-rank if mask > 50%.
- [ ] T023 [US2] Implement `code/training/train_gating.py` with multi-task loss (reconstruction + regression + rank classification). **Hyperparameters**: Loss weights = {reconstruction: dominant, regression: minor, rank: minor}. **Optimizer**: AdamW. **Dependency**: T035 (Gate Pass). **Critical**: This task MUST wait for T035 to complete successfully; if T035 exits, this task is skipped. **Note**: T023 depends on the *output artifact* (`data/results/proxy_validation.json`) of T035 to proceed. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T024 [US2] Implement `code/training/train_end_to_end.py` for fine-tuning
- [ ] T025 [US2] Implement permutation test logic in `code/eval/stats.py` to verify no overfitting (FR-008). **Implementation**: `code/eval/stats.py::run_permutation_test`. **Logic**: Run `n_permutations=1000` permutations, re-evaluate model, calculate p-value using `scipy.stats.permutation_test` with `alternative='two-sided'`. **Output**: Persist p-value and gate status to `data/results/permutation_test.json` regardless of success or failure.
 - [ ] T025a [US2] **Pre-Deployment Gate**: Implement a validation step that checks the permutation test p-value. **Implementation**: `code/eval/stats.py::check_permutation_gate`. **Logic**: Shuffle labels `n_permutations=1000` times, re-evaluate model, calculate p-value using `scipy.stats.permutation_test`. **Gate**: **If p <= 0.05**, the model has learned a signal distinct from random noise (success). **If p > 0.05**, the model has NOT learned the signal (failed to distinguish from random) and deployment is blocked. **Action**: If p > 0.05, raise `SystemExit` with code 1. **Output**: Persist p-value and gate status to `data/results/permutation_test.json`.
 - [ ] T025b [US2] **Persistence**: Explicitly persist the permutation test results (p-value, gate status, number of permutations) to `data/results/permutation_test.json` whether the gate passes or fails. **Dependency**: T025a.
 - [ ] T026 [US2] Save model weights to `code/models/moebius_dynamic.pt` and gating weights to `data/results/` **ONLY IF T025a gate passes**. **Logic**: Use `torch.save`. **Verification**: Check parameter count ≤ 5M. **Dependency**: Success of T025a gate. **Status**: Blocked by T025a.
**Status**: Blocked by T025a.

**Checkpoint**: At this point, User Stories 1, 4, AND 2 should all work independently

---

## Phase 5.5: Ablation & Causal Isolation (Priority: P3)

**Goal**: Isolate the efficiency gain from the prediction mechanism.

**Independent Test**: Run static model with forced low rank; compare with dynamic model.

**⚠️ DEPENDENCY**: This phase requires Phase 5 (T026) to be complete.

### Implementation for Phase 5.5

- [X] T032a [P] [US3] Implement counterfactual run logic in `code/eval/report.py`: Run static model with forced low rank (simulating dynamic outcome). **Dependency**: Completion of Phase 5 (T026). **Logic**: Force rank of LλMI matrices to 1 for all inputs to isolate the *prediction overhead* from the *reduction gain*.
 - [X] T032b [US3] Run comparison: (Dynamic Model) vs (Static Low Rank) vs (Static High Rank). **Logic**: Calculate latency reduction % and FID delta. **Output**: Save results to `data/results/ablation_comparison.csv`. **Dependency**: T026. **Status**: Blocked by T026.
 - [ ] T032c [US3] **Analyze prediction overhead vs. reduction gain and generate `data/results/ablation_report.json`**. **Implementation**: `code/eval/report.py::generate_ablation_report`. **Logic**: Compare (Dynamic Latency) vs (Static Low Rank Latency + Prediction Overhead). **Dependency**: T032b. **Output**: Generate `data/results/ablation_report.json` containing the analysis and the Spearman correlation coefficient. **Spearman Correlation**: Explicitly calculate and persist the Spearman correlation coefficient between ground truth complexity and effective model rank in `data/results/evaluation_report.json` as `spearman_correlation`. **Library**: `scipy.stats.spearmanr`. **Note**: T032c depends on T026 (which depends on T025a) and T032b.
 - [X] T032d [US3] **REMOVED**: Merged into T032c.
 - [X] T032e [US3] **Spearman Correlation**: **Merged into T032c**.
 - [X] T032f [US3] **Static High Rank Baseline**: Implement the 'Static High Rank' baseline runner to force rank to max for all inputs, ensuring the ablation comparison includes the full baseline as required by Plan Phase 3.5. **Dependency**: T026.
 - [X] T032g [US3] **Spearman Correlation Implementation**: **Merged into T032c**.

**Checkpoint**: Ablation complete; evaluation report can now be generated with full data.

---

## Phase 6: User Story 3 - Efficiency and Fidelity Evaluation (Priority: P3)

**Goal**: Benchmark dynamic vs. static models on CPU for latency and quality.

**Independent Test**: Run evaluation script on held-out set; generate report comparing latency/FID.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for FID/LPIPS calculation on CPU in `tests/unit/test_metrics.py`
- [X] T028 [P] [US3] Integration test for statistical significance (t-test) in `tests/integration/test_stats_eval.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/eval/metrics.py` for FID, LPIPS, and wall-clock latency measurement (CPU only)
- [ ] T033a [P] [US3] **Run Inference**: Execute inference on test set across complexity bins; save raw latency metrics to `data/results/latency_raw.csv`. **Implementation**: `code/eval/inference.py::run_benchmark`. **Test Set Definition**: Use the **first 100 rows** of `data/annotations/decoupled_scores.csv` (CI Mode) or a **50% holdout** of `data/annotations/validated_scores.csv` (Research Mode). **Logic**: Ensure reproducibility by sorting by `image_id` before selection. **Output**: `data/results/latency_raw.csv`. **Dependency**: T032b and T026. **Note**: T033a depends on T032b (which depends on T026, which depends on T025a) and T026.
 - [ ] T033b [US3] **Verify Target**: Calculate latency reduction from `latency_raw.csv` against Static High Rank baseline. Verify ≥30% reduction for low-complexity regions (defined as images where `score <= 2.5` AND `rank_in_bin <= 33%` of the sorted complexity list). **Output**: Write `data/results/evaluation_report.json` with field `latency_reduction_pct`. **Dependency**: T033a. **Note**: T033b waits for the aggregation of all T033a parallel runs before processing.
- [ ] T030a [P] [US3] Implement `code/eval/stats.py` power analysis calculation (SC-005). **Logic**: Use `scipy.stats.power` for two-sample t-test, alpha=0.05, effect size=0.5. Output power value to `data/results/power_analysis.json`.
 - [ ] T030b [US3] **Decision Gate**: If power < 0.8, update `data/results/power_analysis.json` with `status: UNDERPOWERED` and **block further execution** or **require remediation** (e.g., re-sampling) before proceeding. If power ≥ 0.8, proceed. **Update**: Mark the statistical significance claim in the final report as INVALID if underpowered and no remediation is possible.
 - [X] T034 [US3] Verify FID difference ≤0.5 vs static baseline and statistical significance (p > 0.05) using paired t-test.
 - [ ] T034c [US3] **Statistical Significance Test**: Implement paired t-test logic in `code/eval/stats.py` for latency and FID differences. **Logic**: Use `scipy.stats.ttest_rel` (paired). **Decision**: If p < 0.05, mark as significant; else mark as not significant. **Output**: Persist p-values and decision to `data/results/statistical_significance.json`. **Dependency**: T033a, T032b. **Goal**: Confirm the claim of statistical significance (p > 0.05) as required by US3.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `paper/draft.md` with mode labeling (CI vs Research). **Action**: Append Section 4.1 to `paper/draft.md` with content from `data/results/evaluation_report.json`, explicitly labeling results as 'CI Simulation' or 'Research Mode'. **Status**: Pending until T043 generates the draft.
- [ ] T039 [P] Code cleanup and refactoring. **Action**: Refactor `code/eval/metrics.py` to extract the FID calculation logic into a standalone function `calculate_fid_chunked()` to improve modularity and testability.
- [ ] T040 [P] Performance optimization (chunked processing for FID/LPIPS to stay within 7GB RAM). **Action**: Refactor `code/eval/metrics.py` to process images in chunks of a defined size. **Trigger**: If system RAM usage > 6GB (measured via `psutil`), switch to chunked processing.
- [X] T041a [P] [US2] Create unit test `test_gating_head_output_range` in `tests/unit/test_gating_head.py` to verify scalar range (positive integers).
- [ ] T041b [P] [US3] Create unit test `test_fid_calculation` in `tests/unit/test_metrics.py` to verify FID calculation on CPU.
- [ ] T041c [P] [US1] Create unit test `test_mask_generator_metrics` in `tests/unit/test_mask_generator.py` to verify gradient variance and entropy.
- [X] T042 Run `quickstart.md` validation and ensure all artifacts are checksummed
- [ ] T043 [P] [US3] Generate final `paper/draft.md` with embedded metrics and mode distinctions. **Action**: Use `paper/templates/draft_template.md` as a base. Map metrics from `data/results/evaluation_report.json` and `data/results/ablation_report.json` to the corresponding sections in the template. **Status**: Blocked until upstream metrics (T033b, T032c) are complete.
- [X] T038b [P] Create `paper/templates/draft_template.md` with sections for Methodology, Results, Ablation, and Conclusion to support T043. **Content Requirements**: Include placeholders `{{latency_reduction_pct}}`, `{{fid_delta}}`, `{{p_value}}`, `{{mode_label}}`.
- [X] T046 [US2] Implement dynamic rank fallback logic in `code/models/moebius_dynamic.py` to strictly enforce CPU-only execution by disabling CUDA device placement and verifying `torch.backends.cudnn.enabled = False`. **Dependency**: T022. **Logic**: Assert `torch.cuda.is_available()` is False or explicitly ignore CUDA if present, ensuring strict compliance with CPU-only constraints.
- [ ] T047 [US3] Add statistical power validation in `code/eval/stats.py` to calculate required sample size for latency reduction claims and log warnings if current sample size is insufficient for p > 0.05 significance. **Dependency**: T030a. **Logic**: Use `scipy.stats.power` to compute effect size and sample size requirements, updating `data/results/power_analysis.json` with recommendations.
- [ ] T048 [US4] Implement proxy correlation gate in `code/eval/stats.py` to block execution if correlation r < 0.7 in Research Mode, ensuring synthetic metrics are validated before training. **Dependency**: T035. **Logic**: Raise `SystemExit` with code 1 if gate fails, preventing further execution until data quality is confirmed.
- [X] T050 [US3] Implement latency measurement standardization in `code/utils/cpu_profiler.py` to ensure consistent wall-clock timing across all inference runs, excluding initialization overhead. **Dependency**: T006. **Logic**: Use `time.perf_counter()` with warmup runs and median aggregation for stable latency metrics.
- [X] T052 [US1] **Streaming Loader Documentation**: Update `code/data/streaming_loader.py` to explicitly state the sampling rule (e.g., `itertools.islice(first config.sample_size rows)`) and log the exact sample size and representativeness limitation. **Dependency**: T044. **Logic**: Source of sample size is `config.sample_size`. **Output**: Log to `data/results/streaming_log.txt`.
- [ ] T056 [US4] **Create Missing Wrapper Script**: Create `code/data/download.py` to serve as the entry point for the quickstart run-book. **Logic**: This script should wrap the logic from `code/data/loader.py` (T012) to ensure the run-book command `python code/data/download.py` executes successfully. **Dependency**: T012.
- [ ] T057 [US4] **Create Missing Wrapper Script**: Create `code/eval/evaluate.py` to serve as the entry point for the quickstart run-book. **Logic**: This script should wrap the logic from `code/eval/report.py` (T031/T032c) to ensure the run-book command `python code/eval/evaluate.py` executes successfully. **Dependency**: T032c.

---

## Phase O: Revision & Hardening (Post-Analysis Fixes)

**Purpose**: Address specific reviewer concerns regarding data flow ordering, streaming fidelity, and strict gate enforcement.

- [ ] T053 [US4] **Gate Enforcement Hardening**: Refactor `code/eval/stats.py` (T035) to ensure the `SystemExit` in Research Mode is unconditionally raised if `r < 0.7`, removing any conditional logging that might allow the pipeline to proceed. **Dependency**: T035. **Rationale**: Prevents the "fabrication" risk where a low-correlation dataset is used to train a gating mechanism that cannot be trusted.
- [ ] T054 [US3] **Statistical Rigor**: Update `code/eval/report.py` (T031) to automatically append a "Limitations" section to `data/results/evaluation_report.json` if T030b (Power Analysis) flags the study as "UNDERPOWERED". **Dependency**: T030b. **Rationale**: Ensures that statistical claims are never presented without their validity context, adhering to the "Fix the code, not the test" principle.
- [X] T055 [US2] **Causal Isolation Verification**: Add a specific unit test in `tests/unit/test_dynamic_rank.py` to verify that the gating head's prediction cost is explicitly subtracted from the total latency gain in the ablation report. **Dependency**: T032c. **Rationale**: Ensures the "Efficiency" claim (US3) is not inflated by ignoring the computational cost of the gating mechanism itself.
- [ ] T056 [US4] **Reconcile Run-Book vs Implementation**: Create `code/data/download.py` (see T056 in Phase N) to satisfy the run-book invocation. **Dependency**: T056 (Phase N).
- [ ] T057 [US4] **Reconcile Run-Book vs Implementation**: Create `code/eval/evaluate.py` (see T057 in Phase N) to satisfy the run-book invocation. **Dependency**: T057 (Phase N).
- [X] T058 [US1] **Streaming Data Integrity Verification**: Implement a dedicated task to verify that the `streaming_loader.py` correctly handles the full dataset checksum before applying any sampling logic. **Implementation**: `code/data/streaming_loader.py::verify_full_checksum`. **Dependency**: T044. **Logic**: Ensure the `hash_registry` in `config.py` is updated with the checksum of the FULL dataset before any `islice` operation occurs. If the full dataset cannot be downloaded, the task must fail loudly without falling back to a sample. **Verification**: Log the full dataset hash to `data/results/streaming_log.txt` prior to any sampling.
- [ ] T059 [US4] **Proxy Correlation Reporting Enhancement**: Enhance `code/eval/stats.py` (T035) to output a detailed breakdown of the correlation metrics (not just the scalar `r`), including the scatter plot data points and the confidence interval for the correlation coefficient. **Implementation**: `code/eval/stats.py::compute_correlation_details`. **Dependency**: T035. **Output**: Append a `correlation_details` object to `data/results/proxy_validation.json` containing `scatter_data` and `confidence_interval`. **Rationale**: Provides deeper insight into the proxy validity, especially in Research Mode where a low correlation might indicate a specific subset of images causing the issue.
- [ ] T060 [US3] **Ablation Report Granularity**: Refactor `code/eval/report.py` (T032c) to generate a per-image breakdown of the latency reduction, rather than just an aggregate average. **Implementation**: `code/eval/report.py::generate_per_image_latency_breakdown`. **Dependency**: T032b. **Output**: Add `per_image_latency` array to `data/results/ablation_report.json`. **Rationale**: Allows for outlier detection and ensures the "[deferred] reduction" claim holds across the distribution, not just on average, addressing potential statistical masking of poor performance on specific samples.
