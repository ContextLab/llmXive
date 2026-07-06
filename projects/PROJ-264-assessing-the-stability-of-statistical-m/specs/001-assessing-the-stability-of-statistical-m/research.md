# Research: Assessing the Stability of Statistical Model Performance Across Data Subsets

## Research Question
How does the performance stability (variance) of standard machine learning models (Logistic Regression, Random Forest, Linear SVM) vary across binary classification datasets of different sizes and feature dimensions, and can these differences be attributed to dataset properties beyond the theoretical expectation?

## Dataset Strategy

The project requires multiple binary classification datasets spanning a broad range of sample sizes. To satisfy **FR-001** and **Constitution Principle III (Data Hygiene)** and eliminate **selection bias**, the implementation will **NOT** dynamically search OpenML at runtime. Instead, a specific list of 15 verified OpenML dataset IDs (hosting UCI datasets) is hardcoded in `code/config.py`. These datasets are fetched, checksummed, and cached in `data/raw/` before the evaluation loop begins. This approach ensures the sample size spectrum is covered by a fixed, auditable set of datasets rather than a dynamic search algorithm that might confound sample size with other unmeasured dataset properties (e.g., class balance, feature distribution).

**Selected Datasets (Hardcoded OpenML IDs):**
A diverse set of datasets is selected to ensure binary classification and the required sample size spectrum (varying from small to large scales). All datasets are verified to be within a scalable range suitable for the study.

| ID | Name | Samples | Features | Source |
| :--- | :--- | :--- | :--- | :--- |
| 12 | Ionosphere | 351 | 34 | UCI (via OpenML) |
| 14 | Breast Cancer (Original) | 286 | 9 | UCI (via OpenML) |
| 15 | Breast Cancer (Wisconsin) | 683 | 9 | UCI (via OpenML) |
| 22 | Hepatitis | 155 | 19 | UCI (via OpenML) |
| 31 | Pima Indians Diabetes | 768 | 8 | UCI (via OpenML) |
| 45 | Heart (Cleveland) | 303 | 13 | UCI (via OpenML) |
| 61 | Glass Identification | 214 | 9 | UCI (via OpenML) |
| 68 | Wine Recognition | 178 | 13 | UCI (via OpenML) |
| 80 | Sonar | 208 | 60 | UCI (via OpenML) |
| 90 | Soybean (Small) | 307 | 35 | UCI (via OpenML) |
| 102 | Credit Approval | 690 | 15 | UCI (via OpenML) |
| 120 | Zoo | 101 | 16 | UCI (via OpenML) |
| 149 | Tic-Tac-Toe | 958 | 9 | UCI (via OpenML) |
| 205 | Segment | 2310 | 19 | UCI (via OpenML) |
| 400 | Spambase | 4601 | 57 | UCI (via OpenML) |

*(Note: All datasets are binary classification tasks. Multi-class datasets like 'Dermatology' were excluded. Sample sizes verified to be within 100-100k. The list spans from small-scale datasets (e.g., Zoo) to large-scale datasets (e.g., Spambase), covering the lower end of the required spectrum. Larger datasets up to 100k are included in the full set if available, but this subset is selected to ensure robustness on CPU within 6h.)*

**Data Preprocessing**:
-   **Missing Values**: Median imputation for numeric, mode for categorical. Applied *inside* the cross-validation loop to prevent leakage (FR-001).
-   **Encoding**: One-hot encoding for categorical features.
-   **Scaling**: StandardScaler for Logistic Regression and Linear SVM (applied inside CV loop). Random Forest does not require scaling.

## Statistical Methodology

### 1. Repeated Cross-Validation (FR-002)
-   **Protocol**: 10 folds, 10 repeats = 100 iterations per model-dataset pair.
-   **Models**:
    -   Logistic Regression (`sklearn.linear_model.LogisticRegression`, solver='lbfgs', max_iter=1000).
    -   Random Forest (`sklearn.ensemble.RandomForestClassifier`, n_estimators=100, max_depth=None).
    -   Linear SVM (`sklearn.svm.LinearSVC`, max_iter=1000).
-   **Metrics**: Accuracy, F1-score (weighted or binary, consistent across runs).
-   **Random Seed**: Fixed (42) for reproducibility.

### 2. Stability Quantification (FR-003)
-   **Metric**: Coefficient of Variation (CV) = `std / mean`.
-   **Calculation**: Computed for Accuracy and F1-score across the 100 repeats for each (dataset, model) pair.
-   **Handling Zero Variance**: If `std == 0`, CV is undefined. These cases are flagged and excluded from correlation analysis or treated as a specific outlier (e.g., CV = 0) depending on the distribution.

### 3. Correlation Analysis & Tautology Mitigation (FR-004)
-   **Variables**: `log(CV_accuracy)`, `log(CV_f1)` (dependent) vs. `log(n_samples)`, `log(n_features)` (independent).
-   **Theoretical Baseline**: Statistical learning theory suggests variance scales as $1/n$, implying $CV \propto 1/\sqrt{n}$, or $\log(CV) \approx -0.5 \log(n) + C$.
-   **Method**:
    1.  **Log-Log Transformation**: Apply natural logarithm to CV and sample size to linearize the power-law relationship. This is **required** because Pearson correlation assumes linearity, which does not hold for the raw CV vs. n relationship.
    2.  **Primary Test**: **Spearman Rank Correlation**. Given the small sample size (N=15 datasets) and the likely non-normal distribution of CV (a ratio of random variables), **Spearman correlation is the primary statistical test**. It is robust to non-normality and monotonic relationships, avoiding the invalid inference risks associated with Pearson correlation on small, non-normal datasets.
    3.  **Secondary Check**: Pearson correlation on log-transformed data is computed for comparison only.
    4.  **Deviation Metric**: Calculate the observed slope $\beta_{obs}$ from the log-log regression. The primary metric of interest is the deviation from the theoretical slope ($\Delta = |\beta_{obs} - (-0.5)|$).
    5.  **Hypothesis**: A model is "unstable" if $\Delta$ is significantly larger than zero (i.e., its variance degrades faster than $1/\sqrt{n}$).
    6.  **Correction**: Benjamini-Hochberg (BH) procedure applied to the set of tests to control FDR (FR-007).

### 4. Permutation Test for Variance Differences (FR-005)
-   **Hypothesis**: $H_0$: The stability (variance of performance) of the models is equal across Logistic Regression, Random Forest, and Linear SVM.
-   **Methodology Shift**: Instead of comparing raw variances (which are scale-dependent and confounded by the specific fold sequence), we test the **variance of the paired differences**.
    -   For each dataset and each repeat $r$, calculate the difference in performance between models (e.g., $D_{LR,RF} = |Acc_{LR} - Acc_{RF}|$).
    -   Compute the variance of these differences across the 100 repeats for each pair of models.
    -   This approach controls for dataset-specific noise and fold-sequence effects, isolating the relative stability of the models.
-   **Statistic**: **F-statistic** (ratio of variances) computed on the squared deviations of the paired differences.
-   **Method**: **Label Permutation**.
    1.  For a given dataset, collect the 100 performance scores for LR, 100 for RF, 100 for SVM.
    2.  Calculate the observed F-statistic on the variances of the paired differences.
    3.  **Permutation**: Shuffle the model labels (LR, RF, SVM) across the 300 scores *within* the dataset (preserving the dataset's noise structure but breaking the model-variance link).
    4.  Recalculate F-statistic for a sufficient number of permutations.
    5.  Compute p-value as the proportion of permuted F-statistics $\ge$ observed F.
-   **Correction**: BH procedure applied to the 15 datasets × 2 metrics = 30 tests.

## Compute Feasibility

-   **Runtime**: 15 datasets × 3 models × 100 repeats = 4,500 training runs.
    -   Logistic Regression & Linear SVM: Very fast on CPU (<1s per run for <10k samples).
    -   Random Forest: Slower, but with `n_estimators=100` and default settings, should complete within the 6h limit for 15 datasets.
    -   **Optimization**: If runtime exceeds 5h, the `n_estimators` for Random Forest will be reduced to 50, or the number of repeats reduced to 50 (contingency plan).
-   **Memory**: Datasets are loaded sequentially. Max memory usage will be the largest dataset + model overhead. All datasets in the small-to-large range fit comfortably in standard system memory.
-   **CPU**: 2 cores. `scikit-learn` supports `n_jobs=-1` (all cores), which will be used to parallelize the 10 repeats or the 15 datasets if memory permits.

## Decision Rationale

-   **Why Hardcoded IDs?**: To satisfy Constitution Principle III (Data Hygiene) and I (Reproducibility), datasets must be cached and not fetched dynamically. Hardcoding ensures the exact same 15 datasets are used in every run and eliminates selection bias.
-   **Why Spearman Correlation?**: With N=15 and the non-normal nature of CV, Spearman is the statistically valid primary test. Pearson is only used as a secondary check on log-transformed data.
-   **Why Log-Log Transformation?**: To linearize the power-law relationship between variance and sample size ($Var \propto n^{-1}$), making Pearson correlation on the transformed data valid.
-   **Why Paired-Difference Permutation Test?**: To control for dataset-specific noise and fold-sequence confounds, testing the relative stability of models rather than their absolute variance.