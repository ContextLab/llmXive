# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Scientific Rationale

The research question investigates whether molecular topology, encoded as SMILES strings, contains sufficient signal to predict the **Raw Packing Coefficient (PC_raw)** of organic crystals. While SMILES captures connectivity, it omits conformational and packing forces. However, the inclusion of 3D geometric descriptors (radius of gyration, asphericity) derived from the crystal coordinates, combined with a frozen SMILES-transformer embedding, creates a hybrid representation that bridges the gap between 1D connectivity and 3D packing.

**Tautology Mitigation**: The previous definition of CAPE (PC_raw / avg_vdW_volume) created a mathematical tautology because the denominator depended directly on atom counts, which were also used as predictors. This revision redefines the target to **PC_raw**, removing the compositional dependency from the prediction task. Atom counts and types are excluded from the primary feature matrix. Instead, a **Residual Analysis** is performed post-training to quantify how much of the unexplained variance in PC_raw is correlated with composition. This isolates the topological signal from the compositional identity.

**Geometry Baseline**: Since 3D descriptors are derived from the same coordinates used to calculate unit cell volume (a component of PC_raw), a "Geometry-Only" baseline model is introduced. This model establishes the theoretical upper bound of prediction using geometric inputs. The primary analysis then compares the SMILES-Topology model against this baseline to determine if SMILES adds *incremental* predictive power beyond what is already captured by the 3D geometry.

## Dataset Strategy

### Verified Sources
The project relies on the following verified datasets to ensure reproducibility and availability on CI runners:

| Dataset | Purpose | Verified URL / Loader | Notes |
| :--- | :--- | :--- | :--- |
| **COD (Crystallography Open Database)** | Source of CIF data, unit cell volumes, lattice systems, solvent flags. | `datasets.load_dataset("cod/cod", split="train")` | Official HuggingFace mirror. Contains `_cell_volume`, `_symmetry_space_group`, `_chemical_solvent`. **Verified**: Schema check in Phase 0 ensures these fields exist. |
| **SMILES Transformers** | Pre-trained weights for frozen embedding. | HuggingFace `transformers` library (weights cached) | Weights downloaded once; frozen during training. |
| **Bondi Radii** | Atomic van der Waals volumes for PC_raw calculation. | Bondi, A. (1964) *J. Phys. Chem.*, 68, 441–451. | No URL; implemented as constant lookup table in code. |

### Variable Fit Verification
*   **Required**: `unit_cell_volume`, `lattice_system`, `temperature_K` (if available), `solvent_present` (if available).
*   **Verification**: The pipeline includes a **Schema Validation Step** in Phase 0. It inspects the schema of the verified COD JSONL. If `temperature_K` is missing, the pipeline proceeds with a `None` value for that feature, flagging it in the VIF diagnostics and model training (covariate missingness handling). If critical fields like `_cell_volume` are missing, the pipeline aborts.
*   **SMILES Generation**: Since many COD entries lack `_chemical_structure_SMILES`, the pipeline uses `rdkit.Chem.MolFromMolBlock` + `rdkit.Chem.MolToSmiles` on the 3D coordinates. This is a standard, reproducible procedure.

### Data Volume & Feasibility
*   **Target**: ≥ 500 valid records after filtering (≤ 50 non-H atoms).
*   **Feasibility**: The verified COD sources contain >100k entries. Filtering for organic molecules < 50 atoms and valid unit cells will easily yield >500 records.
*   **Streaming**: The JSONL will be streamed. A filter mask will be applied in a single pass to generate `data/processed/full_feature_matrix.csv`. Embeddings are generated in batches to respect memory limits.

## Methodological Rigor

### Statistical Plan
1.  **Multiple Comparison Correction**: For the sensitivity analysis (3 thresholds), a **Bonferroni correction** will be applied to the permutation test p-values ($\alpha_{adj} = 0.05 / 3 \approx 0.0167$).
2.  **Power Justification & Distribution Check**: 
    *   With N ≥ 500, the study has >90% power to detect a Pearson correlation of $r=0.4$ at $\alpha=0.05$ **assuming bivariate normality**.
    *   **New Step**: A Shapiro-Wilk test on PC_raw will be performed in Phase 1. If PC_raw is non-normal or has a restricted range, the power calculation will be adjusted using non-parametric estimates or bootstrapping to ensure validity. Spearman's rho will be the primary metric if normality is violated.
3.  **Causal Inference**: The study is **observational**. Claims will be framed as "associational" or "predictive," not causal. No randomization exists.
4.  **Measurement Validity**: PC_raw is derived from Bondi radii (standard in crystallography). SMILES validity is ensured by RDKit canonicalization.
5.  **Collinearity**: The 3D descriptors (e.g., radius of gyration) and atom counts are definitionally related. **VIF diagnostics (FR-009)** will be run on the full feature matrix (fingerprints + 3D). If VIF > 5, the feature will be flagged. **Note**: Atom counts are excluded from the primary model to avoid tautology, but included in the VIF check for the full set of potential features.
6.  **Residual Analysis (FR-014)**: This analysis correlates the *residuals* of the PC_raw prediction with atom-type composition features. This quantifies the unexplained compositional signal without creating a circular dependency, as the target (PC_raw) is no longer a function of the composition in the regression equation.

### Computational Strategy
*   **CPU-First**:
    *   **SMILES Transformer**: `transformers` library with `device="cpu"`. **Batch Size = 64**. Embeddings are streamed to disk to avoid OOM.
    *   **MLP**: `torch.nn.Sequential` (Input -> 64 -> 32 -> 1). < 100k params.
    *   **Permutation Test**: 10,000 shuffles. **Strategy**: Parallelized via `joblib` with `n_jobs=-1`. A timeout is enforced (2 hours); if exceeded, the number of shuffles is reduced to the maximum feasible count (minimum 1,000 per Constitution Principle VII), and the deviation is logged.
*   **GPU Escape Hatch**: If transformer inference OOMs, the execution agent will detect the error and re-run on a Kaggle GPU (8-bit quantization if necessary, though frozen inference usually fits in CPU RAM).

## Decision Rationale
The chosen approach prioritizes **reproducibility** and **statistical validity** over maximizing model complexity. Using a frozen transformer ensures we do not waste compute on training a massive model for a small dataset. The strict adherence to VIF and Bonferroni corrections addresses the panel's concern about statistical rigor. The use of verified COD sources ensures the data is actually obtainable on a CI runner, avoiding the "gated data" trap. The redefinition of the target to PC_raw and the exclusion of compositional predictors from the primary model explicitly address the risk of circularity and mathematical tautology. The geometry baseline provides a necessary context for interpreting the topological signal.
