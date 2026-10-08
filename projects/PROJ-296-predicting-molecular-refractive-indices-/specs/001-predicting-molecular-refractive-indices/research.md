# Research: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations

## Problem Definition

Molecular refractive index (RI) is a critical physical property for drug discovery and material science, traditionally estimated via additive atomic contribution methods (e.g., Lorentz-Lorenz). While effective, these methods struggle with complex electronic effects like conjugation and steric hindrance. This project investigates whether a lightweight Message Passing Neural Network (MPNN) trained on graph-based molecular representations can outperform these baselines while providing interpretable insights into the structural drivers of RI, all within strict CPU-only constraints.

## Dataset Strategy

### Primary Dataset Selection

**Source**: `nglebm19/rdkit_chemical` (Hugging Face)  
**URL**: `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet`  
**Rationale**: This dataset is verified to contain SMILES strings and pre-computed RDKit descriptors, including molecular weight and potentially refractive index values or proxies. It is directly downloadable via `datasets.load_dataset`, fitting the "open, programmatic download" requirement.

**Verification of Variables**:
- **SMILES**: Present.
- **Refractive Index**: The dataset must be inspected for a column named `refractive_index` or `RI`. If the specific RI column is missing, the plan falls back to `chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` (URL: `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet`) which is known to include physical property descriptors.
- **Molecular Weight**: Calculated via RDKit if not present, used for filtering (MW < 500 Da).

*Note: If the primary dataset lacks explicit RI values, the project will utilize the `smiles-transformers` dataset (URL: `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet`) only if it contains the target property. If no verified source contains RI, the project will explicitly state "Dataset Mismatch" and halt, as per the "Dataset-variable fit" rule.*

### Data Preprocessing & Filtering

1. **Parsing**: Use RDKit to parse SMILES. Invalid strings logged to `failed_parsing.log` and excluded.
2. **Filtering**: Exclude molecules with MW > 500 Da to ensure memory compliance and focus on drug-like space.
3. **Normalization**:
   - If temperature data is available, normalize RI to 20°C using the Edlén equation or standard coefficient ($dn/dT \approx -0.0001 K^{-1}$).
   - If temperature is missing, flag samples for uncertainty estimation or exclusion if the deviation is likely > 5%.
4. **Feature Engineering**:
   - **Node Features**: Atomic number, degree, hybridization, formal charge, aromaticity.
   - **Edge Features**: Bond type (single, double, triple, aromatic), conjugation, stereochemistry.

### Data Splitting Strategy

**Method**: Scaffold Split (80/10/10).  
**Implementation**: Use `RDKit.Chem.Scaffolds.MurckoScaffold` to generate Murcko scaffolds. Molecules with identical scaffolds must remain in the same split.  
**Goal**: Ensure zero scaffold overlap between train, validation, and test sets to test generalization to novel chemical structures.

## Methodology

### 1. Baseline: Atomic Contribution Method

**Algorithm**: Additive Molar Refractivity (MR) calculation.
- $MR = \sum (a_i + b_i)$ where $a_i, b_i$ are atomic contributions for atom type $i$.
- Convert MR to RI using Lorentz-Lorenz equation: $RI = \sqrt{\frac{1 + 2(MR/V)}{1 - (MR/V)}}$, where $V$ is molar volume.
- **Rationale**: Serves as a non-learning, physics-based lower bound for comparison.

### 2. Model: Message Passing Neural Network (MPNN)

**Architecture**:
- **Layers**: 3 Message Passing layers.
- **Hidden Dimension**: 64.
- **Aggregation**: Sum or Mean aggregation of neighbor messages.
- **Readout**: Global average pooling followed by a 2-layer MLP.
- **Activation**: ReLU.
- **Constraint**: `device="cpu"`, `torch.no_grad()` where possible, batch size tuned for 7GB RAM (likely 32 or 64).

**Training**:
- **Loss**: Mean Squared Error (MSE).
- **Optimizer**: Adam ($lr=1e-3$).
- **Early Stopping**: Patience=10 epochs based on validation loss.
- **Regularization**: L2 weight decay ($1e-4$).

### 3. Interpretability: Integrated Gradients

**Method**: Apply Integrated Gradients (IG) to the trained MPNN.
- **Baseline**: Zero vector or average feature vector.
- **Steps**: 50 steps for integration.
- **Output**: Attribution scores for each node (atom) and edge (bond).
- **Validation**: Check if top-attributed features correspond to known chemical drivers (e.g., conjugated systems, halogens).

### 4. Evaluation Metrics

- **Primary**: Mean Absolute Error (MAE), Root Mean Square Error (RMSE).
- **Statistical Test**: Paired t-test comparing GNN errors vs. Baseline errors.
- **Stability**: Variance of MAE across 3 random seeds (Target: < 0.01).

## Statistical Rigor & Constraints

- **Multiple Comparisons**: Not applicable as only one primary comparison (GNN vs. Baseline) is performed per metric.
- **Power Analysis**: The dataset size is constrained by availability. We will report the effective sample size ($N$) and acknowledge power limitations if $N < 500$.
- **Causal Claims**: Claims are strictly associational. No causal inference is made about structural modifications; only predictive performance and feature attribution are reported.
- **Collinearity**: Atomic features (e.g., degree and hybridization) may be correlated. The model will report feature importance but will not claim "independent" causal effects for collinear predictors.

## Compute Feasibility

- **CPU-First**: All training and inference runs on CPU.
- **Memory Management**:
  - Dataset loaded in streaming mode (`streaming=True`) if size > 1GB.
  - Batch size adjusted dynamically if OOM occurs.
  - PyTorch Geometric used with `torch_sparse` for efficient CPU graph operations.
- **Time Limit**: Training loop designed for < 6 hours. If convergence is slow, early stopping and reduced epochs will be enforced.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset lacks RI values** | Fatal | Fallback to `chembl-2025` dataset; if both fail, report "Data Unavailable" and stop. |
| **OOM on 7GB RAM** | High | Use streaming, reduce batch size to 16, prune molecular graphs (remove H atoms if redundant). |
| **Model overfitting** | Medium | Early stopping, dropout (0.2), L2 regularization. |
| **Scaffold split fails** | Medium | If dataset is too small for 10/10/10 split, use 80/20 split and note limitation. |
