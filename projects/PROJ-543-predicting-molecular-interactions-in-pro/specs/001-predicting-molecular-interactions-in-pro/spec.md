# Feature Specification: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

The system must successfully ingest the PDBbind v2020 refined set, parse the 3D structural coordinates, and construct a heterogeneous graph representation where atoms are nodes and covalent/non-covalent interactions are edges, enriched with chemical features (charge, hydrophobicity).

**Why this priority**: This is the foundational step; without a valid, structured dataset representing the 3D physics of the complexes, no analysis or model training can occur. It directly addresses the reviewer's concern about steric constraints by ensuring the graph construction explicitly encodes 3D distance-based edges.

**Independent Test**: Run the data pipeline on a subset of 10 complexes. Verify that the output graph contains nodes with atomic coordinates and edges representing interactions within a 5.0 Å cutoff, and that the resulting data structure fits within the 7 GB RAM limit.

**Acceptance Scenarios**:

1. **Given** the PDBbind v2020 refined set is available, **When** the ingestion script processes a complex with resolution < 2.0 Å, **Then** the system constructs a graph where non-covalent edges are created for atom pairs within 5.0 Å, and the graph object is saved to disk.
2. **Given** a complex with missing hydrogen atoms, **When** the system processes it, **Then** the system either infers missing hydrogens based on standard valency or flags the complex for exclusion, ensuring no dangling bonds exist in the graph.
3. **Given** the full dataset ([deferred] complexes), **When** the ingestion process completes, **Then** the total memory footprint of the loaded graphs does not exceed 6 GB, and the output directory contains [deferred] graph files.

---

### User Story 2 - GNN Training and Affinity Prediction (Priority: P2)

The system must train a message-passing Graph Neural Network (3 layers, 128 hidden units) to predict binding affinity (pKd) from the constructed graphs, using a standard 80/10/10 train/validation/test split, and output the trained model weights.

**Why this priority**: This implements the core predictive capability. It is distinct from data ingestion (US-1) and attribution (US-3). It must be testable by verifying prediction accuracy on the held-out test set.

**Independent Test**: Train the model on the training split for 50 epochs. Evaluate on the test split. Verify that the Mean Squared Error (MSE) is finite and that the model file is saved.

**Acceptance Scenarios**:

1. **Given** a valid training set of [deferred] graphs, **When** the training loop executes for 50 epochs, **Then** the model converges to an MSE < 2.0 (pKd units) on the validation set, and the training log shows a decreasing loss curve.
2. **Given** the trained model, **When** it is applied to the test set (500 complexes), **Then** the predicted pKd values are within the range of [-10, 20], and no NaN values are present in the output.
3. **Given** a new, unseen complex graph, **When** the model predicts affinity, **Then** the inference time is < 5 seconds per complex on a CPU-only environment.

---

### User Story 3 - Interpretability and Motif Extraction (Priority: P3)

The system must apply Integrated Gradients to the trained model to generate feature importance scores for atoms and interactions, cluster these high-importance substructures using DBSCAN, and cross-reference them against known pharmacophores to identify 3-5 recurring motifs.

**Why this priority**: This delivers the specific scientific insight requested in the research question (identifying substructures). It is a post-hoc analysis that depends on a trained model but provides the unique value proposition of interpretability.

**Independent Test**: Run the attribution pipeline on the top 100 high-affinity test complexes. Verify that the clustering algorithm produces at least 3 distinct clusters of substructures, and that at least one cluster maps to a known pharmacophore in the ChEMBL database.

**Acceptance Scenarios**:

1. **Given** a trained model and a high-affinity test complex (pKd > 8), **When** Integrated Gradients is applied, **Then** the top [deferred] of atoms by importance score are identified, and their spatial coordinates are extracted.
2. **Given** the set of high-importance substructures from 100 complexes, **When** DBSCAN clustering is performed with a minimum cluster size of 5, **Then** at least 3 distinct substructure clusters are identified.
3. **Given** a identified substructure cluster, **When** it is queried against the ChEMBL pharmacophore database, **Then** at least one cluster shows a structural overlap (RMSD < 1.5 Å) with a known binding motif, and a report is generated listing the matched pharmacophores.

### Edge Cases

- **What happens when** the PDBbind dataset contains complexes with resolution > 2.5 Å? The system must filter these out or flag them, as low-resolution structures may introduce noise in the 3D edge construction.
- **How does the system handle** protein-ligand complexes where the ligand has an unusual atom type not present in the RDKit standard dictionary? The system must map unknown atoms to a generic "unknown" type with a zeroed feature vector rather than crashing.
- **What happens when** the GNN training fails to converge (loss plateaus or diverges)? The system must detect this after 10 epochs without improvement and trigger an early stop, logging the failure reason without blocking the entire pipeline.

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct molecular graphs from 3D coordinates by creating edges between atoms within a 5.0 Å cutoff to explicitly encode steric constraints (See US-1).
- **FR-002**: System MUST train a 3-layer message-passing GNN with 128 hidden units to predict pKd using mean-squared error loss on a CPU-only environment (See US-2).
- **FR-003**: System MUST apply Integrated Gradients to generate atom-level feature importance scores for all predictions in the test set (See US-3).
- **FR-004**: System MUST cluster high-importance substructures using DBSCAN with a minimum cluster size of 5 to identify recurring motifs (See US-3).
- **FR-005**: System MUST validate identified motifs by cross-referencing against the ChEMBL database and reporting matches with RMSD < 1.5 Å (See US-3).
- **FR-006**: System MUST perform multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when reporting statistical significance of motif enrichment (See US-3).
- **FR-007**: System MUST enforce a maximum training time of 4 hours per run to ensure compatibility with free-tier CI limits (See US-2).

### Key Entities

- **MolecularGraph**: Represents a protein-ligand complex; attributes include nodes (atom type, charge, 3D coordinates), edges (bond type, distance), and global properties (pKd, resolution).
- **SubstructureCluster**: A group of spatially similar high-importance atom sets; attributes include centroid coordinates, member count, and associated pharmacophore ID.
- **FeatureImportanceMap**: A mapping from atom indices in a graph to their attribution scores; attributes include atom index, score value, and interaction type.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of test complexes where the model predicts pKd within ±1.0 unit of the experimental value is measured against the baseline of random guessing (See US-2).
- **SC-002**: The number of distinct, statistically significant substructure motifs identified (after multiple-comparison correction) is measured against the target of 3-5 motifs (See US-3).
- **SC-003**: The fraction of identified motifs that overlap with known pharmacophores in ChEMBL (RMSD < 1.5 Å) is measured against the null hypothesis of random structural overlap (See US-3).
- **SC-004**: The inference time per complex on a CPU-only environment is measured against the 6-hour total job limit (See US-2).
- **SC-005**: The memory footprint of the largest loaded graph dataset is measured against the 7 GB RAM limit (See US-1).

## Assumptions

- The PDBbind v2020 refined set contains all necessary 3D coordinates and binding affinity measurements (pKd) required for the analysis; if specific variables (e.g., explicit hydration states) are missing, the model will rely on implicit water effects captured by the ligand-protein interface geometry.
- The "graph representation" limitation regarding steric constraints is mitigated by explicitly encoding 3D Euclidean distances as edge features, allowing the GNN to learn spatial dependencies despite the lack of a full physics-based simulation.
- The ChEMBL database contains sufficient pharmacophore definitions to validate at least one of the identified substructure clusters.
- The free-tier GitHub Actions runner (2 CPU, 7 GB RAM) is sufficient for training a small 3-layer GNN on a subset of [deferred] complexes if the data is pre-processed and loaded efficiently.
- Integrated Gradients provides a sufficiently accurate approximation of feature importance for identifying key interaction motifs, even if it is an approximation method.
- The dataset variables (atom types, coordinates, pKd) are consistent across the PDBbind v2020 refined set, requiring no complex imputation for missing atomic data beyond standard hydrogen addition.
