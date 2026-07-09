# Research: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Problem Statement & Research Question

**Question**: Can publicly available proteomic datasets from plants subjected to abiotic stresses (drought, salinity, heat) be used to train machine learning models that predict stress-responsive gene expression patterns in novel, unseen conditions?

**Hypothesis**: Proteomic profiles under specific abiotic stresses contain stable, stress-specific signatures that correlate with downstream gene expression patterns, allowing for predictive modeling even when tested on different stress conditions (cross-stress generalization), though performance may degrade compared to within-stress prediction.

## 2. Verified Datasets & Data Strategy

*Note: Only the URLs listed in the "Verified datasets" block of the user message are cited. No URLs are invented.*

### 2.1 Data Sources

The project targets **NCBI GEO** and **ProteomeXchange** for paired proteomic and transcriptomic data. However, the "Verified datasets" block provided for this project does not contain direct URLs for NCBI GEO or ProteomeXchange raw plant stress datasets. The available verified sources are:

- **NCBI (zip)**: ` (Note: This is a dummy dataset for disease, not plant stress. It serves as a placeholder for the ingestion pipeline structure but **cannot** be used for the actual biological analysis).
- **GEO (parquet)**: ` (Note: This is a general GEO dataset, not specifically plant stress. It may be used for testing the *ingestion logic* if the schema matches, but biological validity requires specific plant stress metadata).
- **ProteomeXchange**: NO verified source found.

### 2.2 Dataset Strategy & Mismatch Handling

**Critical Mismatch**: The spec requires **paired** proteomic and transcriptomic data for **Arabidopsis, rice, or wheat** under **drought, salinity, or heat**. The verified dataset block contains **NO** verified source for such paired plant stress data. The available GEO/NCBI links are either dummy data or general datasets not guaranteed to contain the specific species/stress pairs required.

**Resolution Strategy & Execution Path**:
1. **Ingestion Phase**: The `ingest.py` script will attempt to download data from the verified URLs to test the pipeline.
2. **Validation Phase**: If the downloaded data does not contain the required species/stress metadata (i.e., no valid paired plant stress data), the pipeline will execute the **Data Unavailable Path**:
 - **Action**: HALT biological modeling (SC-001, SC-002).
 - **Output**: Generate a report stating "Data Unavailable: No valid paired plant proteomic/transcriptomic data found in verified sources."
 - **Metrics**: Report SC-004 (Data Completeness) as [deferred] or "N/A".
 - **Status**: Project terminates without producing biological results.
3. **Fallback (If Valid Data Exists)**:
 - **If n < 50 per fold**: Switch to **Leave-One-Out Cross-Validation (LOOCV)** and flag results as "Exploratory/High-Variance".
 - **If n >= 50**: Proceed with **5-fold Cross-Validation**.

**Decision**: The plan proceeds with the assumption that the *pipeline* can be built and tested on the available (albeit mismatched) data to validate the *ingestion logic*, but the **biological results (SC-001, SC-002) are contingent on the existence of valid data**. If no valid data is found, the project will report "Data Unavailable" rather than producing invalid biological conclusions on dummy data.

## 3. Methodology

### 3.1 Data Preprocessing

1. **Ingestion**: Download raw files. Filter for species (Arabidopsis, Rice, Wheat) and stress (Drought, Salinity, Heat).
2. **Normalization**: Log2 transform protein abundance matrices.
3. **Filtering**: Remove proteins detected in < 50% of samples within a stress condition (FR-002).
4. **Imputation**: Apply Left-Censored Missing (LCM) imputation for remaining missing values (FR-002).
5. **Identifier Mapping**: Use `biomaRt` (current version) to map protein IDs to gene IDs. Drop rows with no match (FR-003).
6. **Merging**: Create a unified matrix with protein abundances (features) and gene expression (target).

### 3.2 Modeling Strategy

- **Algorithms**: `RandomForestRegressor` and `SVR` (scikit-learn).
- **Validation**:
 - **Within-Stress**: 5-fold Cross-Validation (or LOOCV if n<50) on data from a single stress type.
 - **Cross-Stress**: Train on Stress A, Test on Stress B (e.g., Drought -> Salinity).
- **Controls**:
 - **Null Model**: Predict mean expression value.
 - **Raw Feature Baseline (Task T020)**: Train a model using only protein features, ignoring stress labels. This establishes the baseline correlation between proteome and transcriptome.
 - **Stress-Shuffled Baseline (Task T021)**: Train a model where stress labels are randomly shuffled *before* the cross-stress test. This tests the null hypothesis that "stress identity is the sole driver of prediction".
- **Metrics**: R², RMSE, Feature Importance.
- **SC-002 Calculation**: The "drop in R²" is calculated as `Drop = R²(Within-Stress Model) - R²(Raw Feature Baseline)`. This quantifies the improvement provided by stress-specific modeling over general proteome-expression correlation. The Shuffled Baseline (T021) is used to verify that the model is not simply memorizing stress labels.

### 3.3 Statistical Rigor

- **Multiple Comparisons**: If testing multiple stress pairs, apply a **Permutation Test** to derive p-values for the R² drops.
 - **Null Hypothesis**: The distribution of R² differences between within-stress and cross-stress splits is zero.
 - **Permutation**: Stress labels are permuted within the paired sample set repeatedly.
 - **Correction**: Bonferroni correction applied to p-values.
- **Power**: Acknowledge that sample sizes are limited by public data availability. If n < 50, switch to LOOCV and flag results as "Exploratory".
- **Causality**: All claims are strictly **associational**. No causal inference is made.
- **Collinearity**: Feature importance will be reported with a caveat that correlated proteins may share importance scores.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, multi-GB RAM).
- **Memory**: Data will be processed in chunks if necessary. Models are CPU-optimized.
- **Time**: Target < 6 hours. Early stopping implemented if runtime > 4.5 hours.
- **Data Constraint**: If no valid paired data is found, the pipeline terminates early, saving compute resources.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No Paired Data** | Critical: Cannot train model. | **HALT** biological modeling. Report "Data Unavailable". Use dummy data only for pipeline logic validation. |
| **Identifier Mismatch** | High: Data loss during merge. | Log drop counts; use `biomaRt` robust mapping; fallback to UniProt if Ensembl fails. |
| **LCM Imputation Failure** | Medium: Column drop. | Drop columns with [deferred] missing; log warning. |
| **Runtime Exceeds 6h** | High: Job failure. | Implement checkpointing; reduce model complexity (e.g., fewer trees) if needed. |
| **Small Sample Size (n<50)** | High: Unstable 5-fold CV. | Switch to **LOOCV** and flag results as "Exploratory/High-Variance". |

## 6. Conclusion

The proposed methodology is robust and adheres to the project constitution. However, the **absence of a verified dataset** containing paired plant proteomic and transcriptomic data under specific abiotic stresses in the provided "Verified datasets" block is a critical blocker for the biological hypothesis. The project will proceed to validate the **pipeline** using available dummy/general data, but the **scientific results** (SC-001, SC-002) will be contingent on the future availability of a verified, appropriate dataset. If no such data is found, the project will report "Data Unavailable" rather than producing invalid biological conclusions.