# Research: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## 1. Domain Context & Problem Statement

Predicting the aqueous solubility (logS) of drug-like molecules is a critical step in early-stage drug discovery. Solubility affects bioavailability and pharmacokinetics. Traditional methods rely on quantitative structure-property relationship (QSPR) models using hand-crafted molecular descriptors (e.g., Morgan fingerprints). Graph Neural Networks (GNNs), specifically Message Passing Neural Networks (MPNNs), offer a potential advantage by learning representations directly from the molecular graph topology, potentially capturing complex non-linear interactions without manual feature engineering.

**Research Question**: Does an MPNN trained on molecular graphs significantly outperform a Random Forest baseline using Morgan fingerprints in predicting logS on the ESOL dataset, considering statistical significance and computational constraints?

## 2. Dataset Strategy

The study utilizes the **ESOL (Estimated SOLubility)** dataset, also known as the Delaney dataset.

### 2.1 Primary Dataset: ESOL (Delaney)

- **Description**: A curated dataset of drug-like molecules with experimentally measured aqueous solubility (logS) and SMILES strings.
- **Source**: MoleculeNet / DeepChem.
- **Verified URLs**:
 - Primary: `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv`
 - Mirror: `
- **Variables**:
 - `smiles`: Canonical SMILES string.
 - `measured log solubility in mols per litre`: Target variable (logS).
 - `ESOL predicted log solubility...`: Baseline prediction (not used for training, for reference only).
 - Other physicochemical descriptors (MW, H-bond donors, etc.) are present but not used for the GNN input (graph-only) or RF input (fingerprints only), ensuring a fair comparison of representation learning.
- **Data Integrity**: The dataset is known to contain a small number of invalid SMILES. The plan explicitly includes a cleaning step to exclude these before splitting.

### 2.2 Dataset Fit Verification

- **Required Variables**: SMILES (for graph construction), logS (target).
- **Availability**: Both variables are present in the verified source.
- **No Mismatch**: The dataset contains the exact variables needed. No external data (e.g., pH, temperature) is required as the dataset standardizes conditions.

### 2.3 Data Loading Strategy

- **Method**: Direct HTTP download using `pandas.read_csv`.
- **Validation**: Checksum verification (MD5/SHA256) against known values if available, or at least column presence check.
- **Preprocessing**:
 1. Load CSV.
 2. Filter rows where `smiles` is empty or `logS` is NaN.
 3. Validate SMILES using `rdkit.Chem.MolFromSmiles`.
 4. Log count of invalid SMILES.
 5. Exclude invalid rows.
 6. Proceed with clean dataset.

## 3. Methodology

### 3.1 Baseline: Random Forest with Morgan Fingerprints

- **Rationale**: RF is a robust, non-parametric model that performs well with tabular data and is the standard baseline in chemoinformatics. Morgan fingerprints (ECFP) are a well-established representation of molecular structure.
- **Implementation**:
 - **Fingerprint**: Radius=2, 2048 bits.
 - **Model**: `RandomForestRegressor` from `scikit-learn`.
 - **Hyperparameters**: `n_estimators=500`, `max_depth=None`, `random_state=42`.
 - **Validation**: **Stratified 5-Fold Cross-Validation** (Outer Loop).

### 3.2 Proposed Model: Message Passing Neural Network (MPNN)

- **Rationale**: MPNNs (Gilmer et al., 2017) generalize convolution to graphs, allowing the model to learn local and global structural features directly from atomic and bond types.
- **Architecture**:
 - **Node Features**: Atomic number, degree, formal charge, hybridization, aromaticity.
 - **Edge Features**: Bond type, conjugation, stereochemistry.
 - **Layers**: 2-3 Message Passing layers (e.g., GraphConv or GAT).
 - **Readout**: Global mean pooling followed by a fully connected layer.
- **Constraints**:
 - **CPU-Only**: No CUDA. Optimized for minimal vCPU and RAM resources.
 - **Simplified**: Reduced hidden dimensions and batch size to fit memory and time.
 - **Validation**: **Stratified 5-Fold Cross-Validation** (Outer Loop) with early stopping (patience=10) on Inner Validation.

### 3.3 Statistical Evaluation

- **Metric**: RMSE (Root Mean Squared Error) and R² (Coefficient of Determination).
- **Significance Test**: **Nadeau's Corrected Resampled t-test** on absolute errors (|pred - true|) between RF and GNN.
 - **Null Hypothesis**: Mean difference in absolute errors is zero.
 - **Alpha**: 0.05.
 - **Rationale**: This test corrects for the correlation of errors when models are evaluated on the same folds in Cross-Validation, preventing inflated Type I error rates.
- **Power Analysis**: Post-hoc calculation of statistical power given the sample size and observed effect size.
- **Interpretability**: Attention weights (if GAT) or node importance ranking for 5 sample molecules.

## 4. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Nested Cross-Validation** | Required to prevent data leakage. The Outer Loop provides the test set; the Inner Loop handles tuning. This ensures the final evaluation is unbiased. |
| **Stratified 5-Fold CV** | Ensures that each fold has a representative distribution of logS values, preventing unstable model training due to distribution shifts in small datasets. |
| **Nadeau's Corrected t-test** | Necessary to account for the dependence of errors when comparing two models on the same dataset via Cross-Validation. Standard t-test is invalid here. |
| **CPU-Only GNN** | Ensures reproducibility on free-tier CI runners. The dataset is small enough that a simplified MPNN can converge without GPU acceleration. |
| **Morgan Fingerprints** | Standard baseline in the field. Provides a strong, interpretable benchmark. |
| **Post-hoc Power Analysis** | Required to assess the reliability of the significance test, especially if the effect size is small. |

## 5. Limitations

- **Dataset Size**: [deferred] molecules is small for deep learning. Overfitting is a risk, mitigated by 5-Fold CV and early stopping.
- **CPU Constraints**: The GNN architecture must be simplified, which may limit its ability to capture complex patterns compared to a full-scale GPU model.
- **Generalizability**: Results are specific to the ESOL dataset. Performance on other solubility datasets or diverse chemical spaces may differ.
- **Interpretability**: Attention weights are post-hoc and may not always reflect true causal mechanisms.

## 6. Ethical Considerations

- **Reproducibility**: All code and data sources are open and verifiable.
- **Bias**: The ESOL dataset is curated and may not represent the full diversity of chemical space.
- **Transparency**: Statistical limitations (power, small sample size) will be explicitly reported.