# Tasks: Non-Neural Approximation of VLA Priors

**Input**: Design documents from `/specs/001-non-neural-vla-approximation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create directory structure `code/`, `code/utils/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `artifacts/models/` using `mkdir -p` or a setup script.
- [X] T001b Create `code/01_ingest.py`, `code/02_cluster.py`, `code/03_train.py`, `code/04_inference.py`, `code/05_simulate.py`, `code/06_evaluate.py` as empty files.
- [X] T001c Create `requirements.txt` with pinned dependencies: `datasets`, `scikit-learn`, `transformers`, `pybullet`, `pandas`, `numpy`, `scipy`, `pyyaml`, `psutil`, `statsmodels`.
- [X] T001d Initialize `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py` as empty files.
- [X] T001e Create `code/tests/__init__.py` and `.gitkeep` files to initialize the test package.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global seed management in `code/utils/seeds.py` to ensure reproducibility across all scripts (set `random_state`, `torch.manual_seed`).
- [X] T005 [P] Implement kinematic feature extraction utilities (velocity, acceleration, joint angles) in `code/utils/kinematics.py`.
- [X] T006 Setup environment configuration management for dataset paths, simulation parameters, and **clustering strategy parameters** (e.g., silhouette threshold, k-decrement step, max attempts) in `code/utils/config.py`.
- [X] T006a [P] Define specific configuration values for FR-002a: Set `k_reduction_step_size` (default to a small positive integer) and `max_k_reduction_attempts` (A default threshold will be established for initial parameter configuration.) in `code/utils/config.py` to ensure T016 has valid parameters.
- [X] T007 Create base data validation schema and checksumming logic in `code/utils/validation.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Trajectory Clustering (Priority: P1) 🎯 MVP

**Goal**: Ingest Qwen-VLA dataset, extract text-action pairs, and cluster action sequences into behavioral groups using K-means.

**Independent Test**: Verify output contains up to 50 clusters, minimum 100 samples per cluster (if k>1), and kinematic features are normalized within physical bounds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for kinematic feature normalization in `code/tests/test_kinematics.py`.
- [X] T011 [P] [US1] Integration test for clustering pipeline with synthetic data in `code/tests/test_cluster.py` (Assert: silhouette_score > 0.25, cluster count <= 50).

### Implementation for User Story 1

- [X] T012 [US1] Implement dataset ingestion in `code/01_ingest.py`: Download Qwen-VLA/Hy-Embodied from HuggingFace, parse text-action pairs, validate presence, and **FAIL LOUDLY** (raise error) if download fails or data is missing (no synthetic fallback).
- [X] T013 [US1] Implement streaming data loader in `code/01_ingest.py` to handle datasets >7GB using `datasets.load_dataset(..., streaming=True)` and chunked processing.
- [X] T014 [US1] Implement kinematic feature extraction and normalization in `code/02_cluster.py`: Calculate velocity, acceleration, and joint angles from action sequences.
- [X] T015 [US1] Implement K-means clustering in `code/02_cluster.py`: Cluster normalized features into up to 50 groups (k=50), assign samples to clusters.
- [X] T016a [US1] **Document Research Decision**: Create a note in `data/results/research_decisions.md` explicitly documenting the choice of `k_reduction_step_size` heuristic to resolve the '[deferred]' marker in FR-002a. **Prerequisite for T016**.
- [X] T016 [US1] Implement clustering validation in `code/02_cluster.py`: Calculate silhouette score; if < 0.25, reduce k using parameters (`k_reduction_step_size`, `max_k_reduction_attempts`) loaded from `code/utils/config.py` (as per FR-002a) and re-run until valid or k=1 (log warning if k=1 reached). **Requires T016a completion**. Log the final k value used and the final silhouette score achieved. **Research Decision**: The spec marks the decrement logic as '[deferred]'; this task implements the fixed heuristic documented in T016a. **Manifold Robustness**: If K-means diagnostics (Silhouette/Calinski-Harabasz) indicate poor fit after the k-reduction loop (FR-002a), automatically switch to **Hierarchical Agglomerative Clustering (HAC)** with Ward linkage, re-cluster the data, and log the method switch and resulting metrics in `data/results/clustering_method_log.json`. **Note**: HAC fallback logic merged from T046.
- [X] T017 [US1] Save clustering artifacts (cluster centers, assignments, statistics) to `data/processed/clusters.json` and `data/processed/assignments.parquet`.
- [X] T018 [US1] Verify clustering coverage: Calculate the ratio of assigned samples to total ingested samples; save the metric and report to `data/results/coverage_report.json`. Ensure ≥ 98% coverage. **If coverage < 98%**: Re-run clustering with k=1 (degenerate) and log the specific parameters used. **Abort** the pipeline with a non-zero exit code only if the `--allow-low-coverage` flag is NOT passed AND the k=1 fallback also fails to produce a valid assignment (i.e., < 98% of data is usable). **Requires T018a completion**.
- [X] T018a [US1] **Define CLI Interface**: Implement CLI interface in `code/02_cluster.py` to parse the `--allow-low-coverage` flag and pass it to the logic in T018. **Output Requirement**: `code/02_cluster.py` must accept `--allow-low-coverage` as a boolean flag.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Non-Neural Model Fitting and Inference (Priority: P2)

**Goal**: Fit **both Decision Trees and Conditional Gaussian Mixture Models (CGMM)** to each cluster, mapping frozen BERT text embeddings to action distributions, and implement a CPU-only inference engine that compares both.

**Independent Test**: Verify held-out R² ≥ 0.6 for the best-performing model, valid trajectory generation within 2s/prompt, and no GPU usage on CPU runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for BERT embedding generation in `code/tests/test_embeddings.py`.
- [X] T020 [P] [US2] Integration test for model training and inference on sample data in `code/tests/test_train.py`.

### Implementation for User Story 2

- [X] T021 [US2] Implement frozen BERT embedding generation in `code/03_train.py`: Load `bert-base-uncased`, encode text instructions, ensure CPU-only execution. (Prerequisite for T021a)
- [X] T021a [US2/US1] **Generate Training Embeddings**: Run the BERT encoder on the US-01 output (text instructions from T017) to generate and save embeddings to `data/processed/train_embeddings.parquet`. **Requires T017 completion**. **Verify** that embedding dimensions match 768 (as defined for `bert-base-uncased` in the Plan's 'Technical Context'). Save a verification JSON to `data/processed/embedding_verification.json`.
- [X] T022b [US2] **Document Selection Decision Strategy**: Create a note in `data/results/model_selection_decision.md` explicitly stating that the pipeline will train **both** Decision Trees and CGMMs per cluster to satisfy the 'OR' constraint by comparative analysis. Document the selection criteria (e.g., highest R² on validation set) that will be used to choose the final model for each cluster. **Prerequisite for T022**.
- [X] T022 [US2] Implement **Dual Model Training** in `code/03_train.py`:
 1. Train a Decision Tree regressor per cluster mapping BERT embeddings to actions.
 2. Train a Conditional GMM (CGMM) per cluster mapping BERT embeddings to actions.
 3. Evaluate both on a held-out set; calculate R² and conditional variance.
 4. Select the best-performing model per cluster based on R² (satisfying T022b).
 5. Save the selected models and the comparison metrics to `artifacts/models/` (e.g., `cluster_{id}_dt.pkl`, `cluster_{id}_cgmm.pkl`, `cluster_{id}_selection.json`).
- [X] T022a [US2] **Implement Decision Tree Logic**: Specific implementation details for the Decision Tree regressor training and evaluation within T022.
- [X] T027 [US2] Save trained models (both DT and CGMM) and BERT encoder to `artifacts/models/` using the naming convention `cluster_{id}_dt.pkl`, `cluster_{id}_cgmm.pkl`, and `bert_encoder.pt`.
- [X] T045 [US2] **Construct Validity Enforcement**: Implement the **Construct Validity Check** described in `plan.md` as a blocking gate in `code/03_train.py`. Calculate Mutual Information or R² between BERT embeddings and kinematic features *before* fitting any models. If the threshold (R² < 0.1) is not met, the script must **HALT** model training, write a "Hypothesis Failure" report to `data/results/hypothesis_failure_report.md`, and exit successfully (non-error) to signal the negative result phase, preventing wasted compute. **Prerequisite for T022**.
- [X] T023 [US2] Implement cluster selection logic in `code/04_inference.py`: For a new prompt, find nearest cluster based on BERT embedding distance (requires T027).
- [X] T024 [US2] Implement trajectory sampling in `code/04_inference.py`: Sample from the fitted model (selected in T022) for the selected cluster to generate a complete trajectory array.
- [X] T025 [US2] Implement OOD handling in `code/04_inference.py`: If prompt is far outside cluster distribution, default to nearest cluster and log "low-confidence" flag.
- [X] T026 [US2] Validate inference performance: Create and run `code/bench_inference.py` to measure memory usage and execution time for a set of prompts; save results to `data/results/inference_benchmark.csv`. Ensure memory < 7GB and time ≤ 10 minutes. **Enforce CPU-only**: Script must fail if GPU is detected.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulation Evaluation and Statistical Comparison (Priority: P3)

**Goal**: Execute generated trajectories in PyBullet, measure success/collision rates, and perform **Paired T-Tests** against baselines.

**Independent Test**: Verify CSV output with success/collision flags and valid p-values from the statistical test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for PyBullet simulation step and error handling in `code/tests/test_simulate.py`.
- [X] T029 [P] [US3] Integration test for full evaluation loop with mock data in `code/tests/test_evaluate.py`.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement PyBullet simulation engine in `code/05_simulate.py`: Load robot model, execute trajectories for "grasp", "navigate", "place" tasks.
- [X] T031 [US3] Implement simulation error handling in `code/05_simulate.py`: Catch kinematic constraint violations, record as "failure", continue to next prompt (do not crash).
- [X] T032 [US3] **Random Sampling Baseline**: Implement baseline generation in `code/05_simulate.py` by generating random trajectories via uniform sampling within joint limits for comparison. This explicitly satisfies SC-002 and FR-006.
- [X] T032b [US3] **Generate VLA Proxy Baseline**: Generate the VLA Proxy baseline artifact locally. Use the text instructions from the held-out test set (derived from T017) and run the original Qwen-VLA model (or a locally available proxy implementation) to produce the reference trajectories. Save to `data/processed/vla_proxy_baseline.parquet`. **If the local model generation fails, the script must FAIL LOUDLY**. This ensures the artifact exists for T033 without relying on external non-existent IDs.
- [X] T042 [US3] **Memory Profiling**: Implement `code/utils/memory_profiler.py` using `psutil` to measure actual process RSS (Resident Set Size) and integrate into `code/01_ingest.py`, `code/02_cluster.py`, `code/03_train.py`, and `code/04_inference.py` to measure and log the aggregate RAM usage of the pipeline. **Output Requirement**: Save a summary report to `data/results/memory_profile.json` confirming the peak aggregate memory usage is ≤ 7GB (satisfying SC-003). The JSON must contain keys `peak_rss_mb`, `average_rss_mb`, and `timestamp`. If the limit is exceeded, the script must log a warning and suggest garbage collection or chunk size adjustments.
- [X] T033 [US3] Execute simulation loop in `code/05_simulate.py`: Run a set of test prompts per task type for non-neural model, random baseline, and VLA proxy (from T032b). **Requires T042 completion**.
- [X] T034 [US3] Log simulation results to `data/results/simulation_logs.csv` (task type, success flag, collision count, execution time).
- [X] T035a [US3] **Paired T-Tests**: Perform **Paired T-Tests** for success rates comparing non-neural vs. random vs. VLA proxy (Satisfies FR-006/SC-004) using `scipy.stats.ttest_rel` on binary success arrays. Report p-values and confidence intervals.
- [X] T036 [US3] Calculate trajectory fidelity metric: Compute the percentage of kinematic features within error margin of VLA proxy; save results to `data/results/fidelity_metrics.json`.
- [X] T037 [US3] Generate final report in `data/results/evaluation_report.md` with p-values (from T-Tests), confidence intervals, fidelity percentage, and complexity reduction factor.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates: Update `quickstart.md` with execution instructions and `research.md` with methodology notes (DT vs CGMM comparison, T-Tests). **Output Requirement**: `research.md` must explicitly list the **selection rationale** for the final model (comparing DT vs CGMM performance as per T022b) and include the exact command-line flags for the pipeline.
- [X] T039a Code cleanup: Add type hints to `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py`.
- [X] T039b Code cleanup: Remove duplicate imports and unused variables in `code/utils/` modules. **Output Requirement**: Run `flake8 code/utils/` and ensure 0 errors; save the output log to `data/results/lint_report.txt`.
- [X] T040 [P] Add unit tests for edge cases (OOD prompts, simulation crashes) in `code/tests/`. **Output Requirement**: Create `code/tests/test_edge_cases.py` containing at least 3 test functions; run `pytest code/tests/test_edge_cases.py` and ensure exit code 0.
- [X] T041 [P] Run `quickstart.md` validation to ensure end-to-end pipeline executes correctly. **Output Requirement**: Execute the full pipeline as described in `quickstart.md`; save the final console output to `data/results/e2e_run_log.txt` and verify it contains "Pipeline Complete" and "Exit Code: 0".
- [ ] T044 [US1] **Hardened Data Fetch**: Refactor `code/utils/data_loader.py` to remove any `try/except` blocks that might silently catch download errors and proceed. Ensure that if `datasets.load_dataset` fails, the script raises a specific `DataFetchError` with a clear message pointing to the failed URL or HuggingFace ID, forcing the pipeline to halt. **Output Requirement**: Add a unit test in `code/tests/test_data_loader.py` that mocks a network failure and asserts the script exits with a non-zero code and the specific error message.

---

## Phase O: Revision & Review Resolution

**Purpose**: Address specific concerns raised during the analysis phase to ensure robustness and adherence to the "real data only" constitution.

### Implementation for Revision

- [X] T046 [US1] **Manifold Robustness Integration**: Ensure the **Hierarchical Agglomerative Clustering (HAC)** fallback logic described in `plan.md` is fully integrated into the critical path of `code/02_cluster.py` (Phase 3), not just a revision task. Verify that if K-means diagnostics fail, the pipeline automatically switches to HAC with Ward linkage and logs the switch.
- [X] T047 [US3] **Verified Baseline Source**: Ensure `code/05_simulate.py` uses the locally generated VLA Proxy baseline (from T032b) and does not attempt to download from unverified URLs. If the local generation fails, the script must fail loudly.
- [X] T049 [US2] **Model Selection Justification**: Update `data/results/model_selection_decision.md` to explicitly document the trade-off analysis between Decision Trees and CGMMs, explaining the selection criteria used in T022.
- [X] T050 [US1] **Configurable Clustering Heuristic**: Refactor `code/02_cluster.py` to allow the `k_reduction_step_size` heuristic to be overridden via command-line arguments or environment variables, ensuring the "[deferred]" nature of FR-002a is respected and allowing future research iterations to adjust this without code changes.
- [X] T051 [US3] **Baseline Verification Checksum**: If `research.md` or `data-model.md` are generated later, ensure `code/05_simulate.py` can optionally verify the locally generated VLA Proxy baseline against a known checksum if provided in the config. If no checksum is provided, skip verification but log a warning.