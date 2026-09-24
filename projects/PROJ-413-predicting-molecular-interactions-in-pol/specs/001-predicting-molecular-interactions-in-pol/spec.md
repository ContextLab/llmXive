# Specification: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

## 1. Introduction

This document defines the requirements for a machine learning pipeline to predict
interfacial adhesion energy in polymer composite materials. The system utilizes
Graph Neural Networks (GNNs) to model molecular structures and their interactions
at the polymer-filler interface.

## 2. Motivation

Polymer composites are critical in modern engineering, yet the microscopic
mechanisms governing adhesion at the interface between the polymer matrix and
the filler are poorly understood. Current empirical methods are slow and costly.
A data-driven approach using GNNs can accelerate the discovery of high-performance
composite formulations.

## 3. Scope

This project focuses on:
- Constructing a dataset of polymer-filler interface pairs from public chemical
 databases (MolNet).
- Training a Graph Attention Network (GAT) to predict adhesion energy.
- Validating the model via permutation tests and gradient-based attribution.
- Reporting statistical significance and feature importance.

**Out of Scope**:
- Physical parameterization of non-topological features (e.,g., explicit van der Waals
 forces) is excluded; the model relies strictly on topological graph features.
- Deployment to a production web service.

## 4. User Stories

### US1: Data Pipeline Construction
As a researcher, I want to download raw molecular data, validate it for adhesion
energy measurements, and produce a curated dataset of interface pairs.

### US2: Model Training Execution
As a data scientist, I want to train a 3-layer Graph Attention Network (GAT) on
the curated data using CPU resources, ensuring convergence within 6 hours and
memory usage under 6GB.

### US3: Statistical Validation & Attribution
As a reviewer, I want to see a permutation test confirming model significance (p < 0.05),
gradient-based attribution identifying topological features, and a Variance Inflation
Factor (VIF) report to rule out collinearity.

## 5. Functional Requirements

### FR-001: Data Acquisition
The system must download the MolNet dataset from Hugging Face. If the dataset
does not contain 'adhesion_energy' or has fewer than 100 rows, the system MUST
abort with error code E-DATA-001. No proxy metrics or synthetic fallbacks are allowed.

### FR-002: Graph Construction
The system must convert SMILES strings into heterogeneous graphs where:
- Nodes represent atoms (features: atomic number, degree).
- Edges represent bonds (features: bond order, connectivity).
- Only topological features are used.

### FR-003: Model Architecture
The system must implement a **3-layer Graph Attention Network (GAT)** using
`torch_geometric.nn.GATConv`.
- Hidden dimension: 64.
- Dropout: 0.5.
- Attention heads: 4 (default).
- Output: Single scalar (adhesion energy).

*Note: This requirement supersedes any previous mention of Graph Convolutional Networks (GCN).*

### FR-004: Training Constraints
- Hardware: CPU-only execution.
- Time limit: 6 hours (hard fail), 4.5 hours (checkpoint soft fail).
- Memory limit: 6 GB peak.
- Hyperparameters: Learning rate 0.001, Batch size ≤ 32, Epochs = 50.

### FR-005: Permutation Test
The system must run exactly 100 permutations with 10 epochs each to estimate
the null distribution of MSE. The p-value must be calculated and reported.

### FR-006: Feature Attribution
The system must use Integrated Gradients to attribute importance to input
features (topological descriptors). At least 3 features with standard deviation
> 0.1 must be identified.

### FR-007: Collinearity Handling
The system must calculate the Variance Inflation Factor (VIF) for all hand-crafted
descriptors.
- **Clarification**: The GAT attention mechanism handles feature weighting internally.
 VIF is reported separately to ensure the input descriptors themselves are not
 collinear. A VIF > 5 indicates potential collinearity and must be flagged in the report.

## 6. Data Model

### 6.1. Raw Data
Source: Hugging Face `molnet` dataset.
Format: CSV or Parquet.
Required Columns: `polymer_smiles`, `filler_smiles`, `adhesion_energy`.

### 6.2. Curated Dataset
Path: `data/curated/curated_dataset.csv`
Schema:
- `polymer_smiles` (str): SMILES string of the polymer.
- `filler_smiles` (str): SMILES string of the filler.
- `adhesion_energy` (float): Target variable.

### 6.3. Processed Graphs
Path: `data/processed/graphs.pt`
Format: PyTorch Geometric `Data` object list.
Attributes:
- `x`: Node features (14 dimensions: 10 atom + 4 bond).
- `edge_index`: Graph connectivity.
- `edge_attr`: Edge features.

## 7. Non-Functional Requirements

- **Reproducibility**: All random seeds must be fixed (default 42).
- **Auditability**: All artifacts must be hashed and logged in `state/projects/...yaml`.
- **Performance**: Must run within 6 hours on a standard CPU runner.

## 8. Deliverables

1. `data/curated/curated_dataset.csv`: Validated dataset.
2. `data/processed/graphs.pt`: Processed graph objects.
3. `results/model.pt`: Trained GAT model weights.
4. `results/stats.csv`: Statistical validation results (p-values, VIF).
5. `results/attribution.json`: Feature importance scores.
6. `analysis/topology_audit.md`: Graph construction statistics.
7. `analysis/power_analysis.md`: Power analysis assumptions.

## 9. Appendix: Error Codes

- `E-DATA-001`: Data missing or insufficient (adhesion_energy missing or < 100 rows).
- `E-TRAIN-001`: Training timeout exceeded (6h).
- `E-TRAIN-002`: Memory limit exceeded (6GB).