# Research: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

## Dataset Strategy

The project requires a dataset containing:
1. **Microbiome Data**: 16S rRNA OTU tables (relative abundances or counts) at baseline.
2. **Serology Data**: Antibody titers (e.g., HAI titers) pre- and post-vaccination.
3. **Metadata**: Subject IDs linking the two, and potentially covariates (age, sex).

### Verified Datasets

Based on the "Verified datasets" block provided in the prompt, the available sources are:

| Dataset Name | URL | Format | Suitability Assessment |
|:--- |:--- |:--- |:--- |
| **NCBI Disease** | ` | ZIP | **NOT SUITABLE**. This dataset contains text/clinical entity data for disease extraction, not microbiome or serology time-series. |
| **SRA (Wikipedia/BookCorpus)** | ` | Parquet | **NOT SUITABLE**. These are text corpora (Wikipedia/BookCorpus) mislabeled or misindexed in the verified list as "SRA". They contain no biological measurements. |
| **SRA (Imagenet)** | ` | Parquet | **NOT SUITABLE**. Image data. |
| **3D-CLR** | ` | JSON | **NOT SUITABLE**. Concept/semantic embeddings, not microbiome. |
| **bw_spec_cls_4_00_s_clr** | ` | Parquet | **POTENTIAL SUBSTITUTE**. The name suggests "spec" (spectrum/species?) and "clr". However, without metadata confirmation of *influenza serology* columns, it cannot be assumed to contain the required outcome variable (antibody titers). |
| **CLRS** | ` | Parquet | **NOT SUITABLE**. Algorithmic reasoning dataset (CLRS), not biological. |

**Critical Gap Identification**:
The provided "Verified datasets" block **does not contain a verified source** for the specific combination of *Gut Microbiome (16S)* and *Influenza Serology* required by the spec.
- The spec assumes the existence of "pre-processed 16S rRNA OTU tables and corresponding serology metadata from NCBI SRA".
- The verified list contains only text, image, or generic CLR concept data, none of which are known to contain the specific biological variables (taxa abundances + HAI titers) needed.

**Resolution Strategy**:
1. **Project Scope Redefinition**: The project is explicitly scoped as a **Methodological Framework & Pipeline Validation** study. If no real data is found (T010), the pipeline will execute on a synthetic dataset to validate the *code and statistical logic*, but **will not make biological claims**.
2. **Blocking Gate (T010)**: The implementation code will include a specific task (T010) to search for a real, open-access NCBI SRA study with paired 16S and serology data. If no such study is found, the pipeline proceeds to synthetic validation only.
3. **Synthetic Fallback (CI Only)**: If T010 fails (no real data found), the `ingestion.py` script will generate a **synthetic dataset** that mimics the statistical properties of the expected real data *only* to validate the pipeline code.
 - *Note*: Results derived from synthetic data are for **pipeline validation only** and cannot be used for scientific claims in the final paper. The Success Criteria (SC-003) are split: for synthetic data, the target is "Code Correctness"; for real data, the target is ">60% accuracy".
4. **Documentation**: `research.md` and `quickstart.md` will explicitly state that the current run uses a synthetic fallback or a specific subset of the verified data, and that the scientific conclusions are limited to the pipeline's ability to process such data, not the biological reality of the specific dataset.

## Statistical Methodology

### 1. Data Preprocessing
- **Filtering**: Subjects with missing `titer_pre` or `titer_post` are excluded (FR-001).
- **Zero-Replacement Strategy**: To handle zero-inflation in 16S data (which makes CLR undefined), a **multiplicative pseudo-count of 1e-6** is applied to all zero values before CLR transformation. This ensures the geometric mean is non-zero and the log-ratio is defined.
- **Compositional Correction**: Microbiome data is converted to relative abundance, then a **Centered Log-Ratio (CLR)** transformation is applied.
 - Formula: $clr(x_i) = \ln(\frac{x_i + \epsilon}{g(x + \epsilon)})$ where $g(x)$ is the geometric mean of the composition and $\epsilon = 1e-6$.
 - *Rationale*: Addresses the "sum constraint" of microbiome data to prevent spurious correlations (FR-002) and handles zero-inflation (Methodology Concern).
- **Outlier/Limit of Detection**: Titers below detection limit are imputed to $0.5 \times LOD$ (Assumption).

### 2. Correlation Analysis (FR-004, FR-005)
- **Test**: **Permutation-based Spearman Correlation**. Instead of relying solely on asymptotic p-values, the pipeline will generate an empirical null distribution by shuffling sample labels (1000 iterations) while preserving the compositional structure.
- **Multiple Testing**: Benjamini-Hochberg (BH) correction applied to these empirical p-values to control FDR at $\alpha=0.05$.
- **Significance**: Taxa are significant if $p_{adj} < 0.05$.
- **Robustness**: A **Bootstrap Stability** analysis will be performed to assess the consistency of significant taxa across resampled datasets.
- **Feature Selection**: Features for the model are selected based on BH-corrected p-values. If no taxa pass BH, the model falls back to a variance filter (unsupervised) to avoid selecting noise.

### 3. Predictive Modeling (FR-006, FR-007)
- **Model**: Random Forest Classifier (High vs. Low Responder).
- **Validation**: Nested k-Fold Cross-Validation.

The research question is [Research Question]. The method is nested cross-validation [Citation].
 - **Outer Loop**: 5 folds for performance estimation.
 - **Inner Loop**: Feature selection and hyperparameter tuning *strictly within* the training set of each outer fold.
- **Feature Selection Rigor**: To satisfy Constitution Principle VI and avoid tautology:
 1. **Global Unsupervised Filter**: A variance filter is applied to the *full* dataset (before splitting) to remove zero-variance taxa. This ensures a non-empty feature set for the model.
 2. **Supervised Selection**: Within each inner training fold, taxa are selected based on BH-corrected p-values from the correlation analysis.
 3. **Fallback**: If the inner fold yields zero significant features, the model falls back to the top-k taxa by raw magnitude from the *variance-filtered* set.
 4. **Primary Path**: The Random Forest is primarily trained on the **unsupervised variance-filtered features** to avoid data leakage from the outcome definition. The "top correlated taxa" approach is used only as a secondary exploratory analysis.
- **Power Limitation**: With N=50 and high dimensionality, power to detect significant correlations within a single fold is low. The variance filter ensures the model remains trainable.

### 4. Sensitivity Analysis (Threshold Sweep)
- **Requirement**: The sensitivity analysis (threshold sweep) must **re-run the outer fold splits and the null distribution permutation for *each* threshold** to preserve statistical rigor and prevent data leakage.
- **Outcome**: Stability of results (e.g., AUC) across thresholds is reported.

## Power Analysis & Sample Size
- **Limitation**: With N=50 and hundreds of taxa, the study is underpowered for definitive effect size estimation.
- **Reporting**: Effect sizes will be reported with wide confidence intervals. The target accuracy (>60%) is framed as a proof-of-concept for the pipeline (if real data exists), not a definitive biological claim.
- **Validation**: For synthetic data, the "Success Criterion" is "Code Correctness". For real data, it is ">60% accuracy".
- **Synthetic Validation Metric**: The synthetic data success metric is **Pipeline Correctness** (successful execution, no leakage, correct statistical distribution of synthetic noise), distinct from biological accuracy.

## Compute Feasibility

- **CPU-First**: The pipeline uses `scikit-learn` and `scipy` which are highly optimized for CPU.
- **Memory**: Streaming the dataset (if large) and processing taxa one-by-one for correlation ensures memory usage stays < 2 GB.
- **Runtime**: With N ≥ 50 and typical taxa counts (< 1000), the entire pipeline (ingestion -> correlation -> nested CV) is estimated to run in < 1 hour on a 2-core CPU.
- **No GPU Required**: Random Forest and Spearman correlation do not benefit significantly from GPU acceleration at this scale; GPU usage is not planned.

## Decision/Rationale

- **Why CLR?** Standard normalization fails for compositional data; CLR is the standard for microbiome correlation analysis.
- **Why Nested CV?** To prevent "double-dipping" where feature selection on the full dataset leaks information into the test fold, artificially inflating accuracy.
- **Why BH Correction in Feature Selection?** The "Unresolved concerns" explicitly flagged that selecting top taxa based on raw p-values introduces bias. We will enforce BH correction *before* selecting features for the model.
- **Why Synthetic Fallback?** No verified open dataset in the provided list contains the specific microbiome+serology pairing. The pipeline must be runnable on CI to validate the code, so a synthetic generator is used as a placeholder for the real data ingestion logic. **However, T010 is a blocking gate for real data.**
- **Why Zero-Replacement?** CLR is undefined for zeros; pseudo-counts ensure mathematical validity.
- **Why Variance Pre-filter?** To mitigate the risk of zero features selected in low-power folds and to ensure the model is trainable.
- **Why Permutation Testing?** To address the bias of standard correlation on compositional data with external variables.
- **Why Re-run Splits for Sensitivity?** To ensure that the sensitivity analysis does not reuse the same random seed or null distribution across different thresholds, which would invalidate the statistical comparison.