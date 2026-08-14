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

## Phase 1: Setup (Shared Infrastructure)

- [X] T000 [Foundational] Update `specs/001-llmxive-prp-redundancy/spec.md` to correct the typo in FR-006 ("limit of hours" → "limit of 6 hours"), ensuring the Single Source of Truth (Constitution Principle IV) is accurate.
- [X] T000b [Foundational] **(Spec Fix)** Edit `specs/001-llmxive-prp-redundancy/spec.md` to replace the ambiguous wording in FR-006 with a concrete hard runtime limit of **6 hours**. *Plan‑root cause; flagged for downstream spec update.*
- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python project with `requirements.txt` (beir, sentence-transformers, datasketch, scikit-learn, scipy, pandas, numpy, pytest, nltk, onnx, onnxruntime, transformers, huggingface_hub, llama-cpp-python); **Removed heavy GPU-specific dependencies (`bitsandbytes`, `tinyllama`, `accelerate`); replaced with CPU-native LLM inference tools (`llama-cpp-python`) and verified absence of GPU libraries.**
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 [P] Setup configuration management in `code/config.py` with a schema for `MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB` allowing parameterization, setting default values explicitly to **6 hours** and **7GB** respectively, serving FR-006 and Constitution Principle VII.
- [X] T004a [P] Implement watchdog/signal handler in `code/utils.py` to terminate the pipeline if runtime exceeds a **practical threshold** (5.5 h) or memory exceeds **7 GB**, serving FR-006 enforcement. The handler reads the constants from T004 and uses a dual‑layer kill: first `psutil` termination, then fallback to `ulimit` when cgroups are unavailable.
- [X] T004b-1 [P] Implement a "Check cgroups Availability" step in `code/validate_env.sh` to detect if `cgroups` v2 are present.
- [X] T004b-2 [P] Implement a "Configure cgroups" step in `code/validate_env.sh` that sets memory limits **only** when cgroups are available.
- [X] T004b-3 [P] Implement a "Fallback to ulimit/psutil" step in `code/validate_env.sh` for environments lacking cgroups (e.g., GitHub Actions).
- [X] T005 [P] Implement BEIR data loader in `code/data_loader.py` to fetch `nfcorpus` and `scifact` via `beir` library.
- [X] T005a [P] Calculate SHA-256 checksums of raw BEIR files fetched by T005 and record them in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` under `artifact_hashes`.
- [X] T005b [P] Extend BEIR loader to fetch `trec-covid` for FR‑009 validation.
- [X] T006 [X] Implement logging infrastructure in `code/logging_config.py` to record every pairwise comparison and resource usage stats. The log format is JSONL (`data/processed/comparison_log.jsonl`). **(Completed)**
- [X] T006a [P] Verify existence and non‑empty status of `data/processed/comparison_log.jsonl` before any downstream task runs; abort with `DataFlowViolationError` if missing. **(Verification task)**
- [X] T007 Create base entities: `CandidateList` and `ComparisonPair` dataclasses in `code/models.py`.
- [X] T008 [P] Implement environment validation script `code/validate_env.sh` to ensure CPU‑only constraints and no GPU dependencies.
- [X] T050 [P] Update `code/validate_env.sh` to check availability of `all-MiniLM-L6-v2` model on CPU.
- [X] T042 [P] Add "Synthetic Data Fallback Blocker" test in `tests/unit/test_data_loader.py` that asserts a `RuntimeError` is raised when BEIR fetch fails, preventing silent synthetic fallback.
- [X] T041 [Foundational] Add "Data Integrity Check" in `code/run_pipeline.py` that verifies presence and integrity of all intermediate artifacts before proceeding.

## Phase 3: User Story 1 – Quantify Redundancy‑Induced Efficiency Loss (Priority: P1)

- [X] T010 [P] Unit test for synthetic redundancy injection logic in `tests/unit/test_data_loader.py::test_synthetic_injection_creates_clusters`; asserts injected clusters have pairwise cosine similarity > 0.95 (FR‑002).
- [X] T011 [P] Unit test for "wasted" call classification proxy in `tests/unit/test_metrics.py`.
- [X] T012 [X] **Synthetic Redundancy Injection** in `code/data_loader.py` using synonym replacement (probability 0.3) and sentence shuffling (window 2) to create **≥ 20 clusters** of **3–5** near‑duplicate passages with cosine similarity > 0.95. Output: `data/processed/injected_datasets.json`. Includes validation of cluster count; on failure triggers fallback T058.
- [X] T043 [X] **Semantic Similarity Threshold Validator** – reads `injected_datasets.json`, verifies average injected similarity > 0.95 and that at least 20 clusters exist; retries with higher intensity up to 3 attempts, then logs `DataInjectionWarning` and proceeds with achieved data.
- [X] T014 [X] **Baseline Active Ranker** – runs on the (potentially validated) injected dataset (or raw data if validation skipped) to generate `data/processed/comparison_log.jsonl` and `data/processed/unique_subset.json` (unique‑only baseline). Uses CPU‑light embedding model (`bert-base-uncased`) for pairwise scoring.
- [X] T013 [X] **Wasted Call Counter** – parses `comparison_log.jsonl` to count pairs with cosine similarity > 0.95, writes `data/results/flagged_pairs_count.json`.
- [X] T013a [X] **Actual Budget Recorder** – reads `comparison_log.jsonl` to compute total number of LLM calls executed, writes `data/results/budget_config.json` (`actual_budget`, `configured_budget`).
- [X] T013b [X] **Sample Size Calculator** – determines sample size = max(10, of flagged count) and writes `data/results/sample_config.json`. If flagged count = 0, writes `skip_validation: true` and empty list.
- [X] T013c [X] **Consensus Sample Selector** – randomly selects `sample_size` indices from flagged pairs (using `RANDOM_SEED`), writes `data/results/consensus_sample.json`.
- [X] T013e [ ] **LLM Consensus Validation** – loads **TinyLlama‑1.1B‑Chat‑v1.0 (Q4_K_M)** from ` via `llama-cpp-python`. Performs generative voting on the sample; writes `data/results/consensus_ground_truth.json`. Memory check: abort and trigger fallback if `psutil.virtual_memory().available < 3 GB`.
- [X] T013e-proxy [ ] **Proxy‑Only Fallback** – copies cosine‑based labels to `consensus_ground_truth.json` with `consensus_status: "proxy_fallback"`; runs only if T013e fails or is skipped.
- [X] T013f [X] **Correction Factor Calculation** – compares proxy labels to ground truth (from T013e or proxy) to compute precision, recall, confusion matrix; writes `data/results/correction_factor.json`. Raises `CorrectionFactorCalculationError` if ground truth unavailable.
- [X] T015 [X] **NDCG@10 for Baseline** – calculates NDCG@10 for baseline ranker against BEIR relevance judgments; writes `data/results/us1_baseline_ndcg.json`.
- [X] T016 [X] **NDCG@10 for Redundant Run** – calculates NDCG@10 for the full redundant dataset; writes `data/results/us1_redundant_ndcg.json`.
- [X] T017a [X] **Real‑World Validation (nfcorpus)** – scans `nfcorpus` for existing near‑duplicates (cosine > 0.95), logs results in `data/results/real_world_nfcorpus.json`. If none found, logs `validation_skipped`.
- [X] T017b [X] **Real‑World Validation (scifact)** – same as above for `scifact`, output `data/results/real_world_scifact.json`.
- [X] T017c [X] **Real‑World Validation (trec-covid)** – scans `trec-covid` for near‑duplicates, writes `data/results/real_world_trec_covid.json`.

## Phase 4: User Story 2 – Validate CPU‑Tractable Pre‑Clustering Recovery (Priority: P2)

- [X] T018 [P] Unit test for MinHash‑LSH clustering logic with Jaccard > 0.95 in `tests/unit/test_clustering.py`.
- [X] T019 [P] Integration test for full pipeline execution with resource limits in `tests/integration/test_full_pipeline.py`.
- [X] T020 [X] **MinHash‑LSH Clustering** – groups near‑duplicates using `datasketch` with Jaccard threshold **0.95**; writes `data/processed/clusters.json`.
- [X] T044 [X] **Cluster Integrity Check** – verifies that > 95 % of intra‑cluster Jaccard similarities exceed 0.95; logs warning or triggers re‑run with relaxed threshold.
- [X] T024a [X] **Labeled Subset Generation** – builds a labeled subset using ground truth from `consensus_ground_truth.json` (or proxy if LLM failed) for correlation analysis. If only proxy is available, logs `CorrelationValidationSkipped` and writes `data/results/correlation_validation_skipped.json`.
- [X] T024 [X] **Jaccard‑Cosine Correlation Validation** – computes Pearson correlation between MinHash Jaccard and cosine similarity on the labeled subset; writes `data/results/jaccard_cosine_corr.json`.
- [X] T021 [X] **Pre‑Clustering Filter** – applies MinHash clusters to reduce candidate pool before ranking; logs reduction percentage. **[Dep: T012, T020]**
- [X] T022 [X] **NDCG@10 for Clustering‑Aided Variant** – calculates NDCG@10 after pre‑clustering; writes `data/results/us2_ndcg.json`.
- [X] T023 [X] **Resource Monitor** – enforces runtime and RAM limits during the full pipeline; writes `data/processed/resource_log.json`.
- [X] T025 [X] **Threshold Sweep Definition** – adds config entries for sweep values `[0.85, 0.90, 0.95, 0.98]` in `code/config.py`.
- [X] T025b [X] **Threshold Sweep Execution** – runs pipeline for each sweep value across a high-precision range; aggregates results into `data/results/threshold_sweep.json`.
- [X] T025c [X] **Sweep Result Aggregation** – computes mean and std for NDCG and wasted ratio per threshold; updates `threshold_sweep.json`.
- [X] T025d [X] **Optimal Threshold Selection** – identifies best threshold based on NDCG recovery and wasted‑ratio reduction; records in `threshold_sweep.json`.
- [X] T025b-ext [P] **Optional Fine‑Grained Sweep** – if sensitivity peak is near a boundary, runs additional thresholds (e.g., 0.955) and merges results.

## Phase 5: User Story 3 – Statistical Significance of Efficiency Gains (Priority: P3)

- [X] T026 [P] Unit test for Wilcoxon signed‑rank test and Bonferroni correction in `tests/unit/test_metrics.py`.
- [X] T027 [X] **Multi‑Seed Execution Loop** – runs both baseline and clustering‑aided pipelines for **5 independent seeds**; logs seeds to `data/results/seeds.json`.
- [X] T028 [X] **Wilcoxon Test on NDCG@10** – compares NDCG scores across seeds; writes `data/results/wilcoxon_ndcg.json`.
- [X] T029 [X] **Wilcoxon Test on Wasted Ratio** – compares wasted ratios; writes `data/results/wilcoxon_wasted.json`.
- [X] T029a [X] **P‑Value Aggregation** – aggregates p‑values from T028 and T029 into `data/results/p_values_family.json`.
- [X] T030 [X] **Bonferroni Correction** – applies correction to aggregated p‑values; writes `data/results/bonferroni_corrected.json`.
- [X] T031 [X] **Statistical Report Generation** – creates `data/results/statistical_report.md` including Bonferroni‑corrected p‑values, corrected wasted ratio, and a disclaimer if `validated: false` in `us1_efficiency_ratio.json`.

## Phase N: Polish & Cross-Cutting Concerns

- [X] T032 [P] Documentation updates: README, quickstart, data‑model.
- [X] T033 [P] Code cleanup with ruff.
- [X] T034a [P] Add profiling instrumentation to `code/clustering.py` and `code/ranker.py`.
- [X] T034b [X] Run profiler and record bottleneck report in `data/results/performance_bottlenecks.json`.
- [X] T034c [P] Optimize clustering based on bottleneck report.
- [X] T035 [P] Additional unit tests for edge cases.
- [X] T036 [X] Run quickstart validation.

## Phase N+1: Review-Driven Robustness (Addressing Analysis Findings)

- [X] T042 [P] Synthetic Data Fallback Blocker (already in Phase 2).
- [X] T043 [US1] Semantic Similarity Threshold Validator (already in Phase 3).
- [X] T044 [US2] Cluster Integrity Check (already in Phase 4).
- [X] T045 [US1/US2] Budget Exhaustion Early Exit (already in Phase 4).
- [X] T047 [US2] MinHash Parameter Sensitivity Report (already in Phase 5).
- [X] T048 [US1/US2] Cross‑Dataset Generalization Check (already in Phase 5).

## Phase N+2: Final Validation & Reporting

- [ ] T051 [US1/US2/US3] Generate reproducibility package script `code/scripts/generate_repro_package.sh`.
- [ ] T054 [US1/US2/US3] Write final research conclusions in `docs/research_conclusions.md`.
- [X] T055 [US1/US2/US3] Finalize README with results summary.

## Phase N+3: Analysis-Driven Corrections

- [ ] T057 [US1/US2] **Data Flow Correction** – enforce strict ordering: `injected_datasets.json` → `clusters.json` → `unique_subset.json` → `comparison_log.jsonl` → downstream. Raise `PipelineDependencyError` on violation.
- [X] T058 [US1] **Parameter Adaptation Fallback** – already used by T012/T043 for injection retries.
- [ ] T059 [US2] **Threshold Sensitivity Fallback** – if > 10 % false‑positive merges, automatically relax Jaccard threshold and log adjustment; raise `ClusteringFailureError` if still > 10 %.
- [X] T060 [US3] **Statistical Degeneracy Handling** – added to Wilcoxon implementation to log warning and set p‑value to 1.0 when variance is zero.
- [X] T061 [US1/US2] **Graceful Degradation** – enhanced `code/utils.py` to allow partial run completion when runtime limit is approached.

## Phase N+4: Final Data Flow & Execution Order Verification

- [X] T065 [US1/US2] **Dependency Graph Validator** – validates existence and JSON schema of `injected_datasets.json` and `clusters.json` before pipeline start.
- [X] T065a [US1/US2] **Schema Definitions** – provides inline JSON Schemas for `injected_datasets.json` and `clusters.json`.
- [X] T066 [US1/US2] **Artifact Chain Verification** – checks full chain from injection to final metrics, aborting on missing/invalid artifacts.
- [X] T067 [US3] **Confirm Statistical Robustness** – re‑run Wilcoxon tests with zero‑variance handling; output `data/results/statistical_robustness_audit.json`.

## Phase N+5: Final Analysis Review & Cleanup

- [X] T068 [Foundational] **Remove Deprecated Logic** – audit `run_pipeline.py` and `metrics.py` to ensure no residual correction‑factor code outside T013f/T013d.
- [X] T069 [US1/US2] **Verify Proxy Validation Chain** – re‑run full proxy chain and output `data/validation_chain_audit.json` with checksums and pass/fail status.
- [X] T070 [US2] **Validate Threshold Sweep Completeness** – assert `threshold_sweep.json` contains entries for all four planned thresholds (0.85, 0.90, 0.95, 0.98).
- [X] T071 [US3] **Confirm Statistical Robustness** – re‑run Wilcoxon tests with zero‑variance handling; output `data/results/statistical_robustness_audit.json`.

## Phase N+6: New Task Additions (Review Feedback)

- [ ] T072 [P][US1] Create a unit test to verify the correct behavior of the "wasted call" counter when the comparison log file is empty, ensuring it handles edge cases gracefully and does not raise an error.
- [ ] T073 [P][US2] Implement a mechanism to automatically adjust the MinHash LSH threshold based on dataset characteristics (e.g., average document length), aiming to optimize clustering performance and minimize false positives.
- [ ] T074 [US1/US2] Add detailed logging statements within the data loading and preprocessing steps to track the size of intermediate datasets at each stage, helping identify potential memory bottlenecks or inefficiencies.
- [ ] T075 [P][US3] Implement a visualization tool to display the distribution of p-values from the statistical tests, enabling easier interpretation of results and identification of statistically significant differences.
- [ ] T076 [US1/US2] Add a mechanism to cache intermediate processing steps (e.g., embeddings) to reduce redundant computations and improve overall pipeline execution time, especially when dealing with large datasets.
- [ ] T077 [P][US3] Implement a more robust error handling strategy for the Wilcoxon signed-rank test, including checks for data validity and appropriate logging of any encountered issues or warnings.
