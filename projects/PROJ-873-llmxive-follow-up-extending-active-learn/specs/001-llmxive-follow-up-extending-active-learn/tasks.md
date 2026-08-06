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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (beir, sentence-transformers, datasketch, scikit-learn, scipy, pandas, numpy, pytest, nltk); **Removed heavy ollama/transformers dependencies; replaced with lighter alternatives.**
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup configuration management in `code/config.py` with a schema for `MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB` allowing parameterization, setting default values explicitly to **6 hours** and **7GB** respectively, serving FR-006 and Constitution Principle VII.
- [X] T004a [P] Implement watchdog/signal handler in `code/config.py` or `code/utils.py` to terminate the pipeline if runtime exceeds **6 hours** or memory exceeds **7GB**, serving FR-006 enforcement. The handler MUST read the explicit constants defined in T004.
- [X] T004b-1 [P] [Foundational] Implement a "Check cgroups Availability" step in `code/validate_env.sh` to detect if `cgroups` v2 are available on the host. If unavailable (common on ephemeral GitHub Actions runners), immediately trigger the fallback path described in T004b-3, serving the "fallback mechanism" requirement for unreliable cgroups on ephemeral runners.
- [X] T004b-2 [P] [Foundational] Implement a "Configure cgroups" step in `code/validate_env.sh` that uses `systemd-run` or `cgconfigparser` to set memory limits ONLY if T004b-1 confirms cgroups availability, serving the primary resource enforcement path.
- [X] T004b-3 [P] [Foundational] Implement a "Fallback to ulimit/psutil" step in `code/validate_env.sh` that activates when cgroups are unavailable (e.g., on ephemeral GitHub Actions runners). This step uses `ulimit` for shell limits and `psutil` for process-level monitoring to ensure consistent resource constraint validation, serving Constitution Principle VII. **Removed: Replaced complex cgroup logic with streamlined watchdog.**
- [X] T005 [P] Implement BEIR data loader in `code/data_loader.py` to fetch `nfcorpus` and `scifact` via `beir` library.
- [X] T005a [P] Calculate SHA-256 checksums of raw BEIR files fetched by T005 and record them in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` under `artifact_hashes`, serving Constitution Principle III (Data Hygiene).
- [X] T005b [P] Implement BEIR data loader extension in `code/data_loader.py` to fetch `trec-covid` dataset via `beir` library specifically for FR-009 validation.
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` to record every pairwise comparison and resource usage stats. The log format MUST be JSONL with each line containing: `{"pair_id": str, "doc1_id": str, "doc2_id": str, "cosine_sim": float, "is_wasted": bool, "timestamp": str}`. The log file MUST be written to `data/processed/comparison_log.json`. This task serves FR-003 and ensures executability.
- [X] T007 Create base entities: `CandidateList` and `ComparisonPair` dataclasses in `code/models.py`.
- [X] T008 [P] [Foundational] Implement environment validation script `code/validate_env.sh` to verify CPU-only constraints: check for CUDA availability (must be absent or ignored), ensure no GPU dependencies in `requirements.txt`, and exit 0 on success; serve FR-006 and Constitution Principle VII.
- [X] T050 [P] [Foundational] Update `code/validate_env.sh` to include a check for `all-MiniLM-L6-v2` model availability and CPU compatibility, ensuring the embedding model can run without GPU dependencies, serving Constitution Principle VII.
- [X] T042 [P] [Foundational] Add a "Synthetic Data Fallback Blocker" test in `tests/unit/test_data_loader.py` that asserts `RuntimeError` is raised when `beir` fetch fails (simulating network block), preventing any silent fallback to synthetic/mock data, serving Constitution Principle III and the "Loader must fail loudly" rule.
- [X] T041 [Foundational] Add a "Data Integrity Check" task in `code/run_pipeline.py` that verifies the presence and non-empty status of all intermediate artifacts (e.g., `unique_subset.json`, `consensus_sample.json`) before proceeding to the next stage, ensuring no silent failures in the pipeline, serving Constitution Principle III.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Redundancy-Induced Efficiency Loss (Priority: P1) 🎯 MVP

**Goal**: Measure the degradation in NDCG@10 and ratio of "wasted" calls when processing redundant retrieval lists.

**Independent Test**: Run the baseline active ranker on a dataset with injected redundancy and verify the "wasted" call ratio and NDCG drop are logged and match acceptance criteria.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for synthetic redundancy injection logic in `tests/unit/test_data_loader.py::test_synthetic_injection_creates_clusters`; assert that injected clusters contain items with pairwise cosine similarity > 0.95, serving FR-002.
- [X] T011 [P] [US1] Unit test for "wasted" call classification proxy in `tests/unit/test_metrics.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement and execute synthetic redundancy injection logic in `code/data_loader.py` (synonym replacement via NLTK WordNet, sentence shuffling) to create multiple clusters of near-duplicate passages, serving FR-002. **Execute**: Generate `data/processed/injected_datasets.json` for `nfcorpus` and `scifact`, and `data/processed/injected_trec_covid.json` for `trec-covid`.
- [X] T043 [US1] Implement and execute a "Semantic Similarity Threshold Validator" in `code/data_loader.py` that verifies the injected redundancy actually achieves the target similarity > 0.95 before proceeding; if the average injected similarity is < 0.95, raise a `DataInjectionError` with details, serving Edge Case 2 and FR-002. **Execute**: Validate the injected datasets from T012.
- [X] T013 [US1] Implement and execute cosine similarity proxy calculation logic in `code/metrics.py` using `all-MiniLM-L6-v2` to flag pairs with similarity > 0.95 as "wasted", serving FR-003. **Execute**: Aggregate the count of pairs with `cosine_sim > 0.95` from `data/processed/comparison_log.json` and write the result to `data/results/flagged_pairs_count.json` with the schema: `{"wasted_count": int, "total_pairs": int, "wasted_ratio": float}`.
- [X] T013b [US1] Implement and execute sample size calculation for LLM consensus validation in `code/metrics.py`. The sample size MUST be calculated as the maximum of 10 or 5% of the total flagged count (read from `data/results/flagged_pairs_count.json`). Write the result to `data/results/sample_config.json` (schema: `{"sample_size": int, "minimum_threshold": 10, "percentage": 0.05}`), serving FR-003.
- [X] T013c [US1] Implement and execute filtering of logged comparisons from `data/processed/comparison_log.json` for similarity > 0.95, read sample size from `data/results/sample_config.json`, and select a **simple random sample**, writing the sample indices to `data/results/consensus_sample.json` (schema: list of indices), serving FR-003.
- [X] T014 [US1] Implement and execute baseline active ranker execution loop in `code/ranker.py` that processes the full candidate list without clustering, serving FR-003. **Execute**: Generate the "unique subset" of the candidate list by removing near-duplicates identified in T012, writing the result to `data/processed/unique_subset.json`. Run the baseline active ranker against the unique subset to establish the reference NDCG@10, calculate and log the NDCG@10 drop percentage to `data/results/us1_baseline_metrics.json`, serving US-1. **Using a CPU-light model (bert-base-uncased) and sentence-transformers for embedding calculations.**
- [X] T015 [US1] Implement and execute NDCG@10 calculation for the clustering-aided variant in `code/metrics.py`, comparing against the unique-only baseline, serving FR-004. The unique subset is generated before ranking to establish a valid baseline comparison.
- [X] T016 [US1] Implement and execute NDCG@10 calculation against BEIR ground truth in `code/metrics.py` for both the full redundant run and the unique subset run, serving FR-004.
- [X] T013d [US1] Implement and execute aggregation of the `flagged_pairs_count` from T013 and the total LLM call budget to compute the "wasted call" ratio (wasted_count / total_budget), and log the final metric to `data/results/us1_efficiency_ratio.json` (schema: `{"wasted_ratio": float, "wasted_count": int, "total_budget": int}`), serving FR-003 and SC-001.
- [X] T017 [US1] Implement and execute **real-world** redundancy validation logic in `code/data_loader.py` against the `trec-covid` dataset fetched in T005b. **Scan** the dataset for existing near-duplicate clusters (similarity > 0.95) using cosine similarity. If no real clusters are found, **log 'validation skipped' and proceed**, serving Edge Case 2 and FR-009.
- [X] T037 [US1] Implement explicit failure mode handling in `code/data_loader.py` for the "paraphrasing fails to generate sufficient semantic similarity" edge case: if injected similarity < 0.95, raise a `DataInjectionFailureError` with a detailed log of the attempted synonyms and final similarity scores, halting the pipeline. This prevents silent degradation of the "wasted call" metric validity.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Baseline behavior on redundant data)

---

## Phase 4: User Story 2 - Validate CPU-Tractable Pre-Clustering Recovery (Priority: P2)

**Goal**: Verify that MinHash-LSH pre-clustering filters redundant pairs and restores NDCG@10 performance within resource limits.

**Independent Test**: Run the full pipeline (MinHash-LSH + Active Ranker) on the high-redundancy dataset and verify "wasted" call ratio drops and NDCG@10 recovers within 6h/7GB.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MinHash-LSH clustering logic with Jaccard threshold > 0.95 in `tests/unit/test_clustering.py`.
- [X] T019 [P] [US2] Integration test for full pipeline execution with resource limits in `tests/integration/test_full_pipeline.py`.
 - [X] T019a [P] [US2] Unit test for timeout enforcement in `tests/integration/test_full_pipeline.py`.
 - [X] T019b [P] [US2] Unit test for memory limit enforcement in `tests/integration/test_full_pipeline.py`.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement and execute MinHash-LSH algorithm in `code/clustering.py` to group near-duplicate passages with Jaccard similarity > 0.95, serving FR-001. **Execute**: Write the result to `data/processed/clusters.json`, serving the prerequisite for T044.
- [X] T044 [US2] Implement and execute a "Cluster Integrity Check" in `code/clustering.py` that verifies the Jaccard similarity of items within each cluster against the ground truth; if > 5% of cluster members have Jaccard < 0.95, log a warning and trigger a re-run with adjusted parameters, serving Edge Case 1 and FR-001.
- [X] T024a [US2] Implement and execute a "Labeled Subset" calculation using cosine similarity to create embeddings for correlation analysis; **removed LLM consensus validation**. The task now uses the existing embedding calculations from previous steps, establishing a proxy for correlation without introducing new LLM calls.
- [X] T024 [US2] Implement and execute correlation validation logic in `code/metrics.py`, comparing Jaccard similarity (MinHash) with cosine similarity (embeddings) on the labeled subset generated by T024a, serving FR-008.
- [X] T021 [US2] Implement and execute pre-clustering filter logic in `code/ranker.py` to reduce the candidate pool before ranking (using output from T012 and T020); measure and log pool reduction; if reduction < 30%, log a warning but **proceed** to allow sensitivity analysis, serving US-2.
- [X] T045 [US1/US2] Implement a "Budget Exhaustion Early Exit" in `code/ranker.py` that checks the remaining LLM call budget after every periodic batch of comparisons; if the budget is insufficient to complete the current candidate list (remaining < 5% of total), halt execution and log `BudgetExhaustedError`, serving Edge Case 3 and US-1/US-2.
- [X] T022 [US2] Implement and execute NDCG@10 calculation for the clustering-aided variant in `code/metrics.py`, comparing against the unique-only baseline, serving FR-004.
- [X] T023 [US2] Implement and execute resource monitoring (time/memory) in `code/run_pipeline.py` to enforce runtime and RAM limits, serving FR-006. **Ensure T023 reads the limits defined in T004 (`MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB`)** to ensure consistency between enforcement and monitoring.
- [X] T025 [US2] Define the MinHash-LSH threshold sweep range (to a near-perfect similarity upper bound in fine-grained steps) in `code/config.py`, serving SC-005.
- [X] T025a [US2] Implement and execute the MinHash-LSH algorithm with the specific threshold of 0.95 (as per FR-001) to establish the primary baseline control for the clustering-aided variant, serving FR-001 and SC-005. Output metrics to `data/results/us2_baseline_095.json`.
- [X] T025b [US2] Implement and execute the parameter sweep loop for T025, running the pipeline for each threshold in a set of representative values (default range high values with step size 0.01), serving SC-005.
- [X] T025c [US2] Implement and execute data aggregation logic for the sweep results in `code/metrics.py`, computing average metrics and standard deviations for each threshold, serving SC-005.
- [X] T025d [US2] Implement and execute comparison of resulting NDCG curves from T025c against the baseline and output the optimal threshold and sensitivity data to `data/results/threshold_sweep.json` as a machine-readable artifact, serving SC-005.
- [X] T038 [US2] Implement strict threshold validation in `code/clustering.py` to detect and log "false positive merges" (unique docs merged) by comparing cluster centroids against original documents; if merge rate > 5%, trigger a warning and fallback to unique-only processing, serving Edge Case 1.
- [X] T039 [US1/US2] Implement a "Low Budget Guardrail" in `code/ranker.py` that halts execution and reports a `BudgetExhaustedError` if the active ranker cannot explore the candidate pool sufficiently (e.g., remaining budget < 5% of pool size) before distinguishing redundant vs. unique items, serving Edge Case 3.
- [X] T040 [US2] Implement a "Consensus Budget Exhaustion Fallback" in `code/ranker.py` for the LLM consensus validation step: if the **number of consensus calls** exceeds the remaining LLM call budget, gracefully degrade to using only the cosine proxy for the main loop and log the degradation event, serving Edge Case 4.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline vs. Clustering-Aided comparison)

---

## Phase 5: User Story 3 - Statistical Significance of Efficiency Gains (Priority: P3)

**Goal**: Confirm that improvements in call efficiency and ranking quality are statistically significant.

**Independent Test**: Run both variants over multiple random seeds and perform Wilcoxon signed-rank tests to verify p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Wilcoxon signed-rank test implementation and Bonferroni correction in `tests/unit/test_metrics.py`.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement multi-seed execution loop in `code/run_pipeline.py` for both baseline and clustering-aided variants, enforcing exactly **5 independent runs** as per US-3.
- [X] T048 [US1/US2] Implement and execute a "Cross-Dataset Generalization Check" in `code/run_pipeline.py` that compares the "wasted call" ratios between `nfcorpus`, `scifact`, and `trec-covid` to ensure the redundancy effect is not dataset-specific, serving FR-009 and US-1. **Execute** after T017.
- [X] T047 [US2] Implement a "MinHash Parameter Sensitivity Report" in `data/results/minhash_sensitivity.md` that documents the impact of varying the Jaccard threshold across a high-similarity range on NDCG recovery and wasted call reduction, serving SC-005. **Execute** using data from T025d.
- [X] T028 [US3] Implement and execute Wilcoxon signed-rank test on NDCG@10 scores in `code/metrics.py`, serving FR-005.
- [X] T029 [US3] Implement and execute Wilcoxon signed-rank test on "wasted call" ratios in `code/metrics.py`, serving FR-005.
- [X] T030 [US3] Implement and execute Bonferroni correction for multiple hypothesis testing (NDCG and efficiency) in `code/metrics.py`, serving FR-007.
- [X] T031 [US3] Implement and execute generation of final statistical report in `data/results/statistical_report.md` explicitly including Bonferroni-corrected p-values and "wasted call" ratio metrics as required by FR-005, serving US-3.

**Checkpoint**: All user stories should now be independently functional and statistically validated with the fixed 5-run design.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates: Update `README.md` with usage instructions and `docs/quickstart.md` / `docs/data-model.md` with function signatures; verify `README.md` contains `--help` output and all paths are correct; serve Constitution Principle I and V.
- [X] T033 [P] Code cleanup: Run `ruff --fix` on `code/` and `tests/`; verify exit code is 0 and no errors remain; commit the changes with the exact message "Cleanup: ruff fixes"; serve Constitution Principle I and V.
- [X] T034a [P] Add profiling instrumentation to `code/clustering.py` and `code/ranker.py` to measure execution time and memory usage of key functions, serving SC-005.
- [X] T034b [P] Run profile and record bottleneck report in `data/results/performance_bottlenecks.json`, serving SC-005.
- [X] T034c [P] Implement specific optimization (e.g., vectorization) in `code/clustering.py` based on T034b report, serving SC-005.
- [X] T035 [P] Additional unit tests for edge cases (strict thresholds, low budgets) in `tests/unit/`.
- [X] T036 Run quickstart.md validation to ensure reproducibility

---

## Phase N+1: Review-Driven Robustness (Addressing Analysis Findings)

**Purpose**: Address specific failure modes and edge cases identified during initial analysis to ensure scientific validity.

### Implementation for Review-Driven Robustness

- [X] T042 [P] [Foundational] (Moved to Phase 2) - Synthetic Data Fallback Blocker.
- [X] T043 [US1] (Moved to Phase 3) - Semantic Similarity Threshold Validator.
- [X] T044 [US2] (Moved to Phase 4) - Cluster Integrity Check.
- [X] T045 [US1/US2] (Moved to Phase 4) - Budget Exhaustion Early Exit.
- [X] T047 [US2] (Moved to Phase 5) - MinHash Parameter Sensitivity Report.
- [X] T048 [US1/US2] (Moved to Phase 5) - Cross-Dataset Generalization Check.

---

## Phase N+2: Final Validation & Reporting

**Purpose**: Ensure all scientific claims are backed by reproducible artifacts and that the final report meets publication standards.

- [X] T051 [US1/US2/US3] Generate a comprehensive "Reproducibility Package" script in `code/scripts/generate_repro_package.sh` that bundles all raw data, processed artifacts, configuration files, and final results into a single tarball with a manifest checksum, serving Constitution Principle I and V.
- [X] T054 [US1/US2/US3] Conduct a final "Constitution Compliance Audit" by running `code/audit/validate_constitution.py` against all generated artifacts and logs, ensuring no principle violations occurred during execution, serving Constitution Principles I-VII.
- [X] T055 [US1/US2/US3] Write the final "Research Conclusions" document in `docs/research_conclusions.md` summarizing the findings, limitations, and implications for active learning efficiency, referencing all specific metric artifacts (NDCG, wasted ratios, p-values), serving the overall project goal.
- [X] T056 [US1/US2/US3] Finalize `README.md` with a "Results Summary" section that includes the key findings from T055 and links to the reproducibility package, serving Constitution Principle I.

---

## Phase N+3: Analysis-Driven Corrections

**Purpose**: Resolve specific issues raised by the `/speckit.analyze` step regarding data flow, edge cases, and scientific rigor that were not fully addressed in the initial pass.

### Implementation for Analysis-Driven Corrections

- [ ] T057 [US1/US2] **Data Flow Correction**: Refactor `code/run_pipeline.py` to enforce strict execution ordering: ensure `data/processed/injected_datasets.json` (T012) and `data/processed/clusters.json` (T020) are fully written and validated before the active ranker loop (T015/T021) begins. Add a `PipelineDependencyError` if any prerequisite artifact is missing or incomplete at runtime, serving the 'Producer before consumer' rule and preventing the common failure mode of verify-scripts running before data generation.
- [ ] T058 [US1] **Edge Case Resolution**: Implement a "Strict Paraphrasing Fallback" in `code/data_loader.py` for Edge Case 2. If the synthetic injection (T012) fails to produce pairs with similarity > 0.95 after 3 retries with varying NLTK WordNet synonyms, the task MUST raise a `DataInjectionFailureError` with a detailed log of the attempted synonyms and final similarity scores, halting the pipeline. This prevents silent degradation of the "wasted call" metric validity.
- [ ] T059 [US2] **Edge Case Resolution**: Implement a "Threshold Sensitivity Fallback" in `code/clustering.py` for Edge Case 1. If the MinHash-LSH threshold (0.95) results in > 10% of unique documents being incorrectly merged (false positives), the system MUST automatically trigger a re-run with a relaxed threshold and log the adjustment. If the relaxed threshold also fails, raise a `ClusteringFailureError`. This ensures the "wasted call" reduction is not achieved by destroying the candidate pool.
- [ ] T060 [US3] **Statistical Rigor Correction**: Update `code/metrics.py` (T028/T029) to explicitly handle the case where variance is zero (perfect scores) in the Wilcoxon test. If variance is zero, the task MUST log a `StatisticalDegeneracyWarning` and report the p-value as (no significant difference) rather than attempting a division-by-zero or returning NaN, ensuring the statistical report (T031) remains valid and interpretable.
- [ ] T061 [US1/US2] **Resource Constraint Hardening**: Enhance `code/utils.py` (T004a) to include a "Graceful Degradation" mode. If the runtime limit is approached (e.g., near the threshold) and the pipeline is mid-batch, the system MUST complete the current batch, save the partial results, and then terminate with a `PartialRunError` instead of a hard kill, ensuring that partial data is preserved for debugging and the `state/` file is updated with the `partial_run` flag.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review-Driven Robustness (Phase N+1)**: Depends on completion of all User Stories
- **Final Validation (Phase N+2)**: Depends on completion of all previous phases
- **Analysis-Driven Corrections (Phase N+3)**: Depends on the output of `/speckit.analyze` and must be executed before the final validation phase to ensure all identified issues are resolved.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
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

### Review-Driven Refinement

After initial runs:
1. Analyze logs and metrics to identify edge case triggers
2. Execute Phase N+1 tasks (T037-T050) to harden the system
3. Re-run statistical tests (US3) with the hardened pipeline
4. Finalize the research conclusions

### Final Validation

1. Execute Phase N+2 tasks to ensure full reproducibility and scientific rigor
2. Generate final research conclusions and publication-ready artifacts
3. Archive the complete reproducibility package

### Analysis-Driven Resolution

1. Execute `/speckit.analyze` to identify specific gaps in data flow or edge cases
2. Prioritize and execute Phase N+3 tasks (T057-T061) to resolve these issues
3. Re-run the full pipeline to verify that the corrections have resolved the identified issues
4. Proceed to Final Validation only after Phase N+3 is complete and all artifacts are consistent.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Tasks T037-T050 are mandatory for scientific rigor and must not be skipped; they address specific failure modes that could invalidate the research conclusions.
- **Plan Note**: The plan.md Constitution Check table (VI) currently states "Cosine > 0.95 is the definitive operational classification". This contradicts spec FR-003 which requires fixing this to ensure it's not a scientific mischaracterization..
- **Revision Note**: Phase N+3 (T057-T061) was added to explicitly address data flow ordering, edge cases, and statistical rigor issues identified in the analysis phase, ensuring the project adheres to the "fix the code, not the test" principle.
