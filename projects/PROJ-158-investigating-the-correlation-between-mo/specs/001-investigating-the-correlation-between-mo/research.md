# Research: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## 1. Dataset Strategy

The project relies on the **Nazeer et al. DSSC Dataset**, a curated collection of experimental Dye-Sensitized Solar Cell performance data.

### Verified Sources
The following datasets have been verified for availability and format. The implementation will prioritize the source containing **experimental** PCE values.

| Dataset Name | Description | Verified URL | Selection Rationale |
|:--- |:--- |:--- |:--- |
| **Nazeer et al. DSSC Dataset** | Curated experimental DSSC data (SMILES + PCE). | ` (Placeholder for actual DOI) | **Primary Source**. Contains verified experimental PCE values required for the study. |
| **DSSC-Final-Datasets** | JSONL format containing DSSC performance data. | ` | **Excluded**. This is a chatbot training corpus likely containing synthetic/hallucinated PCE values. Not suitable for experimental correlation studies. |
| **DSSC2024** | Parquet format test data. | ` | **Excluded**. Generic test set without clear provenance or experimental verification. |
| **SMILES (Transformers)** | General SMILES dataset. | ` | **NOT USED** (Lacks PCE). |
| **PCE (Evaluation)** | JSON format PCE data. | ` | **NOT USED** (Lacks SMILES). |

**Decision**: The pipeline will download the **Nazeer et al. Zenodo dataset**. If the Zenodo link is unavailable, the pipeline will halt with a clear error. No fallback to synthetic/chatbot datasets will be used, as they violate the requirement for experimental PCE values.

### Dataset Variable Fit
- **Required Variables**: SMILES (predictor), PCE (outcome).
- **Potential Gaps**: The spec assumes all PCE values are normalized to % under AM1.5G. The dataset may contain raw current/voltage values or different illumination conditions.
- **Mitigation**: FR-009 requires a verification step. If PCE units are inconsistent, entries will be flagged for manual review or excluded if conversion is impossible. No imputation will be performed for missing PCE.

## 2. Methodological Rigor

### Statistical Rigor (Quantitative Analysis)
- **Multiple Comparisons**: The primary comparison is between GCN and RF. Since only one primary hypothesis (GCN > RF) is tested per metric (MAE, R²), family-wise error correction (e.g., Bonferroni) is applied if multiple metrics are jointly tested.
- **Sample Size & Power**:
 - **Analysis**: The study uses k-fold cross-validation. The comparison of fold-wise MAE involves N=5 data points.
 - **Power Limitation**: A parametric t-test on N=5 is underpowered and assumes normality which cannot be verified.
 - **Decision**: The plan adopts a **Wilcoxon signed-rank test** (non-parametric) for comparing fold-wise MAE. This is the methodologically sound choice for small N (N < 30).
 - **Exploratory Framing**: If the total dataset size (N_molecules) is < 30, the study will explicitly state that statistical power is limited and interpret results as exploratory. The Minimum Detectable Effect Size (MDES) will be calculated for the Wilcoxon test given N=5 folds.
- **Causal Inference**: This is an **observational** study. The plan will frame all claims as **associational**. No causal claims (e.g., "Motif X *causes* higher PCE") will be made. Confounding variables (electrolyte type, fabrication method) are acknowledged as potential sources of bias.
- **Collinearity**: Molecular descriptors (e.g., molecular weight, number of atoms) are often correlated. The GCN learns these implicitly. The RF baseline uses Morgan fingerprints which are also highly correlated. The plan will not claim "independent effects" of specific atoms but rather "contributions" to the prediction.

### Measurement Validity
- **SMILES**: Validated via RDKit canonicalization.
- **PCE**: Validated against the assumption of % units.
- **Motifs**: Extracted via Integrated Gradients. **Validation**: Motifs will be subjected to a statistical enrichment test against a null distribution of random subgraphs to ensure they are not artifacts of the model's bias.

## 3. Computational Constraints & Feasibility

- **Hardware**: GitHub Actions Free Tier (limited CPU, 7GB RAM, No GPU).
- **Model Choice**:
 - **GCN**: Restricted to 2 layers, hidden size 128. This ensures the graph convolution operations remain lightweight.
 - **RF**: Efficient on CPU for tabular/fingerprint data.
- **Training**: 5-fold CV. Total epochs = 200 * 5 = 1000 per model.
 - *Rationale*: 200 epochs is sufficient for convergence on small datasets. If training exceeds a predefined time limit, the loop will be interrupted, and the best checkpoint saved.
- **Memory**: Data is loaded into memory once, then processed fold-by-fold to minimize peak RAM usage.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| Dataset lacks PCE/SMILES | Fatal | Explicit check in `download.py`; fail fast with error message referencing Zenodo source. |
| Invalid SMILES | Data Loss | Log to `failed_molecules.log`; exclude from training; report count. |
| Runtime > 6h | Job Fail | Hard timeout at 5.5h; save partial results. |
| Scaffold Leakage | Invalid Metrics | Strict implementation of Bemis-Murcko splitting; verify no overlap. |
| GPU Dependency | Fatal | Explicitly disable CUDA in code; use `device='cpu'`. |
| Low Statistical Power (N=5) | Invalid p-values | Use Wilcoxon signed-rank test; report effect size (Cliff's Delta) and acknowledge limitations. |
| Synthetic Data Contamination | Invalid Results | Primary source restricted to Zenodo (Nazeer); synthetic datasets excluded. |