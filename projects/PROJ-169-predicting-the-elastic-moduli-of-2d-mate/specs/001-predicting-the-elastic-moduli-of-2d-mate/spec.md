# Project Specification: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview

This project implements a **Structure-Only Surrogate Model** to predict the elastic moduli (Young's, Shear, and Poisson's ratio) of 2D materials. The model acts as a fast interpolator of pre-computed Density Functional Theory (DFT) data, avoiding the computational cost of solving the Schrödinger equation for new candidates while maintaining high accuracy within the training distribution.

**Critical Distinction**: This is **NOT** a first-principles calculation. It does not solve the Hamiltonian. It is a machine learning model trained on existing DFT results to approximate the mapping from crystal structure to elastic properties.

## 2. Problem Statement

Predicting the elastic moduli of 2D materials is essential for designing flexible electronics, sensors, and composites. Traditional DFT methods are accurate but computationally expensive (hours to days per material). This project aims to reduce inference time to milliseconds while maintaining a Mean Absolute Percentage Error (MAPE) within an acceptable range on held-out chemical families.

## 3. User Stories

### US1: Data Ingestion and Graph Construction
As a researcher, I want to ingest CIF files and elastic tensors from a single canonical public source (e.g., Materials Project) and convert them into graph representations, so that I can train a model on high-quality, consistent data.

### US2: Lightweight GNN Training and Evaluation
As a researcher, I want to train a lightweight Graph Neural Network (GNN) on the constructed dataset and evaluate its performance against held-out DFT values, so that I can verify the model's ability to generalize to unseen chemical families.

### US3: Feature Importance and Ablation Analysis
As a researcher, I want to identify which structural descriptors most strongly influence predicted elastic moduli, so that I can understand the physical correlations learned by the surrogate model.

## 4. Technical Constraints

- **Memory Limit**: The entire pipeline must run within 7GB of RAM.
- **Compute Environment**: Must run on CPU-only hardware.
- **Data Source**: Must use a single, verified public repository per run (no mixing sources).
- **Terminology**: The terms "First-Principles" and "Schrödinger Equation" are strictly forbidden when describing the ML model. The model is a "Surrogate" or "Interpolator".

## 5. Limitations

**Extrapolation Failure**: The model is a **surrogate interpolator** trained on a specific chemical space defined by the training DFT data. It **cannot** reliably predict properties for:
- Materials with chemical compositions or structural motifs entirely absent from the training set.
- Extreme conditions (e.g., high pressure, temperature) not represented in the source DFT data.
- Novel physics outside the scope of the training data's DFT approximations (e.g., strong correlation effects if the training DFT used standard functionals).

**No New Physics Discovery**: The model does not discover new physical laws or solve the underlying quantum mechanical equations. It identifies statistical correlations between structural descriptors (node/edge features) and target elastic moduli. Any "insights" derived from feature importance are correlations, not causal quantum mechanical derivations.

**Data Dependency**: The accuracy of the surrogate is entirely dependent on the quality and coverage of the source DFT data. Errors or biases in the source data will be propagated and potentially amplified by the model.

## 6. Success Criteria

- **SC-001**: Pipeline successfully ingests and processes >1,000 2D material entries from a single canonical source.
- **SC-002**: The model achieves a MAPE < 15% on a test set consisting of entirely unseen chemical families (inter-family generalization).
- **SC-003**: The model inference time is < 100ms per material on CPU.
- **SC-004**: Peak memory usage during training remains within acceptable system limits.
- **SC-005**: Feature importance analysis identifies at least 3 structural descriptors with p < 0.05 correlation to elastic moduli.

## 7. Deliverables

1. `data/processed/graphs_v1.parquet`: Processed graph dataset.
2. `data/results/training_logs.json`: Training metrics and surrogate model disclaimers.
3. `data/results/generalization_metrics.json`: Intra/inter-family performance comparison.
4. `data/results/feature_importance_report.md`: Unified ranked list of descriptors with ablation deltas.
5. `docs/methodology.md`: Detailed distinction between DFT and Surrogate methods.