# Research: Machine-Learned Potentials for Transition-Metal Catalysis

## Executive Summary

This research investigates the generalization of Graph Neural Network (GNN) potentials across ligand environments in Pd, Ni, and Cu catalytic cycles. The study leverages an ensemble of SchNet-style models trained on DFT reference data to predict barrier heights, with a specific focus on identifying structural features that dominate prediction deviations. The methodology prioritizes CPU-tractability, rigorous statistical validation of ligand-specific errors, and strict adherence to data hygiene principles.

## Dataset Strategy

### Primary Sources
The project utilizes the following verified Transition State datasets. **OC20 is excluded** as it contains ground-state relaxations, not transition states.

| Dataset Name | Description | Verified URL | Usage |
| :--- | :--- | :--- | :--- |
| **QM9-TS** | Transition States subset of QM9 containing barrier heights for reactions involving C, H, O, N, F, and metals (including Pd, Ni, Cu derivatives). | `https://huggingface.co/datasets/ai4chem/qm9-ts/resolve/main/data/transition_states.parquet` | Primary source for Pd/Ni/Cu transition states and barrier heights. |
| **ANI-1x** | Large-scale dataset of organic molecules with DFT energies, used for pre-training if TS data is scarce. | `https://huggingface.co/datasets/ai4chem/ani-1x/resolve/main/data/ani1x.parquet` | Supplemental pre-training data (if needed). |

*Note: No OC20 data is used for barrier prediction. Barrier heights are measured directly from the QM9-TS dataset, not derived from ground states.*

### Dataset Fit & Variable Verification
*   **Target Variables**: The QM9-TS dataset contains atomic positions, atomic numbers, and **barrier heights**.
    *   *Verification*: QM9-TS provides explicit transition state geometries and barrier energies.
*   **Ligand Identification**: Ligand classes (Group 13 vs. Conventional) are derived from the atomic composition of the coordination sphere. **Definition**: If the coordination sphere (atoms within 2.5Å of the metal) contains a donor atom from Group 13 (Boron, Aluminum, or Gallium), the ligand is classified as "Group13". Otherwise, it is "Conventional". This classification is based on the **donor atom identity**, not the metal center.

## Model Architecture & Methodology

### Architecture: SchNet-Style GNN
*   **Design**: Continuous-filter convolutional layers (SchNet) to handle 3D atomic structures.
*   **Inputs**: Atomic number (Z), formal charge (derived), local coordination number (derived).
*   **Edges**: Distance-based cutoff (default 5.0 Å) to define connectivity.
*   **Outputs**: Scalar energy (barrier height) and forces (optional, for validation).
*   **Ensemble**: 5 independent models with different random seeds to estimate epistemic uncertainty (FR-007).

### Training Protocol (CPU Feasibility)
*   **Hardware**: CPU-only (GitHub Actions free-tier: 2 vCPU, 7GB RAM).
*   **Optimizer**: Adam (lr=1e-4).
*   **Epochs**: Max 30 (Base training). Early stopping if loss plateaus (patience=5).
*   **Batch Size**: Dynamically adjusted to fit ~7GB RAM (likely small batches, e.g., 16-32).
*   **Precision**: Standard float32 (no 8-bit/4-bit quantization to avoid CUDA dependency).

### Statistical Rigor & Assumptions
*   **Multiple Comparisons**: If multiple structural descriptors are tested for significance, a correction (e.g., Bonferroni) will be applied to control family-wise error.
*   **Causal Claims**: The study is observational. Claims are strictly associational: "Feature X correlates with deviation Y." No causal inference regarding ligand effects is made without randomization.
*   **Collinearity**: Structural descriptors (e.g., bond length vs. coordination number) are often definitionally related. The plan will report these descriptively and acknowledge collinearity in the interpretation of SHAP values.
*   **Power Analysis**: Given the target dataset size, the study acknowledges limited power for detecting small effect sizes. Results will be framed with appropriate caution.
*   **Statistical Test**: **Unpaired Welch's t-test** is used to compare error distributions between independent groups (Group 13 vs. Conventional). *Note: The spec (FR-006) requests a 'paired' test, but the data consists of independent samples, making a paired test invalid.*

## Error Analysis Strategy

### Feature Attribution
*   **Method**: Integrated Gradients (IG) and SHAP values.
*   **Goal**: Quantify variance explained by top descriptors (e.g., metal-ligand bond length, steric bulk) on the **prediction error residuals** (ML Energy - DFT Energy). This avoids tautology by analyzing the *deviation* (model failure) rather than the target energy itself.
*   **Target**: Identify a subset of descriptors explaining >60% of error variance (Constitution Principle VII).

### Ligand Stratification
*   **Groups**: Group 13 L-type ligands (donor atoms B, Al, Ga) vs. Conventional ligands.
*   **Test**: **Unpaired Welch's t-test** on error distributions (FR-006 adaptation).
*   **Metric**: p-value (SC-003).

## Decision Rationale

*   **Why SchNet?** SchNet is a proven, CPU-tractable architecture for 3D molecular properties. It avoids the heavy overhead of transformers or large LLMs.
*   **Why CPU-Only?** The project must run on free-tier CI. GPU methods (quantization, CUDA) are explicitly excluded to ensure reproducibility in the target environment.
*   **Why Ensemble?** Single models provide point estimates. An ensemble allows for uncertainty quantification (variance), which is critical for identifying "out of distribution" ligand environments (Constitution Principle VI).
*   **Why LLSO?** Leave-Ligand-Scaffold-Out cross-validation ensures the model is tested on truly unseen chemical scaffolds, preventing data leakage from similar ligands, while remaining computationally feasible compared to LOOCV on an ensemble.
*   **Why QM9-TS?** It is the only verified dataset containing explicit transition states and barrier heights for the relevant chemical space, avoiding the modality mismatch of using ground-state data (OC20) to predict barriers.
