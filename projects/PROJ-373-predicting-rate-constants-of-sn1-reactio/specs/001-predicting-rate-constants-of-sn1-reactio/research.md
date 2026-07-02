# Research: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## 1. Dataset Strategy

The project relies exclusively on verified datasets available via HuggingFace that contain SMILES and kinetic data. The "Verified datasets" block in the prompt indicates that while general SMILES and RDKit descriptor datasets exist, a dedicated, verified "SN1-specific" dataset with rate constants is not explicitly listed as a single source. However, the following sources are available and will be used:

| Dataset Name | Verified URL | Usage Strategy |
|:--- |:--- |:--- |
| **DTS-SN1-15-01-2024** | ` | **Primary Source**. Contains SN1 reaction data. Will be parsed for SMILES, rate constants, and substrate class. *Note: This is a community-curated collection. Rigorous validation steps (outlier filtering, rate constant standardization) are applied to ensure data quality.* |
| **sn1-miner-evaluations** | ` | **Secondary Source**. Cross-referenced for validation if schema matches. |
| **sn18-all-20240204** | ` | **Tertiary Source**. May contain broader reaction data; will be filtered for SN1-specific entries based on substrate class labels. |

**Critical Note on Data Fit**:
The spec requires "experimental rate constants" and "substrate class" (secondary/tertiary). The DTS-SN1 dataset is the most promising candidate. If the verified source lacks explicit "substrate class" labels (e.g., just SMILES and rate), the system will infer the class using RDKit:
1. Parse SMILES.
2. Identify the leaving group (halide).
3. Analyze the carbon attached to the leaving group.
4. Classify as **Secondary** if 2 carbons attached, **Tertiary** if 3 carbons attached.
5. **Filter Out**: If 0 or 1 carbon attached (Primary/Methyl) -> SN2 mechanism likely.
6. **Filter Out**: If steric hindrance index > 2.0 (calculated via RDKit).

**No Fabricated URLs**: If a specific dataset mentioned in the spec (e.g., "NIST Reaction Database") does not have a verified URL in the prompt's list, it will **not** be used. The plan relies solely on the DTS-SN1 source and its verified derivatives.

**Synthetic Data Augmentation**:
If the verified datasets are insufficient to train a robust MPNN (N < 5k), the plan will generate a synthetic dataset using established Linear Free Energy Relationships (LFER) for SN1 reactions (e.g., Hammett equation parameters). This synthetic data will be clearly labeled and used only for hyperparameter tuning and robustness checks, not for final performance reporting.

**Descriptor Validation**:
Instead of using ChEMBL (which lacks rate constants), descriptor validation will be performed using:
1. **Internal Consistency**: Checking for duplicate SMILES with conflicting rate constants in the DTS-SN1 dataset.
2. **Synthetic Hammett Dataset**: A small set of molecules generated with known Hammett constants to verify that RDKit Gasteiger charge calculations correlate with expected electronic effects.

## 2. Methodological Rationale

### 2.1 Model Architecture: Shallow MPNN
**Choice**: Message Passing Neural Network (MPNN) with 4 layers.
**Rationale**:
- **SN1 Mechanism**: SN1 rates are heavily influenced by the stability of the carbocation intermediate, which depends on electronic effects (inductive, resonance) and steric effects. Graph-based models (MPNNs) are ideal for capturing these local and global structural dependencies.
- **CPU Constraint**: Deep MPNNs (e.g., >10 layers) or large GNNs (e.g., Graphormer) are computationally expensive and may not converge within 6 hours on a 2-core CPU. A shallow multi-layer MPNN with hidden dimension -128 is a proven CPU-tractable approximation.
- **Feature Fit**: The MPNN will learn message passing over the molecular graph, effectively learning the "electronic environment" of the reaction center without needing explicit QM calculations (PM7), which are too slow.
- **Substrate Class Exclusion**: The `substrate_class` label will **NOT** be used as an input feature. It is used ONLY for filtering (to ensure SN1 mechanism) and stratification. The model must distinguish between different tertiary substrates using fine-grained electronic descriptors (Gasteiger charges, local steric indices) to avoid trivial correlation.
- **Scope Clarification**: The model is strictly an "SN1 Rate Predictor" for secondary and tertiary substrates. The filtering of primary substrates is a necessary mechanism definition step, not data leakage. The model is not expected to predict rates for primary substrates (which would follow SN2), and the "trivial correlation" is avoided by ensuring the model learns *variations* in rate *within* the SN1 class based on electronic descriptors, not just the class label itself.

### 2.2 Feature Engineering & Multicollinearity
- **Input**: SMILES strings.
- **Descriptors**: Gasteiger partial charges (fast, approximate electrostatics), Topological Indices (Wiener, Zagreb) for steric/electronic topology.
- **Why Gasteiger?**: It is computationally cheap and deterministic, fitting the CPU constraint. While semi-empirical methods (PMx) are more accurate, they violate the 6-hour runtime limit for a dataset of ~10k entries.
- **Orthogonal Validation & Multicollinearity**:
 - **Model A (Graph-Only)**: MPNN trained on raw graph features only. **SHAP analysis will ONLY be performed on Model A** to avoid ambiguity caused by feeding both raw graph and pre-computed Gasteiger charges (which are derived from the graph) into the same model.
 - **Model B (Graph + Descriptors)**: MPNN trained on raw graph + pre-computed Gasteiger/Topological descriptors. This model is used **solely for performance benchmarking** to test if pre-computed descriptors add value. Its internal feature weights are considered ambiguous due to multicollinearity and will **not** be interpreted.
 - **Disentanglement Strategy**: To explore the inherent correlation between steric and electronic effects (which are both topological), the plan will use **Partial Dependence Plots (PDP)** on Model A. PDPs will visualize the marginal effect of specific topological features while holding others constant, providing a more nuanced view than simple SHAP.

### 2.3 Statistical Rigor & Validation
- **Multiple Comparisons**: The hyperparameter search (multiple configurations) involves multiple comparisons. The plan uses **Random Search** (not Grid Search) to reduce the search space, and the final model selection is based on **Validation Set** performance. The final test set is held out strictly for the final evaluation.
- **Power Analysis & Action Plan**:
 - **MDE Definition**: The Minimum Detectable Effect (MDE) is defined as ΔR² ≥ 0.05.
 - **Power Calculation**: A formal Power Analysis will be conducted to determine the statistical power (1-β) alongside the p-value from the bootstrap comparison (FR-004).
 - **Action if Power < 0.8**: If the calculated power is < 0.8, the project will **switch to a 'Single-Model Evaluation'**. The bootstrap comparison will be dropped, and the result will be reported as "Underpowered for small effects (ΔR² < 0.05)". The limitation will be explicitly stated in the final report rather than proceeding with a potentially false negative/positive test.
- **Causal Inference**: This is an **observational** study (predictive modeling). No causal claims (e.g., "Adding group X causes rate Y") will be made. Claims will be framed as "Predictive Association" or "Structural Determinants (Predictive)". The perturbation study (FR-008) validates predictive dependency, not chemical mechanism.
- **Collinearity**: Gasteiger charges and topological indices may be correlated. The plan includes a **Variance Inflation Factor (VIF)** diagnostic (FR-007). If VIF > 5 is found (which is expected due to chemical definition), the plan will:
 1. Report the correlation matrix and PCA loadings to show the descriptors represent a consistent "electronic/steric" latent space.
 2. **Restrict SHAP analysis to Model A (Graph-Only)** for interpretability, as the descriptors are redundant.
 3. If Model A also fails to converge or perform, the study will report "No robust structural determinants identified" rather than forcing an interpretation on collinear features.
- **Measurement Validity**: The "ground truth" is the experimental rate constant from the dataset. The validity depends on the dataset's curation. The plan assumes the DTS-SN1 dataset is curated for SN1 reactions, with additional outlier filtering applied.

### 2.4 Compute Feasibility
- **Hardware**: 2 CPU cores, 7 GB RAM.
- **Strategy**:
 - **Data**: Limit to a subset if the full dataset exceeds memory. Use `pandas` with `chunksize` if necessary.
 - **Model**: Use `torch` with `device='cpu'`. No `CUDA`.
 - **Training**: Use `scikit-learn`'s `RandomizedSearchCV` for hyperparameter tuning, which is CPU-efficient.
 - **Runtime**: 4-layer MPNN with batch size 32-64 should train in < 2 hours on CPU for 10k samples.

## 3. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|:--- |:--- |:--- |:--- |
| **Dataset Mismatch** | Medium | High | DTS-SN1 might lack "substrate class" labels. **Mitigation**: Infer class via RDKit logic; filter out non-SN1 candidates. |
| **Runtime Exceeded** | Low | High | MPNN training too slow. **Mitigation**: Cap dataset size to 10k; reduce hidden dim to 64; reduce epochs. |
| **Model Convergence** | Medium | Medium | MPNN fails to beat linear baseline. **Mitigation**: Report negative results honestly; analyze feature importance to explain why. |
| **SMILES Parsing Errors** | Medium | Low | Invalid SMILES in raw data. **Mitigation**: Log exclusions; ensure ≥95% success rate (SC-005). |
| **Collinearity Invalidating SHAP** | High | Medium | Descriptors are inherently correlated. **Mitigation**: Use Graph-Only model (Model A) for SHAP; report PCA loadings. |

## 4. Perturbation Study Methodology (FR-008)

The perturbation study will **NOT** remove columns (which is invalid for GNNs). Instead, it will use **Graph-Based Masking**:
1. Identify the top atoms/bonds contributing most to the prediction (via SHAP on Model A).
2. Create a modified molecular graph where these specific nodes/edges have their features zeroed out or masked. **Crucially, the masking will target 'non-reacting' atoms (e.g., distant substituents) to test sensitivity to electronic/steric environment. The leaving group itself will NOT be masked, as doing so would fundamentally change the reaction mechanism (making it impossible) and create a non-physical state.**
3. Re-run the MPNN inference on the masked graph.
4. Measure the drop in R².
This validates that the model's prediction is sensitive to the specific structural features identified, without creating a non-physical input state. The resulting R² drop is reported strictly as "Predictive Sensitivity" to structural perturbations.