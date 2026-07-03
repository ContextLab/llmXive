# Feature Specification: Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

**Feature Branch**: `001-topology-thermal-conductivity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

As a materials scientist, I want to ingest pre-equilibrated amorphous silicon configurations and automatically construct atomic graphs (nodes=atoms, edges=bonds < 3.0 Å) so that I can establish the structural baseline required for topological analysis.

**Why this priority**: Without accurate graph construction from the raw MD snapshots, no subsequent topological metrics or GNN training can occur. This is the foundational data pipeline.

**Independent Test**: Can be fully tested by running the ingestion script on a single sample file and verifying that the output graph contains the expected number of nodes and that edge counts match the bond distribution for the 3.0 Å cutoff, independent of any ML model.

**Acceptance Scenarios**:
1. **Given** a valid XYZ file of an amorphous silicon supercell (≥1000 atoms), **When** the graph construction module is executed with a 3.0 Å cutoff, **Then** the output is a graph object with exactly N nodes and a node-degree distribution consistent with amorphous silicon (peaking at the coordination number characteristic of the material, with tails for defects).
2. **Given** a corrupted or missing input file, **When** the ingestion module is executed, **Then** the system logs a specific error code and halts without generating partial graphs.

---

### User Story 2 - Topological Metric Extraction and Green-Kubo Baseline (Priority: P2)

As a researcher, I want to compute standard graph metrics (degree, clustering coefficient) and run an Equilibrium MD (Green-Kubo) simulation using the Stillinger-Weber potential to generate ground-truth thermal conductivity values so that I can correlate structure with transport properties.

**Why this priority**: This provides the "labels" (thermal conductivity) and the "features" (topology) needed to train the model. It validates the data pipeline before adding the complexity of GNNs. Using Green-Kubo on ≥1000 atoms ensures the result is a bulk property, avoiding finite-size effects.

**Independent Test**: Can be tested by processing a single sample, extracting metrics, running the Green-Kubo simulation, and verifying that the computed thermal conductivity falls within the known literature range for amorphous silicon, independent of the GNN.

**Acceptance Scenarios**:
1. **Given** a constructed atomic graph, **When** the metric extractor runs, **Then** it outputs a feature vector containing node degree, local clustering coefficient, and shortest-path statistics for every atom.
2. **Given** the atomic configuration, **When** the Green-Kubo simulation runs on 2 CPU cores, **Then**:
   a. The simulation completes within 12 hours.
   b. The standard error of the thermal conductivity estimate is < 10% of the mean, confirming the simulation converged.

---

### User Story 3 - GNN Training and Topology-Conductivity Correlation (Priority: P3)

As a data scientist, I want to train a 2-layer GNN on the extracted graphs to predict local heat flux, extract per-sample feature importance (e.g., SHAP values), and perform a Pearson correlation analysis between these importance scores and global thermal conductivity so that I can quantify the specific influence of network topology.

**Why this priority**: This is the core research novelty (using GNNs to find motifs) but relies on the success of US-1 and US-2. It answers the primary research question by linking local topological drivers to global transport.

**Independent Test**: Can be tested by training the GNN on a subset of samples, evaluating the correlation coefficient (r) between per-sample feature importance and global conductivity, and verifying the model outperforms a random baseline, provided N ≥ 10.

**Acceptance Scenarios**:
1. **Given** a dataset of N ≥ 10 independent samples with computed graphs and conductivity labels, **When** the 2-layer GNN is trained on 2 CPU cores, **Then**:
   a. The model converges within 60 epochs (defined as loss change < 1e-4 for 5 consecutive epochs).
   b. The model achieves a validation loss lower than a linear regression baseline.
2. **Given** the trained GNN and N ≥ 10 samples, **When** per-sample feature importance is extracted and correlated with global thermal conductivity, **Then** the system outputs a Pearson correlation coefficient (r), a p-value (p < 0.05 after Bonferroni correction), and a clear interpretation of the topological influence.

---

### Edge Cases

- **What happens when the Green-Kubo simulation fails to converge?** The system must detect non-convergence (e.g., relative change in heat current autocorrelation function > 1% over the final [deferred] of the trajectory) and flag the sample for exclusion, rather than crashing the entire pipeline.
- **How does the system handle samples with extreme topological defects?** If a sample has >15% of atoms with coordination numbers < 3 or > 6, the system must log a warning and optionally exclude the sample from the correlation analysis to prevent outlier skewing.
- **What happens if the dataset is too small for statistical power?** If the number of independent samples is < 10, the system must output a warning regarding statistical power limitations, defer the final correlation conclusion, and require additional data before proceeding.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest pre-equilibrated amorphous silicon configurations (e.g., XYZ format) and construct atomic graphs with a bond cutoff radius of exactly 3.0 Å (See US-1).
- **FR-002**: The system MUST compute local topological metrics (node degree, clustering coefficient, shortest-path distribution) for every atom in the graph (See US-2).
- **FR-003**: The system MUST execute Equilibrium Molecular Dynamics (Green-Kubo) simulations using the Stillinger-Weber potential on a 2-core CPU environment to generate ground-truth thermal conductivity values for supercells of ≥1000 atoms (See US-2).
- **FR-004**: The system MUST train a 2-layer Graph Neural Network (GNN) using PyTorch Geometric to predict local heat flux from the atomic graph features (See US-3).
- **FR-005**: The system MUST extract per-sample feature importance scores (e.g., via SHAP) from the trained GNN and perform a Pearson correlation analysis between these scores and the global thermal conductivity values across all valid samples (See US-3).
- **FR-006**: The system MUST implement a multiple-comparison correction (e.g., Bonferroni) when testing correlations across ≥3 distinct topological metrics to control the family-wise error rate and prevent false positives (See US-3).

### Key Entities

- **AtomicGraph**: A graph object where nodes represent silicon atoms and edges represent bonds within the 3.0 Å cutoff. Attributes include node coordinates and local topological metrics.
- **ThermalSample**: A dataset entry containing the AtomicGraph, the computed Green-Kubo thermal conductivity value, and the associated simulation metadata (temperature, simulation time).
- **GNNModel**: A lightweight 2-layer graph neural network model trained to map AtomicGraph features to local heat flux vectors.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The Pearson correlation coefficient (r) between per-sample topological feature importance and thermal conductivity is measured against a null hypothesis of r=0 to determine statistical significance (See US-3).
- **SC-002**: The GNN prediction accuracy (Mean Squared Error on local heat flux) is measured against a linear regression baseline to demonstrate the added value of non-linear topology modeling (See US-3).
- **SC-003**: The Green-Kubo simulation convergence is measured against a stability threshold (relative change in heat current autocorrelation function < 1% in the final [deferred] of the trajectory) to ensure data validity (See US-2).
- **SC-004**: The statistical power of the correlation analysis is measured against the number of independent samples (N) to ensure the study is not underpowered (See US-3).
- **SC-005**: The computational runtime of the full pipeline (graph construction + Green-Kubo + GNN training) is measured against the 12-hour CPU limit (2 cores) to ensure feasibility (See US-2, US-3).

## Assumptions

- The pre-equilibrated amorphous silicon configurations available from Zenodo or Materials Cloud contain sufficient structural variety (N ≥ 10 independent samples) to perform a statistically valid correlation analysis.
- The Stillinger-Weber potential is an adequate approximation for capturing the thermal conductivity trends in amorphous silicon for this study, as validated by prior literature.
- The GNN architecture is sufficiently expressive to capture the relevant topological motifs without requiring deeper networks that would exceed the 12-hour CPU time limit.
- A standard and robust cutoff radius for bond definition is employed for silicon systems, consistent with established practices [DOI/arXiv/author-year]., capturing the first coordination shell accurately.
- The GitHub Actions free-tier runner (2 CPU cores, ~16 GB RAM) is sufficient to handle the memory footprint of the Green-Kubo simulation and the GNN training on ≥1000-atom supercells without swapping.
- The dataset variables (atomic positions) are sufficient to derive all required topological predictors; no additional dynamic variables (e.g., time-resolved velocities) are needed for the *topological* correlation, though they are used for the Green-Kubo integral.