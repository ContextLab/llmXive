# Research: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Overview

This research phase validates the feasibility of the statistical pipeline, confirms dataset availability, and details the methodological approach for quantifying model stability. The core hypothesis is that model performance variance (instability) is correlated with dataset properties (sample size, feature count) and that certain algorithms (e.g., Random Forest) exhibit lower variance than others (e.g., Linear SVM) under repeated resampling. The analysis aims to quantify **deviations from the theoretical variance ~ 1/N relationship** across different models and datasets, rather than merely confirming the known scaling law.

## Dataset Strategy

The study requires multiple binary classification datasets spanning a wide range of sample sizes. To ensure reproducibility and compliance with the Constitution (Principle I: Reproducibility), the plan uses a **fixed list of 15 OpenML dataset IDs**. These datasets are pre-verified to be binary classification tasks and meet the sample size constraints.

**Selection Criteria**:
1.  **Task Type**: Binary classification (n_classes == 2).
2. **Sample Size**: $100 \le N \le [deferred]$.
3.  **Feature Count**: Diverse range (low to high dimensionality).
4.  **Availability**: Must be available on OpenML (verified by `openml` API).
5.  **Diversity**: The list must explicitly cover the full range of sample sizes and feature dimensions.

**Verified Sources**:
-   **Source**: OpenML / UCI Machine Learning Repository (via `openml` Python library).
-   **Access Method**: `openml.datasets.get_dataset(dataset_id)`.
-   **Note**: The specific 15 dataset IDs are listed below. The `download_data.py` script will fetch these specific IDs and cache them locally with checksums. The main CI execution will use these cached files.

**Fixed Dataset List (15 IDs)**:
1.  **1590** (Adult) - Binary: Income >50k vs <=50k (N ~ 30k-48k)
2.  **1464** (Bank Marketing) - Binary: Subscription (N ~ 45k)
3.  **1479** (Credit Approval) - Binary: Approved vs Rejected (N=690) (Source: 2102.04721)
4.  **1468** (German Credit) - Binary: Good vs Bad (N=1000)
5.  **1476** (Pima Indians Diabetes) - Binary: Diabetes vs No Diabetes (N=768, F=8) (Source: 2509.12259)
6.  **1461** (Heart Disease) - Binary: Disease vs No Disease (N=303)
7.  **1510** (Breast Cancer Wisconsin) - Binary: Malignant vs Benign (N=699)
8.  **1482** (Ionosphere) - Binary: Good vs Bad (N=351)
9.  **1471** (Spambase) - Binary: Spam vs Not Spam (N=4601)
10. **1463** (Vehicle) - Binary: Subset (e.g., 'van' vs 'other' classes) (N=846)
11. **1472** (Soybean) - Binary: Subset (e.g., 'diaporthe' vs 'other') (N=683)
12. **1486** (Hypothyroid) - Binary: Hypothyroid vs Normal (N=3772)
13. **1488** (Letter Recognition) - Binary: Subset (e.g., 'a' vs 'b') (N=20000)
14. **1490** (Magic Gamma Telescope) - Binary: Signal vs Background (N=19020)
15. **1492** (MiniBooNE) - Binary: Signal vs Background (N=130064)

**Binary Mapping Rules for Multi-Class Datasets**:
-   **Vehicle (1463)**: Classes are merged such that 'van' is class 0 and all others ('bus', 'car', 'saab') are class 1.
-   **Soybean (1472)**: Classes are merged such that 'diaporthe' is class 0 and all others are class 1.
-   **Letter Recognition (1488)**: Classes 'a' and 'b' are selected; all others are dropped.
-   **Adult (1590)**: Income >50k is class 1, <=50k is class 0.

**Dataset Properties to be Extracted**:
-   `n_samples`: Number of instances.
-   `n_features`: Number of attributes (excluding target).
-   `n_classes`: Must be 2 (Binary).
-   `source`: "UCI" or "OpenML".

## Methodology

### Phase 1: Data Acquisition & Preprocessing
1.  **Fetch**: Download 15 datasets via `openml` using the fixed ID list.
2.  **Clean**: Handle missing values using median (numeric) and mode (categorical) imputation.
    *   *Constraint*: Imputation must be fit **only** on the training fold to prevent data leakage.
3.  **Split**: Prepare for 10-fold cross-validation.

### Phase 2: Repeated Cross-Validation (FR-002)
-   **Protocol**: 10 Folds $\times$ 10 Repeats = 100 evaluations per (Dataset, Model) pair.
-   **Models**:
    1.  Logistic Regression (`sklearn.linear_model.LogisticRegression`)
    2.  Random Forest (`sklearn.ensemble.RandomForestClassifier`)
    3.  Linear SVM (`sklearn.svm.LinearSVC`)
-   **Metrics**: Accuracy, F1-Score (binary, macro).
-   **Seed**: Fixed global seed for reproducibility.

### Phase 3: Stability Quantification (FR-003, FR-004)
-   **Coefficient of Variation (CV)**:
    $$ CV = \frac{\sigma}{\mu} $$
    Where $\sigma$ is the standard deviation and $\mu$ is the mean of the 100 accuracy/F1 scores for a specific (Dataset, Model) pair.
-   **Log-Log Transformation**: To address the non-normality of CV and the power-law relationship between variance and sample size, the analysis will compute:
    $$ \text{log\_CV} = \log(CV) $$
    $$ \text{log\_N} = \log(n\_samples) $$
    $$ \text{log\_F} = \log(n\_features) $$
-   **Deviation from Theoretical Scaling**: To avoid tautological correlation (since variance ~ 1/N by definition), the plan calculates the deviation from the theoretical baseline:
    $$ \text{Theoretical\_CV} \propto \frac{1}{\sqrt{N}} \implies \log(\text{Theoretical\_CV}) = -0.5 \log(N) + C $$
    $$ \text{Deviation} = \text{log\_CV} - (-0.5 \log(N) + C) $$
    The correlation analysis will then test the relationship between **Deviation** and dataset properties (log_N, log_F).
-   **Correlation**: Pearson correlation between `log_CV_accuracy` / `log_CV_f1` (and Deviation) and `log_N` / `log_F`.
    *   *Note*: The plan acknowledges the theoretical relationship variance ~ 1/N. The analysis aims to quantify the *deviation* from this relationship across models and datasets.
-   **CV Interpretation**: The plan acknowledges that CV=0 can result from either perfect stability or zero variance in poor performance. The report will explicitly report **Mean Accuracy** alongside CV to distinguish 'stable high performance' from 'stable low performance'. If Mean Accuracy is near chance level (0.5 for binary), the dataset-model pair will be flagged as "Stable Poor Performance" and excluded from the "Stable High Performance" correlation analysis to avoid bias.

### Phase 4: Statistical Significance (FR-005)
-   **Permutation Test**: To compare variance distributions between models.
    -   *Null Hypothesis*: The variance of Model A's performance scores is equal to Model B's.
    -   *Test Statistic*: **Absolute difference of variances** (std^2) of the 100 performance scores between Model A and Model B.
    -   *Procedure*: **Block permutation** at the 'repeat' level (permuting the 10 blocks of 10 folds) to maintain the dependence structure of repeated CV scores. Shuffle the blocks of scores between models, recalculate the statistic, repeat a sufficient number of times to build null distribution.
-   **Multiple Comparison Correction (FR-007)**:
    -   Apply **Benjamini-Hochberg (BH)** procedure to all p-values generated from correlation and permutation tests.
    -   BH controls the False Discovery Rate (FDR), which is more appropriate than Bonferroni for a large number of tests arising from the evaluation across multiple datasets, model pairs, and metrics.

## Compute Feasibility

-   **Hardware**: GitHub Actions `ubuntu-latest` (2 vCPU, 7GB RAM).
-   **Memory**: Datasets are loaded one at a time. The largest dataset (100k samples) fits easily in RAM. The 100 repeats are processed sequentially or in small batches using `joblib` to keep memory footprint low.
-   **Time**:
    -   15 datasets $\times$ 3 models $\times$ 100 repeats = 4,500 model fits.
    -   Logistic Regression/Linear SVM are fast (seconds per fit).
    -   Random Forest is slower (minutes per fit for large datasets).
    -   Estimated total time: ~ hours on multiple cores. Well within the 6-hour limit.
-   **GPU**: Not required. All models are standard `scikit-learn` estimators running on CPU.

## Decision/Rationale

-   **Why Fixed Dataset List?** To ensure reproducibility and avoid dynamic selection failures. The list is pre-verified to be binary and within the sample size range.
-   **Why Log-Log Transformation?** CV distributions are often skewed, and the relationship between variance and sample size is a power law. Log-log transformation linearizes this relationship and normalizes the data for Pearson correlation.
-   **Why Benjamini-Hochberg?** The study performs a large number of hypothesis tests. Bonferroni is overly conservative (alpha_adj is substantially reduced), likely resulting in zero significant findings. BH controls FDR, which is standard for exploratory analysis.
-   **Why Block Permutation?** The 100 scores are not independent (they share data splits in repeated CV). Block permutation at the 'repeat' level maintains the dependence structure, ensuring the validity of the test.
-   **Why CV with Mean Accuracy?** CV conflates stability with performance. Reporting mean accuracy alongside CV allows the interpretation to distinguish 'stable high performance' from 'stable low performance'.
-   **Why Deviation from Theoretical Scaling?** Correlating raw CV with N is tautological (variance ~ 1/N). The deviation metric isolates the model-specific stability effect from the inherent statistical scaling law.
