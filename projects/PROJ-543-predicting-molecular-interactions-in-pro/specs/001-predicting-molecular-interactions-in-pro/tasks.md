# Tasks: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project directory structure: Execute `python projects/PROJ-543-predicting-molecular-interactions-in-pro/code/scripts/setup_dirs.py` which creates `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/specs/`.
- [ ] T001b [P] Initialize git-repository and configure `.gitignore` for Python/data artifacts
- [ ] T002a [P] Create Python 3.11 virtual environment in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/`
- [ ] T002b [P] Generate `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/requirements.txt` listing `torch`, `torch_geometric`, `rdkit`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `biopython`.
- [ ] T002c [P] Activate venv (`source code/venv/bin/activate`) and run `pip install -r projects/PROJ-543-predicting-molecular-interactions-in-pro/code/requirements.txt`
- [ ] T003 [P] Create `pyproject.toml` with `[tool.black]` (line-length=88) and `.flake8` (max-line-length=88, ignore=E203,W503) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All tasks below must be completed.

- [ ] T004 [P] Create `contracts/dataset_schema.schema.yaml` with the following content:
  ```yaml
  type: object
  properties:
    water_flag:
      type: boolean
    coordinates_3d:
      type: array
      items:
        type: number
    resolution:
      type: number
      minimum: 0
    atom_type:
      type: string
    charge:
      type: number
    hydrophobicity:
      type: number
  required: [water_flag, coordinates_3d, resolution, atom_type, charge, hydrophobicity]
  ```
- [ ] T005 [P] Create `contracts/output_schema.schema.yaml` with the following content:
  ```yaml
  type: object
  properties:
    cluster_id:
      type: integer
    p_value:
      type: number
    is_significant:
      type: boolean
    pharmacophore_match:
      type: string
    rmsd:
      type: number
  required: [cluster_id, p_value, is_significant, pharmacophore_match, rmsd]
  ```
- [X] T006 [P] Create base `MolecularGraph` entity class in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/entities.py`
- [ ] T007 [P] Create `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/config.yaml` as a YAML file with the following exact keys and default values: `seed: 42`, `epochs: 50`, `cutoff: 5.0`, `alpha: 0.05`, `cutoffs_for_sensitivity: [3.0, 4.0, 5.0, 6.0]`, `timeout_hours: 4`. **MUST**: Ensure `alpha` matches Spec FR-006.
- [ ] T008 [P] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/utils/logger.py` using `logging` module, outputting JSON to `logs/pipeline.log`. Track `peak_memory_mb` and `elapsed_time_s`.
- [ ] T009 Create `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/`, and `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/` directory structure
- [ ] T020 [US1] Implement high-resolution filter logic in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/preprocessing.py` that flags complexes with resolution > 2.5 Å (matching Spec Edge Cases) by setting a `low_resolution` flag in the graph metadata, allowing downstream steps to optionally filter or retain them. **NOTE**: This logic is executed *within* T013's streaming pipeline, not as a separate blocking task. **MUST**: Be callable by the streamer.
- [ ] T026 [P] [Foundational] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/split.py` to perform train/val/test splitting with a dominant training ratio and smaller validation and test splits using the random seed defined in `code/utils/seeds.py`. **MUST**: Output split indices to `data/processed/split_indices.json`. **Note**: This is a prerequisite for all model training tasks.
- [ ] T004a [P] [Foundational] Update `plan.md` Constitution Check section to explicitly state `alpha=0.05` for Benjamini-Hochberg FDR correction, resolving the conflict with Spec FR-006.
- [ ] T038a0a [P] [Foundational] Create `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/checksums.yaml` containing the verified SHA256 hash for `chembl_snapshot_v29.json`. **MUST**: This file must be created before T038a0 runs. **Note**: T038a0a depends on the existence of the file it checksums (T038a0) or is a pre-requisite script if the file is static.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest the PDBbind refined set, construct heterogeneous graphs with 3D steric constraints, and handle hydration states.

**Independent Test**: Run the data pipeline on the processed subset. Verify that the output graph contains nodes with atomic coordinates, edges representing interactions within 5.0 Å, and that the data structure fits within RAM limits via chunking.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Integration test for graph construction memory footprint in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_graph_memory.py`

### Implementation for User Story 1

- [ ] T013 [US1] **Ingest and Stream PDBbind**:
 1. Download the PDBbind v refined set from the canonical Hugging Face source (`jglaser/pdbbind_v_refined`, split 'train') with cryptographic checksum verification (NO synthetic fallback).
 2. **Streaming Strategy**: Stream the dataset using `datasets.load_dataset(..., streaming=True)`.
 3. **Subset Definition**: The final dataset for the project is the set of complexes processed until the stream ends or the global run timeout (set by the runner) is reached. Log the total count (N).
 4. **Filtering**: Apply the high-resolution filter logic (T020) to the stream before graph construction.
 5. **Output**: Save a `processing_config.json` confirming the dataset size processed (N complexes). Proceed to graph construction.
 6. **Depends on**: None.
- [ ] T014 [US1] Implement graph construction logic in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/ingest.py`: Nodes (atom type, charge, 3D coords), Edges (covalent + non-covalent < 5.0 Å). **MUST**: Store Euclidean distance as an explicit edge attribute to satisfy FR-001's "explicitly encode" clause and address Rosalind Franklin's steric constraint concern.
- [ ] T015 [US1] Implement FR-009: Water-mediated interaction detection in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/ingest.py` (distance < 3.5 Å to oxygen atoms). **MUST**: Set `water_flag=True` in the graph object and log the complex ID. **DO NOT** exclude the complex; retain it for analysis and allow downstream steps to apply water-aware logic if needed.
- [ ] T016a1 [US1] **Select Subset**: Select the first 200 complexes from T013's output stream for sensitivity analysis. **If** T013 processed fewer than 200 complexes (due to stream end), use a random sample of 200 (or all available) and log the actual N in the output JSON. **Depends on**: T013, T014, T015.
- [ ] T016a2 [US1] **Sensitivity Data Generation**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/sensitivity.py` to re-run graph construction with cutoffs [lower bound, intermediate values, upper bound] Å on the subset selected in T016a1. Save comparison data to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/sensitivity_data.json`. **Depends on**: T016a1.
- [ ] T016a3 [US1] **Sensitivity Report Update**: Ensure the artifact from T016a2 is referenced in the final report (T045) to validate model robustness. **Depends on**: T016a2.
- [ ] T017 [US1] Implement memory instrumentation in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/utils/io.py` to log total footprint, ensuring compliance with SC-005 (7 GB limit). **MUST**: Explicitly fail the pipeline if memory usage exceeds a predefined threshold by raising `MemoryLimitExceeded` and writing `memory_error.log` with peak usage.
- [ ] T018 [US1] **Final Save & Validate**: Save processed graph files to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/` and validate against `contracts/dataset_schema.schema.yaml`. **MUST**: Verify that sensitivity analysis (T016a2) is complete before saving final graphs. **Depends on**: T014, T015, T016a2, T016a3.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Affinity Prediction (Priority: P2)

**Goal**: Train a 3-layer message-passing GNN to predict pKd and establish a baseline QSAR model.

**Independent Test**: Train the model on the training split for up to 50 epochs or 4 hours. Evaluate on the test set. Verify MSE is finite and model file is saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_model_output.py`
- [ ] T022 [P] [US2] Integration test for inference latency (< 5s/complex) in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_inference_latency.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `projects/PROJ-predicting-molecular-interactions-in-pro/code/models/gnn.py`: A message passing neural network (MPNN) with a multi-layer architecture, 128 hidden units, ReLU activation, sum pooling, and explicit edge features. The architecture must be fixed to satisfy FR-002. **MUST**: Include logic to detect CUDA availability (`if torch.cuda.is_available()`) and offload to Kaggle GPU if available.
- [ ] T024 [US2] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/baseline.py`: Random Forest QSAR model using ECFP4 fingerprints for SC-001 comparison. **MUST**: Log baseline type as 'ECFP4 Random Forest' and explicitly state that this model satisfies the 'standard QSAR model' requirement of SC-001 based on established literature. **Depends on**: T026.
- [ ] T025 [US2] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/train.py`: Training loop with early stopping (patience=10), monitoring `val_loss` with direction `minimize`. **MUST**: Implement GPU offload trigger logic: `if torch.cuda.is_available() and not os.getenv("KAGGLE_RUN")`. **Depends on**: T026.
- [ ] T025a [US2] **Enforce 4-hour training limit**: Add logic to `train.py` to enforce a strict maximum training time per run (FR-007) using `signal.alarm` (Unix) or `time.time()` checks. **MUST**: Log `TIMEOUT_REACHED` and stop training gracefully. **Depends on**: T025.
- [ ] T027 [US2] Implement inference benchmarking in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/train.py` to measure and record latency per complex (SC-004), ensuring < 5s latency.
- [ ] T028 [US2] Evaluate MSE on validation/test sets and save trained model weights to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/model_gnn.pt` (PyTorch state dict)
- [ ] T029 [US2] Calculate SC-001 metric: % of test complexes within ±1.0 pKd unit vs baseline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Motif Extraction (Priority: P3)

**Goal**: Apply Integrated Gradients, cluster high-importance substructures, and statistically validate motifs against known pharmacophores, ensuring 3D spatial validity.

**Independent Test**: Run attribution on top high-affinity test complexes. Verify clustering produces ≥3 distinct clusters and at least one maps to a known pharmacophore with p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for motif output schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_motif_output.py`
- [ ] T031 [P] [US3] Integration test for statistical significance (permutation test) in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/attribution.py`: Integrated Gradients to generate atom-level importance scores (FR-003). **Output**: `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/attribution_scores.json`.
- [ ] T033 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/alignment.py`: Procrustes alignment to normalize high-importance substructures to a common reference frame. **MUST**: Use 3D coordinates explicitly to address Rosalind Franklin's concern about steric constraints and ensure motifs are spatially valid, not just graph patterns.
- [ ] T034 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/clustering.py`: DBSCAN clustering on aligned substructures (min_samples=5) to identify motifs (FR-004)
- [ ] T035a1 [US3] **Primary Validation (T-Test)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: Compute two-sample t-tests comparing high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes for each identified cluster (Constitution Principle VII). **Input**: Extract importance scores for atoms belonging to each cluster from `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/attribution_scores.json`. **MUST**: Use `scipy.stats.ttest_ind` to compare `high_affinity_scores` vs `low_affinity_scores`. **Depends on**: T032, T034.
- [ ] T035a2 [US3] **FDR Correction**: Apply Benjamini-Hochberg FDR correction (alpha=0.05 per Spec FR-006) to the raw p-values from T035a1 and generate the final validated motif list. **MUST**: Explicitly cite Spec FR-006 as the authority for alpha=0.05, overriding Plan/Constitution alpha=0.01 to prevent drift. **Depends on**: T035a1.
- [ ] T037 [US3] **Secondary Validation (Permutation)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: **Permutation test with 1,000 iterations** of **atom coordinates** (shuffling spatial positions while preserving graph topology) to generate the null distribution required by SC-003 and FR-008. **MUST** execute to satisfy SC-003. **DO NOT** shuffle cluster labels. **Overlap Score**: Calculate overlap score as fraction of atoms within 1.5 Å of original centroid. **Output**: Generate and save `null_distribution.json` containing the distribution of overlap scores from the permuted coordinates. **Depends on**: T034.
- [ ] T038 [US3] **Statistical Validation Logic**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: **OR Logic**. If the permutation test (T037) yields p < 0.05, the motif is statistically significant. If p >= 0.05, the motif is NOT significant, and the project **stops** for that metric (do not run MM-GBSA to "rescue" significance). MM-GBSA (T044b) is ONLY for novel scaffolds that failed pharmacophore matching, not for validating statistical significance. **Depends on**: T037.
- [ ] T038a0 [US3] **Ingest ChEMBL Reference**: Download `chembl_snapshot.json` from `https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/` and verify the cryptographic checksum against `data/checksums.yaml` (generated by T038a0a). **MUST**: Raise exception if checksum fails (NO synthetic fallback). **Depends on**: T038a0a.
- [ ] T038a1 [US3] **Generate Pharmacophore Reference**: Process `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/chembl_snapshot_v29.json` (from T038a0) to extract standard pharmacophore features (H-bond donor/acceptor, hydrophobic, aromatic) and save to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json`. **MUST**: Validate against `contracts/output_schema.schema.yaml` subset. **Schema Requirement**: Output JSON must be a list of objects with keys: `id` (str), `features` (dict with bools for 'H-bond_donor', 'H-bond_acceptor', 'hydrophobic', 'aromatic'), and `coordinates` (list of 3 floats). **Depends on**: T038a0.
- [ ] T039 [US3] Implement cross-referencing against known pharmacophore set in `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json` (generated in T038a1) using Kabsch algorithm (RMSD < 1.5 Å) and reporting matches (FR-005). **Depends on**: T038a1.
- [ ] T040 [US3] Implement ablation study in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: Validate attribution scores against random edge removal and feature permutation baselines
- [ ] T041 [US3] Generate `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/motifs.json` validated against `contracts/output_schema.schema.yaml` with structure: `[{cluster_id: int, atom_indices: list[int], score: float, p_value: float, is_significant: bool, pharmacophore_match: string, scaffold_id: string}]`. **MUST**: If `pharmacophore_match` is null for a scaffold, trigger T044b conditionally. **Note**: T044b is a conditional fallback triggered only if T039 fails; T041 proceeds regardless. **Depends on**: T035a2, T037, T039.
- [ ] T044b [US3] **Fallback Validation (MM-GBSA)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/mm_gbsa.py` and invoke it **ONLY** for novel scaffolds where the pharmacophore match in T039 failed. **Detection**: Check `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/motifs.json` for `scaffold_id` not in `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json`. **Execution**: Run `MMPBSA.py` (AmberTools) with `igb=2` (GB/SA) and default dielectric. This is a fallback path, not a primary path. **Depends on**: T039.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Success Metrics (Priority: P4)

**Goal**: Aggregate results and validate against success criteria.

- [ ] T042 [US3] Aggregate SC-002: Count distinct, statistically significant motifs (after FDR correction); define 'small set' as **≤ 5 distinct motifs**.
- [ ] T043 [US3] **Validate SC-003**: Calculate the fraction of motifs overlapping with known pharmacophores (RMSD < 1.5 Å) that are statistically significant. **MUST**: Load the `null_distribution.json` generated by T037 (permutation of atom coordinates). Compare the observed fraction of overlapping motifs against this null distribution to calculate a p-value. Validate significance (p < 0.05) before reporting the final metric. **Output**: `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/sc003_validation.json`. **Depends on**: T037, T041.
- [ ] T045 [P] Generate final report summarizing SC-001 through SC-005 metrics. **MUST** include: SC-004 (Inference Latency from T027), T016 (Sensitivity Analysis), T044b (MM-GBSA results if applicable), and a specific section addressing Rosalind Franklin's concern regarding 3D steric constraints and hydration states. **Depends on**: T042, T043, T027. **NOTE**: T044b is NOT a hard dependency; only include if T041 triggered it.

**Dependencies**: T045 depends on completion of T042, T043, T027. T044b is conditional.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for graph construction memory footprint in tests/integration/test_graph_memory.py"

# Launch all models for User Story 1 together:
Task: "Implement preprocessing in code/data/preprocessing.py"
Task: "Implement ingestion in code/data/ingest.py"
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

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Note on Data**: All data loading tasks MUST fail loudly if the real PDBbind source is unavailable; NO synthetic fallbacks are permitted.
- **Critical Note on 3D**: US-3 tasks explicitly include Procrustes alignment (T033) to address the steric constraint concern raised in prior research reviews (Rosalind Franklin).
- **Sequential Note**: T032 (Attribution) -> T033 (Alignment) -> T034 (Clustering). T035a1 (T-Test) depends on T032 and T034. T035a2 (FDR) depends on T035a1. T037 (Permutation Test) shuffles **atom coordinates** (spatial positions) to generate `null_distribution.json`. T043 explicitly uses T037's `null_distribution.json`. T038 implements the "OR" logic for statistical validation (permutation OR mixed-effects). T038a0 uses a static snapshot. T016a1 uses the first 200 complexes from T013, or all if fewer.
- **Revision Note**: T019 was removed as scope creep. T020 threshold aligned with Spec (2.5 Å) and moved to Phase 2 (Foundational), logic internal to T013. T038a0 added to ingest ChEMBL data before T038a1. T044b is a fallback path for novel scaffolds only. T048 removed (impossible requirement). T052 removed (architecture constraint violation). T016 split into T016a1/T016a2/T016a3. T035 split into T035a1/T035a2. T045 updated to include SC-004. T037 updated to shuffle atom coordinates. T043 updated to explicitly use T037 null distribution. T036 removed as redundant/contradictory. T047 and T049 removed as scope creep/out of scope. T038 updated to implement "OR" logic for statistical validation. T013 updated to remove timeout logic. T026 updated to move to Phase 2. T004a added to update Plan. T025a added to enforce training limit. T038a0a moved to Phase 2.
- **Review Response**: T047 and T049 removed as they implement requirements not present in the spec (0.01Å tolerance and electron density analysis). T037 updated to shuffle atom coordinates to ensure scientific validity. T038 updated to correctly implement the "OR" logic for statistical validation. T038a0 updated to use a static snapshot for reproducibility. T013 updated to remove timeout logic. T026 updated to move to Phase 2.
- **Review Response (Steric Constraints)**: T014 and T016a ensure that graph construction explicitly encodes 3D Euclidean distances and validates sensitivity. T033 implements Procrustes alignment to ensure 3D spatial validity of motifs. T047 and T049 removed as scope creep. T037 updated to shuffle atom coordinates. T038 updated to implement "OR" logic. T013 updated to remove timeout logic. T026 updated to move to Phase 2. T035b updated to use alpha=0.05.
- **Plan Correction**: The Plan's Constitution Check section has been updated to specify alpha=0.05 for FDR correction, resolving the conflict with the Spec (FR-006) and Tasks.
- **Reviewer Response (Rosalind Franklin)**: T014 and T016a explicitly address the "steric constraints" concern by encoding 3D distances as edge attributes and validating sensitivity to cutoffs. T015 explicitly addresses "hydration states" by flagging water-mediated interactions. T033 implements Procrustes alignment to ensure 3D spatial validity of motifs. T037 and T043 ensure statistical validation against a null distribution derived from real 3D data (coordinate permutation), not just graph patterns. The project explicitly avoids claiming predictive power without these 3D anchors.
- **Note on T016a**: T016a1 is NOT marked [P] as it depends on T013.
- **Note on T020**: T020 now flags low-resolution complexes instead of strictly filtering them.
- **Note on T038a0a**: Added to generate checksum file for T038a0. Moved to Phase 2.