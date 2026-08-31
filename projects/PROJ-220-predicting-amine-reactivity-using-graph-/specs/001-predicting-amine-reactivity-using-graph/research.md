# Research: Predicting Amine Reactivity Using Graph Neural Networks and Public Databases

## 1. Problem Formulation

The goal is to predict the logarithm of the reaction rate constant ($\log(k)$) for SN2 reactions involving primary and secondary amines. This is a regression problem where the input is a molecular graph representing the reactants and the output is a continuous scalar.

**Key Challenges**:
1. **Data Scarcity & Quality**: High-quality kinetic data with temperature and solvent metadata is sparse in public databases.
2. **Heterophily**: Reaction graphs often exhibit heterophily (nodes with similar features are not connected, or connected nodes have dissimilar features) due to the distinct electronic environments of the nucleophile and electrophile.
3. **Compute Constraints**: The model must train on CPU within 6 hours and <7GB RAM.
4. **Construct Validity**: External descriptors used for validation must be computed for the specific dataset molecules, not assumed.

## 2. Dataset Strategy

We will utilize the following **verified** datasets to construct the training set. **Synthetic or LLM-generated datasets (e.g., SN2K Distilabel) are explicitly excluded** as they do not contain experimental ground truth.

| Dataset Name | Purpose | Verified URL / Source | Loading Strategy |
|:--- |:--- |:--- |:--- |
| **ChEMBL (BioAssay)** | Primary source for experimental SN2 kinetic data ($k$, $t_{1/2}$) with temperature metadata. | ` (via `chembl_webresource_client`) | Use `chembl_webresource_client` to query assays with "SN2" and "kinetic" keywords. Filter for primary/secondary amines. |
| **NIST Kinetics Database** | Supplemental source for experimental rate constants and activation energies. | ` (Direct download of curated subset if available, or API) | If API is rate-limited, use the `nist_kinetics` subset from `openml` if available, otherwise manual download of CSV subset. |
| **PubChem (Canonicalized)** | **Structural validation only**. Used for SMILES canonicalization and pKa calculation. | ` (via `requests` or `pubchempy`) | Fetch structure only. **NOT** used for kinetic data ($k$). |

**Data Ingestion Plan (FR-001)**:
1. **Filter**: Select records from ChEMBL/NIST where the nucleophile SMILES matches primary (`[NH2]`) or secondary (`[NH]`) amine patterns.
2. **Normalize**: Extract temperature ($T$) and rate constant ($k$). If $T$ is missing, exclude the record (per FR-001). If $E_a$ is missing, use a reaction-class-specific average (calculated from the subset of records with $E_a$) to normalize $k$ to 298K using the Arrhenius equation.
3. **Validation**: Calculate pKa for the amine reactant using RDKit (Gasteiger method) if not available. Exclude records with invalid SMILES or NaN pKa (FR-007).

**Dataset-variable Fit**:
* **Required Variables**: Reactant SMILES, Product SMILES, Rate Constant ($k$), Temperature ($T$), Activation Energy ($E_a$).
* **Verification**: ChEMBL and NIST are the only sources with *experimental* kinetic data. PubChem is excluded for kinetics.
* **Gap Handling**: If the dataset size is insufficient, the plan will explicitly log this gap and proceed with the available subset, acknowledging the limitation in power (FR-001, SC-006).

## 3. Methodology

### 3.1 Graph Construction (FR-002, Principle VI)
We will construct heterogeneous molecular graphs using RDKit.
* **Nodes**: Atoms. Features: Atomic number, hybridization, formal charge, Gasteiger partial charge, and calculated pKa.
* **Edges**: Bonds. Features: Bond order, conjugation, ring membership.
* **Heterophily Handling**: Standard message passing (GCN) assumes homophily. We will implement a **Graph Attention Network (GAT)** with edge-type awareness or a **GraphSAGE** variant that allows for distinct aggregation functions for different edge types (e.g., bond order) to better capture the heterophilous nature of reaction centers.

### 3.2 Baseline Model (FR-004)
A **Random Forest Regressor** trained on traditional chemical descriptors:
* pKa (calculated)
* Molecular Weight
* Steric parameters (Taft $E_s$, Charton $\nu$ - derived from 3D geometry if available, or approximated via topological indices).
* Hammett $\sigma$ values (if substituents are identifiable).

### 3.3 GNN Model (FR-003)
* **Architecture**: 3-layer GAT/GraphSAGE.
* **Input**: Node/Edge feature vectors.
* **Readout**: Global pooling (mean/sum) to get a graph-level representation.
* **Output Head**: Linear layer predicting $\log(k)$.
* **Training**: 70/15/15 scaffold-based split to ensure generalization to unseen chemical scaffolds.
* **Compute Feasibility**: The model will be trained using PyTorch on CPU. We will use `torch_geometric`'s CPU-optimized data loaders. If the dataset is too large, we will sample a representative subset to fit within the 6-hour window., ensuring the sample is statistically representative (FR-008).

### 3.4 Interpretability and Validation (FR-005, Principle VII)

**Descriptor Computation Protocol**:
To satisfy SC-003 and resolve the construct validity gap, we will compute the "independent descriptor vector" for **every molecule** in the dataset using the `mordred` and `rdkit` libraries.
* **Hammett $\sigma$**: Calculated based on substituent position (ortho/meta/para) relative to the reaction center using `rdkit` fragment matching.
* **Taft $E_s$**: Calculated using `mordred` steric descriptors or approximated via Van der Waals volume of the alpha-substituent.
* **Verloop B1/B5**: Calculated via `mordred` 3D descriptors (requires conformer generation).
* **Charton $\nu$**: Derived from steric volume.
* **Molar Refractivity (MR)**: Calculated via `mordred`.

**Validation Strategy**:
1. **SHAP Analysis**: Apply SHAP to the GNN predictions to rank atomic features.
2. **Correlation Test**: Calculate the Pearson correlation ($r$) between the aggregated SHAP importance (for the reaction center atoms) and the **computed** descriptor vector.
3. **Collinearity Check**: Explicitly calculate the correlation between the model's input features (pKa) and the validation vector (Hammett/Taft). If $r > 0.9$, the validation is flagged as "collinear" and the interpretation is limited to "convergence with input physics" rather than "novel feature discovery".
4. **Non-Linearity Check**: Compare the SHAP-descriptor correlation of the GNN against a Linear Model baseline. If the GNN's correlation is significantly higher, it implies the GNN captured non-linear interactions beyond the linear descriptors.

### 3.5 Statistical Rigor (FR-006)

**Power Analysis and Sample Size Justification**:
* **Goal**: Detect a medium effect size (Cohen's $f^2 = 0.15$) in a regression with 10 predictors at 80% power ($\alpha = 0.05$).
* **Minimum N**: Requires $N \approx 1200$ records.
* **Limitation**: If the dataset contains $N < 1200$, the project will report the achieved power and avoid claiming "statistical significance" for small effects. The results will be framed as "exploratory" if $N < 500$.
* **Action**: The pipeline will count the final dataset size and log the calculated power. If $N < 500$, the training will proceed but the interpretation section will be restricted.

**Sensitivity Analysis for Activation Energy Imputation**:
* **Risk**: Imputing $E_a$ may introduce spurious correlations.
* **Mitigation**: Train a secondary model using **only** records with *measured* $E_a$. Compare the performance ($R^2$) and feature importance of this "Measured-Only" model against the "Imputed" model. If the difference in $R^2$ is $> 0.05$ or feature importance rankings differ significantly, the imputed records will be excluded from the final analysis.

**Significance Testing**:
* **Bootstrap CI**: A bootstrap-based confidence interval on the absolute errors of the GNN vs. Baseline.
* **Multiple Comparisons**: If multiple metrics are compared, Bonferroni correction will be applied.

## 4. Compute Feasibility & Escape Hatch

**Primary Strategy (CPU)**:
* Use `datasets` library with `streaming=True` to avoid loading full data into RAM.
* Use `torch` (CPU build) and `torch_geometric` (CPU build).
* Limit graph size: Filter for molecules with <100 atoms to ensure graph convolution speed.
* Limit training epochs: Early stopping based on validation loss.

**GPU Escape Hatch (Kaggle)**:
* **Trigger**: If the GNN training fails to converge or exceeds time limits on CPU due to graph complexity, the execution stage will auto-offload to a Kaggle GPU.
* **Scaled Down**: If offloaded, we will use a smaller batch size and potentially a smaller subset of data to ensure the kernel limit is respected.
* **No Fabrication**: We will not simulate a GPU run on CPU. If the method truly requires GPU (e.g., massive graph), the plan will explicitly state that the CPU run is a "small-scale feasibility test" and the full run is deferred to the GPU environment.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **ChEMBL/NIST over SN2K** | SN2K is synthetic/LLM-generated and lacks experimental ground truth. ChEMBL/NIST provide the required kinetic data. |
| **Descriptor Computation** | External descriptors must be computed for the specific dataset to ensure the validation vector is real and not assumed. |
| **Collinearity Check** | To ensure the correlation test is not tautological due to shared physics between inputs and validation targets. |
| **Power Analysis** | To explicitly acknowledge sample size limitations and prevent over-claiming significance in small datasets. |
| **Heterophily-aware GAT** | Standard GCNs fail on reaction graphs where the nucleophile and electrophile have dissimilar features. GAT allows the model to learn which neighbors to attend to, handling heterophily better. |
| **Streaming Data Loading** | Prevents OOM errors on the 7GB RAM GitHub Actions runner. |
| **SHAP for Interpretability** | Provides atomic-level resolution required to map to Hammett/Taft descriptors, unlike simple feature importance from tree models. |
| **Scaffold-based Split** | Ensures the model is tested on novel chemical scaffolds, preventing data leakage and over-optimistic performance estimates. |