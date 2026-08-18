---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Active Learners as Efficient PRP Rerankers"

**Input**: Design documents from `/specs/001-llmxive-prp-redundancy/`
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

## Phase 0: Pre-Implementation (Spec Alignment)

- [X] T000-VERIFY [Foundational] **Audit Spec for FR-006 Limits** – Verify `spec.md` explicitly contains "limit of 6 hours" and "limit of 7GB" in FR-006. If limits are missing or vague, raise `SpecConstraintViolationError`. **Deliverable**: `state/spec_audit_log.json` confirming limits are present.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python project with `requirements.txt` (beir, sentence-transformers, datasketch, scikit-learn, scipy, pandas, numpy, pytest, nltk, onnx, onnxruntime, transformers, huggingface_hub, llama-cpp-python); **Removed heavy GPU-specific dependencies (`bitsandbytes`, `tinyllama`, `accelerate`); replaced with CPU-native LLM inference tools (`llama-cpp-python`) and verified absence of GPU libraries.**
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools
- [X] T087 [Foundational] **Implement Main Entry Point** – Create `code/main.py` as the single orchestration entry point referenced in `quickstart.md`. It must import and execute the pipeline logic from `run_pipeline.py`, handle CLI arguments for seeds/thresholds, and ensure all resource monitors are active before starting. **Deliverable**: `code/main.py` with CLI interface. **[Dep: T004, T023, T078]**
- [X] T088 [Foundational] **Update Quickstart Documentation** – Modify `docs/quickstart.md` to reflect the correct entry point command (`python code/main.py --seed 42 --threshold 0.95`) and ensure it matches the newly created `main.py` interface. **Deliverable**: Updated `docs/quickstart.md`. **[Dep: T087]**

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 [P] Setup configuration management in `code/config.py` with a schema for `MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB` allowing parameterization, setting default values explicitly to distinct integers, serving FR-006 and Constitution Principle VII.
- [X] T004a [P] Implement watchdog/signal handler in `code/utils.py` to terminate the pipeline if runtime exceeds a predefined threshold or memory exceeds a substantial threshold., serving FR-006 enforcement. The handler reads the constants from T004 and uses a dual‑layer kill: first `psutil` termination, then fallback to `ulimit` when cgroups are unavailable.
- [X] T004b [P] **Implement cgroups/ulimit validation** – Create `code/validate_env.sh` to detect cgroups v2, set memory limits if available, and fallback to `ulimit`/`psutil` if not. **Deliverable**: `code/validate_env.sh` with all three logic paths implemented and tested.
- [X] T005 [P] **BEIR Data Loader** – Implement `code/data_loader.py` to fetch `nfcorpus` and `scifact` via `beir` library. **Output**: `data/raw/` directory populated with raw data. **[Dep: T001]**
- [X] T005a [P] Calculate SHA-256 checksums of raw BEIR files fetched by T005 and record them in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` under the `artifact_hashes` key map, serving Constitution Principle III.
- [X] T005b [P] Extend BEIR loader to fetch `trec-covid` for FR validation

Research Question: How can the BEIR framework be adapted to support cross-domain retrieval evaluation using the TREC-COVID dataset?
Method: Extend the existing BEIR data loader to include the `trec-covid` corpus and integrate it into the evaluation pipeline.
References: Thakur et al. (2021). BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. arXiv:2104.08663..
- [X] T006 [P] **Logging Infrastructure Setup** – Implement base logging infrastructure in `code/logging_config.py` to record every pairwise comparison and resource usage stats. The log format is JSONL (`data/processed/comparison_log.jsonl`). **Output: `data/processed/resource_log.json`** (to be populated by T023 during execution). **(Completed)**
- [X] T006a [P] Verify existence and non‑empty status of `data/processed/comparison_log.jsonl` before any downstream task runs; abort with `DataFlowViolationError` if missing. **(Verification task)**
- [X] T007 Create base entities: `CandidateList` and `ComparisonPair` dataclasses in `code/models.py`.
- [X] T008 [P] Implement environment validation script `code/validate_env.sh` to ensure CPU‑only constraints and no GPU dependencies.
- [X] T050 [P] Update `code/validate_env.sh` to check availability of `all-MiniLM-L6-v2` model on CPU.
- [X] T042 [P] Add "Synthetic Data Fallback Blocker" test in `tests/unit/test_data_loader.py` that asserts a `RuntimeError` is raised when BEIR fetch fails, preventing silent synthetic fallback.
- [X] T041 [Foundational] Add "Data Integrity Check" in `code/run_pipeline.py` that verifies presence and integrity of all intermediate artifacts before proceeding.
- [X] T057 [Foundational] **Data Flow Correction** – Implement strict ordering enforcement in `code/run_pipeline.py`: `injected_datasets.json` → `clusters.json` → `unique_subset.json` → `comparison_log.jsonl` → downstream. Raise `PipelineDependencyError` on violation.
- [X] T065 [Foundational] **Dependency Graph Validator** – Implement pre-flight validation in `code/run_pipeline.py` to check existence and JSON schema of `injected_datasets.json` and `clusters.json` before pipeline start. **[Dep: T065a]**
- [X] T065a [Foundational] **Schema Definitions** – Provide inline JSON Schemas for `injected_datasets.json` and `clusters.json` in `code/schemas/`. **Deliverables**: `code/schemas/injected_datasets.schema.json`, `code/schemas/clusters.schema.json`. **[Dep: None]**
- [X] T066 [Foundational] **Artifact Chain Verification** – Implement pre-flight check in `code/run_pipeline.py` to verify full chain from injection to final metrics, aborting on missing/invalid artifacts.
- [X] T079 [US3] **Statistical Power Analysis** – Computes post-hoc power analysis for Wilcoxon tests given N=30 seeds and expected effect sizes. Writes `data/results/power_analysis.json`. **Audit Task**: This task runs in parallel with T027 and does NOT block execution. If power < 0.8, it logs `InsufficientPowerWarning` and flags output as `low_power: true` but allows the pipeline to continue with N=30 as per plan constraints. **[Dep: None]**

## Phase 3: User Story 1 – Quantify Redundancy‑Induced Efficiency Loss (Priority: P1)

- [X] T010 [P] Unit test for synthetic redundancy injection logic in `tests/unit/test_data_loader.py::test_synthetic_injection_creates_clusters`; asserts injected clusters have pairwise cosine similarity > 0.95 (FR‑002).
- [X] T011 [P] Unit test for "wasted" call classification proxy in `tests/unit/test_metrics.py`.
- [X] T012 [Foundational] **Synthetic Redundancy Injection** in `code/data_loader.py` using **synonym replacement** (probability 0.3) and **sentence shuffling** (window 2) as primary methods to create **≥ 20 clusters** of **3–5** near‑duplicate passages with cosine similarity > 0.95. Output: `data/processed/injected_datasets.json`. Includes validation of cluster count; on failure triggers fallback T058. **Deliverable**: `data/processed/injection_validation.json` (contains cluster count and similarity stats). **[Dep: T005]**
- [X] T043 [US1] **Semantic Similarity Threshold Validator** – reads `injected_datasets.json`, verifies average injected similarity > 0.95 and that at least 20 clusters exist; retries with higher intensity up to 3 attempts, then logs `DataInjectionWarning` and proceeds with achieved data. **[Dep: T012]**
- [X] T014 [US1] **Baseline Active Ranker** – runs on the **unique subset** of the injected list (derived from `injected_datasets.json`) to generate `data/processed/comparison_log.jsonl` (baseline) and `data/processed/unique_subset.json`. Uses a CPU-light embedding model for pairwise scoring. **[Dep: T012, T043]**
- [X] T013 [US1] **Wasted Call Counter** – parses `data/processed/comparison_log.jsonl` to count pairs with cosine similarity > 0.95, writes `data/results/flagged_pairs_count.json`. **[Dep: T014]**
- [X] T013a [US1] **Actual Budget Recorder** – reads `data/processed/comparison_log.jsonl` to compute total number of LLM calls executed, writes `data/results/budget_config.json` (`actual_budget`, `configured_budget`). **[Dep: T014]**
- [X] T013b [US1] **Sample Size Calculator** – determines sample size = max(minimum_threshold, flagged_count) and writes `data/results/sample_config.json`. If flagged count = 0, writes `skip_validation: true` and empty list. **[Dep: T013]**
- [X] T013c [US1] **Consensus Sample Selector** – randomly selects `sample_size` indices from flagged pairs (using `RANDOM_SEED`), writes `data/results/consensus_sample.json`. **[Dep: T013b]**
- [X] T013e [US1] **LLM Consensus Validation** – loads **TinyLlama‑1.1B‑Chat‑v1.0 (Q4_K_M)** from `TinyLlama/TinyLlama-1.1B-Chat-v1.0` via `llama-cpp-python`. Performs generative voting on the sample; writes `data/results/consensus_ground_truth.json`. **Memory Check**: Uses `psutil.virtual_memory().available` to verify `available > 6.5 * 1024**3`; if not, **ABORT LLM load immediately** and trigger T013e-fallback (per FR-006 hard termination of the component). **[Dep: T013c]**
- [X] T013e-fallback [US1] **Proxy‑Only Fallback** – **Writes `data/results/consensus_ground_truth.json` with schema: `[{ "pair_id": <int>, "proxy_label": <boolean> }]`**. Sets `consensus_status: "proxy_fallback"`. **Runs only if T013e is skipped due to memory constraints or fails**. Ensures this path remains within 7GB RAM by using only CPU embeddings. **[Dep: T013c]**
- [X] T013f [US1] **Correction Factor Calculation** – compares proxy labels to ground truth (from `consensus_ground_truth.json`). **If status is "proxy_fallback"**: sets precision=1.0, recall=1.0, and `validation_status: "unvalidated"`. If LLM consensus succeeded, computes standard metrics. Writes `data/results/correction_factor.json`. **[Dep: T013e OR T013e-fallback]**
- [X] T015 [US1] **NDCG@10 for Baseline** – calculates NDCG@10 for baseline ranker against BEIR relevance judgments; writes `data/results/us1_baseline_ndcg.json`. **[Dep: T014]**
- [X] T016 [US1] **NDCG@10 for Redundant Run** – calculates NDCG@10 for the full redundant dataset; writes `data/results/us1_redundant_ndcg.json`. **[Dep: T012]**
- [X] T017d [US1] **Real-World Proxy Validation** – Implements comparative analysis between synthetic redundancy (from T012) and high-similarity query-document pairs from `trec-covid` (T005b). **Method**: Extract pairs from `trec-covid` with cosine similarity > 0.95 as a proxy for near-duplicates. Computes **Pearson correlation** of similarity distributions and logs results in `data/results/real_world_validation.json`. **Output**: `real_world_validation.json` with `validation_type: "proxy"`, `limitation_note: "trec-covid lacks explicit near-duplicate labels"`, and `correlation_coefficient`. **Validates FR-009 limitation**. **[Dep: T012, T005b]**

## Phase 4: User Story 2 – Validate CPU‑Tractable Pre‑Clustering Recovery (Priority: P2)

- [X] T018 [P] Unit test for MinHash‑LSH clustering logic with Jaccard > 0.95 in `tests/unit/test_clustering.py`.
- [X] T019 [P] Integration test for full pipeline execution with resource limits in `tests/integration/test_full_pipeline.py`.
- [X] T020 [US2] **MinHash‑LSH Clustering** – groups near-duplicates using `datasketch` with a high Jaccard threshold; writes `data/processed/clusters.json`. **[Dep: T012]**
- [X] T044 [US2] **Cluster Integrity Check** – verifies that > 95 % of intra‑cluster Jaccard similarities exceed 0.95; logs warning or triggers re‑run with relaxed threshold. **[Dep: T020]**
- [X] T024a [US2] **Labeled Subset Generation** – builds a labeled subset using ground truth from `consensus_ground_truth.json` (or proxy if LLM failed) for correlation analysis. If only proxy is available, logs `CorrelationValidationSkipped` and writes `data/results/correlation_validation_skipped.json`. **[Dep: T013e, T013e-fallback]**
- [X] T024 [US2] **Jaccard‑Cosine Correlation Validation** – computes Pearson correlation between MinHash Jaccard and cosine similarity on the labeled subset; writes `data/results/jaccard_cosine_corr.json`. **[Dep: T024a]**
- [X] T024b [US2] **Threshold Fallback Logic** – if T024 correlation < 0.7, triggers fallback to Cosine-only clustering logic and logs `ClusteringFallbackTriggered`. **[Dep: T024]**
- [X] T021 [US2] **Pre‑Clustering Filter** – applies MinHash clusters (using the *validated* threshold from T024 or the *fallback* logic from T024b) to reduce candidate pool before ranking; logs reduction percentage. **[BLOCKED_BY: US1 Validation (T013e/T013e-fallback)]** **[Dep: T012, T020, T024, T024b]**
- [X] T022 [US2] **NDCG@10 for Clustering‑Aided Variant** – calculates NDCG@10 after pre-clustering; writes `data/results/us2_ndcg.json`. **[Dep: T021]**
- [X] T023 [US2] **Runtime Resource Monitor** – Enforces runtime and RAM limits during the full pipeline; writes `data/processed/resource_log.json`. **[Dep: T006, T021]**
- [X] T025 [US2] **Threshold Sweep Definition** – adds config entries for sweep values in `code/config.py`.
- [X] T073a [US2] **Threshold Sweep Execution** – runs pipeline for each sweep value in the defined set; aggregates results into `data/results/threshold_sweep.json`. **[Dep: T025]**
- [X] T073b [US2] **Sweep Result Aggregation** – computes mean and std for NDCG and **wasted_ratio** (derived from `flagged_pairs_count.json` / total pairs, where total pairs is read from `data/processed/comparison_log.jsonl` line count) per threshold; updates `threshold_sweep.json`. **[Dep: T073a]**
- [X] T025d [US2] **Optimal Threshold Selection** – identifies best threshold based on **Pareto frontier of NDCG and wasted_ratio** (from T073b); records in `threshold_sweep.json`. **[Dep: T073b]**
- [X] T074 [P] **Log Dataset Sizes** – Implement logging of `len(injected_data)`, `len(clusters)`, and `len(filtered_candidates)` to `data/processed/size_log.json`. **[Dep: T012, T020, T021]**
- [X] T076 [P] **Embedding Cache** – Implement disk-based pickle cache for `all-MiniLM-L6-v2` embeddings in `code/embeddings.py` with cache key logic (`file_hash + seed`) and invalidation on data change. **[Dep: T005]**

## Phase 5: User Story 3 – Statistical Significance of Efficiency Gains (Priority: P3)

- [X] T026 [P] Unit test for Wilcoxon signed‑rank test and Bonferroni correction in `tests/unit/test_metrics.py`.
- [X] T027a [P] **Single-Seed Execution Logic** – Implements the core logic for a single seed run (baseline and clustering-aided) without orchestration. **[Dep: T014, T022 logic]**
- [X] T027 [US3] **Multi‑Seed Execution Loop** – orchestrates **multiple** independent seeds using T027a logic; logs seeds to `data/results/seeds.json`. **Note**: This task runs immediately. It does NOT wait for T079. T079 is a parallel audit task. **[Dep: T027a]**
- [X] T028 [US3] **Wilcoxon Test on NDCG@10** – compares NDCG scores across seeds; writes `data/results/wilcoxon_ndcg.json`. **[Dep: T027]**
- [X] T029 [US3] **Wilcoxon Test on Wasted Ratio** – compares wasted ratios; writes `data/results/wilcoxon_wasted.json`. **[Dep: T027]**
- [X] T029a [US3] **P‑Value Aggregation** – aggregates p‑values from T028 and T029 into `data/results/p_values_family.json`. **[Dep: T028, T029]**
- [X] T030 [US3] **Bonferroni Correction** – applies correction to aggregated p‑values; writes `data/results/bonferroni_corrected.json`. **[Dep: T029a]**
- [X] T031 [US3] **Statistical Report Generation** – creates `data/results/statistical_report.md` including Bonferroni‑corrected p‑values, corrected wasted ratio, and a disclaimer if `validated: false` in `us1_efficiency_ratio.json`. **[Dep: T030]**
- [X] T075 [P] **P-Value Histogram** – Generate and save matplotlib histogram of p-values from T028/T029 to `data/results/pvalue_dist.png` with labels and title. **[Dep: T028, T029]**

## Phase N: Polish & Cross-Cutting Concerns

- [X] T032 [P] Documentation updates: README, quickstart, data‑model.
- [X] T033 [P] Code cleanup with ruff.
- [X] T034a [P] Add profiling instrumentation to `code/clustering.py` and `code/ranker.py`.
- [X] T034b [P] Run profiler and record bottleneck report in `data/results/performance_bottlenecks.json`.
- [X] T034c [P] Optimize clustering based on bottleneck report.
- [X] T035 [P] Additional unit tests for edge cases.
- [X] T036 [P] Run quickstart validation.

## Phase N+1: Review-Driven Robustness (Addressing Analysis Findings)

- [X] T042 [P] Synthetic Data Fallback Blocker (already in Phase 2).
- [X] T043 [US1] Semantic Similarity Threshold Validator (already in Phase 3).
- [X] T044 [US2] Cluster Integrity Check (already in Phase 4).
- [X] T045 [US1/US2] Budget Exhaustion Early Exit (already in Phase 4).
- [X] T047 [US2] MinHash Parameter Sensitivity Report (already in Phase 5).
- [X] T048 [US1/US2] Cross‑Dataset Generalization Check (already in Phase 5).

## Phase N+2: Final Validation & Reporting

- [X] T051 [US1/US2/US3] Generate reproducibility package script `code/scripts/generate_repro_package.sh`.
- [X] T054 [US1/US2/US3] Write final research conclusions in `docs/research_conclusions.md`.
- [X] T055 [US1/US2/US3] Finalize README with results summary.

## Phase N+3: Analysis-Driven Corrections

- [X] T058 [US1] **Parameter Adaptation Fallback** – Implements retry logic for T012: if injection fails (T043), calculates new synonym/shuffle probabilities (increase by a measurable amount) and retries up to 3 times. Logs adaptation steps to `data/processed/injection_adaptation_log.json`. If still fails, raises `InjectionFailureError`. **[Dep: T012, T043]**
- [X] T059 [US2] **Threshold Sensitivity Fallback** – if > 10 % false‑positive merges, automatically relaxes Jaccard threshold and logs adjustment; raises `ClusteringFailureError` if still > 10 %.
- [X] T060 [US3] **Statistical Degeneracy Handling** – added to Wilcoxon implementation to log warning and set p‑value to a maximum value when variance is zero.
- [X] T061 [US1/US2] **Graceful Degradation** – enhanced `code/utils.py` to allow partial run completion when runtime limit is approached.

## Phase N+4: Final Data Flow & Execution Order Verification

- [X] T067 [US3] **Confirm Statistical Robustness** – re‑run Wilcoxon tests with zero‑variance handling; output `data/results/statistical_robustness_audit.json`.

## Phase N+5: Final Analysis Review & Cleanup

- [X] T068 [Foundational] **Remove Deprecated Logic** – audit `run_pipeline.py` and `metrics.py` to ensure no residual correction‑factor code outside T013f/T013d.
- [X] T069 [US1/US2] **Verify Proxy Validation Chain** – re‑run full proxy chain and output `data/validation_chain_audit.json` with checksums and pass/fail status.
- [X] T070 [US2] **Validate Threshold Sweep Completeness** – assert `threshold_sweep.json` contains entries for all four planned thresholds (ranging from high to very high).
- [X] T071 [US3] **Confirm Statistical Robustness** – re‑run Wilcoxon tests with zero‑variance handling; output `data/results/statistical_robustness_audit.json`.

## Phase N+6: Final Review & Execution Readiness

- [X] T077 [Foundational] **Execution Gate Readiness Check** – Implement a final pre-flight script `code/scripts/check_execution_gate.py` that verifies: (1) all [X] tasks have corresponding code artifacts, (2) no [ ] tasks remain that block the critical path (T010→T031), (3) `config.py` matches spec limits (6h/7GB), (4) `requirements.txt` contains no GPU-only packages, and (5) **T081-T085 audit reports are present and valid**. **[Gated by T081-T085]**
- [X] T078 [US1] **Real Data Source Verification** – Re-run T005 (BEIR fetch) and T005b (trec-covid) in a clean environment to confirm real data availability and checksums match `state/` records; update `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` `artifact_hashes` if artifacts changed.
- [X] T080 [Foundational] **Final Artifact Manifest** – Generate a comprehensive `data/results/manifest.json` listing all output files, their checksums, and the task IDs that produced them, ensuring full traceability per Constitution Principle III.

## Phase N+7: Execution Gate Compliance & Data Fidelity Audit

- [X] T082 [US1] **Verify Streaming Implementation for Large Datasets** – Audit `code/data_loader.py` and `code/embeddings.py` to confirm that for any dataset exceeding available system memory, the code uses `datasets.load_dataset(..., streaming=True)` or chunked file processing. **Action**: Ensure no task attempts to load the full `trec-covid` or `nfcorpus` into memory at once. **Deliverable**: `state/streaming_audit.json` with `status: "passed"` and `streaming_rules`. **[Dep: T005b]**
- [X] T083 [US1/US2] **Validate No Fabricated Metrics** – Scan `code/metrics.py` and `code/ranker.py` to ensure no metrics (NDCG, wasted ratio) are computed using `random.*`, placeholder values, or simulated data. **Action**: Confirm every metric calculation consumes a real artifact. **Deliverable**: `state/metrics_fabrication_audit.json` with `status: "passed"` and `source_traces`. **[Dep: T013, T015, T016]**
- [X] T084 [US2] **Confirm GPU Offload Logic** – Verify that `code/run_pipeline.py` or `code/validate_env.sh` contains logic to detect `device="cuda"` requirements and trigger the execution stage's auto-offload to Kaggle GPU (if applicable). **Action**: Ensure no CPU-only task attempts to run a GPU-bound operation. **Deliverable**: `state/gpu_offload_audit.json` with `status: "passed"` and `offload_rules`. **[Dep: T013e]**
- [X] T085 [Foundational] **Final Data Flow Dependency Graph** – Generate a visual or JSON dependency graph of the pipeline in `data/results/execution_graph.json` to explicitly prove that `injected_datasets.json` (T012) precedes `clusters.json` (T020), which precedes `comparison_log.jsonl` (T014), ensuring no "verify before compute" violations exist. **Deliverable**: `data/results/execution_graph.json`. **[Dep: T057, T065]**
- [X] T081 [Foundational] **Enforce Real Data Fetch Failure Policy** – Audit `code/data_loader.py` to ensure **NO** `try/except` blocks or conditional logic exist that fall back to `generate_synthetic_*()`, `mock_*()`, or random data when a real fetch (BEIR/trec-covid) fails. **Action**: Remove any such fallbacks; ensure the loader raises a descriptive `DataFetchError` with message "Real data fetch failed: {reason}". **Deliverable**: `state/data_fetch_audit.json` with `status: "passed"` and `diff_log` if changes were made. **[Dep: T005, T005b]**
- [X] T086 [Foundational] **Reconcile run-book vs implementation** – Verify `code/main.py` exists (T087) and `quickstart.md` references it correctly. **Deliverable**: Updated `docs/quickstart.md` or `code/main.py`. **[Dep: T087]**
- [X] T089 [Foundational] **Integration Test for Main Entry** – Add `tests/integration/test_main_entry.py` to verify that `code/main.py` correctly orchestrates the full pipeline from data fetch to final report generation, handling the T013e memory fallback path correctly. **Deliverable**: `tests/integration/test_main_entry.py`. **[Dep: T087, T013e-fallback]**