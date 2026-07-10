# Tasks: Mechanistic Interpretability of CTCF Binding-Site Selection

**Input**: Design documents from `/specs/001-mechanistic-interpretability-of-ctcf-binding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/code/`, `projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/tests/`
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create project directory structure per implementation plan:
 ```
 projects/PROJ-001-mechanistic-interpretability-of-ctcf-bin/
 ├── code/
 │ ├── __init__.py
 │ ├── requirements.txt
 │ ├── data/
 │ ├── models/
 │ └── interpret/
 ├── data/
 │ ├── raw/
 │ └── processed/
 ├── tests/
 │ ├── unit/
 │ └── integration/
 └── state/
 ```
- [X] T001b Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scikit-learn`, `torch` (CPU-only), `biopython`, `pyyaml`, `huggingface_hub`, `datasets`. Create `code/requirements.txt` with pinned versions.
- [X] T002 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Data Gap Resolution (CRITICAL BLOCKER)

**Purpose**: Address the "Blocking Data Gap" identified in plan.md. The project is currently HALTED until verified multi-modal data sources are identified OR the scope is revised to sequence-only.

**⚠️ CRITICAL**: Do not proceed to User Stories until Phase 2 is complete and either data is found or the project is halted.

- [X] T003 [P] Implement `code/data/search_sources.py` to query ENCODE API and public repositories (e.g., GEO, SRA) for matched ChIP-seq (CTCF), ATAC-seq, and H3K27ac experiments across ≥5 cell types.
 - **Output**: Generate `data/candidate_sources.json` with fields: `accession_id`, `cell_type`, `file_type`, `url`, `status`.
- [X] T004 [P] Implement `code/data/validate_sources.py` to verify URL accessibility, file format (bam/bigwig), and cross-referencing of cell types.
 - **Output**: If ≥5 matched sets found, generate `data/manifest.json`.
 - **Output**: If <5 matched sets found, generate `data/data_gap_report.md` with fields: `missing_cell_types`, `search_query_log`, `recommendation`, `total_candidates_found`.
 - **Trigger**: If `data/data_gap_report.md` is generated, the pipeline MUST halt.
- [X] T005 [P] Implement `code/data/retrieve_checksum.py` to download and checksum verified data files.
 - **Output**: Update `data/manifest.json` with `checksum` and `local_path` fields.
 - **Dependency**: Must run after T004 succeeds (≥5 sets found).
- [X] T006 [P] If T004 fails (zero matched sets), implement `code/data/generate_halt_report.py` to generate `docs/project_halt_report.md` documenting the failure and **HALT** the pipeline.
 - **Dependency**: Triggers ONLY if T004 finds zero matched sets.
- [ ] T007 [P] Create `data/manifest.json` ONLY if T004 succeeds (≥5 matched sets found). If T004 fails, this task is skipped. <!-- FAILED: unspecified -->

**Checkpoint**: Verified multi-modal data sources identified AND manifest generated, OR Project halted.

---

## Phase 3: Foundational (Conditional on Phase 2 Success)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **ONLY EXECUTE IF Phase 2 Succeeded.**

- [X] T008 [P] Implement low-complexity filtering utility `code/data/filter_complexity.py` using Shannon entropy (threshold >0.8) to exclude repetitive regions.
 - **Dependency**: Requires `data/manifest.json` from T007.
- [ ] T009 [P] Setup environment configuration management for ENCODE API keys and local paths.
 - **Dependency**: Requires `data/manifest.json` from T007.

**Checkpoint**: Foundational utilities ready for ingestion.

---

## Phase 4: User Story 1 - Data Ingestion and Multi-Modal Feature Assembly (Priority: P1) 🎯 MVP
**Status**: CONDITIONAL on Phase 2 Success

**Goal**: Ingest ChIP-seq, ATAC-seq, and histone data from ENCODE for ≥5 cell types, aligning to ±500 bp windows around CTCF peaks/non-peaks to create a unified training dataset.

**Independent Test**: The system can be tested by running the data ingestion script on a subset of ENCODE data and verifying that the output CSV/Parquet file contains exactly one row per genomic window with columns for sequence, accessibility, and histone marks, and that the total file size fits within the available RAM constraint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for sequence extraction `tests/unit/test_sequence_extraction.py` (verify ±500 bp windowing).
- [ ] T011 [P] [US1] Unit test for multi-modal alignment `tests/unit/test_multi_modal_alignment.py` (verify missing data handling/exclusion).

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/data/ingest.py` to download BAM/bigwig files for verified cell types using `data/manifest.json`.
- [~] T013 [US1] Implement `code/data/extract_features.py` to extract 1000bp windows (±500bp) centered on CTCF peaks and non-peaks, converting sequences to one-hot encoding and chromatin signals to normalized floats.
 - **Dependency**: Requires output of T012.
- [~] T014 [US1] Implement `code/data/preprocess.py` to **exclude** cell types with missing ATAC-seq data (per spec Edge Cases: "exclude that cell type... or impute"; we choose exclusion to ensure data integrity).
 - **Constraint**: If exclusion results in <5 cell types, the script MUST trigger a re-search (loop back to T003) or generate `docs/scope_revision_trigger.md`.
- [~] T015 [US1] Implement `code/data/save_dataset.py` to save the unified dataset as `data/processed/unified_ctcf_dataset.parquet`.
- [~] T016 [US1] Add validation to ensure every row contains fixed-length sequence and matched chromatin values; raise error if nulls remain.
- [~] T017 [US1] Add logging for data ingestion steps, including cell type counts and exclusion reasons.

**Checkpoint**: Unified multi-modal dataset produced, ready for model training.

---

## Phase 5: User Story 2 - Predictive Model Training and Baseline Validation (Priority: P2)
**Status**: CONDITIONAL on Phase 4 Success

**Goal**: Train a sequence-context-aware predictor (lightweight CNN/Transformer) to predict CTCF binding probability, achieving AUC-ROC ≥ 0.85 on held-out validation.

**Independent Test**: The system is tested by training the model on a majority of the data, evaluating on a held-out validation set, and verifying the AUC-ROC score exceeds the 0.85 threshold. If the threshold is not met, the system logs the result and proceeds with a warning.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for model architecture `tests/unit/test_model_architecture.py` (verify input shapes and parameter count).
- [~] T019 [P] [US2] Integration test for training loop `tests/integration/test_training_loop.py` (verify convergence and AUC calculation).

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement `code/models/predictor.py` with a lightweight CNN/Transformer architecture optimized for CPU execution (no CUDA dependencies).
- [~] T021 [US2] Implement `code/models/train.py` to train the model on `data/processed/unified_ctcf_dataset.parquet`, splitting into train/validation sets with a standard majority/minority ratio.
 - **Dependency**: Requires output of T020.
- [~] T022 [US2] Implement `code/models/evaluate.py` to compute AUC-ROC on the validation set; log warning if < 0.85 but continue.
- [~] T023 [US2] Implement fallback logic in `code/models/train.py` to reduce sequence window size or switch to simpler CNN if training exceeds a predefined time threshold.
- [~] T024 [US2] Save trained model weights to `data/models/best_ctcf_predictor.pth`.
- [~] T025 [US2] Implement synthetic sequence test: apply model to a sequence with strong CTCF motif but low ATAC-seq; verify output probability ≤ 0.2.
 - **Dependency**: Requires output of T024.

**Checkpoint**: Trained predictive model saved with baseline performance metrics.

---

## Phase 6: User Story 3 - Interpretability Decomposition and Feature Attribution (Priority: P3)
**Status**: CONDITIONAL on Phase 5 Success

**Goal**: Apply Sparse Autoencoders (SAEs) to decompose hidden activations into latent features and use integrated gradients to map them to sequence motifs and chromatin contexts. Identify ≥5 features.

**Independent Test**: The system is tested by running SAE decomposition and checking if top 5 features correspond to known biological patterns (correlation ≥ 0.7 with JASPAR CTCF PWM).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T026 [P] [US3] Unit test for SAE training `tests/unit/test_sae_training.py` (verify sparsity constraints).
- [~] T027 [P] [US3] Unit test for integrated gradients `tests/unit/test_integrated_gradients.py` (verify attribution map shape).

### Implementation for User Story 3

- [~] T028 [P] [US3] Implement `code/interpret/sae.py` to train a Sparse Autoencoder on hidden layer activations from `code/models/predictor.py`.
- [~] T029 [US3] Implement `code/data/fetch_validation_data.py` to retrieve an independent held-out ChIP-seq dataset (e.g., GEO GSE accession) for validation.
 - **Dependency**: Requires T028 to identify features to validate.
- [ ] T030 [US3] Implement `code/interpret/validate_features.py` to correlate latent feature weights with JASPAR CTCF PWM scores (target r ≥ 0.7) AND validate against the independent dataset from T029.
 - **Dependency**: Requires output of T028 and T029.
- [ ] T031 [US3] Implement `code/interpret/find_non_canonical.py` to identify features that predict binding without the canonical motif (using available training data only).
- [ ] T032 [US3] Implement `code/interpret/permutation_test.py` to run a sufficient number of permutations on dinucleotide-shuffled sequences, reporting features with p < 0.05.
- [ ] T033 [US3] Save attribution maps and feature metadata to `data/interpretation/latent_features_manifest.json`.
- [ ] T034 [US3] Generate visualization report `data/interpretation/feature_attribution_report.pdf` showing sequence/chromatin highlights.

**Checkpoint**: ≥5 latent features identified, validated (within constraints), and mapped to biological determinants.

---

## Phase 7: Post-Resolution Polish & Cross-Cutting Concerns (Reviewer Addressal)
**Status**: CONDITIONAL on Phase 2 Success (Project must have proceeded past the data block)

**Purpose**: Address specific reviewer concerns regarding the "Four Causes" (Aristotle) and structural fidelity (Franklin).

- [ ] T035 [P] [Review-Aristotle] Update `code/data/feature_engineering.py` to explicitly separate "Material Cause" (sequence one-hot) from "Formal Cause" (chromatin accessibility/histone marks) as distinct input channels, ensuring the model architecture treats them as separate causal channels.
- [ ] T036 [P] [Review-Aristotle] Add documentation in `docs/interpretability.md` clarifying that "Efficient Cause" (binding machinery) is the model output (prediction) and "Final Cause" (regulatory function) is inferred via downstream analysis. **Explicitly note** that "Structural Fidelity" (B-form/A-form) is excluded per spec assumptions.
- [ ] T037 [P] [Review-Franklin] **Removed**: Task to implement structural proxy deleted as it violates spec scope.
- [ ] T038 [P] [Review-Franklin] Add a constraint in `code/interpret/validate_features.py` to flag any feature that correlates strongly with low-complexity regions (potential artifact) rather than true structural signals.
- [ ] T039 [P] Documentation updates in `README.md` and `docs/quickstart.md` explaining the "Four Causes" framework and structural proxy assumptions (exclusion).
- [ ] T040 [P] Profile and enforce -hour runtime limit. Generate `data/runtime_profile.json`.
 - **Failure Condition**: If runtime > 6h, exit with code 1 and halt the pipeline.
- [ ] T041 [P] Code cleanup and refactoring to ensure all scripts run within 6 hours on 2-CPU runner.
 - **Dependency**: Requires output of T040.
- [ ] T042 [P] Run full pipeline integration test to verify end-to-end execution from ingestion to interpretation.
 - **Output**: Generate `data/integration_test_report.md`.
 - **Failure Action**: If any test fails, generate report with FAIL status and halt the release.
 - **Dependency**: Requires completion of T033 and T041.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Data Gap Resolution (Phase 2)**: **BLOCKS ALL** subsequent phases. Must succeed (data found) or project halts.
- **Foundational (Phase 3)**: Depends on Phase 2 Success.
- **User Stories (Phase 4-6)**: All depend on Phase 3 completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 7)**: Depends on Phase 2 Success and all user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 3 - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires dataset)
- **User Story 3 (P3)**: Depends on US2 (requires trained model)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Phase 2 tasks marked [P] can run in parallel (except conditional logic)
- Once Phase 2 completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for sequence extraction tests/unit/test_sequence_extraction.py"
Task: "Unit test for multi-modal alignment tests/unit/test_multi_modal_alignment.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py"
Task: "Implement code/data/extract_features.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Data Gap Resolution (CRITICAL - blocks all stories)
3. Complete Phase 3: Foundational
4. Complete Phase 4: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify data integrity)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Data Gap Resolution → Foundation ready (Data Gap Resolved)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Data Gap Resolution together
2. Once Data Gap Resolution is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Interpretability)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Phase 2 tasks MUST identify real ENCODE sources; synthetic data is prohibited. If sources are not found, the project halts.
- **Reviewer Addressal**: Phase 7 tasks specifically address Aristotle's "Four Causes" and Franklin's "Structural Fidelity" concerns (noting the exclusion of structural proxies).
- **Runtime Constraint**: SC-004 (6-hour limit) is enforced by T040 and T041.
- **Data Integrity**: Constitution Principle III (Data Hygiene) is enforced by T005 (checksums).