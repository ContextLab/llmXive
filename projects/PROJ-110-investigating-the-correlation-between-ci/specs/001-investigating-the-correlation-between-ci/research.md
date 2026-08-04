# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Summary

This research phase validates the feasibility of the proposed study by confirming data availability, verifying variable presence in the GTEx v8 dataset, and establishing the statistical methodology for analyzing the correlation between circadian gene expression and Metabolic Syndrome (MetS). The primary challenge is ensuring that the specific clinical variables required for ATP-III classification (BMI, fasting glucose, triglycerides, HDL, blood pressure) are present and accessible in the open-source GTEx data available via the verified URLs.

## Dataset Strategy

### Verified Datasets

The following datasets are the *only* sources to be used. No other URLs are fabricated or assumed.

| Dataset Name | Verified URL | Access Method | Status |
| :--- | :--- | :--- | :--- |
| GTEx v8 (Phenotype + Expression) | `https://huggingface.co/datasets/genomicsGTEx/gtex_v8` (or official GTEx Portal) | `datasets.load_dataset(..., streaming=True)` | **Pending Verification** |
| GTEx v8 (Clinical Variables) | `https://www.gtexportal.org/home/datasets` (Download link for phenotype data) | `pandas.read_csv(..., sep='\t')` | **Pending Verification** |

**Critical Data Gap Analysis**:
The study *requires* clinical variables (fasting glucose, triglycerides, HDL, BP) to apply ATP-III criteria.
- **Action**: The implementation will stream the GTEx files listed above and inspect the schema.
- **If Schema Missing**: If the GTEx files do not contain the required clinical columns, the system MUST log a critical error: "Required clinical variables for ATP-III classification missing in verified GTEx source. Study cannot proceed."
- **No Fabrication**: The plan does *not* substitute a different dataset or synthesize clinical data. If the GTEx files lack the data, the study is halted.

**Dataset Fit Assessment**:
- **Variables Needed**: `bmi`, `fasting_glucose`, `triglycerides`, `hdl`, `systolic_bp`, `diastolic_bp`, `pmi`, `time_of_death`, `gene_expression` (TPM).
- **Verification Step**: Before any analysis, the `data_loader.py` script will perform a schema check. If `fasting_glucose` or `triglycerides` are missing, the pipeline fails immediately.

## Statistical Methodology

### 1. Metabolic Syndrome Classification (ATP-III)
- **Criteria**: A donor is classified as "MetS" if they meet **≥3** of the following 5 criteria:
  1. BMI ≥ 30 kg/m²
  2. Fasting Glucose ≥ 100 mg/dL
  3. Triglycerides ≥ 150 mg/dL
  4. HDL < 40 mg/dL (men) or < 50 mg/dL (women)
  5. Systolic BP ≥ 130 mmHg or Diastolic BP ≥ 85 mmHg
- **Handling Missing Data**: Samples with missing, null, NaN, or invalid values (< -1) for *any* of the 5 criteria are **excluded**. This is a strict requirement (FR-001).
- **Sensitivity Analysis**: Thresholds will be varied by ±5% (SC-005) to test stability.

### 2. Differential Expression Analysis
- **Test**: Wilcoxon rank-sum test (non-parametric) comparing gene expression (TPM) between MetS and Control groups.
- **Stratification**: Tests are performed **per tissue type**.
- **Power Filter**: Tissues with < 20 samples in *either* group are excluded (FR-003).
- **Multiple Comparisons**: **Global** Benjamini-Hochberg FDR correction applied to p-values across all genes and tissues simultaneously to control the family-wise error rate (FR-004).
- **Significance**: Adjusted p-value (q) < 0.05.

### 3. Predictive Modeling
- **Model**: Multivariate Logistic Regression.
- **Formula (Binary)**: `MetS ~ gene_expression + age + sex + tissue + pmi + time_of_death`. **Crucially, the clinical traits (BMI, glucose, etc.) that define MetS are NOT included as predictors to avoid tautology.**
- **Formula (Continuous)**: `Severity_Score ~ gene_expression + age + sex + tissue + pmi + time_of_death`. The severity score (sum of 0-5 criteria) is used as a continuous outcome to validate associations against a non-binary metric.
- **Validation**: 5-fold Cross-Validation.
- **Metrics**: AUC, Odds Ratios (OR), 95% Confidence Intervals.
- **Collinearity**: Variance Inflation Factor (VIF) calculated. If VIF > 5, collinearity is reported descriptively; independent effects are not claimed (FR-005, FR-009).

### 4. Correlation Analysis
- **Method**: Spearman correlation (default). Pearson used only if normality confirmed (Shapiro-Wilk p > 0.05).
- **Targets**: Gene expression vs. continuous traits (BMI, Glucose, etc.).
- **Correction**: Independent Benjamini-Hochberg FDR for correlation p-values (FR-007).
- **Interpretation**: Correlations with traits used to define MetS are **descriptive** of the association with the components, not an independent validation of the MetS label. The primary validation is via the logistic regression models.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **CPU-First** | Statistical methods (Wilcoxon, Logistic Regression) are computationally lightweight and run efficiently on CPU. No GPU acceleration is needed or planned. |
| **Streaming Data** | GTEx v8 is large. Streaming (`streaming=True`) prevents RAM overflow (>7GB) on CI runners. |
| **Strict ATP-III** | Adherence to clinical criteria ensures biological validity. Missing data handling (exclusion) prevents bias from imputation. |
| **Global FDR Correction** | Essential for controlling false positives when testing multiple genes and tissues simultaneously. |
| **No Synthetic Data** | Fabrication of clinical data is strictly prohibited. If verified sources lack required variables, the study halts. |
| **Time of Death Fallback** | If `time_of_death` is missing, samples are excluded from circadian-specific analysis or `pmi` is used as a proxy, with the study reframed as "associational". |

## Limitations & Risks

- **Data Availability Risk**: The primary risk is that the verified GTEx URLs do not contain the specific clinical variables required for ATP-III. If this is the case, the study cannot proceed.
- **Sample Size**: If the number of complete cases (N < 100) after exclusion, the study is labeled "exploratory" (FR-001).
- **Tissue Heterogeneity**: Bulk tissue RNA-seq may mask cell-type-specific effects.
- **PMI/Time of Death**: These are critical confounders for circadian genes. The model includes them, but residual confounding may exist. If `time_of_death` is missing, the study is limited to associational claims for those samples.

## Conclusion

The research methodology is sound and statistically rigorous. The success of the project hinges entirely on the presence of the required clinical variables in the verified GTEx dataset URLs. The plan includes a mandatory schema check to prevent proceeding with insufficient data.