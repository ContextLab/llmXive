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

- [X] T001a [P] Initialize data directories: Create `data/raw`, `data/processed`, `data/models`, `data/reports`.
- [X] T001b [P] Initialize source directories: Create `src/`, `src/cli`, `src/data`, `src/features`, `src/models`, `src/report`, `src/utils`.
- [X] T001c [P] Initialize test and contract directories: Create `tests/`, `contracts/`.
- [X] T001d [P] Initialize logging directory: Create `logs/`.
- [X] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` at `projects/PROJ-515-predicting-plant-pathogen-host-range-fro/code/`.
 - **Required Dependencies**: `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `shap>=0.44.0`, `biopython>=1.81`, `requests>=2.31.0`, `loguru>=0.7.0`, `pyyaml>=6.0.1`, `pytest>=7.4.0`, `pytest-cov`.
- [X] T002b [P] Configure Docker environment for non-Python tools: Create `Dockerfile` or `docker-compose.yml` to pin and install EffectorP (image: `effectorp/effectorp:3.0`) and antiSMASH (image: `antismash/antismash:7.0`). Ensure these images are pulled and verified before pipeline execution.
 - **CRITICAL**: After pulling, **verify the checksum** of each Docker image layer against the canonical source (Docker Hub manifest) and record the hash in `data/checksums.json`. This satisfies Constitution Principle III (Data Hygiene) extended to Tool Artifacts.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup configuration management in `src/config.py` for paths, seeds, and thresholds
- [X] T005 [P] Implement logging infrastructure in `src/utils/logging.py` (FR-010, SC-005) ensuring `pipeline.log` is initialized with timestamps and propagates to subprocesses
- [X] T007 [P] Create contract schemas in `contracts/` directory: `dataset.schema.yaml`, `genomic_features.schema.yaml`, `interaction.schema.yaml`, `model_output.schema.yaml`.
 - **Note**: Do not create `data_quality.schema.yaml` or `sensitivity_analysis.schema.yaml` as they are not defined in the plan.
- [ ] T008 Implement base validation utilities in `src/utils/validators.py` to enforce contract schemas (Depends on T007)
- [ ] T009A [P] Implement `src/data/download.py` to fetch pathogen genomes from NCBI GenBank (FR-001) and interaction tables from PHI-base/Interactome3D (FR-002). **Deliverable**: `data/raw/genomes.fasta` and `data/raw/interactions_merged.csv`
 - **CRITICAL**: This task MUST explicitly download the **specific 50-pathogen dataset** defined in the `Assumptions` section of `spec.md`. The script must load the list of 50 accession IDs from a configuration file (derived from spec.md) and **filter** the NCBI download to include **only** those 50 accessions.
 - **Constraint**: Do NOT rely on a pre-existing `data/raw/genomes.fasta`. The script must generate this file by downloading exactly the 50 specified accessions.
 - **Constraint**: If a download fails, the script MUST raise an error and NOT fall back to synthetic data (Constitution Principle I).
- [ ] T009B [P] Implement `src/data/feature_extractor.py` to compute genomic features (FR-003) **DURING PIPELINE RUN** (no pre-computed cache).
 - **Depends on**: T002b (Docker environment ready), T010C (Valid pathogens list generated).
 - **Pre-requisite**: Verify `data/processed/valid_pathogens.json` exists and filter input list to only valid pathogens.
 - **Logic**:
 1. **Verify Tools**: Ensure Docker images `effectorp/effectorp:3.0` and `antismash/antismash:7.0` (from T002b) are present. **CRITICAL**: Before execution, query the Docker daemon for the **exact SHA256 digest** of the pulled images. Record these exact digests in `data/checksums.json` under keys `effectorp_digest` and `antismash_digest`.
 2. **Download Pfam**: Fetch `Pfam-A.35.0.hmm.gz` from `. **Verify the checksum** of the downloaded file against the canonical source before use.
 3. **Invoke Tools**: For each valid FASTA in `data/raw/genomes.fasta`:
 - Run EffectorP (Docker) to extract effector counts. [UNRESOLVED-CLAIM: c_e051ed18 — status=not_enough_info]
 - Run antiSMASH (Docker) to extract SM cluster counts. [UNRESOLVED-CLAIM: c_2f00809b — status=not_enough_info]
 - Compute GC content using Biopython.
 - Compute **4-mer** frequency profiles: **Set k=4**. Count raw 4-mers, then normalize by **total k-mer count** (formula: `count / total_kmers`) to produce frequency profiles. **Do not use sequence length for normalization.**
 - Compute Pfam domain counts using `hmmsearch` with the downloaded `Pfam-A.35.0.hmm`. Parse output to count unique domain hits per pathogen.
 - **Deliverable**: `data/processed/features_matrix.csv` (NOT a cache). This file is regenerated from `data/raw/genomes.fasta` on every run to satisfy Constitution Principle I (Reproducibility).
- [ ] T009C [DEPRECATED - Merged into T009B]
- [ ] T010A [P] Implement data merging and deduplication logic in `src/data/preprocess.py` (FR-013) handling 'unknown' labels
- [ ] T010B [P] Implement logic to treat missing interaction records as 'unknown' (exclude from training) and generate `data/reports/data_quality_report.json` (FR-013)
- [ ] T010C [P] Implement "Zero Interaction" check in `src/data/preprocess.py` (FR-011) to log critical error and halt if a pathogen has no interactions after merging.
 - **Output**: `data/processed/valid_pathogens.json` (list of pathogen IDs with >0 interactions).
 - **Constraint**: This task MUST run BEFORE T009B.
 - **Dependency Note**: This task depends only on T009A (Interaction Download), not on feature extraction.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Generate Predictive Host‑Range Model (Priority: P1) 🎯 MVP

**Goal**: Run the pipeline on a curated set of pathogens to produce a cross-validated logistic-regression model and report AUPRC.

**Independent Test**: Execute `run_pipeline.sh --data-dir./test_data` and verify `model.pkl` exists, console prints "Cross‑validated AUPRC = [value]", and `feature_importance.csv` has ≥3 non-zero SHAP values.

### Implementation for User Story 1

- [ ] T013 [US1] Implement data splitting in `src/data/preprocess.py` to create **pathogen-stratified** Train/Val sets.
 - **CRITICAL ORDERING**: This split MUST occur **BEFORE** any feature selection (VIF) or model training steps.
 - Reserve a **10-pathogen hold-out set** for independent validation (FR-012, SC-001).
 - **Output**: `data/processed/train_val_split.json` (indices for each fold) and `data/processed/holdout_set.json`.
- [ ] T014 [US1] Implement L1-regularized (L penalty) Logistic Regression **Training Function** in `src/models/train.py` (FR-004).
 - **Depends on**: T013 (Data splitting).
 - **Input**: Feature matrix and labels for a single training fold.
 - **Logic**:
 1. Perform **Nested VIF Analysis** strictly on the *input training fold*:
 - Calculate VIF for all features.
 - While any feature has VIF ≥ 5: remove feature with highest VIF (tie-break: lower variance). **Apply this logic consistently across all folds.**
 2. Fit `LogisticRegression(penalty='l1', solver='liblinear')` on the reduced feature set.
 - **Output**: Trained model object AND save the reduced feature set to `data/processed/vif_filtered_features_fold_{fold}.csv` **immediately after each fold iteration** to ensure traceability.
- [ ] T020 [US1] Implement **Nested Cross-Validation Orchestration Loop** in `src/models/evaluate.py` (FR-006).
 - **Depends on**: T014 (Training function), T013 (Data splitting).
 - **Logic**:
 - **Outer Loop**: Iterate through outer CV folds. Split data into Outer Train and Outer Test.
 - **Inner Loop**: For each Outer Train split, split into **Inner Train** and **Inner Val**.
 - **Model Selection (Inner)**: On the Inner Train/Val split, perform hyperparameter tuning (e.g., L1 penalty lambda) and **Nested VIF analysis** (strictly on Inner Train).
 - **Permutation Testing (Outer)**:
 1. **Generate Null Distribution**: For 1000 permutations, shuffle labels **only within the Outer Test set** (or a held-out validation set derived from the Outer Train split, strictly not the Inner Train used for tuning).
 2. **Re-train**: Train the model (with VIF and hyperparameter tuning) on the shuffled Outer Train data.
 3. **Evaluate**: Evaluate the shuffled model on the **Outer Test** set to get a shuffled AUPRC.
 4. **Compare**: Compare the observed AUPRC (from the unshuffled model on Outer Test) against the null distribution of shuffled AUPRCs.
 5. **Calculate Significance**: Compute the p-value.
 - Aggregate metrics and permutation results.
 - **CRITICAL**: This loop MUST generate the **outer training fold data split object** and use it for the permutation test to ensure unbiased significance estimation.
 - **Deliverable**: Permutation test results stored in `data/processed/permutation_results_fold_{fold}.json`.

- [ ] T015 [US1] Implement k-fold cross-validation evaluation in `src/models/evaluate.py` reporting AUPRC, precision, and calibrated probabilities (FR-005, SC-001)
- [ ] T016a [US1] Implement SHAP value generation in `src/models/interpret.py` to compute SHAP values for **every feature in the model** (FR-007).
 - **Logic**: Load the trained model and the full feature matrix. Compute SHAP values for all features.
 - **Deliverable**: `data/reports/shap_values_all.npy` containing values for all features.
- [ ] T016b [US1] Save ranked list of significant features in `data/reports/feature_importance.csv` (FR-007).
 - **Logic**: Aggregate SHAP values and rank features.
 - **Deliverable**: `feature_importance.csv` with non-zero SHAP values.
- [ ] T017 [US1] Create `run_pipeline.sh` CLI entry point in `src/cli/`. **Args**: `--data-dir` (path to data directory), `--mode` (primary|sensitivity), `--seed` (integer for reproducibility). **Outputs**: `model.pkl`, `feature_importance.csv`, `significant_features.tsv`, `prediction.csv`, `pipeline.log`. **Logic**: Orchestrates download, feature extraction (inline), preprocessing, training, evaluation, and reporting based on the selected mode.
- [ ] T018 [US1] Add error handling for "Missing Genome" and "Zero-Feature Pathogen" edge cases in `src/data/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 – Identify Significant Genomic Feature Categories (Priority: P2)

**Goal**: Run on the full pathogen dataset to identify genomic feature groups statistically associated with broad host ranges.

**Independent Test**: Run pipeline on full dataset; verify `significant_features.tsv` contains ≥2 rows with effect size (Cohen's d) and adjusted p-value ≤ 0.05.

### Implementation for User Story 2

- [ ] T021 [US2] Implement Benjamini-Hochberg FDR correction logic in `src/models/evaluate.py` to adjust p-values (FR-006)
- [ ] T022 [US2] Generate `data/reports/significant_features.tsv` with columns: `feature_name`, `cohen_d`, `adj_p_value`, `significant_flag` using tab delimiter (US-2 Acceptance)
 - **CRITICAL**: Apply the following filter logic: **Keep rows where (adj_p_value <= 0.05) AND (cohen_d >= 0.4)**.
 - **Edge Case Handling**: **If no features pass the filter, save the file with the header row ONLY and a single data row indicating "no_significant_features_found"**. Do not create an empty file.
 - **Logic**:
 1. Load feature importance results.
 2. Calculate Cohen's d for each feature.
 3. Apply FDR correction to p-values.
 4. **Filter**: Keep only rows meeting both significance and effect size thresholds.
 5. **If filtered list is empty**: Write header + "no_significant_features_found" row.
 6. **Else**: Save the filtered list to `significant_features.tsv`.
- [ ] T024 [US2] Implement Bias-Awareness Report generation in `src/models/interpret.py` (FR-018). **Logic**: Calculate interaction count per pathogen; flag if top 10 pathogens account for >80% of interactions. Output `data/reports/bias_awareness.json`
- [ ] T023 [US2] Integrate full dataset processing into `run_pipeline.sh` ensuring the CI limit is respected (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 – Predict Host‑Range for a Novel Pathogen (Priority: P3)

**Goal**: Predict infection likelihood for a single novel genome FASTA file.

**Independent Test**: Run `predict_host_range.sh --genome novel.fa` and verify `prediction.csv` lists ≥20 plant species with probabilities [0, 1].

### Implementation for User Story 3

- [ ] T025a [P] [US3] Implement logic import in `src/data/feature_extractor.py` (offline mode) to reuse exact logic from T009B.
 - **Constraint**: MUST **import and reuse** the exact logic, parameters, and tool versions from `src/features/extract_genomic_features.py` (T009B) to ensure feature space consistency with the trained model.
- [ ] T025b [P] [US3] Implement tool invocation for a *single* novel genome in `src/data/feature_extractor.py`.
 - **Input**: `--genome novel.fa`
 - **Tool Invocation**: Call EffectorP and antiSMASH with standard CLI arguments (via Docker); parse outputs to extract counts.
 - **Logic**: Use `k=4` for k-mers; normalize by total k-mer count.
- [ ] T025c [P] [US3] Implement output generation in `src/data/feature_extractor.py`.
 - **Output**: `data/processed/novel_features.json` containing keys: `effector_count`, `sm_clusters`, `gc_content`, `kmer_profile` (normalized 4-mer counts), `pfam_counts`.
- [ ] T026 [US3] Implement `predict_host_range.sh` CLI script in `src/cli/` to load `model.pkl`, process input FASTA (via T025), and output probabilities
- [ ] T027 [US3] Implement probability calculation for all unique hosts in reference matrix (FR-017).
 - **Metric Calculation**: Compute **Host-Range Breadth** as the **mean** of all predicted infection probabilities across the unique hosts.
 - **Output**: Save to `data/reports/prediction.csv` (columns: `host_species`, `probability`) and `data/reports/host_range_breadth.json` (key: `mean_probability`).
- [ ] T028 [US3] Ensure prediction runtime ≤ 30s and memory ≤ 4GB in `src/cli/predict_host_range.sh` (SC-003)
- [ ] T029 [US3] Handle "Zero-Feature Pathogen" by assigning baseline prevalence probability (Edge Case)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis & Reporting (Cross-Cutting)

**Goal**: Address FR-016 (Sensitivity to missing data) and generate final reports.

- [ ] T030 [P] Implement "Sensitivity Dataset" generation in `src/data/preprocess.py`.
 - **Logic**: Treat missing interaction records as negative (0) to create a dense label vector.
 - **Output**: `data/processed/sensitivity_interactions.csv`.
- [ ] T031a [P] Implement sensitivity dataset preparation in `src/data/preprocess.py` (reusing T030 output).
 - **Output**: `data/processed/sensitivity_features.csv`.
- [ ] T031b [P] Train a secondary "Sensitivity Model" using the dataset from T031a in `src/models/train.py` (reusing T014 logic). <!-- ATOMIZE: requested -->
 - **Output**: `data/models/sensitivity_model.pkl`.
- [ ] T032 [P] Compare metrics in `src/models/evaluate.py`.
 - **Logic**: Calculate AUPRC for the Sensitivity Model and compare against the Primary Model AUPRC.
 - **CRITICAL**: You MUST calculate and report the **variance** (and standard deviation) of the AUPRC difference.
 - **CRITICAL**: You MUST **flag** the result if the difference exceeds a predefined significance threshold.
 - **Deliverable**: `data/reports/sensitivity_analysis.json` containing `primary_auprc`, `sensitivity_auprc`, `delta`, `variance`, `std_dev`, `flag`, and `methodology`. (FR-016)
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
Task: "Implement L1-regularized Logistic Regression training function in src/models/train.py"
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
- **Feasibility Note**: All tasks are designed for CPU-only execution (no CUDA/GPU). Feature extraction is performed inline during the pipeline run to ensure reproducibility, utilizing efficient CLI tools for EffectorP and antiSMASH (via Docker) to meet the CI time limit.