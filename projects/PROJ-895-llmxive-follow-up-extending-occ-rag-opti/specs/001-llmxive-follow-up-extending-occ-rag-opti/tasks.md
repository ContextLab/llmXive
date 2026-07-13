# Tasks: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

**Input**: Design documents from `/specs/001-llmxive-occrag-sparse-core/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/`)
- [ ] T002 Initialize Python 3.11 project with `torch` (CPU-only wheel), `transformers`, `scikit-learn`, `pandas`, `numpy`, `datasets` in `code/requirements.txt`. **Explicitly exclude** `bitsandbytes` and other 8-bit/4-bit quantization libraries that depend on GPU to align with CPU-only constraints.
- [ ] T003 [P] Configure linting and formatting tools (black, flake8) in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/dataset_loader.py` to fetch a large synthetic multi-hop QA corpus from the original project repository (GitHub/Zenodo) or HuggingFace Datasets, ensuring checksum verification
- [ ] T004.1 [P] Download, verify checksum, and cache the frozen OCC-RAG model weights. The research question is: How can retrieval-augmented generation improve performance on domain-specific tasks? The method involves fine-tuning a pre-trained language model with retrieved context. References: arXiv:2305.15294. to `data/raw/model_weights.pt` from the specified HuggingFace/GitHub source. Ensure the artifact is ready for layer-wise loading.
- [ ] T005 [P] Implement `code/utils/faithfulness_score.py` to calculate the "Context Faithfulness Score" (weighted ConFiQA accuracy + citation precision) on CPU
- [ ] T006 [P] Implement `code/utils/masking.py` with layer-wise loading logic to ensure memory usage remains within acceptable limits for CPU-only execution.
- [ ] T007 Create `data/raw/occ_rag_corpus.jsonl` directory structure and `data/checksums.json` for artifact tracking
- [ ] T008 Setup `code/00_config.py` to define random seeds and CPU-only device constraints. **Define specific empirical values** required by the spec: `MASK_FRACTION` (e.g., 0.1), `RETENTION_PCT` (e.g., 0.5), `FINE_TUNE_SAMPLE_SIZE` (10000), and `SAMPLE_SEED`. These values must be hardcoded or loaded from a config file to ensure all downstream tasks are executable without placeholders.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Sparse Sub-network Identification via Gradient-Free Sensitivity (Priority: P1) 🎯 MVP

**Goal**: Execute gradient-free sensitivity analysis to identify critical parameters for faithfulness

**Independent Test**: Can be fully tested by running the sensitivity analysis script on a subset of the synthetic corpus and verifying that the output CSV correctly lists parameters ranked by sensitivity score, with a clear distinction between high-sensitivity and low-sensitivity parameters compared to random masking.

### Implementation for User Story 1

- [ ] T009a [US1] Implement logic in `code/01_sensitivity_analysis.py` to mask **attention heads** per layer based on `CONFIG.MASK_FRACTION` from `code/00_config.py`.
- [ ] T009b [US1] Implement logic in `code/01_sensitivity_analysis.py` to mask **feed-forward neurons** per layer based on `CONFIG.MASK_FRACTION` from `code/00_config.py`.
- [ ] T009c [US1] Implement the orchestration loop in `code/_sensitivity_analysis.py` to execute the masking steps in 10 sequential iterations as defined in the spec.
- [ ] T010 [US1] Implement `code/_sensitivity_analysis.py` logic to run a control baseline of 10 random masking iterations to distinguish specific sensitivity from general capacity loss (FR-001).
- [ ] T010.1 [US1] Aggregate the results of the 10 random masking iterations into a baseline artifact `data/processed/random_baseline_scores.csv` containing the average faithfulness scores for random masking, to be consumed by the delta calculation task.
- [ ] T011 [US1] Implement logic in `code/01_sensitivity_analysis.py` to calculate `delta_faithfulness` for each masked configuration relative to the `random_baseline_scores.csv` artifact (FR-002).
- [ ] T012 [US1] Ensure `code/01_sensitivity_analysis.py` loads the frozen OCC-RAG-1.7B model using layer-wise loading to stay within 7 GB RAM (FR-006).
- [ ] T012.1 [US1] Implement memory monitoring and assertion logic within `code/_sensitivity_analysis.py` to **log peak RAM usage** and assert that it remains under 7 GB (US1-Acceptance-3, SC-003).
- [ ] T013 [US1] Write output to `data/processed/sensitivity_results.csv` with columns: `layer_id`, `param_id` (formatted as `layer_id.param_type.param_index`), `sensitivity_score`, `delta_faithfulness`, `random_baseline_score` (US1-Acceptance-1).
- [ ] T013.1 [US1] Run inference on the **original** (unpruned) OCC-RAG-1.7B model on the held-out test set to generate per-sample faithfulness scores, saving the result to `data/processed/original_faithfulness_scores.csv` (required for FR-005 paired t-test).
- [ ] T014 [US1] Implement logic to identify the "Critical Sub-network" candidate by sorting parameters by magnitude of performance drop relative to random baseline, using `CONFIG.RETENTION_PCT` to determine the cutoff (US1-Acceptance-2).
- [ ] T015 [US1] Add edge case handling: flag if sensitivity delta < 0.01 indicating no meaningful sparse core. **Explicitly link this flag** to the failure of Critical Sub-network identification and the SC-005 collinearity check (Edge Case 1).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pruned Model Construction and Lightweight Re-mid-training (Priority: P2)

**Goal**: Construct a pruned model retaining only critical parameters and perform lightweight fine-tuning

**Independent Test**: Can be fully tested by loading the pruned model architecture, running inference on the held-out test set, and confirming that the model structure matches the pruning mask (zeroed weights) and that the fine-tuning process completes without CUDA dependency.

### Implementation for User Story 2

- [ ] T016 [US2] Implement `code/02_prune_model.py` to construct `OCC-RAG-Pruned-{retention_pct}B` by retaining only the top `CONFIG.RETENTION_PCT` of parameters from `sensitivity_results.csv` and setting others to zero (FR-003).
- [ ] T016.1 [US2] Log the selected `CONFIG.RETENTION_PCT` and the resulting number of retained parameters to `data/processed/pruning_config.log` for auditability.
- [ ] T017 [US2] Ensure `code/02_prune_model.py` preserves the original architecture topology even with zeroed weights to maintain inference compatibility (Edge Case 2).
- [ ] T018 [US2] Save pruned weights to `data/processed/pruned_model_weights.pt`
- [ ] T019 [US2] Implement `code/03_finetune_pruned.py` to perform lightweight fine-tuning on a **random sample of [deferred] examples** drawn from `data/raw/occ_rag_corpus.jsonl` using `CONFIG.SAMPLE_SEED` for deterministic sampling and a low learning rate (FR-004).
- [ ] T020 [US2] Implement early stopping in `code/03_finetune_pruned.py` based on **gradient magnitude < 1e-4 for 3 consecutive epochs** (FR-004, US2-Acceptance-2).
- [ ] T021 [US2] Ensure `code/03_finetune_pruned.py` runs entirely on CPU within 4 hours and uses standard CPU optimizers (AdamW) (FR-006, US2-Acceptance-2).
- [ ] T022 [US2] Add logging to `code/03_finetune_pruned.py` to report final faithfulness score and handle collapse scenarios without falsely claiming recovery (Edge Case 3).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation of Pruning Impact (Priority: P3)

**Goal**: Compare performance of pruned vs. original model using paired t-test

**Independent Test**: Can be fully tested by running the statistical validation script on the results of the original and pruned models and verifying that the p-value is calculated correctly and the conclusion (significant or not) is reported.

### Implementation for User Story 3

- [ ] T023 [US3] Implement `code/04_statistical_validation.py` to collect per-sample faithfulness scores from `data/processed/original_faithfulness_scores.csv` (generated by T013.1) and `data/processed/pruned_faithfulness_scores.csv` (generated by T022) (FR-005).
- [ ] T024 [US3] Implement paired t-test logic in `code/04_statistical_validation.py` to calculate p-value and confidence interval (FR-005, US3-Acceptance-1).
- [ ] T025 [US3] Implement logic to flag performance drop as statistically significant if p < 0.05, or not significant if p ≥ 0.05 (US3-Acceptance-2 & 3).
- [ ] T026 [US3] Calculate collinearity (Pearson correlation) between sensitivity scores of selected sub-network and a random subset; flag if > 0.2 (SC-005).
- [ ] T027 [US3] Write final validation report to `data/processed/statistical_validation_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Documentation updates in `paper/draft.md` referencing `data/processed/` results
- [ ] T029 Code cleanup and refactoring of `code/utils/` modules
- [ ] T030 Performance optimization for CPU-only execution (batching strategies)
- [ ] T031 [P] Add unit tests for `masking.py` and `faithfulness_score.py` in `tests/unit/`
- [ ] T032 Run `quickstart.md` validation to ensure end-to-end reproducibility on free-tier runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015 (Sensitivity Results) to identify parameters to prune
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022 (Fine-tuned model) and T013.1 (Original model inference)

### Within Each User Story

- Models/Utils before services
- Services before endpoints/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T004.1, T005, T006) can run in parallel
- Once Foundational phase completes, T009a-T015 (US1) can start
- T016-T022 (US2) depends on US1 output but can start as soon as US1 CSV is generated
- T023-T027 (US3) depends on outputs from US1 and US2

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV output and sensitivity ranking)
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
   - Developer A: User Story 1 (Sensitivity Analysis)
   - Developer B: User Story 2 (Pruning & Fine-tuning) - *Note: Must wait for T015 output*
   - Developer C: User Story 3 (Statistical Validation) - *Note: Must wait for T022 output*
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
- **Constraint Reminder**: All tasks MUST run on CPU-only free-tier CI (CPU, limited RAM, 6h). No GPU, no 8-bit/4-bit quantization.
- **Data Integrity**: All datasets must be fetched from real sources (GitHub/Zenodo/HF); no synthetic/fake data generation tasks.