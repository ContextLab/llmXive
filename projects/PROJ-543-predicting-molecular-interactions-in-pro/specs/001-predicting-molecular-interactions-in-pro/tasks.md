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

- [ ] T001a Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `specs/`
- [ ] T001b Initialize git repository and configure `.gitignore` for Python/data artifacts
- [ ] T002a Create Python 3.11 virtual environment in `code/`
- [ ] T002b Install dependencies: `torch`, `torch_geometric`, `rdkit`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `biopython` into the virtualenv
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Setup `contracts/dataset_schema.schema.yaml` to validate US-1 (Data Ingestion) including: `water_flag` (bool), `coordinates_3d` (list[float]), `resolution` (float > 0), `atom_type` (string), `charge` (float), `hydrophobicity` (float).
- [ ] T005 [P] Setup `contracts/output_schema.schema.yaml` to validate US-3 (Motif Extraction) including: `cluster_id` (int), `p_value` (float), `is_significant` (bool), `pharmacophore_match` (string), `rmsd` (float).
- [X] T006 [P] Create base `MolecularGraph` entity class in `code/models/entities.py`
- [X] T007 Setup environment configuration management in `code/utils/config.py` (seeds, hyperparameters)
- [X] T008 Implement robust logging infrastructure in `code/utils/io.py` for memory and time tracking
- [ ] T009 Create `data/raw/`, `data/processed/`, and `data/results/` directory structure
- [ ] T038a [P] [US3] Generate `data/reference/pharmacophores.json` from a verified "known pharmacophore set" (e.g., ChEMBL) as defined in the spec. **MUST**: Calculate SHA256 checksum, record version, and raise exception on API failure (NO synthetic fallback). The query must align with the spec's definition of a "known set" without hard-coding specific filters unless defined in the spec.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest the PDBbind refined set, construct heterogeneous graphs with 3D steric constraints, and handle hydration states.

**Independent Test**: Run the data pipeline on a subset of complexes. Verify that the output graph contains nodes with atomic coordinates, edges representing interactions within 5.0 Å, and that the data structure fits within RAM limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Integration test for graph construction memory footprint in `tests/integration/test_graph_memory.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data/preprocessing.py` to handle missing hydrogens via RDKit inference. This task prepares data for filtering but relies on T020 for the strict resolution threshold enforcement.
- [ ] T013 [US1] Implement `code/data/ingest.py` to download the PDBbind refined set. from ` with SHA256 checksum verification (NO synthetic fallback)
- [ ] T014 [US1] Implement graph construction logic in `code/data/ingest.py`: Nodes (atom type, charge, 3D coords), Edges (covalent + non-covalent < 5.0 Å)
- [ ] T015 [US1] Implement FR-009: Water-mediated interaction detection in `code/data/ingest.py` (distance < 3.5 Å to oxygen atoms) and set `water_flag` as a **global attribute** in the `MolecularGraph` metadata. If flag is set, exclude the complex or apply water-aware analysis path as defined in plan.
- [ ] T016 [US1] Implement 3D sensitivity analysis in `code/data/ingest.py`: Re-run graph construction with varying cutoffs within a standard molecular interaction range (approximately typical interaction distances), save comparison report to `data/results/sensitivity_analysis.json` with metrics: edge count, node feature variance. **Ensure this artifact is referenced in the final report (T045) to validate model robustness.**
- [ ] T016b [P] [US1] Define `contracts/sensitivity_schema.schema.yaml` to validate the output of T016, including: `cutoff_value` (float), `edge_count` (int), `node_feature_variance` (float).
- [ ] T017 [US1] Implement memory instrumentation in `code/utils/io.py` to log total footprint, ensuring compliance with SC-005 (A storage capacity limit will be imposed. The research question, method, and references remain unchanged as per the planning document requirements.)
- [ ] T018 [US1] Save processed graph files to `data/processed/` and validate against `contracts/dataset_schema.schema.yaml`
- [ ] T019 [P] [US1] Implement `tests/contract/test_dataset_schema_validation.py` to explicitly verify that the ingested data from T018 matches `contracts/dataset_schema.schema.yaml` before proceeding to training.
- [ ] T020 [US1] Implement high-resolution filter in `code/data/preprocessing.py` that strictly excludes complexes with resolution > 2.5 Å (matching Spec Edge Cases) to ensure data quality before ingestion.
- [ ] T051 [US1] **Steric Constraint Validation**: Implement `code/data/steric_validator.py` to compute the steric clash score (Lennard-Jones potential energy) for every generated graph. Flag and exclude any complex where the potential energy exceeds a significant threshold., ensuring the graph representation respects 3D physical constraints as required by the Rosalind Franklin review.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Affinity Prediction (Priority: P2)

**Goal**: Train a 3-layer message-passing GNN to predict pKd and establish a baseline QSAR model.

**Independent Test**: Train the model on the training split for up to 50 epochs or 4 hours. Evaluate on the test set. Verify MSE is finite and model file is saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T022 [P] [US2] Integration test for inference latency (< 5s/complex) in `tests/integration/test_inference_latency.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/models/gnn.py`: A multi-layer message passing neural network (MPNN) with a configurable number of hidden units and message-passing logic
- [ ] T024 [US2] Implement `code/models/baseline.py`: Random Forest QSAR model on molecular fingerprints for SC-001 comparison
- [ ] T025 [US2] Implement `code/models/train.py`: Training loop with early stopping (patience=10) and a maximum time limit of **4 hours** (FR-007)
- [ ] T026 [US2] Implement scaffold-based splitting with a standard train/validation/test partition to ensure chemical diversity in `code/models/train.py`
- [ ] T027 [US2] Implement inference benchmarking in `code/models/train.py` to measure and record latency per complex (SC-004), ensuring < 5s latency.
- [ ] T028 [US2] Evaluate MSE on validation/test sets and save trained model weights to `data/processed/model_gnn.pt` (PyTorch state dict)
- [ ] T029 [US2] Calculate SC-001 metric: % of test complexes within ±1.0 pKd unit vs baseline
- [ ] T052 [US2] **Hydration State Modeling**: Modify `code/models/gnn.py` to explicitly incorporate the `water_flag` and water-mediated edge features (from T015) as distinct node/edge types. Train the model to weigh these hydration-specific interactions differently than protein-ligand contacts, addressing the review concern that hydration states determine pocket fit.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Motif Extraction (Priority: P3)

**Goal**: Apply Integrated Gradients, cluster high-importance substructures, and statistically validate motifs against known pharmacophores.

**Independent Test**: Run attribution on top high-affinity test complexes. Verify clustering produces ≥3 distinct clusters and at least one maps to a known pharmacophore with p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for motif output schema in `tests/contract/test_motif_output.py`
- [ ] T031 [P] [US3] Integration test for statistical significance (permutation test) in `tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/analysis/attribution.py`: Integrated Gradients to generate atom-level importance scores (FR-003)
- [ ] T033 [US3] Implement `code/analysis/alignment.py`: Procrustes alignment to normalize high-importance substructures to a common reference frame
- [ ] T034 [US3] Implement `code/analysis/clustering.py`: DBSCAN clustering on aligned substructures (min_samples=5) to identify motifs (FR-004)
- [ ] T035a [US3] **Primary**: Implement `code/analysis/validation.py`: Two-sample t-tests comparing high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes for each identified cluster (Constitution Principle VII). Apply Benjamini-Hochberg FDR correction (alpha=0.05) (FR-006).
- [ ] T035 [US3] **Secondary**: Implement `code/analysis/validation.py`: Permutation test with A sufficient number of iterations and scaffold-aware label shuffling to validate motif significance (FR-008). Execute only if permutation assumptions hold.
- [ ] T036 [US3] Implement `code/analysis/validation.py`: Scaffold-aware label shuffling logic for the permutation test in T035.
- [ ] T036b [US3] **Fallback**: Implement `code/analysis/validation.py`: Mixed-effects model fallback for statistical validation (FR-008); execute ONLY if the permutation test (T035) fails or p-value > 0.05.
- [ ] T038 [US3] Implement cross-referencing against known pharmacophore set in `data/reference/pharmacophores.json` (generated in T038a) using Kabsch algorithm (RMSD < 1.5 Å) and reporting matches (FR-005).
- [ ] T039 [US3] Implement ablation study in `code/analysis/validation.py`: Validate attribution scores against random edge removal and feature permutation baselines
- [ ] T040 [US3] Generate `data/results/motifs.json` validated against `contracts/output_schema.schema.yaml` with structure: `[{cluster_id: int, atom_indices: list[int], score: float, p_value: float, is_significant: bool, pharmacophore_match: string}]`
- [ ] T053 [US3] **Physical Validation Report**: Implement `code/analysis/physical_report.py` to generate a report correlating identified motifs with their steric clash scores (from T051) and hydration states (from T052). Explicitly state whether high-importance motifs correspond to physically plausible (low clash, appropriate hydration) regions, addressing the review's demand for a "quantitative anchor" in 3D space.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Success Metrics (Priority: P4)

**Goal**: Aggregate results and validate against success criteria.

- [ ] T042 [US3] Aggregate SC-002: Count distinct, statistically significant motifs (after FDR correction); define 'small set' as a few motifs.
- [ ] T043a [US3] **Metric Calculation**: Explicitly calculate SC-003: Fraction of identified motifs that overlap with known pharmacophores (RMSD < 1.5 Å, p < 0.05) against the null hypothesis of random structural overlap.
- [ ] T043 [US3] Aggregate SC-003 results from T043a.
- [ ] T044 [US3] **Conditional**: Identify novel scaffolds (Bemis-Murcko) if T038 finds NO pharmacophore matches. **Skip if T038 finds matches.**
- [ ] T044b [US3] **Conditional Fallback**: Implement MM-GBSA validation on the novel scaffolds identified in T044 ONLY IF T038 finds no pharmacophore matches. Use MM-PBSA.py protocol with default parameters. Ensure the validation set is strictly disjoint from the training set to avoid circularity. This task is secondary to the primary t-test (T035a) and secondary permutation test (T035).
- [ ] T045 [P] Generate final report summarizing SC-001 through SC-005 metrics, referencing T016 sensitivity analysis, T044/T044b conditional results, and T053 physical validation. The report must explicitly list: SC-001 (GNN vs Baseline accuracy), SC-002 (Motif count), SC-003 (Pharmacophore overlap fraction), SC-004 (Inference latency), SC-005 (Memory footprint), T016 (Sensitivity), and T053 (Physical validation).

**Dependencies**: T045 depends on completion of T042, T043, and T044/T044b. T044/T044b depends on T038 results.

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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Note on Data**: All data loading tasks MUST fail loudly if the real PDBbind source is unavailable; NO synthetic fallbacks are permitted.
- **Critical Note on 3D**: US-3 tasks explicitly include Procrustes alignment to address the steric constraint concern raised in prior research reviews.
- **Sequential Note**: T032, T033, T034 are sequential (Attribution -> Alignment -> Clustering). T035a (Primary T-Test) MUST execute first. T035 (Permutation) and T036b (Mixed-Effects) are secondary/fallback. T016 depends on T014.
- **Revision Note**: T019 was added for schema verification. T020 moved to Phase 3. T038a moved to Foundational. T044b added for conditional MM-GBSA. T016b added for sensitivity schema. T043a added for explicit SC-003 calculation. T0050 threshold corrected to 2.5 Å. T0025 corrected to 4 hours. T035a citation cleaned.
- **Review Response (Rosalind Franklin)**: Added T050 (High-res validation, threshold corrected to 2.5 Å), T051 (Steric clash validation, threshold fixed to 10.0 kcal/mol), T052 (Explicit hydration modeling in GNN), and T053 (Physical validation report) to ensure the model is anchored in 3D physical reality and electron density constraints, addressing the concern that graph representations alone are insufficient without quantitative 3D anchors.