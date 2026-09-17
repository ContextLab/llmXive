# Tasks: llmXive follow-up: extending "Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

## Phase 0: Research & Feasibility

**Purpose**: Validate experimental design and dataset availability before coding begins

- [ ] T001 Create project directory structure per implementation plan (`mkdir -p projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/{data,models,analysis,config} data/ results/`)
- [X] T002 Initialize empty project files (e.g., `requirements.txt`, `config/settings.yaml`)
- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (torch, transformers, datasets, scikit-learn, nltk, sentence-transformers, pandas, numpy, matplotlib, pytest)
- [ ] T004 [P] Configure linting (ruff/flake8) and formatting (black/isort) tools
- [X] T005 [P] Setup configuration management (`config/settings.yaml`) with seeds, hyperparameters, and 5.5h timeout limits
- [X] T006 [P] Perform pre-study Power Analysis in `code/analysis/statistical_test.py` to confirm N ≥ 30 for power ≥ 0.8 (FR-013, SC-007)
- [ ] T007 [P] Implement error handling for data fetch failures (must raise, never fallback to synthetic)
- [ ] T008 [P] Setup environment variable management for HuggingFace token and dataset paths
- [ ] T009 [P] Create utility functions for streaming dataset loading and chunked processing

**Checkpoint**: Research validated - experimental design confirmed feasible

---

## Phase 1: Data Model & Contracts

**Purpose**: Define schemas and documentation for data ingestion and outputs

- [ ] T010 [P] Generate `quickstart.md` documentation per plan.md Phase 1 output requirements
- [ ] T011 [P] Create base data schemas in `contracts/` (dataset.schema.yaml, training_output.schema.yaml, analysis_results.schema.yaml)
- [ ] T012 [P] Implement validation logic for schema compliance in `code/data/`

**Checkpoint**: Contracts ready - data model defined

---

## Phase 2: User Story 1 - Data Acquisition and Context Simulation (Priority: P1) 🎯 MVP

**Goal**: Ingest UltraFeedback and Dolly, filter for ≥4 traces, and simulate privileged context vs. target distribution.

**Independent Test**: Load dataset, perform split, output JSON report confirming prompt count, rationale count (≥4), and statistical distribution of selected privileged contexts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for dataset filtering logic in `code/data/test_preprocess.py` (verify prompts with <4 traces are skipped per FR-016)
- [X] T014 [P] [US1] Integration test for context simulation in `code/data/test_context_sim.py` (verify random sampling of 1 privileged vs. remaining target)

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `code/data/download.py` to fetch UltraFeedback and Dolly via `datasets.load_dataset` (streaming=True) with checksumming per Constitution
- [X] T016 [P] [US1] Implement `code/data/preprocess.py` to filter prompts with ≥4 distinct annotated reasoning traces (FR-001, FR-016)
- [ ] T017 [US1] Implement context simulator in `code/data/preprocess.py` to randomly sample 1 rationale as "privileged context" $c$, detect and re-sample if identical to unselected rationales, and output `data/context_splits.json` (FR-002, Edge Case)
- [ ] T018 [US1] Implement statistics reporter in `code/data/preprocess.py` to output JSON report (prompt count, avg tokens, deliberation token frequency)
- [ ] T019 [US1] Add validation to ensure no synthetic fallback occurs; raise error if real data fetch fails (Constitution Rule)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: Pre-Training Infrastructure (Blocking for US2)

**Purpose**: Execute Inference-Only Pass, compute Teacher Distribution, and verify model feasibility.

- [ ] T020 [P] [US2] Implement `code/models/inference_only.py` to load `data/context_splits.json` and compute Teacher Distribution (average logit distribution over all unselected rationales)
- [ ] T021 [US2] Execute Inference-Only Pass on all unselected rationales for each prompt and persist raw logits to `data/teacher_logits_raw.json` (FR-014)
- [ ] T022 [US2] Implement validation to ensure `data/teacher_logits_raw.json` is complete and matches expected prompt count
- [ ] T048 [US2] Implement averaging logic in `code/models/inference_only.py` to compute the "Teacher Distribution" (average of raw logits) from `data/teacher_logits_raw.json` and save to `data/teacher_distribution.json` (FR-003, FR-014)
- [ ] T049 [US2] Verify model architecture/size (e.g., DistilBERT) against CPU constraints (RAM, compute) in `code/models/model_check.py` before training begins (Assumptions)

**Checkpoint**: Teacher Distribution ready - Training Loop can now start

---

## Phase 4: User Story 2 - AntiSD Signal Computation and Training Loop (Priority: P2)

**Goal**: Implement custom PyTorch training loop with gradient inversion to ascend JS divergence, running on CPU with full/partial fine-tuning.

**Independent Test**: Run training on single prompt, log loss curves, verify negative gradient dot product and increasing JS divergence over multiple training steps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for JS divergence calculation in `code/models/test_metrics.py` (verify numerical stability)
- [ ] T024 [P] [US2] Unit test for gradient inversion logic in `code/models/test_anti_sd.py` (verify ascending vs. descending divergence)

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement `code/models/anti_sd_loop.py` custom PyTorch training loop with token-level gradient inversion (FR-008)
- [ ] T026 [US2] Implement JS divergence calculation between student and the averaged Teacher Distribution (from T048) using PMI (FR-003)
- [ ] T027 [US2] Implement gradient ascent logic for AntiSD condition and gradient descent for standard condition (FR-004)
- [ ] T028 [US2] Implement 5.5h hard timeout logic AND log actual elapsed time to `results/training_metrics.json` if job completes (FR-007, SC-004)
- [ ] T029 [US2] Implement logging for token probabilities, loss curves, and trajectory data for a sufficient number of steps to capture training dynamics; explicitly generate multiple trajectories for evaluation. (FR-008)
- [ ] T030 [US2] Implement memory monitoring using `psutil` to assert peak RAM < 6.5 GB during training; output `results/memory_log.json` with peak values (SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Diversity Measurement, Quality Validation, and Statistical Analysis (Priority: P3)

**Goal**: Compute BLEU/semantic similarity, validate with Human Evaluation Proxy, and run Wilcoxon signed-rank tests.

**Independent Test**: Compute metrics against unselected rationales, output Wilcoxon p-value, effect size, and correlation coefficient.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for BLEU and semantic similarity calculation in `code/models/test_metrics.py`
- [ ] T032 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `code/analysis/test_statistical_test.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement pairwise BLEU and semantic similarity calculation in `code/models/metrics.py` against unselected rationales (FR-005)
- [ ] T034 [US3] Implement deliberation token counter (e.g., "Wait", "However") in `code/models/metrics.py` (FR-009)
- [ ] T035 [US3] Generate HTML rater interface at `docs/rater.html` and output format for scores to `data/human_scores.csv` (FR-010, FR-015)
- [ ] T047 [US3] Implement parser in `code/analysis/human_score_ingest.py` to read `data/human_scores.csv` and compute the "Human Evaluation Proxy Score" (FR-010)
- [ ] T036 [US3] Implement Pearson correlation calculation between deliberation token frequency and Human Evaluation Proxy Score (FR-011)
- [ ] T037 [US3] Implement Wilcoxon signed-rank test comparing AntiSD vs. standard self-distillation on diversity and quality metrics (FR-006, FR-017)
- [ ] T046 [US3] Implement post-hoc power analysis in `code/analysis/statistical_test.py` to calculate observed statistical power (1-β) based on effect size (FR-018)
- [ ] T038 [US3] Generate final analysis report with p-values, effect sizes, correlation coefficients, and observed statistical power (FR-013, FR-018, SC-001, SC-002, SC-003)
- [ ] T039 [US3] Visualize loss curves and diversity metrics in `code/analysis/visualize.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` including runbook for streaming datasets
- [ ] T041 Code cleanup and refactoring of training loop for readability
- [ ] T042 Performance optimization for CPU-only inference pass
- [ ] T043 [P] Additional unit tests for edge cases (e.g., identical privileged context) in `tests/unit/`
- [ ] T044 Security hardening of dataset download scripts
- [ ] T045 Run validation script to verify SC-001 through SC-007 against `data/` and `results/` (using `quickstart.md` guidelines)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately (T006 depends on T009/T015 data stats)
- **Phase 1 (Contracts)**: Depends on Phase 0 completion
- **Phase 2 (US1)**: Depends on Phase 1 completion - No dependencies on other stories
- **Phase 3 (Pre-Training)**: Depends on Phase 2 (US1) completion - Produces Teacher Distribution
- **Phase 4 (US2)**: Depends on Phase 3 completion - Requires Teacher Distribution
- **Phase 5 (US3)**: Depends on Phase 4 completion - Requires Training Output
- **Phase N (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Depends on Phase 3 (Inference-Only Pass + Averaging) which depends on US1
- **User Story 3 (P3)**: Depends on US2 training output and US1 data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] (except T006) can run in parallel
- All Phase 1 tasks marked [P] can run in parallel
- Once Phase 1 completes, US1 (Phase 2) can start
- Once US1 completes, Pre-Training (Phase 3) can start
- Once Pre-Training completes, US2 (Phase 4) can start
- Once US2 completes, US3 (Phase 5) can start

---

## Parallel Example: Phase 0

```bash
# Launch all Phase 0 tasks together (except T006 which needs data stats):
Task: "Initialize Python 3.11 project with requirements.txt"
Task: "Configure linting and formatting tools"
Task: "Setup configuration management"
Task: "Create utility functions for streaming dataset loading"
# T006 (Power Analysis) must wait for data stats from T009/T015
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: Contracts
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Phase 1 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Phase 3 (Inference + Averaging) → Test independently
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Phase 1 together
2. Once Phase 1 is done:
 - Developer A: User Story 1
 - Developer B: Pre-Training Infrastructure (Phase 3) - *after US1 completes*
 - Developer C: User Story 2 - *after Phase 3 completes*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T006)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loading tasks must use streaming or strict sampling; never load full dataset into RAM.
- **No Fabrication**: If real data fetch fails, the script must raise an error; never fallback to synthetic data.
- **CPU Constraints**: Training loop must be optimized for CPU; use small models (DistilBERT/TinyLlama) and partial fine-tuning if necessary.
- **Timeout**: Hard timeout of 5.5 hours must be enforced to respect CI limits; actual elapsed time must be logged.
- **Human Proxy**: FR-015 requires 3 independent human raters; tasks must generate the interface for manual execution (T035) and ingest scores (T047) for automated analysis.
- **Power Analysis**: Must be performed BEFORE data collection (Phase 0) to validate experimental design; T046 calculates observed power post-experiment.
- **Teacher Distribution**: Must be computed via Inference-Only Pass (T021) and Averaging Logic (T048) before training begins.