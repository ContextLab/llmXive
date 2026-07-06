# Research: Predicting Plant Stress Response from Publicly Available Proteomic Data

## 1. Problem Statement & Hypothesis

**Hypothesis**: Publicly available proteomic datasets from plants subjected to abiotic stresses (drought, salinity, heat) contain sufficient signal to train machine learning models that predict stress-responsive gene expression patterns in novel, unseen conditions.

**Challenge**: The relationship between protein abundance and mRNA expression is often decoupled due to post-translational regulation. Furthermore, public datasets are fragmented, heterogeneous, and often lack matched proteomic/transcriptomic pairs for the same sample.

## 2. Dataset Strategy

The plan relies on the following verified sources. **Note**: The `# Verified datasets` block provided in the prompt contains NO verified source for NCBI GEO or ProteomeXchange raw plant data. The plan must explicitly handle this gap.

| Dataset Type | Target Content | Verified URL / Source | Status / Strategy |
|:--- |:--- |:--- |:--- |
| **NCBI GEO** | Transcriptomic data (RNA-seq) for Arabidopsis, Rice, Wheat under stress. | *NO verified source found in prompt block* | **Gap Identified**: The prompt's verified list contains no plant GEO URLs. The implementation will use `wget`/`curl` to fetch from `ncbi.nlm.nih.gov/geo` directly using accession numbers, but **no specific URL can be cited from the prompt**. The plan must include a fallback to manually curated accession lists if automated discovery fails. |
| **ProteomeXchange** | Proteomic data (Mass Spec) for same conditions. | *NO verified source found in prompt block* | **Gap Identified**: Similar to GEO, no verified URL exists in the prompt block. Implementation will fetch from `proteomexchange.org` via accession. |
| **SVR (parquet)** | *Note: This appears to be a financial/math dataset in the verified list, not plant data.* | ` | **Not Applicable**: This dataset is unrelated to plant stress. It will NOT be used. |
| **GEO (csv)** | *Note: The provided GEO URLs in the prompt are for road sequencing, pandaset, and geometry, not plant stress.* | `...label_color_map_ausenv_roadseq.csv`, `...pandaset.zip`, `...geometry3k...` | **Not Applicable**: These datasets do not contain plant proteomic/transcriptomic data. They will NOT be used. |

**Critical Dataset Mismatch Note**: The `# Verified datasets` block provided for this task **does not contain any verified URLs for plant proteomic or transcriptomic data** (NCBI GEO/ProteomeXchange). The prompt explicitly states: "If a dataset the spec needs has NO verified source in the block, state that explicitly rather than fabricating one."

**Revised Strategy**:
1. **Manual Curation**: The `download.py` script will require a configuration file (`data/config.yaml`) containing a list of **manually curated** accession numbers (e.g., GSE12345, PXD000123) that have been verified by the researcher to contain paired data.
2. **No Automated Discovery**: The plan will NOT attempt to scrape NCBI/ProteomeXchange for *unknown* datasets, as this violates the "Verified Accuracy" principle and the specific constraint to not invent URLs.
3. **Fallback**: If no paired datasets are found in the curated list, the pipeline will halt with a "No Paired Data" error, logging the specific missing conditions.

## 3. Methodological Approach

### 3.1 Data Ingestion & Preprocessing
* **Filtering**: Proteins detected in < 50% of samples within a stress condition will be removed (FR-002).
* **Imputation**: **MinProb** (Minimum Probability) algorithm will be used for Left-Censored Missing (LCM) imputation, implemented via the `impyute` library.
 * *Rationale*: Proteomic missing values are often due to detection limits. MinProb replaces missing values with a value drawn from a distribution shifted below the detection limit (e.g., 5th percentile), preserving the "missing not at random" nature without introducing the bias of mean imputation.
 * **Detection Limit Estimation Protocol**:
 * To avoid arbitrary thresholds, the detection limit (DL) for each protein is determined hierarchically:
 1. **Reported DL**: If the dataset metadata provides a DL, use it.
 2. **Percentile DL**: If >5 non-missing values exist, calculate DL as the 5th percentile of non-missing values.
 3. **Small Sample Fallback**: If 1-5 non-missing values exist, use the **global minimum non-zero value** across the entire dataset as the DL.
 4. **All Missing Handling**: If a protein has **0 non-missing values** (all missing), the column is **dropped** immediately with a log entry. No imputation is attempted to prevent runtime errors.
* **Identifier Mapping**: Use `mygene` (Python) as primary, with `biomaRt` (R) as fallback.
 * *Constraint*: If `biomaRt` requires R, the pipeline will spawn an R subprocess or use `rpy2`. Given the CPU constraints, a pre-computed mapping table (if available) or a lightweight `mygene` query is preferred to avoid heavy R installation overhead. **Decision**: Use `mygene` in Python for simplicity and CPU efficiency, falling back to `biomaRt` (using `plants_mart`) only if mapping success rate is < 80%.

### 3.2 Modeling Strategy
* **Algorithms**: Random Forest Regressor (`RandomForestRegressor`) and Support Vector Regression (`SVR`).
 * *Rationale*: RF handles non-linear relationships and missing data well; SVR is robust for small datasets. Both are CPU-tractable.
* **Stress-Blind Baseline (Addressing Methodology-a8545604)**:
 * To distinguish between learning a universal biological mapping vs. learning stress-class signatures, we will implement a **Stress-Blind Baseline**.
 * **Method**: For each protein feature, we will regress out the `StressCondition` effect using a linear model: `Protein_residual = Protein - (Stress_Coeff * Stress_Label)`.
 * The main models will be trained on these **residualized features**. This ensures the predictors are orthogonal to the stress label, forcing the model to learn the Protein->Gene regulatory logic rather than "Drought = High Protein X".
 * Performance will be compared against a model trained on raw features to quantify the contribution of stress signatures.
* **Validation**:
 1. **Within-Stress (LOOCV)**: Due to small sample sizes (n < 10) common in public plant datasets, **Leave-One-Out Cross-Validation (LOOCV)** is used instead of 5-fold CV.
 * *Rationale*: 5-fold CV on n=10 yields test sets of size 2, resulting in extremely high variance for R² estimates. LOOCV maximizes training data and provides a more stable (though potentially optimistic) estimate.
 * *Statistical Power Limitation*: We acknowledge that with n < 10, statistical power to detect subtle effects is low. Confidence intervals will be derived via bootstrap resampling if n permits (n > 20), otherwise, we will report the LOOCV standard error and explicitly note the limitation in the results.
 2. **Cross-Stress**: Train on Drought, Test on Salinity/Heat.
 3. **Null Model**: Predict the mean of the training set.
 4. **Target-Permutation Test (Addressing Methodology-957283ae & 5903924b)**: **Shuffle the target gene expression values** (not stress labels) relative to the predictors. This establishes a null distribution for the R² score. If the model's R² on real data is not significantly higher than on shuffled data, the model is learning noise.
* **Metrics**: R², RMSE.

### 3.3 Statistical Rigor & Limitations
* **Multiple Comparisons**: If multiple stress pairs are tested, apply Benjamini-Hochberg correction to p-values (if hypothesis testing is performed on performance differences).
* **Power Analysis**: Acknowledge that public plant datasets often have small sample sizes (n < 30). The plan will report the sample size and note that statistical power may be low for detecting subtle cross-stress effects.
* **Collinearity**: If predictors (proteins) are highly correlated (e.g., members of the same family), RF importance may be diluted. This will be noted in the discussion.
* **Causal Inference**: Claims will be strictly **associational**. The model predicts correlation, not causation.
* **Data Leakage Prevention**: All preprocessing (normalization, imputation, feature selection) will be performed **strictly within** each cross-validation fold to prevent data leakage (Addressing Scientific-Soundness-18aa8dd0).

## 4. Computational Feasibility (CPU-Only)

* **Hardware**: GitHub Actions Free Tier (limited CPU, constrained RAM).
* **Data Volume**: Target < 1 GB processed data.
* **Model Training**:
 * `RandomForestRegressor`: Set `n_estimators=100`, `max_depth=10` (or `None` with `min_samples_split`).
 * `SVR`: Use `kernel='rbf'`, `C=1.0`. Avoid large kernels or high-dimensional feature spaces.
 * **Constraint**: If training exceeds a predefined duration threshold, the script will reduce `n_estimators` or sample the dataset.
* **Libraries**: `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `impyute` (all have CPU wheels).

## 5. Risk Mitigation

| Risk | Mitigation |
|:--- |:--- |
| **No Paired Data Found** | Pipeline halts early with clear error (`E001_NO_PAIRED_DATA`). Research phase will attempt to find a single "gold standard" dataset manually or pivot to meta-analysis. |
| **Identifier Mapping Failure** | If < 50% of proteins map to genes, the dataset is discarded for that stress type. Fallback to pre-computed mapping table. |
| **Runtime Exceeds Threshold** | Implement a "checkpoint" mechanism: save intermediate data after ingestion. If time is low, skip complex SVR and only run RF. |
| **LCM Imputation Failure** | If a column is all missing, drop it and log. Use MinProb from `impyute` with strict DL estimation. |
| **Stress Confounding** | Use Stress-Blind Baseline (residualization) to isolate regulatory signals. |
| **Data Leakage** | Enforce within-fold preprocessing strictly. |
| **Low Statistical Power** | Use LOOCV to maximize data usage. Report standard errors if bootstrapping is not feasible. |