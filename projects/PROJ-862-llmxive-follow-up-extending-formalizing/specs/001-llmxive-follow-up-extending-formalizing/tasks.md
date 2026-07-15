# Tasks: llmXive Follow-up: Input Noise Injection for Latent Separability

**Input**: Design documents from `/specs/001-lm-axive-noise-injection/`
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

- [X] T001 [P] Create `code/` directory and `code/__init__.py`
- [X] T002 [P] Create `data/` directory and `data/raw/.gitkeep`, `data/processed/.gitkeep`
- [ ] T003 [P] Create `tests/` directory and `tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/requirements.txt` with pinned versions (transformers, torch, sentence-transformers, scikit-learn, bertscore, pandas, numpy, pytest)
- [X] T005 [P] Setup virtual environment instructions in `docs/` (or `code/scripts/setup.sh`)
- [ ] T006 [P] Implement `code/data_loader.py` to fetch the reasoning dataset (BigBench subset) from a verified URL/HF dataset, ensuring `expected_answer` column exists, and **raise ConfigurationError and halt** if missing (NO synthetic fallback)
- [~] T007 [P] Implement `code/model_utils.py` to load the frozen transformer model (Llama or distilled variant) in CPU-only mode with `torch.no_grad()` and `model.eval()`
- [~] T008 [P] Implement `code/streaming_utils.py` to provide chunked/batched iteration over large datasets to respect the available RAM limit
- [~] T008b [P] Implement `code/memory_monitor.py` to instrument `tracemalloc` and enforce a hard "peak RSS ≤ 7GB" failure condition; raise `MemoryLimitExceeded` if the threshold is breached during execution (SC-004)
- [~] T009 [P] Implement `code/config.py` to define noise sweep parameters ($\sigma \in [\text{low}, \text{high}]$), model paths, random seeds, and memory limits
- [~] T010 [P] Create data schema contracts in `specs/001-lm-axive-noise-injection/contracts/` (dataset.schema.yaml, latent-vector.schema.yaml, statistical-result.schema.yaml, validity-log.schema.yaml)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Latent Vector Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract baseline "thought" token hidden states for the reasoning dataset to establish the control group.

**Independent Test**: Run extraction on a single task type; verify output CSV contains normalized vectors matching model hidden size and correct PairIDs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Contract test for baseline output schema in `tests/contract/test_baseline_vectors.py`
- [~] T012 [P] [US1] Unit test for hidden state extraction logic in `tests/unit/test_extract_hidden.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data_loader.py` function to pair questions by task type and assign unique `PairID`s (output: `data/processed/pairing_config.json`)
- [ ] T014 [US1] Implement `code/model_utils.py` function `extract_thought_vector(model, input_ids, thought_token_pos)` to return the hidden state vector
- [ ] T015 [US1] Implement `code/main.py` baseline extraction loop: Load data -> Extract vectors -> Normalize to unit length -> Save to `data/processed/baseline_vectors.csv`
- [ ] T016 [US1] Add validation to ensure output vectors match model hidden dimension and are L2-normalized
- [ ] T017 [US1] Add logging for baseline extraction progress and memory usage

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Noise-Augmented Perturbation & Re-Extraction (Priority: P2)

**Goal**: Inject controlled Gaussian noise into input embeddings, project to nearest valid token, and re-extract latent vectors while enforcing semantic validity.

**Independent Test**: Inject known perturbation; verify embedding distance matches expected Euclidean distance and output retains ground truth (BERTScore ≥ 0.85).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for noise injection and token projection math in `tests/unit/test_perturbation.py`
- [ ] T019 [P] [US2] Contract test for validity log schema in `tests/contract/test_validity_log.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/perturbation.py` function `inject_and_project(embedding, sigma, model_embedding_matrix)` that adds Gaussian noise and **projects to nearest valid token by minimizing Euclidean distance against model.embedding_matrix**, returning `perturbed_token_ids` and `perturbed_embeddings`
- [ ] T021 [US2] Implement `code/validity_check.py` function `check_input_drift(baseline_input, perturbed_input, sbert_model)` using `sentence-transformers/all-MiniLM-L6-v2` (threshold ≥ 0.95); **explicitly exclude pairs failing this check (cosine similarity < 0.95) from the dataset immediately** and save the filtered pair set to `data/processed/filtered_pairs_input_drift.csv` (FR-009)
- [ ] T022 [US2] Implement `code/validity_check.py` function `check_output_validity(model_output, expected_answer)` using BERTScore (F1 ≥ 0.85) and perplexity bound (≤ 2.0x baseline); **if the dataset lacks an `expected_answer` column, raise a ConfigurationError and halt** (FR-006)
- [ ] T023 [US2] Implement `code/validity_check.py` function `check_validity_collapse(pass_rate, threshold)` to detect if >90% of pairs fail at a specific $\sigma$
- [ ] T024 [US2] Implement `code/main.py` perturbation sweep loop: Iterate $\sigma$ across a range of small positive values. -> **Call streaming/batching logic (T008)** -> Perturb inputs -> Extract vectors -> Run validity checks -> **Call check_validity_collapse; if true: record validity collapse point (sigma, pass-rate) for THIS TASK TYPE to validity_log.csv and break ONLY the sigma-loop for this task type, then continue to the next task type** -> Save results (FR-003, FR-011)
- [ ] T025 [US2] Save perturbed vectors and metadata to `data/processed/perturbed_vectors.csv` linked by `PairID` and `sigma`
- [ ] T026 [US2] Add logging for sweep progress and memory usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Separability Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing on the filtered pairs to determine if noise injection significantly increased latent separability.

**Independent Test**: Feed mock dataset with known difference; verify test selects correct distribution (t-test vs Wilcoxon) and reports correct p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for normality check and test selection logic in `tests/unit/test_statistical_test.py`
- [ ] T028 [P] [US3] Integration test for end-to-end analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis.py` function `calculate_pairwise_cosine_similarity(vectors, pair_ids)` to generate similarity distributions for baseline and perturbed sets
- [ ] T030 [US3] Implement `code/analysis.py` function `run_hypothesis_test(baseline_sims, perturbed_sims)` that:
 - Filters pairs based on `data/processed/validity_log.csv` (passed both input drift and output validity)
 - Checks normality (Shapiro-Wilk) and sample size (n ≥ 30)
 - Selects Paired t-test or Wilcoxon signed-rank test
 - Applies family-wise error correction (Bonferroni or Holm)
 - **Generates sensitivity report for full range of valid sigma values**
 - **Explicitly calculates and reports the 'validity collapse point' distribution across all task types (FR-003)**
 - **Explicitly generates the trade-off curve (perturbation magnitude vs. semantic validity pass-rate) if no valid $\sigma$ exists (FR-007, SC-002)**
 - Saves to `data/processed/sensitivity_report.json`
- [ ] T031 [US3] Implement `code/main.py` analysis orchestration: Load filtered vectors -> Run tests -> Generate sensitivity report -> Save to `data/processed/statistical_results.json`
- [ ] T032 [US3] Implement logic to flag "Significant Separability Increase" if corrected p-value < 0.05
- [ ] T033 [US3] Generate a trade-off curve report (perturbation magnitude vs semantic validity pass-rate) if no valid $\sigma$ is found (fallback)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` including `quickstart.md` with exact run commands for CPU-only execution
- [ ] T035 Code cleanup and refactoring of `main.py` for clarity
- [ ] T036 Performance optimization for the perturbation sweep loop (vectorized operations where possible)
- [ ] T037 [P] Additional unit tests for edge cases (e.g., normality violation, no valid sigma) in `tests/unit/`
- [ ] T038 Security hardening: Ensure no PII leaks in logs or output files
- [ ] T039 Run `quickstart.md` validation to verify end-to-end execution on a small subset

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data structure (PairIDs) but can be implemented independently
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data produced by US1 and US2 (vectors and validity logs)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for baseline output schema in tests/contract/test_baseline_vectors.py"
Task: "Unit test for hidden state extraction logic in tests/unit/test_extract_hidden.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py function to pair questions by task type"
Task: "Implement model_utils.py function extract_thought_vector"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV output and vector dimensions)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Verify perturbation and validity checks)
4. Add User Story 3 → Test independently → Deploy/Demo (Verify statistical results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline extraction)
 - Developer B: User Story 2 (Perturbation & Validity)
 - Developer C: User Story 3 (Statistical Analysis)
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
- **Data Hygiene**: NEVER use synthetic data. If real data fetch fails, the script MUST crash (raise error) rather than falling back to mock data.
- **Resource Limits**: Strictly enforce a constrained RAM limit via `tracemalloc` and streaming/batching (T008b).
- **CPU Constraint**: All model operations must be CPU-only; do not attempt CUDA offloading unless explicitly re-targeted to a GPU runner.