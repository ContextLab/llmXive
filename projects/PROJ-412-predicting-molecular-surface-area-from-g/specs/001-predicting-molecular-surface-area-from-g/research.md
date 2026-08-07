# Research: Predicting Molecular Surface Area from Graph Convolutional Networks

## Problem Statement

Can a Graph Convolutional Network (GCN) trained solely on 2D molecular topology predict the 3D Solvent Accessible Surface Area (SASA) of a molecule with accuracy comparable to direct 3D geometry calculations? This study investigates the information bottleneck between 2D graph representations and 3D conformational properties, aiming to determine if lightweight 2D models can serve as effective surrogates for computationally expensive 3D geometry generation.

## Dataset Strategy

The study relies on open, directly downloadable datasets to ensure CI feasibility. No access-gated data (e.g., ZINC15 original, PubChem) will be used unless a verified open mirror exists.

### Verified Datasets

The following datasets are verified and used for the study. All citations refer to the verified URLs provided in the project input.

| Dataset Name | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **ZINC15 Subset** | ` | Primary source for SMILES strings. Contains pre-processed SMILES. | **Verified**: Direct Parquet download. |
| **SMILES Test Set** | ` | Supplementary validation set if ZINC15 is insufficient. | **Verified**: Direct Parquet download. |
| **RDKit Descriptors** | ` | Reference for descriptor calculation logic (not used as primary label source). | **Verified**: Direct Parquet download. |

**Data Loading Strategy**:
1. **Primary Load**: The pipeline will attempt to load `zinc_processed.parquet` using `pandas.read_parquet` or `pyarrow`.
2. **Fallback**: If the primary source fails or is empty, the pipeline will load `smiles-transformers` test set.
3. **No OpenDataPubChem**: As per the input, "OpenDataPubChem: NO verified source found". The plan **does not** cite or attempt to download from OpenDataPubChem.
4. **Streaming**: If the dataset exceeds ~7GB, `datasets.load_dataset(..., streaming=True)` will be used to iterate and process in chunks, ensuring RAM constraints are met.

### Dataset Verification Step
To ensure the dataset contains **only** raw SMILES and no pre-computed 3D labels (which would bypass the core experimental step), the pipeline will:
1. Load the dataset.
2. Check for the presence of columns like `sasa`, `conformer`, `3d_coords`.
3. If any such columns are found, the pipeline will raise a `CriticalError` and halt, forcing the user to select a different dataset or manually strip the columns.
4. This ensures the pipeline actually performs the 3D generation step required by the spec.

### Data Preprocessing Plan

1. **SMILES Validation**: Use `rdkit.Chem.MolFromSmiles`. Invalid SMILES are logged and excluded.
2. **2D Graph Generation**: Convert valid SMILES to `ConvMol` (DeepChem) or `DGLGraph` (PyTorch Geometric) using atom type, hybridization, and charge features.
3. **3D Conformer Generation**:
 * Use RDKit `AllChem.EmbedMolecule` with ETKDGv3 parameters.
 * **Variance Methodology**: Generate **10 conformers** per molecule. Compute SASA for each.
 * **Label**: Use the **mean SASA** of the 10 conformers as the ground truth label.
 * **Uncertainty**: Record the **standard deviation** of the 10 SASA values as the "Conformer Uncertainty".
 * **Constraint**: If conformer generation fails for >10% of the batch, the pipeline halts (Constitution Principle VII).
4. **Feature Matrix**: Create a DataFrame with columns: `smiles`, `graph_features` (sparse/dense), `sasa_label` (mean), `sasa_uncertainty` (std), `molecular_weight`.

## Methodological Rigor

### Statistical Methods

1. **Model Comparison**:
 * **Metric**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), R².
 * **Test**: Paired t-test on the prediction errors (GCN vs. Linear Baseline) to determine statistical significance. **Note**: The t-test compares GCN vs. Linear Baseline, NOT GCN vs. Oracle (which would be trivial).
 * **Correction**: Bonferroni correction applied if multiple thresholds are tested (FR-007).
2. **Sensitivity Analysis**:
 * Sweep MAE thresholds: **{0.5, 2.5, 10.0} Å²**.
 * **Justification**: These values represent [deferred], [deferred], and [deferred] of a typical SASA value (50 Å²), which are physically realistic and above the noise floor of RDKit calculations.
 * Report variation in "Success Rate" (percentage of molecules within threshold).
3. **Collinearity Check**:
 * Acknowledge that molecular weight is a strong predictor of SASA. The baseline model will include MW as a covariate to ensure fair comparison.
4. **Pre-study Power Analysis**:
 * **Formula**: $n = \frac{(Z_{\alpha} + Z_{\beta})^2 \cdot 2 \cdot \sigma^2}{\delta^2}$
 * **Parameters**: $\alpha=0.05$ (Z=1.96), $\beta=0.20$ (Power=80%, Z=0.84), $\sigma$ (estimated SD of errors) $\approx 5.0$ Å², $\delta$ (minimum detectable effect size, Cohen's d=0.5) $\approx 2.5$ Å².
 * **Calculation**: $n \approx \frac{(1.96 + 0.84)^2 \cdot 2 \cdot 25}{6.25} \approx 128$.
 * **Justification**: The study requires a minimum of **128 valid molecules** to detect a medium effect size (Cohen's d=0.5) with [deferred] power. If the dataset yields <128 molecules, the study will report a "power-limited" status and interpret results with caution.

### Dataset-Variable Fit

* **Requirement**: The dataset must contain valid SMILES and allow for 3D conformer generation.
* **Verification**: The ZINC15 subset (verified URL) contains SMILES. RDKit will attempt 3D generation.
* **Risk**: If the dataset contains only 2D topological data without the ability to generate 3D conformers (e.g., salts, polymers), those entries are excluded. The plan does **not** assume the dataset contains pre-computed 3D SASA; it **generates** it via RDKit. This is a computed ground truth, not an experimental one (Spec Assumption).

## Compute Feasibility

### CPU-First Strategy

* **Hardware**: GitHub Actions free-tier (2 CPU, ~7 GB RAM).
* **Model**: Lightweight GCN (2-3 layers, hidden dim ≤ 256).
* **Training**: Batch size adjusted to fit RAM (e.g., 32 or 64). Early stopping (patience=5) prevents overfitting and saves time.
* **3D Generation**: RDKit 3D generation is CPU-bound but parallelizable. Chunked processing (e.g., 100 molecules at a time) prevents OOM.
* **Fallback Strategy**: If the full dataset exceeds the 6-hour CPU limit, the pipeline will automatically sample a subset (e.g., [deferred] molecules) to ensure completion. No automated GPU offload is planned to avoid CI failure risks; manual offload is an optional user step.

### Decision/Rationale

| Method | Run Location | Rationale |
|:--- |:--- |:--- |
| Data Ingestion/Preprocessing | CPU | I/O and RDKit 3D generation are CPU-optimized. |
| GCN Training | CPU (Default) | Small GCN fits in CPU RAM. |
| Baseline (Linear Reg) | CPU | Trivial for CPU. |
| Sensitivity Analysis | CPU | Simple arithmetic on prediction arrays. |

## Ethical and Safety Considerations

* **No Causal Claims**: The study is associative. No claim is made that 2D topology *causes* surface area; rather, it predicts it.
* **Ground Truth Definition**: SASA is defined as the mean of 10 RDKit-computed conformers. This is a computational approximation, not a physical measurement. The plan explicitly states this limitation.
* **Conformer Uncertainty**: The standard deviation of the 10 conformers is reported to quantify the heuristic variance of ETKDG.