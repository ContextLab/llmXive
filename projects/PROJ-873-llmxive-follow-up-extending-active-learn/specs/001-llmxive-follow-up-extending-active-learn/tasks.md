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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (beir, sentence-transformers, datasketch, scikit-learn, scipy, pandas, numpy, pytest, nltk)
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management in `code/config.py` with hardcoded runtime limit of **6 hours** and memory limit of **7GB** (as mandated by FR-006 and US-2), removing vague references to 'varying configurations' or 'moderate size'
- [X] T004a Implement watchdog/signal handler in `code/config.py` or `code/utils.py` to terminate the pipeline if runtime exceeds 6 hours or memory exceeds 7GB, serving FR-006 enforcement
- [X] T004b [P] Implement OS-level resource limit enforcement (e.g., `ulimit` or `cgroups` configuration script) in `code/validate_env.sh` to harden the 7GB RAM constraint, serving Constitution Principle VII
- [X] T005 [P] Implement BEIR data loader in `code/data_loader.py` to fetch `nfcorpus` and `scifact` via `beir` library
- [X] T005a [P] Calculate SHA-256 checksums of raw BEIR files fetched by T005 and record them in `state/projects/PROJ-873-llmxive-follow-up-extending-active-learn.yaml` under `artifact_hashes`, serving Constitution Principle III (Data Hygiene)
- [X] T005b [P] Implement BEIR data loader extension in `code/data_loader.py` to fetch `trec-covid` dataset via `beir` library specifically for FR-009 validation
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` to record every pairwise comparison and resource usage stats
- [X] T007 Create base entities: `CandidateList` and `ComparisonPair` dataclasses in `code/models.py`
- [X] T008 [P] [Foundational] Implement environment validation script `code/validate_env.sh` to verify CPU-only constraints: check for CUDA availability (must be absent or ignored), ensure no GPU dependencies in `requirements.txt`, and exit 0 on success; serve FR-006 and Constitution Principle VII by confirming the runner environment matches constraints.
- [X] T041 [Foundational] Add a "Data Integrity Check" task in `code/run_pipeline.py` that verifies the presence and non-empty status of all intermediate artifacts (e.g., `unique_subset.json`, `consensus_sample.json`) before proceeding to the next stage, ensuring no silent failures in the pipeline, serving Constitution Principle III.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Redundancy-Induced Efficiency Loss (Priority: P1) 🎯 MVP

**Goal**: Measure the degradation in NDCG@10 and ratio of "wasted" calls when processing redundant retrieval lists.

**Independent Test**: Run the baseline active ranker on a dataset with injected redundancy and verify the "wasted" call ratio and NDCG drop are logged and match acceptance criteria.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for synthetic redundancy injection logic in `tests/unit/test_data_loader.py`
- [X] T011 [P] [US1] Unit test for "wasted" call classification proxy (cosine > 0.95) in `tests/unit/test_metrics.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement synthetic redundancy injection logic in `code/data_loader.py` (synonym replacement via NLTK WordNet, sentence shuffling) to create multiple clusters of near-duplicates per dataset, serving FR-002
- [X] T012a [US1] **Execute** T012 to generate the injected dataset artifacts for `nfcorpus` and `scifact`, writing the results to `data/processed/injected_datasets.json`, serving FR-002
- [X] T013 [US1] Implement cosine similarity proxy calculation logic in `code/metrics.py` using `all-MiniLM-L6-v2` to flag pairs with similarity > 0.95 as "wasted", serving FR-003
- [X] T013a [US1] **Execute** T013 on the injected dataset to produce the list of flagged pairs and their counts, writing the result to `data/results/flagged_pairs_count.json`, serving FR-003
- [X] T013c [US1] Calculate the dynamic sample size for LLM consensus validation using the count from T013a, capped at a maximum limit, and write the result to `data/results/sample_config.json`, serving FR-003
- [X] T013b [US1] Filter logged comparisons from T013a for similarity > 0.95, read sample size from `data/results/sample_config.json`, and select a stratified random sample, writing the sample indices to `data/results/consensus_sample.json`, serving FR-003
- [X] T014 [US1] Implement LLM consensus validation logic in `code/ranker.py` function `validate_proxy_consensus` to estimate ground truth accuracy on the sample defined in `data/results/consensus_sample.json`, serving FR-003. Configure the LLM to use `gpt-4o-mini` with temperature=0.0, max_tokens=200, and prompt template `code/prompts/consensus_validation.txt`.
- [X] T014a [US1] Configure the LLM consensus execution to use `gpt-4o-mini` with temperature=0.0, max_tokens=200, and prompt template `code/prompts/consensus_validation.txt`, ensuring deterministic results
- [X] T014b [US1] **Execute** the LLM consensus validation (T014/T014a) on the sample from T013b to generate ground truth accuracy metrics, writing the result to `data/results/consensus_accuracy.json`, serving FR-003
- [X] T015 [US1] Implement baseline active ranker execution loop in `code/ranker.py` that processes the full candidate list without clustering, serving FR-003
- [X] T015a [US1] Generate the "unique subset" of the candidate list by removing near-duplicates identified in T012a, writing the result to `data/processed/unique_subset.json`, serving US-1
- [X] T015b [US1] Run the baseline active ranker against the unique subset generated in T015a to establish the reference NDCG@10, calculate and log the NDCG@10 drop percentage to `data/results/us1_baseline_metrics.json`, serving US-1
- [X] T016 [US1] Implement NDCG@10 calculation against BEIR ground truth in `code/metrics.py` for both the full redundant run and the unique subset run, serving FR-004
- [X] T017 [US1] Implement synthetic redundancy validation logic in `code/data_loader.py` against the `trec-covid` dataset fetched in T005b to ensure generalizability, serving FR-009
- [X] T037 [US1] Implement explicit failure mode handling in `code/data_loader.py` for the "paraphrasing fails to generate sufficient semantic similarity" edge case: if injected similarity < 0.95, raise a `DataInjectionError` with details rather than silently proceeding, serving Edge Case 2.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Baseline behavior on redundant data)

---

## Phase 4: User Story 2 - Validate CPU-Tractable Pre-Clustering Recovery (Priority: P2)

**Goal**: Verify that MinHash-LSH pre-clustering filters redundant pairs and restores NDCG@10 performance within resource limits.

**Independent Test**: Run the full pipeline (MinHash-LSH + Active Ranker) on the high-redundancy dataset and verify "wasted" call ratio drops and NDCG@10 recovers within 6h/7GB.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MinHash-LSH clustering logic with Jaccard threshold > 0.95 in `tests/unit/test_clustering.py`
- [X] T019 [P] [US2] Integration test for full pipeline execution with resource limits in `tests/integration/test_full_pipeline.py`
  - [X] T019a [P] [US2] Unit test for timeout enforcement in `tests/integration/test_full_pipeline.py`
  - [X] T019b [P] [US2] Unit test for memory limit enforcement in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement MinHash-LSH algorithm in `code/clustering.py` to group near-duplicate passages with Jaccard similarity > 0.95, serving FR-001
- [X] T021 [US2] Implement pre-clustering filter logic in `code/ranker.py` to reduce the candidate pool before ranking (using output from T012a and T020), ensuring pool size reduction >= 30%; if reduction < 30%, abort execution and log a constraint violation, serving US-2
- [X] T022 [US2] Implement NDCG@10 calculation for the clustering-aided variant in `code/metrics.py`, comparing against the unique-only baseline, serving FR-004
- [X] T023 [US2] Implement resource monitoring (time/memory) in `code/run_pipeline.py` to enforce runtime and RAM limits, serving FR-006
- [X] T024a [US2] Generate the labeled subset of pairs required for T024 by computing ground-truth similarity via high-precision embedding (`all-MiniLM-L6-v2`), writing the result to `data/results/labeled_subset.json`, serving FR-008
- [X] T024 [US2] Implement correlation validation logic in `code/metrics.py` between Jaccard (MinHash) and Cosine (Embeddings) similarity on the labeled subset generated in T024a, serving FR-008
- [X] T025 [US2] Implement parameter sweep for MinHash-LSH threshold in `code/run_pipeline.py` to measure sensitivity of NDCG recovery, serving SC-005
- [X] T025a [US2] Compare resulting NDCG curves from T025 against the baseline and output the optimal threshold and sensitivity data to `data/results/threshold_sweep.json` as a machine-readable artifact, serving SC-005
- [X] T038 [US2] Implement strict threshold validation in `code/clustering.py` to detect and log "false positive merges" (unique docs merged) by comparing cluster centroids against original documents; if merge rate > 5%, trigger a warning and fallback to unique-only processing, serving Edge Case 1.
- [X] T039 [US1/US2] Implement a "Low Budget Guardrail" in `code/ranker.py` that halts execution and reports a `BudgetExhaustedError` if the active ranker cannot explore the candidate pool sufficiently (e.g., remaining budget < 5% of pool size) before distinguishing redundant vs. unique items, serving Edge Case 3.
- [X] T040 [US2] Implement a "Consensus Timeout Fallback" in `code/ranker.py` for the LLM consensus validation step: if the validation sample exceeds the allocated time slice, gracefully degrade to using only the cosine proxy for the main loop and log the degradation event, serving Edge Case 4.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline vs. Clustering-Aided comparison)

---

## Phase 5: User Story 3 - Statistical Significance of Efficiency Gains (Priority: P3)

**Goal**: Confirm that improvements in call efficiency and ranking quality are statistically significant.

**Independent Test**: Run both variants over multiple random seeds and perform Wilcoxon signed-rank tests to verify p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Wilcoxon signed-rank test implementation and Bonferroni correction in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement multi-seed execution loop in `code/run_pipeline.py` for both baseline and clustering-aided variants, enforcing exactly **5 independent runs** as per US-3
- [X] T028 [US3] Implement Wilcoxon signed-rank test on NDCG@10 scores in `code/metrics.py`, serving FR-005
- [X] T029 [US3] Implement Wilcoxon signed-rank test on "wasted call" ratios in `code/metrics.py`, serving FR-005
- [X] T030 [US3] Apply Bonferroni correction for multiple hypothesis testing (NDCG and efficiency) in `code/metrics.py`, serving FR-007
- [X] T031 [US3] Generate final statistical report in `data/results/statistical_report.md` explicitly including Bonferroni-corrected p-values and "wasted call" ratio metrics as required by FR-007 and SC-003, serving US-3

**Checkpoint**: All user stories should now be independently functional and statistically validated

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates: Update `README.md` with usage instructions and `docs/quickstart.md` / `docs/data-model.md` with function signatures; verify `README.md` contains `--help` output and all paths are correct; serve Constitution Principle I and V.
- [X] T033 [P] Code cleanup: Run `ruff --fix` on `code/` and `tests/`; verify exit code is 0 and no errors remain; commit the changes with the exact message "Cleanup: ruff fixes"; serve Constitution Principle I and V.
- [X] T034 [P] Performance optimization of MinHash-LSH for CPU efficiency: profile `code/clustering.py`, identify bottlenecks, and optimize using vectorized operations or reduced hash sets if necessary; document changes in `code/clustering.py` comments.
- [X] T035 [P] Additional unit tests for edge cases (strict thresholds, low budgets) in `tests/unit/`
- [X] T036 Run quickstart.md validation to ensure reproducibility

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

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for synthetic redundancy injection logic in tests/unit/test_data_loader.py"
Task: "Unit test for 'wasted' call classification proxy in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic redundancy injection in code/data_loader.py"
Task: "Implement cosine similarity proxy calculation in code/metrics.py"
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

### Review-Driven Refinement

After initial runs:
1. Analyze logs and metrics to identify edge case triggers
2. Execute Phase N+1 tasks (T037-T041) to harden the system
3. Re-run statistical tests (US3) with the hardened pipeline
4. Finalize the statistical report with robustness guarantees

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Tasks T037-T041 are mandatory for scientific rigor and must not be skipped; they address specific failure modes that could invalidate the research conclusions.