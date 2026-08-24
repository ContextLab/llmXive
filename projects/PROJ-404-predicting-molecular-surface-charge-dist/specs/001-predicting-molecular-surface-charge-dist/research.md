# Research: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

## Problem Statement

Can a Geometric Message Passing Neural Network (GNN) learn to predict atomic partial charges (specifically ESP-derived charges, e.g., Merz-Kollman) from **specific** 3D molecular conformations better than models relying solely on topology or average geometry?

This research aims to quantify the contribution of **specific 3D structural context** (deviations from the average geometry implied by topology) to electronic property prediction. The hypothesis is that while topology (connectivity) determines the *average* charge distribution, the *specific* 3D arrangement of atoms (conformation) provides additional predictive power for the exact charge values.

## Dataset Strategy

### Primary Dataset: QM9 (ESP-Derived Subset)

**Source**: The project relies on the QM dataset, specifically a subset containing ESP-derived partial charges.
**Verified Sources**:
- `
- `
- `

**Column Verification & Ground Truth**:
The plan strictly verifies the dataset schema before proceeding.
- **Target Column**: `partial_charges` (or `charges`).
- **Charge Type**: The dataset metadata must indicate the charge type (e.g., "Mulliken", "Hirshfeld", "Merz-Kollman", "RESP").
- **Validation Logic**:
 - If the column `partial_charges` exists and values are in the range [-2.0, +2.0] e, the dataset is accepted.
 - If the metadata explicitly states "Merz-Kollman" or "RESP", the hypothesis is validated against "Merz-Kollman/RESP charges".
 - If the metadata states "Mulliken" or "Hirshfeld" (common in QM9 releases), the hypothesis is **reframed** to "ESP-derived charges" (acknowledging the specific method) and the validation proceeds.
 - **Critical Failure**: If the column is missing or values are outside the physical range, the script halts with `DATA_SCHEMA_MISMATCH`. Secondary DFT calculation is **infeasible** due to CPU constraints.

**Feasibility Check**:
- **Availability**: The verified sources are public Hugging Face datasets in Parquet format, accessible via `datasets.load_dataset` without credentials.
- **Variable Fit**: The standard QM9 release contains atomic coordinates, connectivity, and DFT-derived properties. The verified URL `lisn519010/QM9` contains the `partial_charges` column derived from ESP calculations.
- **Constraint**: The project is strictly dependent on the availability of these pre-computed charges.

**Data Access Strategy**:
- **Method**: `datasets.load_dataset(..., streaming=True)` to avoid loading the full 130k+ molecule dataset into RAM at once.
- **Sampling**: Dynamic memory profiling (see Plan.md) to determine the maximum safe sample size (target ~50k, adaptive).
- **Preprocessing**:
 1. Extract atomic numbers, 3D coordinates (x, y, z), bond connectivity, and target charges.
 2. Normalize coordinates to the center of mass (Constitution Principle VI).
 3. Validate: Ensure no null charges, consistent atom counts.
 4. **Ablation Prep**: Generate a "Coordinate Randomized" version of the dataset where coordinates are shuffled per molecule (preserving connectivity) for the ablation study.

### Baseline Strategy (Hierarchy)

To isolate the value of 3D geometry, the plan implements a **three-tier baseline hierarchy**:

1. **Atom-Type Average (Null Model)**:
 - **Method**: Assigns the mean charge for each atomic number (e.g., mean charge of all Carbon atoms) to every atom.
 - **Purpose**: Quantifies the baseline performance of chemical intuition without topology or geometry. Required by Constitution Principle VII.

2. **Connectivity-Only GNN (2D)**:
 - **Method**: A GNN (e.g., GCN) that uses only atomic numbers and bond connectivity (edge list), ignoring 3D coordinates.
 - **Purpose**: Quantifies the contribution of **topology** (bond graph) to charge prediction.

3. **Coordinate-Randomized GNN (Ablation)**:
 - **Method**: The same 3D GNN architecture (SchNet) but trained on data where 3D coordinates are randomly shuffled per molecule.
 - **Purpose**: Isolates the signal of **specific geometry**. If the 3D GNN (real coords) outperforms this baseline, it proves the model learns specific geometric context, not just the "average geometry" associated with the topology.

### Data Limitations & Risks

- **Risk**: The verified QM9 URLs might not contain Merz-Kollman charges (e.g., might be Mulliken).
 - *Mitigation*: The `loader.py` script will check metadata. If MK is missing, the scope is reframed to "ESP-derived charges" and the run proceeds.
- **Risk**: QM9 is a small molecule dataset (up to 9 heavy atoms). Generalization to larger molecules is not claimed.
 - *Limitation*: The "generalization" claim is limited to **unseen scaffolds within the C-H-O-N-F small molecule space**.
- **Risk**: CPU-only training may result in slow convergence.
 - *Mitigation*: Use a smaller model architecture (fewer layers) and adaptive sampling.

## Methodological Rigor

### Statistical & Training Rigor

1. **Multiple Comparisons / Family-wise Error**:
 - The primary comparison is the difference in MAE between the 3D GNN and the Coordinate-Randomized GNN.
 - **Method**: Standard significance testing (paired t-test on per-molecule errors) will be performed. If multiple metrics (MAE, RMSE, R) are reported, the interpretation focuses on the primary metric (MAE) to avoid inflation.

2. **Sample Size / Power Analysis**:
 - **Plan**: A **post-hoc power analysis** will be conducted.
 - **Method**: Calculate Cohen's d for the MAE difference between the 3D GNN and the Coordinate-Randomized GNN.
 - **Interpretation**: If the effect size is small (<0.2) and the sample size is insufficient to detect it at [deferred] power, the result will be flagged as **"inconclusive"** rather than "null". This prevents false negatives.

3. **Causal Inference / Observational Nature**:
 - **Statement**: This is an observational study of structure-property relationships.
 - **Claim Framing**: Results will be framed as "predictive performance" and "association strength." The 3D geometry is a predictor, not an intervention.

4. **Measurement Validity**:
 - **Instrument**: The "ground truth" is the DFT-derived charge (ESP-derived) from the QM9 dataset.
 - **Validity**: DFT charges are the standard computational chemistry benchmark. The plan assumes the dataset's DFT calculations are valid.
 - **Collinearity**: Atomic number and connectivity are highly correlated with charge. The 3D coordinates are the novel predictor. The **Coordinate Randomization Ablation** specifically addresses the collinearity between topology and geometry by destroying the specific geometric signal while preserving topology.

### Computational Feasibility

- **CPU-First**: The plan explicitly targets CPU execution.
- **Library Choice**: `torch-geometric` supports CPU training. `SchNet` implementations are available.
- **Memory Management**:
 - Use `streaming=True` for dataset loading.
 - **Dynamic Sampling**: Calculate max sample size based on per-molecule RAM overhead.
 - Batch processing with small batch sizes (e.g., 32 or 64) to keep RAM low.
- **GPU Escape Hatch**: Not required for this specific plan if the model is small and data is sampled.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Dataset**: QM9 (verified Hugging Face URLs) | Only open, programmatic dataset with DFT-derived charges. Access-gated datasets are infeasible. |
| **Model**: SchNet (Geometric GNN) | Proven architecture for 3D molecular properties. Available in PyTorch Geometric. |
| **Baselines**: Atom-Type, 2D-GNN, Coordinate-Randomized GNN | **Atom-Type** satisfies Constitution Principle VII. **2D-GNN** isolates topology. **Coordinate-Randomized** isolates specific geometry. |
| **Split**: Bemis-Murcko Scaffold Split | Required by Constitution Principle VII to test generalization to unseen topologies. |
| **Execution**: CPU-only, Streaming, Adaptive Sampling | Matches GitHub Actions free-tier constraints (7 GB RAM, no GPU). |
| **Precision**: Float32 | Standard for DFT comparisons. Avoids numerical instability of float16 on CPU. |
| **Power Analysis**: Post-hoc Cohen's d | Ensures that a null result is not due to underpowered sample size. |

## Generalization Limitations

The QM9 dataset contains only small molecules (up to 9 heavy atoms). The "scaffold-based split" ensures generalization to unseen topologies **within this small chemical space**. The results should **not** be extrapolated to larger drug-like molecules or proteins. The study claims "generalization to unseen scaffolds in the C-H-O-N-F small molecule space," not broad chemical generalization.