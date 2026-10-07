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
As a researcher, I want to identify which structural descriptors most strongly influence predicted elastic moduli, so that I can understand the statistical determinants learned by the surrogate model.

## 4. Technical Constraints

- **Memory Limit**: The entire pipeline must run within 7GB of RAM.
- **Compute Environment**: Must run on CPU-only hardware.
- **Data Source**: Must use a single, verified public repository per run (no mixing sources).
- **Terminology**: The terms "First-Principles" and "Schrödinger Equation" are strictly forbidden when describing the ML model. The model is a "Surrogate" or "Interpolation".

## 5. Limitations

**Extrapolation Failure**: The model is a **surrogate interpolator** trained on a specific chemical space defined by the training DFT data. It **cannot** reliably predict properties for:
- Materials with chemical compositions or structural motifs entirely absent from the training set.
- Extreme conditions (e.g., high pressure, temperature) not represented in the source DFT data.
- Novel physics outside the scope of the training data's DFT approximations (e.g., strong correlation effects if the training DFT used standard functionals).

**No New Physics Discovery**: The model does not discover new physical laws or solve the underlying quantum mechanical equations. It identifies statistical correlations between structural descriptors (node/edge features) and target elastic moduli. Any "insights" derived from feature importance are correlations, not causal quantum mechanical derivations.

**Data Dependency**: The accuracy of the surrogate is entirely dependent on the quality and coverage of the source DFT data. Errors or biases in the source data will be propagated and potentially amplified by the model.

## 6. Success Criteria

- **SC-001**: Pipeline successfully ingests and processes >1,000 2D material entries (or all available valid entries if <1,000) from a single canonical source (See US1).
- **SC-002**: The model outperforms a composition-only baseline (e.g., linear regression on Magpie features) by ≥ 10% relative MAPE reduction on a test set consisting of unseen chemical families within the source distribution (See US2). A chemical family is defined as a distinct space group combined with a cation-anion stoichiometry class.
- **SC-003**: The model inference time is < 100ms per material on CPU.
- **SC-004**: Peak memory usage during training remains ≤ 7GB (See US2).
- **SC-005**: Feature importance analysis identifies at least 3 structural descriptors with significant contribution to prediction accuracy via permutation importance and SHAP magnitude (See US3).

## 7. Deliverables

1. `data/processed/graphs_v1.parquet`: Processed graph dataset.
2. `data/results/training_logs.json`: Training metrics and surrogate model disclaimers.
3. `data/results/generalization_metrics.json`: Intra/inter-family performance comparison.
4. `data/results/feature_importance_report.md`: Unified ranked list of descriptors with ablation deltas.
5. `docs/methodology.md`: Detailed distinction between DFT and Surrogate methods.
6. `data/results/constitution_title_audit.json`: Audit result confirming the project title does not contain forbidden "First-Principles" terminology.
7. `data/processed/split_indices.json`: Train/validation/test split indices generated by clustering.
8. `data/results/split_validation.json`: Validation metrics for the generated split.
9. `data/processed/model_v1.pt`: Saved model weights.
10. `data/results/predictions.json`: Model predictions on the test set.
11. `code/utils/disclaimer_template.py`: Source file containing the scientific integrity statement and Feynman quote.

### Functional Requirements

- **FR-001**: System MUST ingest CIF files and elastic tensors from a single canonical public source, parse them using CifParser, and convert them into graph representations (nodes, edges, features) for training (See US1).
- **FR-002**: System MUST implement a split generator that clusters structures by chemical family and generates train/validation/test splits, ensuring no data leakage between families (See US2).
- **FR-003**: System MUST train a lightweight GNN on CPU-only hardware, enforcing a hard memory limit of 7GB via `tracemalloc` (See US2).
- **FR-004**: System MUST evaluate model performance against a composition-only baseline (e.g., linear regression on Magpie features) and report relative MAPE reduction (See US2).
- **FR-005**: System MUST compute feature importance using permutation importance and SHAP values, not marginal correlation p-values (See US3).
- **FR-006**: System MUST generate an audit report (`constitution_title_audit.json`) verifying the project title does not contain forbidden "First-Principles" terminology (See Constitution).
- **FR-007**: System MUST save model weights, split indices, and validation metrics to the specified output paths (See US2).

### Key Entities

- **Structure**: Represents a 2D material crystal structure with lattice parameters, atomic positions, and species.
- **Graph**: A node-edge representation of the Structure, where nodes are atoms and edges represent bonds or proximity.
- **ElasticTensor**: The target property vector (C11, C12, C13, C33, C44, C66) derived from DFT.
- **FeatureDescriptor**: A structural attribute (e.g., coordination number, electronegativity difference) used as a node/edge feature.

## Assumptions

- Users have stable internet connectivity to download data from the canonical source.
- The public source (e.g., Materials Project) provides at least 1,000 valid 2D material entries with elastic tensors.
- Existing authentication system (if any) will be reused; no new auth system is built.
- The "unseen chemical families" test set is generated by splitting the source data by chemical family, not random sampling.