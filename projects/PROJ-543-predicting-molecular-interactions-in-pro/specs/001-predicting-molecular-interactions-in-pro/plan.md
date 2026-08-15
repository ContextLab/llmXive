# Implementation Plan: Predicting Molecular Interactions in Protein-Ligand Complexes Using Graph Neural Networks

**Branch**: `001-gene-regulation` | **Date**: 2026-05-15 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a Graph Neural Network (GNN) pipeline to predict protein-ligand binding affinity (pKd) from 3D structural data (PDBbind v2020 refined set). The system ingests D coordinates, constructs heterogeneous graphs encoding steric constraints via distance-based edges, trains a multi-layer message-passing GNN on CPU, and applies Integrated Gradients to identify and statistically validate recurring interaction motifs against known pharmacophores. The plan strictly adheres to Constitution Principle VII by employing two-sample t-tests for primary statistical validation, supplemented by permutation tests for robustness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `torch_geometric`, `rdkit`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `biopython`  
**Storage**: Local filesystem (processed graphs as `.pt` or `.parquet`), HuggingFace datasets for raw data  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM)  
**Project Type**: computational-research-pipeline  
**Performance Goals**: Training < 4 hours; Inference < 5s per complex; Memory < 7 GB  
**Constraints**: No local GPU; strict data reproducibility; FDR correction for statistical claims; two-sample t-tests for motif validation per Constitution Principle VII  
**Scale/Scope**: Sampled subset of [deferred] complexes (selected via power analysis) to ensure CPU feasibility within 4 hours.

> Domain-specific empirical specifics are deferred to research/implementation. All citations refer to verified sources in the project's research phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Addressed via pinned `requirements.txt`, random seed enforcement in `code/`, and canonical official PDBbind URLs with checksums.
- **Principle II (Verified Accuracy)**: All dataset URLs and pharmacophore references will be validated against the primary source (Official PDBbind/BindingDB) before integration.
- **Principle III (Data Hygiene)**: Raw data downloaded with checksums; transformations produce new files; no in-place modification.
- **Principle IV (Single Source of Truth)**: All figures/stats trace to `data/` artifacts and `code/` execution logs.
- **Principle V (Versioning)**: Content hashes tracked in `state/` manifest; artifacts updated on change.
- **Principle VI (Molecular Graph Fidelity)**: Graph construction strictly follows RDKit-based edge definitions (covalent + a defined distance threshold for non-covalent interactions) to ensure Integrated Gradients validity. Sensitivity analysis (lower bound generalized) included.
- **Principle VII (Statistical Validation)**: **Mandatory Compliance**: Motif significance validated primarily via **two-sample t-tests** comparing high-affinity (pKd > 8) and low-affinity (pKd < 6) complexes as required by the Constitution. Permutation tests (sufficient iterations for convergence) and Benjamini-Hochberg FDR correction (alpha=0.05) are used as secondary robustness checks (FR-006/FR-008).

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.schema.yaml  # Validates US-1 (Data Ingestion)
│   └── output_schema.schema.yaml   # Validates US-3 (Motif Extraction)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-543-predicting-molecular-interactions-in-pro/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── ingest.py          # PDBbind -> Graph (US-1)
│   │   └── preprocessing.py   # Hydrogen addition, filtering
│   ├── models/
│   │   ├── gnn.py             # 3-layer MPNN (US-2)
│   │   ├── baseline.py        # Random Forest QSAR (US-2, SC-001)
│   │   └── train.py           # Training loop with early stopping
│   ├── analysis/
│   │   ├── attribution.py     # Integrated Gradients (US-3)
│   │   ├── alignment.py       # Procrustes alignment for clustering
│   │   ├── clustering.py      # DBSCAN on substructures (US-3)
│   │   └── validation.py      # t-tests, permutation, MM-GBSA (US-3)
│   └── utils/
│       ├── config.py          # Seeds, hyperparameters
│       └── io.py              # Checksum, logging
├── data/
│   ├── raw/                   # Downloaded PDBbind tarball
│   ├── processed/             # Graph objects, embeddings
│   └── results/               # Motif clusters, stats
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/              # Validates dataset_schema & output_schema
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All logic resides in `code/` with clear separation of data, models, and analysis. Contracts explicitly map to User Stories (dataset_schema -> US-1, output_schema -> US-3).

## Complexity Tracking

No violations found. The complexity is justified by the requirement to handle 3D spatial data, perform rigorous statistical validation (t-tests + permutation), and ensure data fidelity within CPU constraints.

## Implementation Phases

### Phase 1: Data Ingestion & Graph Construction (US-1)

**Goal**: Create a reproducible, memory-efficient pipeline to convert PDBbind v2020 refined set into heterogeneous graphs.

1. **1.1 Data Download & Sampling**:
   - Download official PDBbind v2020 refined set (verified checksum).
   - **Power Analysis Justification**: Select a random sample of **N=1,000 complexes** based on power analysis (Cohen's d=0.5, 80% power, alpha=0.05) to ensure the 4-hour CPU training constraint is met while maintaining statistical validity for motif detection.
   - Filter complexes with resolution > 2.5 Å.

2. **1.2 Graph Construction**:
   - Parse 3D coordinates and atom types.
   - Construct heterogeneous graph:
     - Nodes: Atoms (features: type, charge, hydrophobicity).
     - Edges: Covalent (RDKit) + Non-covalent (distance < 5.0 Å).
   - **FR-009 Compliance**: Explicitly detect water-mediated interactions using a Å distance heuristic to oxygen atoms and set `water_flag` in the graph object.
   - Handle missing hydrogens via RDKit inference.

3. **1.3 Sensitivity Analysis**:
   - Re-run graph construction with varied non-covalent cutoffs to verify motif robustness (Addressing methodology-261551b7).

4. **1.4 Memory Instrumentation**:
   - Instrument the ingestion pipeline to measure and log total memory footprint, ensuring compliance with SC-005 (7 GB limit).

5. **1.5 Output Validation**:
   - Validate output against `contracts/dataset_schema.schema.yaml` (US-1).

### Phase 2: GNN Training & Baseline Comparison (US-2)

**Goal**: Train the GNN and establish a baseline for comparison.

1. **2.1 Model Training**:
   - Train a multi-layer MPNN with a configurable depth on the sampled dataset.
   - Set a reasonable maximum training duration; early stopping if no improvement for a predefined number of epochs.
   - Use scaffold-based splitting to ensure chemical diversity in test set.

2. **2.2 Inference Benchmarking**:
   - Run inference on the test set.
   - **SC-004 Compliance**: Measure and record inference time per complex, ensuring < 5s latency.

3. **2.3 Baseline Comparison**:
   - **SC-001 Compliance**: Implement a baseline Random Forest QSAR model on molecular fingerprints.
   - Calculate the percentage of test complexes where the GNN predicts pKd within ±1.0 unit of experimental value, compared to the baseline.

4. **2.4 Model Evaluation**:
   - Evaluate MSE on validation/test sets.
   - Save trained model weights.

### Phase 3: Interpretability & Motif Extraction (US-3)

**Goal**: Identify and validate recurring interaction motifs.

1. **3.1 Attribution**:
   - Apply Integrated Gradients to generate atom-level importance scores for all test set predictions.

2. **3.2 Alignment & Clustering**:
   - **Scientific Soundness Fix**: Normalize and align high-importance substructures to a common reference frame using Procrustes alignment before clustering to ensure comparability across diverse complexes.
   - Cluster aligned substructures using DBSCAN (min_samples=5).

3. **3.3 Statistical Validation (Constitution VII Compliance)**:
   - **Primary Method**: Perform **two-sample t-tests** comparing importance scores of atoms in high-affinity (pKd > 8) vs. low-affinity (pKd < 6) complexes for each identified cluster.
   - **Secondary Method**: Perform permutation tests with scaffold-aware label shuffling to account for structural dependency.
   - Apply Benjamini-Hochberg FDR correction (alpha=0.05) to all p-values.

4. **3.4 Ablation Study**:
   - Validate attribution scores against baselines (random edge removal, feature permutation) to ensure motifs are not model artifacts (Addressing methodology-dfa0d9de).

### Phase 4: Reporting & Success Metrics (SC-002, SC-003)

**Goal**: Aggregate results and validate against success criteria.

1. **4.1 Success Metric Aggregation**:
   - **SC-002 Compliance**: Count distinct, statistically significant motifs (after FDR correction) and compare against the target "small set" or "all found".
   - **SC-003 Compliance**: Calculate the fraction of motifs overlapping with known pharmacophores (RMSD < 1.5 Å) with p < 0.05 significance.

2. **4.2 External Validation**:
   - Validate novel scaffolds against MM-GBSA on a strictly disjoint chemical space subset (BindingDB or held-out PDBbind) to avoid circularity.

3. **4.3 Final Report Generation**:
   - Generate `data/results/motifs.json` validated against `contracts/output_schema.schema.yaml`.

## Contracts & Validation

- **`contracts/dataset_schema.schema.yaml`**: Validates the output of Phase 1 (US-1). Ensures `water_flag` and 3D coordinates are present.
- **`contracts/output_schema.schema.yaml`**: Validates the output of Phase 3/4 (US-3). Ensures statistical metrics (p-value, is_significant) are present.

## Feasibility & Risk Mitigation

- **CPU Constraint**: Addressed by sampling N=1,000 complexes (Phase 1.1) based on power analysis.
- **Data Fidelity**: Addressed by using official PDBbind v2020 source with checksums.
- **Statistical Validity**: Addressed by strict adherence to Constitution Principle VII (t-tests) and scaffold-aware permutation.
- **Circularity**: Addressed by using external/disjoint scaffolds for MM-GBSA validation.