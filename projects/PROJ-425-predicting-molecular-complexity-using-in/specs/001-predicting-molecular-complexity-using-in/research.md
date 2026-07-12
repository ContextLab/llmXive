# Research: Predicting Molecular Complexity Using Information Theory

## Overview

This research phase validates the feasibility of the data sources, confirms the variable fit, and outlines the statistical methodology to ensure the study meets the rigorous requirements of the specification and constitution.

## Dataset Strategy

The specification requests molecules from "PubChem CID 1-5000". Direct API access for [deferred] individual requests is prone to rate limiting and timeout failures on free-tier CI runners. Furthermore, the verified HuggingFace dataset (`sagawa/pubchem-10m-canonicalized`) does not contain a contiguous range of CIDs 1-5000. To satisfy **Constitution Principle III (Data Hygiene)** and **Principle I (Reproducibility)**, and to avoid the selection bias of early CIDs, we will use a **stratified random sample** from the verified dataset.

| Dataset Name | Description | Verified URL | Selection Rationale |
|:--- |:--- |:--- |:--- |
| **PubChem 10M Canonicalized** | Large-scale dataset of canonicalized SMILES and CIDs from PubChem. | ` | Contains the required `smiles` and `cid` fields. Pre-canonicalized SMILES ensures consistent LZ compression. We will use a **stratified random sample** of [deferred] valid entries to ensure chemical diversity and representativeness, addressing the bias concern of CID 1-5000. |

**Variable Fit Verification**:
- **Required**: `smiles` (string), `cid` (int).
- **Derived**: `shannon_entropy` (graph), `lz_length` (string), `sa_score` (RDKit), `qed_score` (RDKit).
- **Fit**: The dataset provides the raw `smiles` and `cid`. All other variables are computable via RDKit. **No mismatch exists.**

**Data Loading Strategy**:
- Use `datasets.load_dataset` or `pandas.read_parquet` with `columns=['smiles', 'cid']` in **chunks** to minimize memory overhead during the initial load.
- **Checksum**: A checksum of the downloaded file will be computed and recorded in `state/` to satisfy Constitution Principle III.
- **Sampling**: A stratified random sample of [deferred] valid rows (where `smiles` is not null and can be converted to an RDKit Mol object) will be extracted.
- **Citation Verification**: The Reference-Validator Agent will verify the dataset URL before execution to satisfy Constitution Principle II.

## Statistical Methodology

### 1. Metric Computation
- **Shannon Entropy**: Calculated on the distribution of vertex degrees in the molecular graph (adjacency matrix derived from RDKit).
 - **Normalization**: To address the confounding by molecular size, we will compute **Per-Atom Entropy** ($H / N_{atoms}$) in addition to raw entropy.
 - $H = -\sum p(d) \log_2 p(d)$, where $p(d)$ is the frequency of degree $d$.
- **Lempel-Ziv (LZ)**: Compressed byte length of the canonical SMILES string.
 - Use `zlib.compress(smiles.encode('utf-8'))` and take `len()`.
 - **Note**: This measures the complexity of the *canonical SMILES representation*, not the absolute graph complexity. The specific RDKit version for canonicalization is recorded.
 - **Raw SMILES and LZ length are stored side-by-side** in the processed CSV for verification.
- **SA & QED**: Standard RDKit implementations (`rdkit.Chem.QED.default` and `rdkit.Chem.QED.descriptors`).

### 2. Correlation Analysis
- **Primary Method**: Pearson correlation coefficient ($r$) and p-value.
- **Robustness Check**: **Spearman's rank correlation** will be computed for all pairs to account for non-normal distributions and non-linear relationships.
- **Pairs**: (Entropy, SA), (Entropy, QED), (LZ, SA), (LZ, QED).
- **Framing**: Explicitly labeled as **associational**. No causal claims.
- **Partial Correlation**: To address the circular validation risk (SA includes a topological complexity term), we will compute **partial correlations** controlling for **molecular weight** or **atom count**. This tests whether information-theoretic measures provide *incremental* predictive power beyond standard size metrics.

### 3. Robustness & Validation
- **Bootstrap Resampling**: 1,000 iterations.
 - Resample rows with replacement.
 - Recalculate $r$ for each iteration.
 - Compute 95% Confidence Interval (CI) using the percentile method (2.5th and 97.5th percentiles).
- **Multiple-Comparison Correction**:
 - Apply **Bonferroni correction** (or Holm-Bonferroni) to the four p-values.
 - Adjusted $\alpha = 0.05 / 4 = 0.0125$.
- **Collinearity Handling**:
 - Compute correlation between Entropy and LZ.
 - Calculate **Variance Inflation Factors (VIF)** if both are considered in a joint model.
 - **Strategy**: If VIF is high (>5), the study will **not** use them as joint predictors. Instead, they will be reported as **distinct definitions of complexity** (graph topology vs. string redundancy), and their individual correlations with SA/QED will be compared.

### 4. Timeout & Error Handling
- **Per-Molecule Timeout**: A reasonable timeout is enforced for each molecule's processing (graph conversion, metric calculation).
- **Retry Mechanism**: A retry mechanism with exponential backoff (max 3 attempts) is implemented for dataset loading to satisfy the robustness intent of FR-001.
- **Logging**: Timeouts and invalid entries are logged and skipped, with counts reported in the final output.

### 5. Success Criteria Mapping
- **SC-001/002**: Correlation $r > 0.5$ (hypothesized).
- **SC-003**: 95% CI does not include zero.
- **SC-004**: Adjusted p-value < 0.05.
- **SC-005/006**: Runtime < 45 min, Memory < 4 GB (enforced by chunking and sampling).

## Decision Log

| Decision | Rationale | Impact |
|:--- |:--- |:--- |
| **Use HuggingFace PubChem dataset** | Avoids API rate limits and ensures reproducibility. | High reliability, no external API dependency during CI. |
| **Stratified Random Sample** | Avoids selection bias of CID 1-5000; ensures representativeness. | Results generalize better to chemical space. |
| **Per-Atom Entropy & Partial Correlation** | Addresses confounding by molecular size and circular validation risk. | More accurate assessment of incremental predictive power. |
| **Spearman Correlation** | Robust to non-normal distributions of complexity metrics. | Valid p-values for non-Gaussian data. |
| **Collinearity Handling (VIF)** | Prevents unstable estimates from highly correlated predictors. | Clearer interpretation of distinct complexity definitions. |
| **Use Bonferroni Correction** | Conservative control of Family-Wise Error Rate (FWER). | Reduces Type I errors; aligns with SC-004. |
| **Frame as Associational** | Observational study; no randomization. | Prevents causal overreach; aligns with US-1 acceptance criteria. |
| **Timeout & Retry Logic** | Ensures robustness against hangs and transient failures. | Prevents CI job failures. |
| **Checksum & Citation Verification** | Satisfies Constitution Principles II and III. | Ensures data integrity and accuracy. |
