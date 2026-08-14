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
- [X] T001b Create `code/01_ingest_cluster.py`, `code/02_train_models.py`, `code/03_inference.py`, `code/04_simulate_eval.py` as empty files.
- [X] T001c Create `requirements.txt` with pinned dependencies: `datasets`, `scikit-learn`, `transformers`, `pybullet`, `pandas`, `numpy`, `scipy`, `pyyaml`, `psutil`, `statsmodels`.
- [X] T001d Initialize `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py` as empty files.
- [X] T001e Create `code/tests/__init__.py` and `.gitkeep` files to initialize the test package.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global seed management in `code/utils/seeds.py` to ensure reproducibility across all scripts (set `random_state`, `torch.manual_seed`).
- [X] T005 [P] Implement kinematic feature extraction utilities (velocity, acceleration, joint angles) in `code/utils/kinematics.py`.
- [X] T006 Setup environment configuration management for dataset paths, simulation parameters, and clustering strategy parameters (e.g., silhouette threshold, max attempts) in `code/utils/config.py`.
- [X] T007 Create base data validation schema and checksumming logic in `code/utils/validation.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Trajectory Clustering (Priority: P1) 🎯 MVP

**Goal**: Ingest Qwen-VLA dataset, extract text-action pairs, and cluster action sequences into behavioral groups using K-means (with HAC fallback).

**Independent Test**: Verify output contains up to 50 clusters, minimum 100 samples per cluster (if k>1), and kinematic features are normalized within physical bounds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for kinematic feature normalization in `code/tests/test_kinematics.py`.
- [X] T011 [P] [US1] Integration test for clustering pipeline with synthetic data in `code/tests/test_cluster.py` (Assert: silhouette_score > 0.25, cluster count <= 50).

### Implementation for User Story 1

- [X] T012 [US1] Implement dataset ingestion in `code/01_ingest_cluster.py`: Download Qwen-VLA/Hy-Embodied from HuggingFace, parse text-action pairs, validate presence, and **FAIL LOUDLY** (raise error) if download fails or data is missing (no synthetic fallback).
- [X] T013 [US1] Implement streaming data loader in `code/01_ingest_cluster.py` to handle datasets >7GB using `datasets.load_dataset(..., streaming=True)` and chunked processing.
- [X] T014 [US1] Implement kinematic feature extraction and normalization in `code/01_ingest_cluster.py`: Calculate velocity, acceleration, and joint angles from action sequences.
- [X] T015 [US1] Implement K-means clustering in `code/01_ingest_cluster.py`: Cluster normalized features into up to 50 groups (k=50), assign samples to clusters.
- [X] T016 [US1] **Implement K-means Clustering and Initial Check**:
 1. Run K-means clustering on the kinematic features with an initial `k` (e.g., 50).
 2. Calculate the silhouette score for this initial configuration.
 3. Save the initial cluster assignments and score to a temporary state file.
 4. **Constraint**: This task ONLY runs the initial K-means and checks the score. It does NOT perform the adaptive reduction loop or the HAC fallback. Those are handled by T016b.
- [X] T016b [US1] **Implement Adaptive K-Reduction Loop and HAC Decision (FR-002a)**:
 1. Read the initial silhouette score and `k` from T016.
 2. **If** score < 0.25 AND k > 1:
 - Reduce `k` by a step size. **Note**: The specific step size is [deferred] per FR-002a. The implementation MUST determine the step size (e.g., via a configuration parameter or a heuristic defined in `config.py`) and log it. Do NOT hard-code a default step size in the task description.
 - Re-run K-means with the new `k`.
 - Repeat until score >= 0.25 OR k reaches 1.
 3. **If** score < 0.25 AND k == 1:
 - Log a "degenerate clustering" warning.
 - Proceed with k=1 (K-means).
 4. **If** K-means diagnostics indicate poor manifold fit (e.g., persistent low silhouette despite reduction, or specific failure modes identified in Plan), **switch** to Hierarchical Agglomerative Clustering (HAC) with Ward linkage.
 5. Run HAC if the switch is triggered.
 6. Log the final `k` value, the final silhouette score, the method used ("K-means" or "HAC"), and the reduction step size used to `data/results/clustering_method_log.json`.
 7. **Prerequisite**: Requires T016 completion.
- [X] T016a [US1] **Implement HAC Fallback Logic (Plan: Manifold Robustness Mitigation)**:
 1. This task contains the implementation of the HAC algorithm with Ward linkage, to be called by T016b if the K-means fallback condition is met.
 2. Determine optimal cluster count using silhouette threshold logic or dendrogram cut-off.
 3. Save clustering artifacts (cluster centers, assignments, statistics) to `data/processed/clusters.json` and `data/processed/assignments.parquet`.
 4. **Constraint**: This task is the implementation of the fallback logic, not the decision maker. T016b decides when to call this.
- [X] T017 [US1] Save clustering artifacts (cluster centers, assignments, statistics) to `data/processed/clusters.json` and `data/processed/assignments.parquet`. (Note: If T016a runs, this task uses the HAC output).
- [X] T018 [US1] Verify clustering coverage: Calculate the ratio of assigned samples to total ingested samples; save the metric and report to `data/results/coverage_report.json`. Ensure ≥ 98% coverage. **If coverage < 98%**: The pipeline MUST log a warning "Clustering coverage < 98% (SC-005 violation)." and **PROCEED** (do not abort). This allows the research to continue on degenerate datasets as per Spec intent.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Non-Neural Model Fitting and Inference (Priority: P2)

**Goal**: Fit a lightweight probabilistic model (Decision Tree OR GMM) to each cluster, mapping frozen BERT text embeddings to action distributions, and implement a CPU-only inference engine.

**Independent Test**: Verify held-out R² ≥ 0.6 for the selected model, valid trajectory generation within 2s/prompt, and no GPU usage on CPU runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for BERT embedding generation in `code/tests/test_embeddings.py`.
- [X] T020 [P] [US2] Integration test for model training and inference on sample data in `code/tests/test_train.py`.

### Implementation for User Story 2

- [X] T020a [US2] **Construct Validity Gate (Pre-Training Check)**: Implement a pre-training check in `code/02_train_models.py` that calculates R² between frozen BERT embeddings and kinematic features using a simple linear regression baseline. **If R² < 0.1**: Halt the pipeline, write a "Hypothesis Failure" report to `data/results/hypothesis_failure_report.md`, and exit with code 1. **Constraint**: This task MUST run BEFORE T022. If this check fails, no models are trained.
- [X] T021 [US2] Implement frozen BERT embedding generation in `code/02_train_models.py`: Load `bert-base-uncased`, encode text instructions, ensure CPU-only execution. (Prerequisite for T021a)
- [X] T021a [US2/US1] **Generate Training Embeddings**: Run the BERT encoder on the US-01 output (text instructions from T012 and cluster assignments from T017) to generate and save embeddings to `data/processed/train_embeddings.parquet`. **Requires T012 (Ingestion) and T017 (Clustering) completion**. **Verify** that embedding dimensions are aligned with the model's configuration (as defined for `bert-base-uncased` in the Plan's 'Technical Context'). **Explicitly consume `data/processed/assignments.parquet` and `data/processed/clusters.json` from T017**. Save a verification JSON to `data/processed/embedding_verification.json`. **Data Hygiene**: Calculate and save the SHA256 checksum of `train_embeddings.parquet` to `data/processed/train_embeddings.sha256` and record the hash in the project state. **Data Flow**: This task explicitly consumes `data/processed/assignments.parquet` and `data/processed/clusters.json` from T017 to ensure the data flow is unambiguous for the implementer.
- [X] T022 [US2] Implement **Sequential Model Training** in `code/02_train_models.py` to satisfy FR-003 ("Decision Tree or GMM"):
 1. For each cluster:
 a. Split data into training and testing subsets using a stratified approach based on cluster labels, with the `random_state` parameter sourced from `seeds.py`.
 b. Train a Decision Tree regressor mapping BERT embeddings to actions.
 c. Evaluate the Decision Tree on the held-out set. Calculate R² and inference time.
 d. If R² >= 0.6 AND inference time < 2s/prompt: Select Decision Tree. **Stop training for this cluster.**
 e. Else: Train a Conditional Gaussian Mixture Model (CGMM) for the same cluster.
 f. Evaluate the CGMM. If R² >= 0.6, select CGMM.
 g. If neither meets the threshold, log a "Model Failure" warning for the cluster and select the best available (highest R²).
 2. Save the selected models and the selection criteria (R², time) to `artifacts/models/` (e.g., `cluster_{id}_selected.pkl`, `cluster_{id}_selection.json`).
 3. **Constraint**: Do NOT train both models simultaneously for every cluster. Use the sequential fallback logic to minimize computational cost and adhere to the CPU-only constraint (SC-003). **Requires T020a completion.**
- [X] T023 [US2] Implement cluster selection logic in `code/03_inference.py`: For a new prompt, find nearest cluster based on BERT embedding distance (requires T022).
- [X] T024 [US2] Implement trajectory sampling in `code/03_inference.py`: Sample from the fitted model (selected in T022) for the selected cluster to generate a complete trajectory array.
- [X] T025 [US2] Implement OOD handling in `code/03_inference.py`: If prompt is far outside cluster distribution, default to nearest cluster and log "low-confidence" flag.
- [X] T026 [US2] Validate inference performance: Create and run `code/bench_inference.py` to measure memory usage and execution time for a set of prompts; save results to `data/results/inference_benchmark.csv`. Ensure memory < 7GB and time ≤ 10 minutes. **Enforce CPU-only**: Script must fail if GPU is detected. **Verification Gate**: This task serves as the verification step for the US-02 acceptance scenario regarding execution time.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulation Evaluation and Statistical Comparison (Priority: P3)

**Goal**: Execute generated trajectories in PyBullet, measure success/collision rates, and perform **Paired T-Tests** against baselines.

**Independent Test**: Verify CSV output with success/collision flags and valid p-values from the statistical test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for PyBullet simulation step and error handling in `code/tests/test_simulate.py`.
- [X] T029 [P] [US3] Integration test for full evaluation loop with mock data in `code/tests/test_evaluate.py`.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement PyBullet simulation engine in `code/04_simulate_eval.py`: Load robot model, execute trajectories for "grasp", "navigate", "place" tasks.
- [X] T031 [US3] Implement simulation error handling in `code/04_simulate_eval.py`: Catch kinematic constraint violations, record as "failure", continue to next prompt (do not crash).
- [X] T032b [US3] **Fetch VLA Proxy Baseline**: Fetch the `data/processed/vla_proxy_baseline.parquet` artifact from a verified, pre-computed source (e.g., a specific HuggingFace repository or internal storage). **Constraint**: Do NOT generate this baseline using the original VLA model (which requires GPU). The task MUST fail if the static artifact cannot be fetched, ensuring the project remains CPU-only and reproducible. **Output**: `data/processed/vla_proxy_baseline.parquet` with checksum. **Constraint**: This task is the producer for T032a and T033.
- [X] T032a [US3] **Validate VLA Proxy Baseline Input**: Verify the existence and validity of `data/processed/vla_proxy_baseline.parquet` produced by T032b. If the file is missing or invalid, the script MUST raise a `RuntimeError` with a clear message: "VLA Proxy Baseline artifact not found or invalid at data/processed/vla_proxy_baseline.parquet. This artifact is a required input for SC-001 and FR-006. Please ensure T032b has completed successfully." The script must exit with code 1. **This task acts as a hard gate for Phase 5.**
- [X] T032 [US3] **Random Sampling Baseline**: Implement baseline generation in `code/04_simulate_eval.py` by generating random trajectories via uniform sampling within joint limits for comparison. This explicitly satisfies SC-002 and FR-006.
- [X] T042a [US3] **Full Inference Pipeline Memory Profiling**: Implement memory measurement for the **inference pipeline** (loading clustering artifacts, dataset context, and running inference) as a subprocess with `--inference-only` flag. Use `psutil` to measure peak RAM usage during the execution of `code/03_inference.py` (including artifact loading). **Constraint**: Must measure the total memory overhead of the inference engine (excluding the PyBullet simulation step). Save the result to `data/results/memory_profile.json` with keys `peak_rss_mb`, `average_rss_mb`, and `timestamp`. **Verification**: Ensure the reported memory is ≤ 7GB.
- [X] T033 [US3] Execute simulation loop in `code/04_simulate_eval.py`: Run a set of test prompts per task type for non-neural model, random baseline, and VLA proxy (from T032b). **Requires T032a completion**. (Note: T042a is independent and does not block T033).
- [X] T034 [US3] Log simulation results to `data/results/simulation_logs.csv` (task type, success flag, collision count, execution time).
- [X] T035a [US3] **Data Alignment Verification**: Before running statistical tests, verify that the prompt IDs used for the Non-Neural model, Random Baseline, and VLA Proxy are identical. Assert that the lists are byte-identical. If not, raise an error. **Prerequisite for T035b**.
- [X] T035b [US3] **Paired T-Tests (Binary Success)**: Perform **Paired T-Tests** for binary success rates comparing non-neural vs. random vs. VLA proxy (Satisfies FR-006/SC-004) using `scipy.stats.ttest_rel` on binary success arrays. **Constraint**: This task is strictly for binary success/failure flags. **Requires T035a completion**.
- [X] T035c [US3] **Paired T-Tests (Continuous Fidelity)**: Perform **Paired T-Tests** for continuous trajectory fidelity metrics (SC-001) comparing non-neural vs. VLA proxy using `scipy.stats.ttest_rel` on continuous fidelity score arrays. **Requirement**: This task explicitly addresses SC-001 by testing the "percentage of kinematic features within error margin" as a continuous variable, ensuring the full scope of "proxy metrics" is statistically validated. **Requires T035a completion**.
- [X] T036 [US3] Calculate trajectory fidelity metric: Compute the percentage of kinematic features within error margin of VLA proxy; save results to `data/results/fidelity_metrics.json`.
- [X] T037a [US3] **Final Evaluation Report**: Generate final report in `data/results/evaluation_report.md` with p-values (from T-Tests), confidence intervals, fidelity percentage (SC-001), **actual clustering coverage value**, **computational cost metrics** (memory usage and execution time against SC-003 constraints), and **complexity reduction factor**. **Complexity Reduction Factor Calculation**: Calculate the ratio of model parameters (or FLOPs, if easily computable) between the original VLA proxy and the non-neural model (Decision Tree/GMM). **Constraint**: Must calculate and report the "complexity reduction factor" (e.g., ratio of parameters/compute between VLA and non-neural model).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates: Update `quickstart.md` with execution instructions and `research.md` with methodology notes (DT vs GMM selection logic, T-Tests). **Output Requirement**: `research.md` must explicitly list the **selection rationale** for the final model (comparing DT vs GMM performance as per T022) and include the exact command-line flags for the pipeline.
- [X] T039a Code cleanup: Add type hints to `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py`.
- [X] T039b Code cleanup: Remove duplicate imports and unused variables in `code/utils/` modules. **Output Requirement**: Run `flake code/utils/` and ensure error-free performance; save the output log to `data/results/lint_report.txt`.
- [X] T040 [P] Add unit tests for edge cases (OOD prompts, simulation crashes) in `code/tests/`. **Output Requirement**: Create `code/tests/test_edge_cases.py` containing at least 3 test functions; run `pytest code/tests/test_edge_cases.py` and ensure exit code.
- [X] T041 [P] Run `quickstart.md` validation to ensure end-to-end pipeline executes correctly. **Output Requirement**: Execute the full pipeline as described in `quickstart.md`; save the final console output to `data/results/e2e_run_log.txt` and verify it contains "Pipeline Complete" and "Exit Code: 0".
- [X] T044 [US1] **Hardened Data Fetch**: Refactor `code/utils/data_loader.py` to remove any `try/except` blocks that might silently catch download errors and proceed. Ensure that if `datasets.load_dataset` fails, the script raises a specific `DataFetchError` with a clear message pointing to the failed URL or HuggingFace ID, forcing the pipeline to halt. **Output Requirement**: Add a unit test in `code/tests/test_data_loader.py` that mocks a network failure and asserts the script exits with a non-zero code and the specific error message.

---

## Phase O: Revision & Review Resolution

**Purpose**: Address specific concerns raised during the analysis phase to ensure robustness and adherence to the "real data only" constitution.

### Implementation for Revision

- [X] T047 [US3] **Verified Baseline Source**: Ensure `code/04_simulate_eval.py` uses the locally provided VLA Proxy baseline (from T032b) and does not attempt to download from unverified URLs. If the local baseline is missing, the script must fail loudly by raising a `RuntimeError` with the message as defined in T032a.
- [X] T049 [US2] **Model Selection Justification**: Update `data/results/model_selection_decision.md` to explicitly document the trade-off analysis between Decision Trees and GMMs, explaining the selection criteria used in T022 (sequential fallback).
- [X] T050 [US1] **Configurable Clustering Heuristic**: Refactor `code/01_ingest_cluster.py` to allow the k-reduction step size (default 5) to be overridden via command-line arguments or environment variables, ensuring flexibility for future research iterations.
- [X] T051 [US3] **Baseline Verification Checksum**: If `research.md` or `data-model.md` are generated later, ensure `code/04_simulate_eval.py` can optionally verify the locally provided VLA Proxy baseline against a known checksum if provided in the config. If no checksum is provided, skip verification but log a warning.

---

## Phase P: Final Validation & Handoff

**Purpose**: Ensure the final pipeline meets all success criteria and is ready for the research phase.

- [X] T052 [P] **Final End-to-End Validation**: Run the complete pipeline on a representative subset of the Qwen-VLA dataset to verify all data flows correctly from ingestion to evaluation report. **Output Requirement**: Save the full execution log to `data/results/final_validation.log` and verify the presence of all expected artifacts in `data/`, `artifacts/`, and `data/results/`.
- [X] T053 [P] **Success Criteria Verification**: Generate a final checklist document `data/results/success_criteria_checklist.md` that explicitly maps each Success Criterion (SC-001 to SC-005) to the specific output file and metric value that satisfies it. **Output Requirement**: The checklist must be human-readable and confirm that all SCs are met or explicitly state if any are pending further data.
- [X] T054 [P] **Research Handoff Note**: Create `data/results/research_handoff.md` summarizing the pipeline architecture, known limitations (e.g., CPU constraints, clustering heuristics), and specific recommendations for the next research phase. **Content Requirement**: This document MUST **NOT** suggest GPU offloading strategies as they contradict the project's CPU-only constraint. Instead, focus on **CPU-specific limitations** (e.g., memory bandwidth, single-threaded performance) and **algorithmic optimizations** (e.g., model pruning, quantization for CPU) that could improve performance within the existing constraints.

---

## Phase Q: Analysis-Driven Revisions

**Purpose**: Resolve specific issues identified by `/speckit.analyze` regarding data flow, CPU constraints, and fabrication risks.

### Implementation for Analysis Resolutions

- [X] T055 [US1] **Streamlined Dataset Ingestion**: Refactor `code/01_ingest_cluster.py` to explicitly use `datasets.load_dataset("Qwen/Qwen-VLA", split="train", streaming=True)` and process in chunks of samples to ensure memory usage stays under a manageable threshold while processing the full dataset. **Constraint**: Do NOT load the full dataset into RAM; use `itertools.islice` for any sampling logic. **Verification**: Add a check that `psutil` reports memory usage < 6GB during the a set of initial samples processed.
- [X] T056 [US1] **Silhouette Score Validation Logic**: Update the clustering validation in `code/01_ingest_cluster.py` to strictly enforce the `silhouette_score < 0.25` condition before reducing `k`. Ensure the loop terminates if `k` reaches 1, logging a "degenerate clustering" warning as per FR-002a, rather than looping infinitely. **Verification**: Add a unit test in `code/tests/test_cluster.py` that mocks a dataset with poor clustering and asserts the loop terminates at k=1.
- [X] T057 [US2] **CPU-Only Enforcement for BERT**: Refactor `code/02_train_models.py` to explicitly force `torch.device("cpu")` for the BERT encoder and all model training steps. Add a pre-flight check that raises `RuntimeError` if `torch.cuda.is_available()` is True, ensuring the "CPU-only" constraint is never violated by accident. **Verification**: Add a test that mocks `torch.cuda.is_available()` to return True and asserts the script exits with the specific error message.
- [X] T058 [US3] **Paired T-Test Data Alignment**: Refactor `code/04_simulate_eval.py` to ensure the "paired" nature of the t-tests is strictly enforced. The test set prompts must be loaded from a single source (the VLA Proxy Baseline from T032b) and used identically for the Non-Neural model, Random Baseline, and VLA Proxy. **Verification**: Add a check that asserts the `prompt_id` lists for all three baselines are identical before running the t-test.
- [X] T059 [US3] **Random Baseline Reproducibility**: Ensure the "Random Sampling Baseline" in `code/04_simulate_eval.py` uses a fixed seed (from `code/utils/seeds.py`) to ensure reproducibility. The random trajectories must be generated via uniform sampling within joint limits, as defined in the Assumptions. **Verification**: Run the baseline generation twice with the same seed and assert the output trajectories are byte-identical.
- [X] T060 [US1] **Data Loader Failure Handling**: Verify that `code/utils/data_loader.py` does not contain any `try/except` blocks that catch `datasets.load_dataset` errors and return synthetic data. If a download fails, the script must raise a `DataFetchError` and exit. **Verification**: Add a unit test that mocks `datasets.load_dataset` to raise a `ConnectionError` and asserts the script exits with the correct error message and no synthetic data is generated.
- [X] T061 [US2] **Construct Validity Threshold Enforcement**: Ensure the "Construct Validity Check" in `code/02_train_models.py` (T020a) uses the exact threshold `R² < 0.1` as defined in the Plan. If the threshold is not met, the script must halt and write the "Hypothesis Failure" report, preventing any model training. **Verification**: Add a unit test that mocks the R² calculation to return a low value indicating minimal explanatory power and asserts the script halts and writes the report.
- [X] T062 [US3] **Simulation Error Handling**: Verify that `code/04_simulate_eval.py` catches all PyBullet simulation errors (e.g., joint limit violations) and records them as "failure" without crashing the entire pipeline. **Verification**: Add a unit test that mocks a PyBullet step to raise an exception and asserts the script records a "failure" and continues to the next prompt.
- [X] T063 [US2] **Model Selection Criteria Documentation**: Update `data/results/model_selection_decision.md` to explicitly state that the selection criteria is "highest R² on held-out validation set, provided inference time < 2s per prompt" (with fallback to GMM). **Verification**: Ensure the document is present and contains the exact phrase "highest R² on held-out validation set".
- [X] T065 [US3] **VLA Proxy Baseline Verification**: Ensure `code/04_simulate_eval.py` does not attempt to download the VLA Proxy Baseline from an unverified URL. If the local baseline (from T032b) is missing, the script must fail loudly with the error message defined in T032a. **Verification**: Add a unit test that removes the local baseline file and asserts the script exits with the specific error message.

---

## Phase R: Final Integration & Verification

**Purpose**: Ensure all analysis-driven revisions are integrated and the pipeline is robust against the identified failure modes.

- [ ] T066 [US1] **Integrated Streaming & Clustering**: Run the full ingestion and clustering pipeline (T055 + T056 + T016a) on a large subset of the Qwen-VLA dataset to verify that streaming works correctly and the adaptive k-reduction loop terminates as expected, including the HAC fallback path. **Verification**: Save the execution log and clustering metrics to `data/results/streaming_clustering_validation.json`.
- [ ] T067 [US2] **Integrated CPU Enforcement & Validity Gate**: Run the model training pipeline (T057 + T061) to verify that the CPU-only check and Construct Validity Gate function correctly. **Verification**: Ensure the script fails with the correct error messages when the conditions are not met and succeeds when they are.
- [ ] T068 [US3] **Integrated Simulation & Statistical Validation**: Run the full simulation and evaluation pipeline (T058 + T059 + T062) to verify that the paired t-tests are correctly aligned and the simulation handles errors gracefully. **Verification**: Save the simulation results and statistical test outputs to `data/results/final_simulation_validation.json`.
- [ ] T069 [All] **End-to-End Fabrication Check**: Execute the entire pipeline from ingestion to evaluation and verify that no synthetic data is generated or used at any stage. **Verification**: Review all output files and logs to confirm that all data originates from the real Qwen-VLA dataset or the external VLA Proxy baseline (T032b).
- [ ] T070 [All] **Final Documentation Update**: Update `quickstart.md`, `research.md`, and `README.md` to reflect all changes made in Phases O, P, and Q. **Verification**: Ensure all documentation accurately describes the current pipeline architecture, constraints, and validation procedures.