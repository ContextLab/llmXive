# Research: Predicting Molecular Permeability Coefficients Using Graph Neural Networks

## 1. Problem Definition
The objective is to determine whether Graph Neural Networks (GNNs) provide a statistically significant improvement over classical machine learning baselines (Random Forest) in predicting molecular properties. **Scope Pivot**: Due to the absence of verified datasets containing *experimental* permeability coefficients, this study is framed as a **Feasibility Study**. The target variable is **calculated logP** (a standard molecular descriptor derived from SMILES). This allows validation of the GNN pipeline's ability to learn structure-property relationships (topology) compared to a baseline using standard descriptors. The core hypothesis remains: GNNs capture topological nuances (substructures, connectivity) that standard molecular descriptors (MW, logP, TPSA) miss, even when the target is a descriptor itself.

## 2. Dataset Strategy

### 2.1 Verified Datasets
The following datasets are the **only** sources used for this project, as verified by the "Verified datasets" block:

| Dataset Name | Source URL | Format | Relevance |
|:--- |:--- |:--- |:--- |
| **ChEMBL-derived Descriptors** | ` | Parquet | Contains SMILES and standard RDKit descriptors (MW, logP, TPSA, etc.). **Target**: `logP` (calculated). |
| **Half-ChEMBL Descriptors** | ` | Parquet | Larger subset with similar descriptors. **Target**: `logP` (calculated). |
| **SMILES Transformers** | ` | Parquet | SMILES strings, may lack specific permeability targets. |
| **SELFormer SMILES** | ` | CSV | SMILES strings. |
| **TPSA/GRAPO** | ` | Parquet | Specific descriptors (TPSA, HBA, HBD). |

### 2.2 Critical Gap Analysis & Pivot
**Status**: **CRITICAL MISMATCH DETECTED** (Resolved via Pivot).
- **Requirement**: The study requires a dataset with **SMILES strings** AND **experimental permeability coefficients** (e.g., logP, permeability across polymeric membranes).
- **Verified Source Check**:
 - The `fabikru/chembl-2025...` datasets contain SMILES and *standard descriptors* (MW, logP, TPSA), but **do not contain experimental permeability coefficients**. They are likely pre-computed feature sets.
 - The `maykcaldas/smiles-transformers` and `HUBioDataLab/SELFormer-smiles` datasets contain SMILES but lack the specific permeability target column required for supervised learning.
 - The `Alan123` dataset focuses on specific descriptors (TPSA) but lacks the target.
 - The `nist_800_53` datasets are security/IT standards, not chemical data.
- **Conclusion**: **None of the verified datasets contain the required target variable (experimental permeability coefficients).**
- **Action Plan (Pivot)**:
 1. The pipeline will **Switch to Proxy Mode**.
 2. The target variable will be set to the **calculated `logP`** column (if present in the dataset) or a synthetic proxy derived from standard descriptors.
 3. The study will be explicitly framed as a **Feasibility Study** to validate the GNN pipeline's ability to learn the logP formula from SMILES, rather than predicting experimental permeability.
 4. A strong disclaimer will be included in the final report: "This study uses calculated logP as a proxy target. Results validate the GNN pipeline's topological learning capabilities but do not directly predict experimental permeability."
 5. The bias check (FR-013) will be expected to show high correlation (|r| > 0.85) due to the proxy nature, which will be flagged as "Expected for Proxy" rather than an error.

*Note: If the "Verified datasets" block is incomplete or if the user intended to provide a specific permeability dataset that was not listed, this plan will fail the "Dataset-variable fit" check. The implementation will strictly check for the presence of a target column and switch to proxy mode if missing.*

### 2.3 Data Volume & Streaming
- The `fabikru` datasets are likely < 1GB. Streaming is not strictly required but will be enabled for robustness.
- If the dataset size > 7GB, the pipeline will switch to `streaming=True` and perform online statistics accumulation.

## 3. Methodology

### 3.1 Feature Engineering
- **Input**: SMILES strings.
- **Graph Construction**: RDKit `MolFromSmiles`. Atoms = nodes, Bonds = edges.
- **Standard Descriptors**: MW, logP (calculated), TPSA, HBA, HBD, Rotatable Bonds, etc. (via RDKit `Descriptors`).
- **Graph Features**: Node features = atomic number, degree, hybridization, formal charge, aromaticity. Edge features = bond type, conjugation.
- **Ablation Features**: For the Random Forest ablation baseline, a flattened vector of graph statistics (e.g., mean node degree, graph connectivity, substructure counts) will be derived from the GNN graph.

### 3.2 Model Architectures
- **GNN (MPNN)**:
 - Architecture: 3-layer Message Passing Neural Network.
 - Aggregation: Mean/Sum.
 - Readout: Global mean pooling.
 - Hardware: CPU (PyTorch Geometric).
- **Random Forest**:
 - Input: Vector of standard descriptors (Baseline) and graph-derived features (Ablation).
 - Parameters: `n_estimators=100`, `max_depth=None`.

### 3.3 Training Strategy
- **Split**: 80/20 stratified by "polymer type" (if available) or random.
- **Optimization**: Adam (GNN), Default (RF).
- **Early Stopping**: Patience = 5 epochs on validation loss.
- **GPU Escape Hatch**: If `torch-geometric` fails on CPU due to memory, attempt to run a **single epoch** on a small subset (100 samples) on a Kaggle GPU (if the CI runner supports offload). *Note: Standard CI free tier has no GPU. If the model fails on CPU, the plan is to reduce complexity (fewer layers) or sample size, not to offload unless the execution agent detects a specific CUDA error and triggers the escape hatch.*

### 3.4 Evaluation & Statistics
- **Metrics**: RMSE, MAE, R².
- **Statistical Test**: Paired t-test on prediction errors (GNN vs. RF).
- **Significance**: p < 0.05.
- **Bias Check**: Correlation between input descriptors and target (FR-013). High correlation is expected for the proxy target and will be flagged as "Expected for Proxy".

#### 3.4.1 Statistical Power & Effect Size Analysis
**Addressing Methodology Concerns**:
- **Power Limitation**: Given the estimated dataset size (likely < 500 valid samples after cleaning), the study is explicitly acknowledged as **underpowered** to detect small effect sizes (e.g., Cohen's d < 0.2) with high confidence (80% power).
- **Mitigation Strategy**:
 1. **Effect Size Reporting**: The analysis will report **Cohen's d** (standardized mean difference of errors) alongside p-values. This quantifies the magnitude of the GNN's improvement regardless of statistical significance.
 2. **Confidence Intervals**: 95% Confidence Intervals for the difference in RMSE/MAE will be calculated to provide a range of plausible effect sizes.
 3. **Post-Hoc Power Calculation**: A post-hoc power analysis will be performed using the observed effect size and sample size, reported transparently in the results.
 4. **Framing**: Results will be framed as **exploratory feasibility**. A non-significant p-value will not be interpreted as "no difference" but rather as "insufficient evidence to detect a difference given the sample size."
 5. **Threshold Adjustment**: If the dataset is extremely small (< 100), the t-test may be replaced or supplemented with non-parametric tests (Wilcoxon signed-rank) to ensure robustness against non-normal error distributions, though the t-test remains the primary metric for consistency with FR-007.

## 4. Risks & Mitigations
- **Risk**: No experimental permeability data in verified sources.
 - **Mitigation**: Pivot to calculated logP proxy; frame as Feasibility Study.
- **Risk**: GNN overfitting on small dataset.
 - **Mitigation**: Early stopping, dropout, small architecture.
- **Risk**: Invalid SMILES.
 - **Mitigation**: RDKit error handling, logging, exclusion.
- **Risk**: Memory overflow.
 - **Mitigation**: Streaming, batch processing, CPU-only optimization.
- **Risk**: High bias due to proxy target.
 - **Mitigation**: Explicitly flag high correlation as "Expected for Proxy" and document in the report.
- **Risk**: Low statistical power due to small sample size.
 - **Mitigation**: Report effect sizes (Cohen's d) and confidence intervals; frame conclusions as exploratory; perform post-hoc power analysis.