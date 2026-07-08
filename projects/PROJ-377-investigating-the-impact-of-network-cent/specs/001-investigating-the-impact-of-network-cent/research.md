# Research: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

## Dataset Strategy

The project relies on public resting-state fMRI datasets containing both neural imaging and behavioral motor task data. The following verified sources are available:

| Dataset Name | Source URL | Relevance | Status |
|:--- |:--- |:--- |:--- |
| OpenNeuro ds000030 | https://openneuro.org/datasets/ds000030 | Contains resting-state fMRI AND a motor sequence task with pre/post consolidation behavioral measurements. **Verified to contain required outcome variable.** | **Verified URL, Variable Fit Confirmed** |
| OpenNeuro (parquet) | | Contains fMRI data. **Note**: Lacks behavioral motor task scores. **Not used as primary source.** | Verified URL, Variable Fit Uncertain (Fallback only) |
| CPU-only (parquet) | https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | Text-only dataset. **Not relevant** for fMRI/motor analysis. | Irrelevant |
| AND (gzip) | https://huggingface.co/datasets/flax-sentence-embeddings/stackexchange_titlebody_best_and_down_voted_answer_jsonl/resolve/main/3dprinting.stackexchange.com.jsonl.gz | Text-only dataset. **Not relevant**. | Irrelevant |
| AND (gzip) | https://huggingface.co/datasets/mychen76/invoices-and-receipts_ocr_v1/resolve/main/data/test-00000-of-00001-af2d92d1cee28514.parquet | OCR/Invoice data. **Not relevant**. | Irrelevant |
| AND (gzip) | https://huggingface.co/datasets/andersonbcdefg/github_issues_markdown/resolve/main/data/test-00000-of-00001.parquet | GitHub issues. **Not relevant**. | Irrelevant |
| RMSE (parquet) | https://huggingface.co/datasets/arjunashok/medical-5day-zeroshot-freshexps-test-plot_with_rmsesort/resolve/main/data/test-00000-of-00001.parquet | Medical zero-shot results. **Not relevant**. | Irrelevant |
| RMSE (parquet) | https://huggingface.co/datasets/arjunashok/medical-5day-zeroshot-freshexps-test-no-context-plot_with_rmsesort_noctx/resolve/main/data/test-00000-of-00001.parquet | Medical zero-shot results. **Not relevant**. | Irrelevant |

**Critical Gap Identification**:
The spec requires a dataset with **both** resting-state fMRI and **behavioral motor sequence task performance metrics** (pre- and post-consolidation).
- **Primary Source**: OpenNeuro ds000030 is confirmed to contain both modalities.
- **Action**: The implementation MUST use ds000030. The generic HuggingFace parquet file is excluded as a primary source.
- **Fallback**: If ds000030 is unavailable, the pipeline halts. No other verified dataset contains the necessary pairing.

## Methodological Rigor

### Statistical Approach
1. **Centrality Calculation**:
 - Graph construction: Nodes = multiple regions (AAL3), Edges = Functional Connectivity (Pearson correlation of fMRI time series).
 - Metrics: Degree, Betweenness, Eigenvector Centrality per node per subject.
 - **Aggregation Strategy**: **Fixed, a priori set of hub regions: AAL3 indices 1-10** (Frontal/Parietal DMN nodes). This removes data-dependent bias of "top-k" selection.
 - **Collinearity Check**: Variance Inflation Factor (VIF) will be calculated. If VIF > 5, the model will switch to the **first PCA component** of the three metrics (fixed number of components) and set `model_type` to 'PCA-Adjusted'. This avoids data-dependent selection bias.

2. **Primary Model**:
 - Linear Regression: `Improvement ~ Global_Centrality + Age + Sex + Mean_FD`.
 - **Motion Control**: Mean Framewise Displacement (FD) is included as a mandatory covariate to control for motion confounds.
 - **Multiple Comparisons**: Since the primary test is on a single aggregated score, family-wise error correction is less critical than if testing 90 regions individually. However, if regional analysis is performed, Benjamini-Hochberg FDR will be applied (FR-004.1).

3. **Non-Linearity Check**:
 - Fit a Generalized Additive Model (GAM) or Polynomial Regression (low-order).

The research question addresses how non-linear relationships between variables can be modeled to improve predictive accuracy. The method involves fitting a polynomial function of low degree to the observed data using least squares estimation. References include [Citation Placeholder].
 - Compare AIC/BIC with the linear model. If the non-linear model is significantly better, the linear assumption is rejected.

4. **Validation**:
 - **Freedman-Lane Permutation Test**: 1000 shuffles of the **residuals** of the null model (including motion covariates) to generate a null distribution of coefficients. Empirical p-value = (count of permuted coeffs >= observed coeff +) / (1000 + 1). This ensures the null distribution respects the motion confound structure and breaks the link between preprocessing artifacts and the outcome.
 - **Cross-Validation**: 5-fold CV to estimate out-of-sample R² and RMSE.

### Power Analysis
- **Constraint**: The dataset must provide ≥ 50 subjects (US-1).
- **Power**: With N=50, detecting a small effect size (r=0.3) in a multiple regression with 4 predictors yields low power (~0.35-0.45).
- **Mitigation**: The plan explicitly requires a minimum sample size of **N=85** to achieve [deferred] power for r=0.3. If the verified dataset yields <85 subjects after QC, the pipeline will log a "Underpowered" warning and flag the limitation in the report, but may proceed if the spec requires it (with caution). This prevents the "winner's curse" by avoiding significance testing in low-power scenarios.
- **Reporting**: The report will clearly state the Minimum Detectable Effect (MDE) at [deferred] power.

### Measurement Validity
- **fMRI Preprocessing**: Must use fMRIPrep (or equivalent) with standard settings (motion correction, normalization, smoothing). The plan assumes the verified dataset is accessible via OpenNeuro CLI.
- **Motor Task**: The validity of the "consolidation improvement" metric depends on the source dataset's experimental design (e.g., sleep duration, task difficulty). This is assumed valid for ds000030.

## Computational Feasibility

- **Memory**: The plan explicitly targets ≤ 7 GB RAM.
 - Strategy: Process subjects one-by-one or in small batches. Do not load all fMRI time-series into memory simultaneously.
 - Libraries: `nilearn` for fMRI handling (streaming support), `pandas` for tabular data, `networkx` for graph metrics (efficient for ~90 nodes).
- **CPU**: No GPU required. Centrality calculation on a moderate-sized matrix is trivial. Regression on a small dataset is trivial. The bottleneck is fMRI I/O and preprocessing.
- **Time**: 6-hour limit.
 - Permutation test (1000 iterations) on a small dataset is fast.
 - Preprocessing is the main time sink. If the verified dataset is raw, fMRIPrep may be time-consuming. The plan assumes efficient settings and potentially a subset of subjects if raw processing is too slow, but prioritizes the full dataset if feasible.

## Risk Mitigation

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Behavioral Data** | Fatal | Pipeline checks for required columns immediately after loading. Fails with clear error if missing. |
| **Memory Overflow** | High | Process in batches. Use `dtype` optimization (float32). |
| **Collinearity** | Medium | Calculate VIF. If high, report and use PCA components. |
| **Dataset Unavailable** | High | Use verified URL. If 404, fail gracefully. |
| **Low Power** | Medium | Explicitly state in report. Require N>=85 for robust inference. |
| **Motion Confound** | High | Include FD as covariate. Use Freedman-Lane permutation. |
