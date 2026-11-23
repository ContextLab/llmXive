# Specification: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

## Overview

This project aims to develop a Graph Neural Network (GNN) model to predict interfacial adhesion energy in polymer composites based on the topological structure of the molecular interfaces. The hypothesis is that specific topological features (e.g., node degree, edge connectivity, graph density) significantly influence adhesion strength.

## User Stories

### US1: Data Pipeline Construction
Download and validate molecular data, construct a dataset of polymer-filler interface pairs with adhesion energy measurements.

### US2: Model Training Execution
Train a Graph Attention Network (GAT) on the curated data, ensuring convergence within 6 hours and ≤6GB RAM.

### US3: Statistical Validation & Attribution
Validate model significance via permutation tests, perform gradient-based attribution, and report Variance Inflation Factor (VIF) for collinearity.

## Functional Requirements

### FR-001: Data Acquisition
The system must download molecular data from a public, programmatic source (e.g., MolNet via Hugging Face). The dataset must contain polymer-filler interface pairs with measured adhesion energy.

### FR-002: Feature Extraction
The system must extract topological features from molecular graphs:
- Node degree
- Edge connectivity
- Graph density
- Clustering coefficient

### FR-003: Model Architecture
The system must implement a **3-layer Graph Attention Network (GAT)** using `torch_geometric.nn.GATConv`.
*Note: This requirement supersedes the initial proposal for a Graph Convolutional Network (GCN) to better capture feature weighting via attention mechanisms.*

### FR-004: Training Constraints
- CPU-only execution
- Maximum runtime: 6 hours
- Maximum memory: 6GB
- Convergence: MSE reduction ≥50%

### FR-005: Statistical Validation
The system must perform a permutation test with exactly 100 iterations (10 epochs each) to calculate a p-value < 0.05.

### FR-006: Attribution Analysis
The system must identify topological features with standard deviation > 0.1 using Integrated Gradients.

### FR-007: Collinearity Handling
The system must report Variance Inflation Factor (VIF) scores for hand-crafted descriptors separately from the attention mechanism weights.
*Clarification: Attention mechanisms within the GAT handle feature weighting during model training. Collinearity among input descriptors is assessed independently via VIF to ensure statistical validity of the reported feature importance.*

### FR-008: Reproducibility
All scripts must fix random seeds for reproducibility.

### FR-009: Error Handling
The data pipeline must abort with exit code `E-DATA-001` if adhesion energy is missing or if the dataset contains fewer than 100 rows.

### FR-010: Artifact Hashing
All generated artifacts must be hashed and recorded in the state file.

## Data Model

### Entities
- **MolecularGraph**: Represents a single molecule or interface.
 - `smiles`: str
 - `nodes`: List[Dict]
 - `edges`: List[Dict]
 - `features`: Dict[str, Any]

- **InterfacePair**: Represents a polymer-filler interaction.
 - `polymer_smiles`: str
 - `filler_smiles`: str
 - `adhesion_energy`: float
 - `graph_data`: PyG Data object

## Constraints

- **Scope**: Only topological features are included. Physical parameterization (e.g., explicit atomic coordinates from MD simulations) is excluded.
- **Hardware**: CPU-only execution.
- **Data**: Real data only. No synthetic fallbacks.
- **Time**: Permutation test limited to 5h estimated runtime.

## Version History
- v1.0: Initial draft (GCN proposed).
- v1.1: Updated to GAT (FR-003) per Plan "Critical Note on Spec Alignment". Clarified FR-007 to separate attention weights from VIF collinearity checks.