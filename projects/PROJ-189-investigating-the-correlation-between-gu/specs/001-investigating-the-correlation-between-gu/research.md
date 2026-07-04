# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement

The project aims to determine if specific gut microbial genera are associated with cognitive decline in older adults, using public 16S rRNA sequencing data (American Gut Project) and cognitive assessment metadata (Health and Retirement Study). The primary challenge is the compositional nature of microbiome data, the potential non-random missingness of covariates, and the critical need to verify if the official datasets share a participant identifier for linkage.

## 2. Dataset Strategy

### 2.1 Verified Sources
The following datasets are used, sourced exclusively from the official, canonical repositories. No user-uploaded mirrors (e.g., HuggingFace) are cited.

| Dataset | Description | Source URL / ID | Usage |
|:--- |:--- |:--- |:--- |
| **AGP (Qiita)** | 16S rRNA taxonomic data (American Gut Project) | **Qiita Study ID**: `10317` (Official AGP repository). <br> Access: ` | Microbiome features (predictors). |
| **HRS (Official)** | Cognitive assessment scores and demographic metadata | **Health and Retirement Study**: `https://hrs.isr.umich.edu/data` (Requires Data Use Agreement). | Outcome variable (cognitive score) and covariates. |

**Note on Access**: The HRS dataset requires a formal Data Use Agreement (DUA) and is not publicly available as a raw Parquet file. The pipeline assumes the user has obtained the official HRS data files. If the official HRS data cannot be obtained, the project cannot proceed with the specified research question.

### 2.2 Dataset Fit & Variable Verification
**CRITICAL FEASIBILITY GATE**: The spec requires linking AGP and HRS via a "shared participant identifier".
- **AGP**: The official AGP dataset (Qiita 10317) uses anonymized sample IDs.
- **HRS**: The official HRS dataset uses HRS-specific participant IDs.
- **Gap Risk**: There is **no public record** of a shared participant ID between the standard AGP release and the HRS release. These are distinct cohorts with different recruitment protocols.
- **Decision**: The pipeline will first inspect the columns of the official datasets.
 - **If a shared ID exists**: Proceed with merge.
 - **If no shared ID exists**: The project **MUST TERMINATE** with a "Fatal Coverage Gap" report. The research question (linking *specific* AGP samples to *specific* HRS cognition) is unanswerable with public data.
 - **Scope Redefinition**: If the gate fails, the project is **CANCELLED**. A simulation study or synthetic merge is **NOT** permitted as it cannot validate the pipeline's ability to find real-world associations. The only valid alternative is to switch to a different dataset pair that actually contains linked microbiome and cognitive data (e.g., a specific longitudinal cohort study), which would require a new feature specification.
 - **No Synthetic Merge**: A "synthetic merge" of real AGP and real HRS data is **NOT** permitted as it creates mathematically invalid correlations.

### 2.3 Data Volume & Feasibility
- **RAM Limit**: 7 GB.
- **Strategy**:
 1. Load AGP and HRS in chunks if necessary.
 2. Filter for age ≥ 60 immediately after loading HRS.
 3. Perform merge. If resulting N < 500, log a warning (SC-001) but proceed with available data.
 4. For the Random Forest permutation test (multiple iterations), if memory usage exceeds 7 GB, the code will downsample the number of taxa (e.g., keep top 100 most abundant genera) or reduce permutations to a lower count, as per the "Edge Cases" in the spec.

## 3. Methodological Approach

### 3.1 Data Preprocessing (FR-001, FR-002)
1. **Ingestion**: Load AGP and HRS. Verify columns: `age`, `sex`, `BMI`, `cognitive_score`, `participant_id`.
2. **Merge**: Inner join on `participant_id`. **Abort if no overlap.**
3. **Filter**: Keep rows where `age` ≥ 60.
4. **Normalization**: Replace rarefaction with **Cumulative Sum Scaling (CSS)**. Rarefaction to minimum depth is rejected as it discards excessive data and introduces bias. CSS normalizes sequencing depth while preserving relative abundance information (FR-002).
5. **Aggregation**: Collapse OTUs/ASVs to Genus level.
6. **Imputation**: For missing covariates (BMI), use **MICE (Multiple Imputation by Chained Equations)**.
 - **Sensitivity Analysis (Delta-Adjustment)**: To address non-random missingness (MNAR), the plan implements a **Delta-Adjustment** sensitivity analysis.
 - **Scenario 1 (MAR)**: Standard MICE imputation.
 - **Scenario 2 (MNAR-Positive)**: Imputed values are increased by a delta (e.g., +1 SD) to simulate sicker participants having higher BMI but missing data.
 - **Scenario 3 (MNAR-Negative)**: Imputed values are decreased by a delta (e.g., -1 SD) to simulate sicker participants having lower BMI but missing data.
 - **Action**: The final model results are compared across these three scenarios. If the significance of key associations changes direction or magnitude significantly, the results are flagged as highly sensitive to the missingness mechanism. A simple "Missing Indicator" is insufficient; the delta-adjustment directly tests the bias in the imputed values.

### 3.2 Correlation Analysis (FR-003)
1. **Primary Method**: **SparCC (Sparse Correlations for Compositional Data)**.
 - **Justification**: CLR+Spearman is methodologically flawed for compositional data due to rank distortion from zero-inflation. SparCC models the underlying log-ratio variances and is robust to compositionality.
2. **Secondary Method (Robustness Check)**: **SPIEC-EASI (Sparse Inverse Covariance Estimation for Ecological Association Inference)**.
 - **Justification**: To address the compositional dependency (where a significant correlation for Taxon A may be a mathematical artifact of the depletion of Taxon B), SPIEC-EASI is used to infer a sparse inverse covariance network. This helps distinguish direct interactions from indirect correlations driven by the compositional constraint.
3. **Interpretation Constraint**: Results from SparCC and SPIEC-EASI are explicitly labeled as "associational" and "direct/indirect interaction estimates". The plan acknowledges that even SparCC cannot fully disentangle all compositional effects, and results are interpreted with this limitation in mind.
4. **Correction**: Apply Benjamini-Hochberg FDR correction to p-values.
5. **Output**: Table of significant associations ($q < 0.05$). Explicitly label as "associational".

### 3.3 Predictive Modeling (FR-004, FR-005, FR-006)
1. **Model**: Random Forest Regressor (`scikit-learn`).
2. **Split**: [deferred] train / [deferred] test.
3. **Cross-Validation**: **Nested Cross-Validation**.
 - **Inner Loop**: Hyperparameter tuning (`n_estimators`, `max_depth`) and feature selection.
 - **Outer Loop**: Performance evaluation.
 - **Rationale**: Prevents data leakage and overfitting in high-dimensional space.
4. **Evaluation**: R² and RMSE on hold-out set.
5. **Null Distribution**: Perform a sufficient number of permutations of the outcome variable.
 - **Multiple Testing Correction**: The model's R² must exceed the 95th percentile of the null distribution **adjusted using the Holm-Bonferroni method** on the p-values derived from the permutation distribution. This controls the Family-Wise Error Rate (FWER) given the high dimensionality of the feature space (~200-500 genera).
6. **Collinearity Check**: Calculate Variance Inflation Factors (VIF) on CLR-transformed data *before* model training.
 - **Action**: Features with VIF > 5 are **FLAGGED** (not removed) in the output.
 - **Rationale**: VIF is a linear diagnostic used to flag linear collinearity *before* training. The Random Forest model itself is robust to non-linear interactions and collinearity for prediction purposes. The two methods serve distinct roles: VIF for linear diagnostic flagging, RF for non-linear prediction.
7. **Interpretability**: Calculate **SHAP (SHapley Additive exPlanations)** values for feature importance. Rankings are archived alongside model metrics.
8. **Sensitivity**: Sweep rarefaction depth from [deferred] to `min_depth` (FR-005) as a robustness check, even though CSS is the primary method.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: Benjamini-Hochberg FDR applied to correlations; **Holm-Bonferroni** applied to permutation test p-values.
- **Power**: If the merged N < 100, a warning is issued. The plan acknowledges that low power may result in Type II errors.
- **Causality**: The study is observational. Claims are strictly limited to "association". No causal inference is made.
- **Collinearity**: Acknowledged that closely related taxa may be collinear. VIF analysis flags these; results are interpreted descriptively.
- **Measurement Validity**: Cognitive scores are assumed valid per HRS documentation. Microbiome data validity relies on the 16S rRNA protocol of AGP.
- **Missing Data**: MICE with **Delta-Adjustment** sensitivity analysis addresses non-random missingness (MNAR).
- **Compositional Dependency**: Acknowledged that CLR values are interdependent. SPIEC-EASI is used to attempt to distinguish direct vs. indirect effects, with explicit caveats on interpretability.

## 5. Compute Feasibility

- **Hardware**: CPU-only (2 cores, 7 GB RAM).
- **Libraries**: `scikit-learn` (CPU optimized), `scikit-bio`, `sparcc`, `shap`, `pymice`. No `torch`/`tensorflow` or GPU-specific code.
- **Runtime**:
 - Data loading/merging: < 30 mins.
 - Correlation (SparCC/SPIEC-EASI): < 45 mins.
 - Random Forest (Nested CV + 1000 permutations): Estimated 3-5 hours on 2 cores for N=500. If > 6h, the code reduces permutations or taxa count.
- **Memory**: Data is processed in a single dataframe. If > 6 GB, the pipeline will sample taxa or reduce the dataset size.