# Research: Predicting Molecular Ionization Energies with Graph Neural Networks

## Problem Statement
Can a 2D Graph Neural Network (GNN), trained exclusively on atom/bond connectivity derived from SMILES, predict molecular ionization energies with accuracy comparable to semi-empirical quantum methods (DFTB) while operating on constrained CPU resources? The study uses `-HOMO` (negative HOMO energy) as a proxy for Ionization Energy, acknowledging the approximation error of Koopmans' theorem.

## Dataset Strategy

| Dataset | Source URL | Variables Available | Fit for Purpose | Action |
| :--- | :--- | :--- | :--- | :--- |
| **QM9 (Parquet)** | `https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet` | SMILES, `HOMO`, `LUMO`, molecular properties | **High**. Contains `HOMO` which is used as a proxy for Ionization Energy via Koopmans' theorem (IE ≈ -HOMO). | Primary dataset. Target variable is `-HOMO`. |
| **QM9 (Enthalpy)** | `https://huggingface.co/datasets/hadoan/enthalpy-QM9-1k/resolve/main/data/train-00000-of-00001-ffd5f7908688c934.parquet` | SMILES, Enthalpy | **Low**. Target is enthalpy, not ionization energy. | Use only for validation of preprocessing logic if primary fails. |
| **QM9 (Gaps)** | `https://huggingface.co/datasets/Hassanharb/gaps-qm9-1k/resolve/main/data/train-00000-of-00001-3e8a1863fa44a20f.parquet` | SMILES, HOMO-LUMO gap | **Medium**. Gap is related but not identical to ionization energy. | Fallback if `HOMO` column is missing in primary. |
| **SMILES (Druglike)** | `https://huggingface.co/datasets/MKEChem/mke-novel-druglike-smiles/resolve/main/preview_100_molecules.csv` | SMILES | **None**. No energy labels. | Not used for training. |
| **RDKit (ChEMBL)** | `https://huggingface.co/datasets/fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors/resolve/main/data/test-00000-of-00001.parquet` | SMILES, Descriptors | **None**. No energy labels. | Not used for training. |
| **NIST Webbook** | `https://webbook.nist.gov/chemistry/` | Experimental Ionization Energies | **High**. Used for construct validity check of -HOMO proxy. | Phase 0 validation of target variable. |

**Dataset Fit Verification**:
- The primary hypothesis relies on the QM9 dataset containing `HOMO`.
- **Risk**: If the verified URL only contains `HOMO` (not `ionization_energy`), the study uses `-HOMO` as a proxy for Ionization Energy, citing Koopmans' theorem. This introduces a systematic error margin (often > 1 eV) which will be documented.
- **Decision**: The plan explicitly uses `-HOMO` as the target variable. The research question is reframed as "Can a 2D GNN predict `-HOMO` (proxy for IE) with accuracy comparable to semi-empirical methods?"

## Model Architecture & Rationale

### Message-Passing Neural Network (MPNN)
- **Type**: Graph Convolutional Network (GCN).
- **Input**: 2D Graph (Nodes: Atom type, Formal Charge; Edges: Bond type, Conjugation, Stereo).
- **Layers**: 3 layers (to capture local functional groups without excessive depth).
- **Embedding**: Atom features embedded to 64-dim; Bond features to 32-dim.
- **Readout**: Global average pooling + MLP head.
- **Rationale**: MPNNs are standard for molecular property prediction. 2D graphs are sufficient for small, rigid molecules (Constitution Principle VI).
- **CPU Feasibility**: Small hidden dimensions (64) and limited layers ensure training fits within 6h on 2 CPU cores.

### Baselines
1.  **DFTB (Density Functional Tight Binding)**:
    -   **Method**: Generate 3D conformers (RDKit ETKDG), compute energy via semi-empirical DFTB.
    -   **Constraint**: 3D generation + DFTB is computationally expensive.
    -   **Fallback**: If DFTB exceeds time limits, use **AM1** (if available in RDKit) or a **Linear Regression** model on RDKit molecular descriptors (Morgan fingerprints, MW, LogP) as the primary physics-based proxy.
2.  **Linear Regression (Fingerprint)**:
    -   **Method**: Morgan Fingerprints (radius 2) + Linear Regression.
    -   **Rationale**: Simple, fast, establishes a lower bound for "learnable" signal.

## Ablation Strategy
- **Target**: Bond features.
- **Method**: **Retrain** the model with bond features **zeroed out** during training (not just noise injection). Perform **5 independent stochastic runs** (seeds) for both the baseline and perturbed models to generate 5 paired error vectors.
- **Metric**: Compare the mean of the per-molecule error differences (Baseline Error - Perturbed Error) across the 5 pairs using a **paired t-test** (p < 0.05, Bonferroni corrected).
- **Hypothesis**: Retraining without bond features will increase MAE significantly (p < 0.05), confirming bond types are critical predictors.

## Statistical Rigor
- **Multiple Comparisons**: Bonferroni correction applied when comparing >2 baselines or ablation conditions.
- **Power**: Minimum N=20,000 molecules is fixed to ensure power > 0.8 for effect sizes > 0.05 eV. If this N is computationally infeasible, the study is declared underpowered.
- **Causal Inference**: None. Claims are strictly associational (predictive).
- **Collinearity**: Atom and bond features are correlated. The model learns joint representations; independent effect claims are avoided.
- **Statistical Test for Ablation**: The ablation study uses **5 paired runs** (baseline and perturbed) to generate 5 per-molecule error difference vectors. A **paired t-test** is performed on these vectors to determine if the perturbed model's errors are significantly higher.

## Compute Feasibility Decision
- **Batch Size**: Dynamically tuned. Start at a high batch size. If OOM, reduce to a lower batch size, then a further reduced batch size.
- **Data Subset**: Minimum N=20,000 molecules (fixed for power). If 20k exceeds 6h:
  1.  Reduce model complexity (hidden dims from 64 to 32, layers from 3 to 2).
  2.  Reduce epochs (if early stopping allows).
  3.  If still infeasible, declare study "underpowered" and document the trade-off. N is maintained at a sufficiently large scale to ensure statistical robustness.
- **Precision**: Float32 (default). No 16-bit mixed precision (CPU overhead often negates benefit).

## Edge Cases & Handling
- **Missing Ionization Energy**: Exclude molecule, log count, re-normalize dataset.
- **Invalid SMILES**: Exclude, log error (RDKit `SanitizeMol` failure).
- **Timeout**: Save best checkpoint, log "TIMEOUT" status, report partial results.
- **Out-of-Distribution (Scaffold)**: Evaluate normally, but flag in report if error > 2x mean.
- **Target Validity**: Document the systematic error margin of the `-HOMO` proxy for Ionization Energy.

## Chemical Validation Plan
- **Attribution Analysis**: Compare gradient-based attribution scores (Integrated Gradients) against **Hammett constants** for functional groups to quantify the correlation between model attribution and known chemical trends. This distinguishes between model reliance and chemical reality.
- **Error Correlation**: Analyze if GNN errors are uncorrelated with DFTB residuals (where 3D effects dominate) to validate the independence of the 2D signal.