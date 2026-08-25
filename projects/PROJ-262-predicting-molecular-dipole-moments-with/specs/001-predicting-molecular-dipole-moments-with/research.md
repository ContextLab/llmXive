# Research: Predicting Molecular Dipole Moments with Graph Neural Networks

## Summary

This research investigates whether 3D conformational geometry provides independent predictive information for molecular dipole moments beyond 2D connectivity and atom types. The study leverages the QM dataset, a large-scale collection of small organic molecules with quantum-chemical properties calculated at the BLYP/6-31G(2df,p) level. The core hypothesis is that 3D-aware models (SchNet-style GNNs) will outperform 2D-only baselines (Random Forest on Morgan fingerprints) in predicting dipole moments, and that feature attribution will reveal specific structural drivers (e.g., electronegative atom placement, bond angles).

Crucially, this study employs an **Ablation Study** design to isolate the causal contribution of 3D geometry. By comparing the SchNet GNN against a "SchNet-Randomized" variant (shuffled coordinates) and a "2D-GNN" (identical architecture without coordinates), we distinguish between gains due to true geometric signal versus mere model capacity. Additionally, a **Marginal Gain Analysis** compares a Random Forest on 2D features vs. a Random Forest on 2D+3D features to quantify the independent predictive power of 3D geometry.

## Dataset Strategy

The study relies on the QM dataset, which contains a large collection of molecules with dipole moments calculated via DFT. The dataset is accessed via verified Hugging Face mirrors to ensure programmatic download on CI runners.

| Dataset | Source | Verified URL | Access Method | Notes |
|:--- |:--- |:--- |:--- |:--- |
| QM9 (Parquet) | Hugging Face | ` | `datasets.load_dataset(..., streaming=True)` | Contains 3D coordinates, atom types, dipole moments. Streaming used to stay within 8GB RAM. |
| QM9 (Subset) | Hugging Face | ` | `datasets.load_dataset` | Alternative subset for testing; primary source is `lisn519010/QM9`. |
| QM9 (Subset) | Hugging Face | ` | `datasets.load_dataset` | Alternative subset; not used in primary pipeline. |
| DFT (Parquet) | Hugging Face | ` | `datasets.load_dataset` | Not used; QM9 contains required dipole moments. |
| DFT (Parquet) | Hugging Face | ` | `datasets.load_dataset` | Not used. |
| BLYP (JSON) | DOI | ` | Manual check | Not used; QM9 DFT values are the ground truth. |

**Dataset Selection Rationale**: The `lisn519010/QM9` mirror is selected as the primary source because it provides a complete, programmatic Parquet file that can be streamed. The dataset includes all required variables: 3D coordinates, atom types, bond connectivity, and dipole moments. The DOI `10.1038/sdata.2014.22` (original QM9 publication) has no verified URL, so the Hugging Face mirror is used as the canonical source for data access, consistent with the "Verified datasets" block.

**Data Availability & Feasibility**: The QM9 dataset is open and directly downloadable. Streaming is employed to handle a large number of molecules within the 8GB RAM constraint. A random subset is drawn using a **Fixed-Seed Index Sampling** protocol: a random subset of indices is selected from the full dataset *before* streaming, ensuring the subset is representative of the full distribution. If the full dataset exceeds a predefined computational time limit, a well-defined real sample (first-N rows / fixed-seed random sample) is used., with power limitations explicitly noted.

**Limitations**:
- **Hydration State**: QM9 molecules are gas-phase DFT calculations. Hydration effects are out of scope (Constitution Principle VII, Assumptions).
- **Conformational Ensembles**: Only the lowest-energy conformer per molecule is used. Ensemble sampling is future work.
- **Physical Validation**: Dipole moments are validated against QM9 DFT reference data, not experimental measurements (FR-011).

## Methodological Approach

### Feature Engineering
- **3D Features**: 3D coordinates, atom types, bond connectivity. Used as input for SchNet.
- **2D Features**: Morgan fingerprints (radius=2, 2048 bits). Used for Random Forest baseline.
- **Combined Features**: Morgan fingerprints + Normalized Distance Matrices (3D-derived). Used for Marginal Gain Analysis.
- **Preprocessing**: Missing 3D coordinates are flagged and excluded (T019). Exclusion report generated.

### Model Architecture
- **GNN**: Lightweight SchNet-style model (CPU-only). Uses distance-based message passing.
- **Ablation Models**:
 - `SchNet-Randomized`: SchNet with shuffled 3D coordinates (destroys geometric signal).
 - `SchNet-2D`: SchNet architecture without coordinate input (tests architecture capacity).
- **Baseline**: Random Forest (a sufficient ensemble size, max_depth=None) on 2D features.
- **Combined Baseline**: Random Forest on 2D+3D features.
- **Training**: 30 epochs (reduced for speed if needed, but target 50), early stopping (patience=10), 30 random seeds.
- **Loss**: Mean Squared Error (MSE) for dipole moment prediction.

### Statistical Analysis
- **Metrics**: MAE, RMSE (with 95% CI across 30 seeds).
- **Marginal Gain Test**: Paired t-test (α=0.05) comparing RF (2D) vs RF (2D+3D) RMSE distributions.
- **Geometry Sensitivity Test**: Paired t-test comparing SchNet vs SchNet-Randomized RMSE distributions.
- **Bootstrap**: 1000-resample Bootstrap Confidence Intervals for RMSE to ensure robustness.
- **Attribution**: Integrated Gradients (GNN), SHAP (RF). **Saliency maps are explicitly discarded** due to instability.
- **Power**: Sample size determined by Power Analysis (Cohen's d=0.5, power). If subset used, power limitation noted.

### Compute Feasibility
- **CPU-First**: All models trained on CPU. SchNet uses `torch_geometric` in CPU mode.
- **GPU Escape Hatch**: Not required; SchNet is lightweight and feasible on CPU.
- **Streaming**: Data loaded via `datasets.load_dataset(..., streaming=True)` to avoid OOM.
- **Time Limit**: 6h total pipeline. Subset sampling if full dataset exceeds limit.

## Statistical Rigor

- **Multiple Comparisons**: Paired t-tests are performed across 30 seeds, controlling for family-wise error via the paired design.
- **Sample Size**: Determined by Power Analysis. If subset used, power limitation explicitly quantified.
- **Causal Inference**: Observational study. Claims framed as associational. Ablation study provides causal control for geometry.
- **Measurement Validity**: QM9 dipole moments are DFT-calculated (BLYP/6-31G(2df,p)), a standard benchmark.
- **Collinearity**: 2D and 3D features are correlated (geometry constrained by topology). A **Collinearity Check** will compute the correlation matrix between 2D fingerprints and 3D distance matrices to quantify this overlap.

## Decision/Rationale

- **Dataset**: `lisn519010/QM9` chosen for verified URL and streaming capability.
- **Model**: SchNet chosen for 3D-equivariance; RF for 2D baseline.
- **Compute**: CPU-only feasible for SchNet on subset; streaming ensures RAM compliance.
- **Validation**: DFT reference data used; experimental validation out of scope.
- **Statistical Power**: A sufficient number of seeds used to ensure sufficient degrees of freedom for t-tests.

## References

- **QM9 Dataset**: `https://huggingface.co/datasets/lisn519010/QM9` (Verified URL)
- **SchNet**: Schütt et al., "SchNet: A Continuous-filter Convolutional Neural Network for Modeling Quantum Interactions," 2017.
- **Morgan Fingerprints**: Rogers & Hahn, "Extended-Connectivity Fingerprints," 2010.
- **DFT Validation**: QM9 paper (DOI: 10.1038/sdata.2014.22) - no verified URL; DFT values are ground truth.