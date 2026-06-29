# Tasks: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

**Input**: Design documents from `/specs/001-predicting-plant-pathogen-host-range-fro/`
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

- [ ] T001A Create source directories: `src/data`, `src/models`, `src/cli`, `src/utils`
- [ ] T001B Create data directories: `data/raw`, `data/processed`, `data/models`, `data/reports`
- [ ] T002 Initialize Python 3.11 project with dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup configuration management in `src/config.py` for paths, seeds, and thresholds
- [ ] T005 [P] Implement logging infrastructure in `src/utils/logging.py` (FR-010, SC-005) ensuring `pipeline.log` is initialized with timestamps
- [ ] T007A Create `contracts/interaction.schema.yaml` with properties: pathogen_id, host_id, infects, source
- [ ] T007B Create `contracts/genomic_features.schema.yaml` with properties: accession_id, gc_content, kmer_profile, effector_count, pfam_counts, sm_clusters
- [ ] T007C Create `contracts/model_output.schema.yaml` with properties: model_path, auprc, precision, shap_values
- [ ] T007D Create `contracts/data_quality.schema.yaml` with properties: pathogen_id, missing_pct, total_interactions
- [ ] T007E Create `contracts/sensitivity_analysis.schema.yaml` with properties: primary_auprc, sensitivity_auprc, delta, flag
- [ ] T007F Create `contracts/bias_awareness.schema.yaml` with properties: top_10_pct, flag, distribution
- [ ] T008 Implement base validation utilities in `src/utils/validators.py` to enforce contract schemas (Depends on T007A-F)
- [ ] T009A [P] Implement `src/data/download.py` to fetch pathogen genomes from NCBI GenBank (FR-001) and interaction tables from PHI-base/Interactome3D (FR-002). **Deliverable**: `data/raw/genomes.fasta` and `data/raw/interactions_merged.csv`
- [ ] T009B [P] Implement `src/data/feature_extractor_offline.py` to compute EffectorP 3.0, antiSMASH 7.0, GC, k-mers, and Pfam counts (FR-003). **Deliverable**: `data/raw/features_cache.parquet` (Single Source of Truth)
- [ ] T010A [P] Implement data merging and deduplication logic in `src/data/preprocess.py` (FR-013) handling 'unknown' labels
- [ ] T010B [P] Implement logic to treat missing interaction records as 'unknown' (exclude from training) and generate `data/reports/data_quality_report.json` (FR-013)
- [ ] T010C [P] Implement "Zero Interaction" check in `src/data/preprocess.py` (FR-011) to log critical error and halt if a pathogen has no interactions after merging
- [ ] T011 [P] Implement "Pre-computed Feature Cache" loader in `src/data/preprocess.py` to read `data/raw/features_cache.parquet` (GC, k-mer, EffectorP, antiSMASH, Pfam) as per Plan.md. **Input**: `data/raw/features_cache.parquet`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Generate Predictive Host‑Range Model (Priority: P1) 🎯 MVP

**Goal**: Run the pipeline on a curated set of pathogens to produce a cross-validated logistic-regression model and report AUPRC.

**Independent Test**: Execute `run_pipeline.sh --data-dir ./test_data` and verify `model.pkl` exists, console prints "Cross‑validated AUPRC = [value]", and `feature_importance.csv` has ≥3 non-zero SHAP values.

### Implementation for User Story 1

- [ ] T013 [US1] Implement data splitting in `src/data/preprocess.py` to create **pathogen-stratified** Train/Val sets and reserve a **10-pathogen hold-out set** for independent validation (FR-012, SC-001)
- [ ] T014 [US1] Implement L2-regularized Logistic Regression training with inner k-fold CV in `src/models/train.py` (FR-004). **Sub-task**: Implement **Nested VIF analysis** strictly within CV folds (FR-014) to remove collinear features (threshold ≥ 5) before model fitting
- [ ] T019 [P] [US1] Implement nested cross-validation loop in `src/models/evaluate.py` to prevent overfitting during feature selection (FR-006)
- [ ] T020 [P] [US1] Implement permutation testing within nested CV in `src/models/evaluate.py` (FR-006)
- [ ] T015 [US1] Implement k-fold cross-validation evaluation in `src/models/evaluate.py` reporting AUPRC, precision, and calibrated probabilities (FR-005, SC-001)
- [ ] T016 [US1] Implement SHAP value generation in `src/models/interpret.py` and save `data/reports/feature_importance.csv` (FR-007)
- [ ] T017 [US1] Create `run_pipeline.sh` CLI entry point in `src/cli/`. **Args**: `--data-dir` (path to data directory), `--mode` (primary|sensitivity), `--seed` (integer for reproducibility). **Outputs**: `model.pkl`, `feature_importance.csv`, `significant_features.tsv`, `prediction.csv`, `pipeline.log`. **Logic**: Orchestrates download (if not cached), feature loading, preprocessing, training, evaluation, and reporting based on the selected mode.
- [ ] T018 [US1] Add error handling for "Missing Genome" and "Zero-Feature Pathogen" edge cases in `src/data/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 – Identify Significant Genomic Feature Categories (Priority: P2)

**Goal**: Run on the full pathogen dataset to identify genomic feature groups statistically associated with broad host ranges.

**Independent Test**: Run pipeline on full dataset; verify `significant_features.tsv` contains ≥2 rows with effect size (Cohen's d) and adjusted p-value ≤ 0.05.

### Implementation for User Story 2

- [ ] T021 [US2] Implement Benjamini-Hochberg FDR correction logic in `src/models/evaluate.py` to adjust p-values (FR-006)
- [ ] T022 [US2] Generate `data/reports/significant_features.tsv` with columns: `feature_name`, `cohen_d`, `adj_p_value`, `significant_flag` using tab delimiter (US-2 Acceptance)
- [ ] T024 [US2] Implement Bias-Awareness Report generation in `src/models/interpret.py` (FR-018). **Logic**: Calculate interaction count per pathogen; flag if top 10 pathogens account for >80% of interactions. Output `data/reports/bias_awareness.json`
- [ ] T023 [US2] Integrate full dataset processing into `run_pipeline.sh` ensuring -hour CI limit is respected (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 – Predict Host‑Range for a Novel Pathogen (Priority: P3)

**Goal**: Predict infection likelihood for a single novel genome FASTA file.

**Independent Test**: Run `predict_host_range.sh --genome novel.fa` and verify `prediction.csv` lists ≥20 plant species with probabilities [0, 1].

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement feature extraction for a *single* novel genome in `src/data/feature_extractor.py` (offline mode). **Mandatory**: Run EffectorP 3.0 and antiSMASH 7.0 on the input FASTA (FR-003). **Output**: `data/processed/novel_features.json`
- [ ] T026 [US3] Implement `predict_host_range.sh` CLI script in `src/cli/` to load `model.pkl`, process input FASTA (via T025), and output probabilities
- [ ] T027 [US3] Implement probability calculation for all unique hosts in reference matrix (FR-017) and save to `data/reports/prediction.csv`
- [ ] T028 [US3] Ensure prediction runtime ≤ 30s and memory ≤ 4GB in `src/cli/predict_host_range.sh` (SC-003)
- [ ] T029 [US3] Handle "Zero-Feature Pathogen" by assigning baseline prevalence probability (Edge Case)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis & Reporting (Cross-Cutting)

**Goal**: Address FR-016 (Sensitivity to missing data) and generate final reports.

- [ ] T030 [P] Implement "Sensitivity Mode" and full sensitivity analysis in `src/data/preprocess.py` and `src/models/evaluate.py`. **Logic**: 
  1. Treat missing interactions as negative (0) to create a dense label vector.
  2. Train a secondary model on this data.
  3. Compare the secondary model's AUPRC against the Primary Mode AUPRC.
  4. Calculate the variance/delta in AUPRC.
  5. Flag if the difference exceeds the significance threshold.
  6. Generate `data/reports/sensitivity_analysis.json` containing `primary_auprc`, `sensitivity_auprc`, `delta`, `flag`, and `methodology`. (FR-016)
- [ ] T033 [P] Generate `data/reports/data_quality_report.json` quantifying missing % per pathogen (FR-013)
- [ ] T035 [P] Finalize `pipeline.log` ensuring INFO entries exist for all major steps (SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Sensitivity & Reporting (Phase 6)**: Depends on US1 and US2 completion

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
# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py to fetch pathogen genomes"
Task: "Implement data merging and deduplication logic in src/data/preprocess.py"
Task: "Implement VIF analysis and collinearity removal logic within CV folds in src/models/train.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on 10 pathogens
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
   - Developer A: User Story 1 (Core Model)
   - Developer B: User Story 2 (Feature Significance)
   - Developer C: User Story 3 (Prediction CLI)
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
- **Feasibility Note**: All tasks are designed for CPU-only execution (no CUDA/GPU). Feature extraction for the full dataset is pre-computed offline (TB) to meet the 5-hour CI limit, while runtime download (T009A) is preserved for spec compliance.