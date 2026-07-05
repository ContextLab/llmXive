# Research: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

## Dataset Strategy

The project relies on the **USPTO** reaction dataset. The spec requires reaction yields and SMILES strings.

| Dataset Name | Verified Source URL | Usage | Notes on Variable Fit |
|:--- |:--- |:--- |:--- |
| **USPTO Balanced** | ` | Primary Source | Contains SMILES and reaction classes. **Critical Check**: Must verify if `yield` column exists. If not, **HALT**. This dataset is labeled for classification (IPC codes), which creates a high risk of lacking the continuous `yield` variable required for regression. |
| **USPTO (Bing Yan)** | ` | Fallback | Contains reaction data. Must verify `yield` column and raw SMILES presence. Standard USPTO test sets often lack continuous yield distributions. |
| **USPTO Full** | ` | Fallback | Larger subset. Verify `yield` column and raw SMILES presence. |
| **RDKit Descriptors** | ` | **NOT USED FOR BASELINES** | Contains pre-computed descriptors. **Cannot** be used for Morgan fingerprints if raw SMILES are missing. The plan requires raw SMILES from the primary source to generate fingerprints locally. |

**Dataset Fit Analysis**:
The spec requires **reaction yield** (0-100%) as the target variable. The verified USPTO URLs provided are primarily for *classification* (IPC codes) or general reaction data.
- **Risk**: The verified URLs listed in the "Verified datasets" block are labeled as "classification" or "test" sets which may not contain the continuous `yield` variable required for regression (FR-001, FR-003).
- **Mitigation**: The implementation must first inspect the schema of the downloaded parquet file.
 - If `yield` is present: Proceed.
 - If `yield` is **missing**: The plan **cannot** proceed with regression as specified using *only* these verified sources. The spec assumes yield data exists (Assumption A-001). If the verified URLs lack yield, this constitutes a **fatal dataset mismatch**.
 - **Action**: The `download.py` script must validate the presence of the `yield` column immediately. If absent, the pipeline halts with a clear error: "Dataset does not contain required 'yield' column. Spec assumption A-001 violated."
- **Baseline Feasibility**: The Random Forest baseline requires raw SMILES to generate Morgan fingerprints. If the primary verified source (e.g., `ufukhaman`) lacks raw SMILES (or if the `yield` check passes but SMILES are missing), the RF baseline cannot be implemented. The plan explicitly requires the primary dataset to contain both `yield` and raw SMILES. If not, the project scope is reduced or halted.
- **Decision**: The plan assumes the `ufukhaman` or `bing-yan` dataset contains a yield column and raw SMILES. If the specific parquet file provided does not, the project scope (regression) is unachievable with the *verified* sources. The research phase must confirm this schema. **If the verified sources lack yield, the project cannot proceed.**

*Note: The "MPNN" and "MAE" datasets in the verified list are irrelevant for the training data itself (MPNN is an architecture, MAE is a metric).*

## Statistical Rigor & Methodological Choices

### 1. Multiple Comparison Correction
- **Context**: We are comparing three models (GNN, RF, LR) across multiple metrics (R², MAE, RMSE) using 5-Fold CV.
- **Method**: We will report all metrics. If formal hypothesis testing (e.g., paired t-tests on CV folds) is performed, we will apply **Bonferroni correction** for the number of comparisons (3 models * 3 metrics = 9 tests) to control family-wise error rate.
- **Status**: Deferring specific p-values to implementation; method is fixed.

### 2. Sample Size & Power
- **Constraint**: CPU-only limits dataset size.
- **Acknowledgement**: The project cannot guarantee high statistical power for small effect sizes due to the small subset size required for CPU feasibility.
- **Mitigation**: We will report the effective sample size, mean metrics, and **95% Confidence Intervals** for the R² improvement. The study is framed as a "feasibility and comparative analysis" rather than a definitive power study. The statistical significance test will be used to determine if the observed improvement is likely due to chance.

### 3. Causal Inference & Observational Nature
- **Nature**: The USPTO dataset is **observational** (historical reaction records).
- **Claim Limitation**: The model predicts *associational* yield based on structure. We **cannot** claim that a specific subgraph *causes* higher yield without a randomized experimental design.
- **Framing**: Results will be described as "predictive associations" and "feature importance," avoiding causal language. All GNNExplainer outputs will include a mandatory disclaimer stating that identified patterns are associational and may reflect dataset bias.

### 4. Measurement Validity
- **Yield**: Assumed to be accurately reported in the USPTO dataset (Assumption A-002).
- **Graph Features**: RDKit is the standard for chemical graph generation. Validity is assumed based on widespread community usage, but the plan includes a "Graph Validity" check (Constitution Principle VI) to filter invalid valences.

### 5. Predictor Collinearity
- **Baseline**: Morgan fingerprints (binary) vs. Descriptors (continuous).
- **GNN**: Learns features directly from graph topology.
- **Risk**: If we combine GNN and Baseline features, collinearity is high.
- **Strategy**: Models are trained **separately** on their respective feature sets. We do not combine them in a single model to avoid multicollinearity issues. Comparison is done at the metric level (R²), not feature level.

### 6. Data Leakage Prevention
- **Issue**: Simple random or class-based splits can leak information if identical molecules appear in train and test sets.
- **Strategy**: Implement a **Scaffold Split** (grouped by MurckoScaffold) to ensure that molecules in the test set share no scaffold with the training set. This is critical for evaluating generalization to new chemical spaces. The plan explicitly rejects simple reaction class stratification if it leads to leakage.

## Compute Feasibility Decision

- **Hardware**: GitHub Actions Free Tier (standard CPU allocation, 7GB RAM).
- **Strategy**:
 - **Data**: Sample to [deferred] - [deferred] reactions. This fits in RAM for graph conversion.
 - **Model**: MPNN with a configurable number of message passing layers, hidden dim 64.
 - **Training**: A maximum number of epochs per fold will be determined during the implementation phase to prevent overfitting while ensuring convergence., early stopping.
 - **Libraries**: `torch` (CPU), `torch-geometric` (CPU).
- **Rationale**: Deep learning on CPU is slow. A small subset and shallow network are the only way to meet the CI limit while maintaining a valid GNN architecture. This is an approximation of the full-scale study, acceptable for the "feasibility" stage.
