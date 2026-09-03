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

- [ ] T001a Create project directory structure: `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/specs/` using `mkdir -p` or Python `os.makedirs`.
- [ ] T001b Initialize git repository and configure `.gitignore` for Python/data artifacts
- [ ] T002a Create Python 3.11 virtual environment in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/`
- [ ] T002b Install dependencies: `torch`, `torch_geometric`, `rdkit`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `biopython` into the virtualenv
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All tasks below must be completed.

- [ ] T004 [P] Setup `contracts/dataset_schema.schema.yaml` to validate US-1 (Data Ingestion) including: `water_flag` (bool), `coordinates_3d` (list[float]), `resolution` (float > 0), `atom_type` (string), `charge` (float), `hydrophobicity` (float).
- [ ] T005 [P] Setup `contracts/output_schema.schema.yaml` to validate US-3 (Motif Extraction) including: `cluster_id` (int), `p_value` (float), `is_significant` (bool), `pharmacophore_match` (string), `rmsd` (float).
- [ ] T006 [P] Create base `MolecularGraph` entity class in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/entities.py`
- [ ] T007 Setup environment configuration management in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/utils/config.py` (seeds, hyperparameters)
- [ ] T008 Implement robust logging infrastructure in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/utils/io.py` for memory and time tracking
- [ ] T009 Create `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/`, `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/`, and `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/` directory structure
- [ ] T020 [P] [US1] Implement high-resolution filter logic in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/preprocessing.py` that strictly excludes complexes with resolution > 2.5 Å (matching Spec Edge Cases) to ensure data quality. **NOTE**: This logic is executed *within* T013's streaming pipeline, not as a separate blocking task. **MUST**: Be callable by the streamer.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest the PDBbind refined set, construct heterogeneous graphs with 3D steric constraints, and handle hydration states.

**Independent Test**: Run the data pipeline on the full dataset (streamed). Verify that the output graph contains nodes with atomic coordinates, edges representing interactions within 5.0 Å, and that the data structure fits within RAM limits via chunking.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Integration test for graph construction memory footprint in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_graph_memory.py`

### Implementation for User Story 1

- [ ] T013 [US1] **Ingest and Stream PDBbind**: 
    1. Download the PDBbind v2020 refined set from the canonical Hugging Face source (`jglaser/pdbbind_v2020_refined`, split 'train') with SHA256 checksum verification (NO synthetic fallback).
    2. **Streaming Strategy**: Stream the FULL dataset using `datasets.load_dataset(..., streaming=True)` and process in chunks (e.g., a manageable batch size) to fit within available RAM. Do NOT download the full set to disk before processing. Do NOT sample N=1,000; use the full set.
    3. **Filtering**: Apply the high-resolution filter logic (T020) to the stream before graph construction.
    4. Ingest the full dataset into graph format.
    5. **Output**: Save a `processing_config.json` confirming the full dataset was used and the chunking strategy applied. Proceed to graph construction.
    6. **Depends on**: None (Filtering is internal to this task).
- [ ] T014 [US1] Implement graph construction logic in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/ingest.py`: Nodes (atom type, charge, 3D coords), Edges (covalent + non-covalent < 5.0 Å). **MUST**: Store Euclidean distance as an explicit edge attribute to satisfy FR-001's "explicitly encode" clause.
- [ ] T015 [US1] Implement FR-009: Water-mediated interaction detection in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/ingest.py` (distance < 3.5 Å to oxygen atoms). **MUST**: Set `water_flag=True` in the graph object and log the complex ID. **DO NOT** exclude the complex; retain it for analysis and allow downstream steps to apply water-aware logic if needed.
- [ ] T016a [US1] **Sensitivity Data Generation**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/sensitivity.py` to re-run graph construction with varying cutoffs on a representative subset. Save comparison report to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/sensitivity_analysis.json` with keys: `edge_count`, `edge_count_variance`, `node_feature_variance`, `cutoff_used`. **Depends on**: T014, T015.
- [ ] T016b [US1] **Sensitivity Report Update**: Ensure the artifact from T016a is referenced in the final report (T045) to validate model robustness.
- [ ] T017 [US1] Implement memory instrumentation in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/utils/io.py` to log total footprint, ensuring compliance with SC-005 (7 GB limit). **MUST**: Explicitly fail the pipeline if memory usage exceeds 7GB.
- [ ] T018 [US1] **Final Save & Validate**: Save processed graph files to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/` and validate against `contracts/dataset_schema.schema.yaml`. **MUST**: Verify that sensitivity analysis (T016a) is complete before saving final graphs. **Depends on**: T016a.
- [ ] T047 [US1] Implement validation logic in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/data/ingest.py` to verify that all generated graphs preserve the original D coordinates from the PDB file by checking that edge distances match the input PDB coordinates within a tolerance of 0.01 Å, raising an error if deviations exceed this threshold (addressing Rosalind Franklin review on steric constraints).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Affinity Prediction (Priority: P2)

**Goal**: Train a 3-layer message-passing GNN to predict pKd and establish a baseline QSAR model.

**Independent Test**: Train the model on the training split for up to 50 epochs or 4 hours. Evaluate on the test set. Verify MSE is finite and model file is saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_model_output.py`
- [ ] T022 [P] [US2] Integration test for inference latency (< 5s/complex) in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_inference_latency.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `projects/PROJ-predicting-molecular-interactions-in-pro/code/models/gnn.py`: A message passing neural network (MPNN) with a configurable number of layers, 128 hidden units, ReLU activation, sum pooling, and explicit edge features. The architecture must be fixed to satisfy FR-002. **MUST**: Include logic to detect CUDA availability and offload to Kaggle GPU if available.
- [ ] T024 [US2] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/baseline.py`: Random Forest QSAR model on molecular fingerprints for SC-001 comparison
- [ ] T025 [US2] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/train.py`: Training loop with early stopping (patience=10), a maximum time limit of 4 hours (FR-007), and GPU offload trigger logic.
- [ ] T026 [US2] Implement scaffold-based splitting with a standard train/validation/test partition to ensure chemical diversity in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/train.py`
- [ ] T027 [US2] Implement inference benchmarking in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/models/train.py` to measure and record latency per complex (SC-004), ensuring < 5s latency.
- [ ] T028 [US2] Evaluate MSE on validation/test sets and save trained model weights to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/processed/model_gnn.pt` (PyTorch state dict)
- [ ] T029 [US2] Calculate SC-001 metric: % of test complexes within ±1.0 pKd unit vs baseline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Motif Extraction (Priority: P3)

**Goal**: Apply Integrated Gradients, cluster high-importance substructures, and statistically validate motifs against known pharmacophores.

**Independent Test**: Run attribution on top high-affinity test complexes. Verify clustering produces ≥3 distinct clusters and at least one maps to a known pharmacophore with p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for motif output schema in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/contract/test_motif_output.py`
- [ ] T031 [P] [US3] Integration test for statistical significance (permutation test) in `projects/PROJ-543-predicting-molecular-interactions-in-pro/tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/attribution.py`: Integrated Gradients to generate atom-level importance scores (FR-003). **Output**: `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/attribution_scores.json`.
- [ ] T033 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/alignment.py`: Procrustes alignment to normalize high-importance substructures to a common reference frame
- [ ] T034 [US3] Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/clustering.py`: DBSCAN clustering on aligned substructures (min_samples=5) to identify motifs (FR-004)
- [ ] T035a [US3] **Primary Validation (T-Test)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: Compute two-sample t-tests comparing high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes for each identified cluster (Constitution Principle VII). **Input**: Extract importance scores for atoms belonging to each cluster from `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/attribution_scores.json`. **MUST**: Apply Benjamini-Hochberg FDR correction with alpha=0.05 to the raw p-values. **Depends on**: T032, T034.
- [ ] T035b [US3] **FDR Correction**: Apply Benjamini-Hochberg FDR correction (alpha=0.05) to the raw p-values from T035a and generate the final validated motif list. **Depends on**: T035a.
- [ ] T037 [US3] **Secondary Validation (Permutation)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: **Permutation test with 1,000 iterations** of atom coordinate permutations (shuffling atom coordinates to generate the null distribution required by SC-003 and FR-008). **MUST** execute to satisfy SC-003. **DO NOT** shuffle cluster IDs or labels. **Output**: Generate and save `null_distribution.json` containing the distribution of RMSD values from the permuted coordinates. **Depends on**: T034.
- [ ] T038 [US3] **Fallback**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: Mixed-effects model fallback for statistical validation (FR-008); execute ONLY if permutation test assumptions fail or p-value > 0.05. **Depends on**: T037.
- [ ] T038a0 [P] [US3] **Ingest ChEMBL Reference**: Download a recent ChEMBL 'standard' bioactivity subset using the query `target_organism=Homo sapiens AND activity_type='IC' OR 'Ki'` via the `chembl_webresource_client` (resource='molecule', fields='molecule_chembl_id,canonical_smiles,target_organism,activity_type'). **MUST**: Calculate SHA256 checksum, record version, and raise exception on API failure (NO synthetic fallback). Output to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/chembl_raw.json`.
- [ ] T038a1 [US3] **Generate Pharmacophore Reference**: Process `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/raw/chembl_raw.json` (from T038a0) to extract standard pharmacophore features (H-bond donor/acceptor, hydrophobic, aromatic) and save to `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json`. **MUST**: Validate against `contracts/output_schema.schema.yaml` subset. **Schema Requirement**: Output JSON must be a list of objects with keys: `id` (str), `features` (dict with bools for 'H-bond_donor', 'H-bond_acceptor', 'hydrophobic', 'aromatic'), and `coordinates` (list of 3 floats). **Depends on**: T038a0.
- [ ] T039 [US3] Implement cross-referencing against known pharmacophore set in `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json` (generated in T038a1) using Kabsch algorithm (RMSD < 1.5 Å) and reporting matches (FR-005). **Depends on**: T038a1.
- [ ] T040 [US3] Implement ablation study in `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/validation.py`: Validate attribution scores against random edge removal and feature permutation baselines
- [ ] T041 [US3] Generate `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/motifs.json` validated against `contracts/output_schema.schema.yaml` with structure: `[{cluster_id: int, atom_indices: list[int], score: float, p_value: float, is_significant: bool, pharmacophore_match: string, scaffold_id: string}]`. **MUST**: If `pharmacophore_match` is null for a scaffold, trigger T044b conditionally. **Depends on**: T035b, T037, T039.
- [ ] T044b [US3] **Fallback Validation (MM-GBSA)**: Implement `projects/PROJ-543-predicting-molecular-interactions-in-pro/code/analysis/mm_gbsa.py` and invoke it **ONLY** for novel scaffolds where the pharmacophore match in T039 failed. **Detection**: Check `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/motifs.json` for `scaffold_id` not in `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/reference/pharmacophores.json`. **Execution**: Run MM-GBSA using AmberTools (via MMPBSA.py or sander), default dielectric constant, and implicit solvent model on the specific failed complexes. This is a fallback path, not a primary path. **Depends on**: T039.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Success Metrics (Priority: P4)

**Goal**: Aggregate results and validate against success criteria.

- [ ] T042 [US3] Aggregate SC-002: Count distinct, statistically significant motifs (after FDR correction); define 'small set' as **≤ 5 distinct motifs**.
- [ ] T043 [US3] **Validate SC-003**: Calculate the fraction of motifs overlapping with known pharmacophores (RMSD < 1.5 Å) that are statistically significant. **MUST**: Load the `null_distribution.json` generated by T037 (permutation of atom coordinates). Compare the observed fraction of overlapping motifs against this null distribution to calculate a p-value. Validate significance (p < 0.05) before reporting the final metric. **Output**: `projects/PROJ-543-predicting-molecular-interactions-in-pro/data/results/sc003_validation.json`. **Depends on**: T037, T041.
- [ ] T045 [P] Generate final report summarizing SC-001 through SC-005 metrics. **MUST** include: SC-004 (Inference Latency from T027), T016 (Sensitivity Analysis), T044b (MM-GBSA results if applicable). **Depends on**: T042, T043, T027. **NOTE**: T044b is NOT a hard dependency; only include if T041 triggered it.
- [ ] T049 [P] Generate a supplementary validation report specifically addressing the Rosalind Franklin review, detailing the correlation between predicted motifs and observed electron density in high-resolution (≤1.5 Å) complexes.

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
- **Critical Note on 3D**: US-3 tasks explicitly include Procrustes alignment to address the steric constraint concern raised in prior research reviews.
- **Sequential Note**: T032 (Attribution) -> T033 (Alignment) -> T034 (Clustering). T035a (T-Test) depends on T032 and T034. T035b (FDR) depends on T035a. T037 (Permutation Test) shuffles atom coordinates (NOT cluster IDs) to generate `null_distribution.json`. T043 explicitly uses T037's `null_distribution.json`. T036 removed as redundant/contradictory. T016 split into T016a/T016b. T035 split into T035a/T035b. T045 updated to include SC-004. T037 updated to shuffle atom coordinates. T043 updated to explicitly use T037 null distribution.
- **Revision Note**: T019 was removed as scope creep. T020 threshold aligned with Spec (2.5 Å) and moved to Phase 2 (Foundational), logic internal to T013. T038a0 added to ingest ChEMBL data before T038a1. T044b is a fallback path for novel scaffolds only. T048 removed (impossible requirement). T052 removed (architecture constraint violation). T016 split into T016a/T016b. T035 split into T035a/T035b. T045 updated to include SC-004. T046 removed (redundant). T037 updated to shuffle atom coordinates. T043 updated to explicitly use T037 null distribution. T036 removed as it was redundant with T037's new coordinate shuffling logic.
- **Review Response**: T047 explicitly addresses the Rosalind Franklin review by ensuring 3D steric constraints are validated against original coordinates. T044b addresses MM-GBSA validation for novel scaffolds as a fallback path. T035a/T035b/T037 naming clarified and dependencies fixed. T023 architecture constraints fixed. T038a API details added. Water handling is strictly via metadata flagging (T015) as per FR-009, not model modification. T013 updated to stream full dataset (no sampling). T038a1 [P] tag removed due to dependency. T037 updated to explicitly shuffle atom coordinates and generate `null_distribution.json`. T043 updated to consume `null_distribution.json`.