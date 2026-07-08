# Research: Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

## Dataset Strategy

The project relies on public repositories for CIF structures and DFT-calculated elastic tensors. Per the project constraints, we will **only** use the verified datasets listed below. We explicitly reject any dataset that does not contain both the structural coordinates (CIF) and the corresponding 6-component elastic tensor in a unified source to avoid join biases.

**Note on Title Correction**: As noted by reviewer `richard-feynman-simulated`, the project title "From First-Principles Calculations" was misleading. The methodology is **Surrogate Modeling**: using GNNs to *approximate* the results of first-principles (DFT) calculations based on structure. The ground truth is DFT; the model is a statistical learner.

### Verified Datasets & Selection Rationale

| Dataset Name | Source URL | Relevance | Selection Rationale |
|:--- |:--- |:--- |:--- |
| **Materials Project Elasticity** | `https://materialsproject.org/rest` (via `pymatgen` API) | **Primary Unified Source** | Contains both CIF structures and complete 6-component elastic tensors for 2D materials. This unified source eliminates the risk of mismatched IDs and selection bias. |
| **AFLOW Elasticity** | ` (via `aflow` API) | **Supplementary** | Used to cross-reference if MP data is insufficient. |
| **Excluded: Generic DFT Sets** | `sdmattpotter/dftest61523` | **Excluded** | Does not guarantee complete elastic tensors for the specific 2D subset. Joining with separate CIF sources is rejected due to high risk of bias. |
| **Excluded: Thermal/Exp** | `foundry-ml/dataset_thermalcond_aflow` | **Excluded** | Contains thermal conductivity, not elastic tensors. |

**Critical Data Availability Gate**:
The project will proceed **only** if the unified source (Materials Project Elasticity via `pymatgen` or a verified single-file dataset) contains at least 5 unique material families with complete elastic tensors.
* **Strategy**: The `ingest/download.py` script will query the unified source. If the count of valid 2D entries with complete tensors is < 5 families, the script will raise a `DataUnavailableError` and halt the pipeline.
* **Risk Mitigation**: No join logic is implemented. The unified source ensures that every structure has a matching elastic tensor, preventing the selection bias of "missing tensors for complex structures."

## Methodological Rigor

### Statistical & Computational Rigor

1. **Multiple Comparison Correction**:
 * The study runs multiple hypothesis tests (comparing model performance across different material families and ablation variants).
 * **Method**: We will apply the **Benjamini-Hochberg procedure** to control the False Discovery Rate (FDR) when comparing performance deltas across the 5-fold cross-validation splits and ablation studies.
 * *Note*: Exact p-values are `[deferred]` until the `analysis/importance.py` script is executed.

2. **Sample Size & Power**:
 * **Limitation**: The available dataset of 2D materials with *complete* elastic tensors is likely small.
 * **Minimum Threshold**: We enforce a minimum sample size of **N ≥ 20 per family** for any family included in the inter-family generalization test. Families with < 20 entries are excluded from the generalization test and flagged as "insufficient data."
 * **Acknowledgement**: We explicitly acknowledge that the statistical power to detect small effect sizes in ablation studies is limited. We will report bootstrapped 95% confidence intervals for all MAPE metrics.

3. **Causal Inference & Observational Nature**:
 * **Statement**: This is an **observational study**. We do not randomize structural features.
 * **Implication**: All claims regarding "influence" of features are framed as **associational correlations**.
 * **Collinearity Handling**: Structural descriptors (e.g., coordination number and bond length) are physically correlated. Instead of VIF (which assumes linearity), we will use **SHAP interaction values** to quantify the **joint contribution** of correlated features. We will not claim "independent" effects for any descriptor. Permutation importance will be applied to decorrelated feature groups only.

4. **Physical Validity & Tautology**:
 * **Observation**: Elastic moduli are defined by the second derivative of the potential energy surface, which is a function of atomic positions. The GNN is learning a mapping from geometry to this derivative.
 * **Interpretation**: The validation is not a test of "new physics" but a test of **descriptor sufficiency**. If the model fails to generalize across families (e.g., TMDs to MXenes), it indicates that **structural descriptors alone are insufficient** and that electronic effects (d-orbital hybridization) are critical.
 * **Analysis**: We will correlate the performance drop (inter-family MAPE increase) with known electronic properties (e.g., band gap) if available in the metadata, to test the hypothesis that electronic effects are the missing link.

5. **Bias Detection**:
 * Before finalizing the dataset, the `ingest/bias_check.py` script will compare the distribution of structural descriptors (e.g., coordination number, density) between entries with complete tensors and those that would have been excluded (if any) in a non-unified scenario.
 * If significant bias is detected (e.g., excluded entries are systematically more complex), the final report will explicitly qualify the generalization claims.

## Compute Feasibility

The plan strictly adheres to the GitHub Actions free-tier constraints (limited CPU, 7GB RAM, 6h limit).

* **Library Selection**:
 * `torch`: Installed via `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
 * `torch-geometric`: Installed with `cpu` backend flags.
 * `pymatgen`: Standard installation (no heavy dependencies).
 * `scikit-learn`: Standard CPU implementation.
* **Model Architecture**:
 * **Layers**: 2 to 3 (configurable).
 * **Hidden Dimension**: ≤ 64.
 * **Batch Size**: Dynamically adjusted (e.g., 16 or 32) to fit within 7GB RAM.
 * **Precision**: Standard float32 (no mixed precision, no 8-bit quantization).
* **Training Strategy**:
 * **Early Stopping**: The training loop will monitor validation loss with a **patience of 3 epochs**. Training will stop automatically when validation loss plateaus, preventing underfitting (arbitrary 20 epochs) or overfitting.
 * **Runtime**: Training on ~1000 samples with early stopping is estimated to take < 2 hours.
 * **Total Estimated**: < 5 hours (within 6h limit).

## Decision Rationale

* **Why GNN?**: Elastic properties are inherently dependent on the 3D (or 2D) connectivity of the lattice. GNNs are the state-of-the-art for structure-property prediction and handle variable-sized inputs naturally.
* **Why CPU Only?**: The compute budget is strict. Training large models on CPU is infeasible, but a lightweight GNN is tractable.
* **Why Structure-Only?**: The research question specifically asks if *structure* alone is sufficient. The study explicitly acknowledges the limitation that electronic effects are likely primary, and uses the model's failure to generalize as evidence of this.