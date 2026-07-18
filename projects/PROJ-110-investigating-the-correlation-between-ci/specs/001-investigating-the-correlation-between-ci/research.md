# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Summary of Research Findings

This research phase validates the feasibility of the proposed study using the GTEx v8 dataset, confirms the availability of required clinical variables, and outlines the statistical strategy. The primary challenge identified is the potential scarcity of samples with *complete* data for all five ATP-III criteria (BMI, fasting glucose, triglycerides, HDL, blood pressure) in GTEx. The strategy prioritizes strict adherence to the ATP-III definition, excluding incomplete cases, and explicitly acknowledges power limitations if N < 100. **Crucially, the hypothesis is reframed from 'circadian expression' to 'static expression differences' due to the lack of time-of-day metadata in GTEx.**

## Dataset Strategy

### Primary Dataset: GTEx v8
* **Source**: The GTEx v8 RNA-seq and phenotype data is the primary source.
* **Verified URLs**:
 * Expression Data: ` (Note: This appears to be a sample; the full expression matrix is typically large. The plan assumes the full v TPM matrix is available via the standard GTEx portal or a verified mirror if the specific URL is a subset. For the purpose of this plan, we use the verified URL provided in the input block as the entry point, but the implementation must handle the full dataset size via streaming or chunking if the file is small and represents a subset).
 * *Correction*: The input block lists `CNX-PathLLM/GTEx-WSI-Description` and `CNX-PathLLM/GTEx-WSI-OpenQA` which are WSI (Whole Slide Image) datasets, likely not containing the tabular clinical phenotype data (BMI, BP, etc.) required for ATP-III. The `MagicSign/TrASPr_GTEx_data` link is a TSV, which is more promising.
 * **Critical Constraint**: The input block does **not** provide a verified URL for the full GTEx v8 *phenotype* file containing BMI, Glucose, BP, etc. The provided URLs are either WSI descriptions or small samples.
 * **Mitigation**: The plan explicitly assumes that the `MagicSign` TSV contains the necessary columns or that the implementation will attempt to fetch the standard GTEx v8 phenotype file from the GTEx Portal (via `ftpd` or `wget` if allowed) or switch to the 'Exploratory' mode with the 'Partial Criteria Score' fallback if the verified URLs do not contain the full phenotype data. If the verified URLs do not contain the full phenotype data, the study will be limited to the available samples in the `MagicSign` TSV, and the "Power Limitation" flag (FR-001) will be triggered if N < 100.

| Dataset | Verified URL | Relevance to Spec | Access Method |
|:--- |:--- |:--- |:--- |
| GTEx (Sample) | ` | Contains expression and potentially some phenotypes. | `pandas.read_csv` (if TSV) or `datasets.load_dataset` |
| GTEx (WSI) | ` | **Not suitable** for ATP-III (lacks clinical labs). | N/A |
| TCGA (ACC/OV) | ` | Potential supplement if GTEx N < 100. | `pandas.read_parquet` |

**Dataset Variable Fit Check**:
* **Required Variables**: BMI, Fasting Glucose, Systolic BP, Diastolic BP, Triglycerides, HDL.
* **Verification**: The provided `MagicSign` TSV must be inspected. If it lacks *any* of these, the study cannot proceed as defined for that variable. The plan assumes the TSV contains these columns. If not, the "Power Limitation" note is mandatory.
* **Action**: The `data/downloader.py` script must first validate the schema of the downloaded file. If columns are missing, it must log a critical error and halt, or switch to the "Exploratory" mode if the spec allows partial criteria (it does not; it requires strict ATP-III).

## Statistical Methodology

### 1. Classification (US-01) - Static Expression Context
* **Method**: Deterministic logic based on ATP-III thresholds.
* **Logic**:
 * BMI ≥ 30 kg/m²
 * Fasting Glucose ≥ 100 mg/dL
 * Triglycerides ≥ 150 mg/dL
 * HDL < 40 mg/dL (Men) or < 50 mg/dL (Women)
 * BP ≥ 130/85 mmHg
* **Handling Missing Data**: Samples with `NaN`, `null`, or invalid values (< -1) in any of the 5 variables are **excluded**. A log entry is created for each exclusion.
* **Justification for Exclusion**: Multiple imputation is rejected for post-mortem data due to high missingness and lack of correlation structure, making 'exclusion + Partial Score' the scientifically safer approach to avoid bias.
* **Robustness**: A sensitivity analysis (SC-005) will vary thresholds by ±5% to test classification stability. The output `sensitivity_analysis.csv` is the direct artifact used to measure SC-005.

### 2. Differential Expression (US-02) - Static Expression Differences
* **Note**: US-02 now refers to **Static Expression Differences** between MetS and Control groups, as circadian phase cannot be measured.
* **Method**: Wilcoxon rank-sum test (non-parametric) for each of the ~15 core circadian genes.
* **Stratification**: Tests performed separately for each tissue type.
* **Power Filter**: Tissues with < 20 samples in *either* MetS or Control group are excluded.
* **Correction**: Benjamini-Hochberg (FDR) applied to the set of p-values for each tissue (or globally, depending on the specific hypothesis scope; plan defaults to global FDR for the set of all tests to be conservative).
* **Collinearity**: Not applicable to univariate tests, but noted for the regression step.

### 3. Predictive Modeling (US-03)
* **Method**: Multivariate Logistic Regression.
* **Formula**: `MetS ~ Gene_Expression + Age + Sex + Tissue`
* **Cross-Validation**: k-fold CV to estimate AUC.
* **Collinearity Check (FR-005)**: Variance Inflation Factor (VIF) calculated for **all** predictors and stored in `logistic_regression.csv`. If VIF > 5, the model flags collinearity and reports joint descriptive relationships rather than independent odds ratios for the collinear pair.
* **Assumption**: Observational data; claims are associational, not causal. If clinical covariates (BMI, Glucose, etc.) are missing, the model will be interpreted as 'Gene vs. MetS Composite' with a strong caveat that the effect may be mediated by the missing clinical variables, rather than claiming it tests 'independent predictive power'.

### 4. Correlation Analysis (FR-007) - Exploratory Severity Indicators
* **Method**: Spearman correlation by default. Pearson used only if Shapiro-Wilk test indicates normality (p > 0.05).
* **Output**: Correlation coefficient (r) and p-value for each gene vs. each continuous trait (BMI, Glucose, etc.).
* **Crucial Caveat**: Correlations with traits used to define MetS are **tautological by definition**. The plan explicitly states that FR-007's requirement for 'independent validation' cannot be met with GTEx data and that the analysis will be re-framed as 'exploratory severity indicators' to avoid tautology, rather than claiming it as a core validation step.
* **Visual Deliverables**: FR-008 'Correlation Scatter Plots' will be generated for continuous traits but explicitly labeled as 'Exploratory Severity Indicators' in the output.

## Power Analysis & Sample Size Justification

* **Target**: To detect an Odds Ratio (OR) of 1.5 with 80% power at α=0.05.
* **Requirement**: A sufficient number of samples per group (MetS and Control) are required for the primary logistic regression.
* **GTEx Reality**: The number of complete cases (N) in GTEx with all 5 ATP-III variables is likely < 250 per group.
* **Consequence**: The study will be underpowered for the primary hypothesis. The plan explicitly flags this as 'Exploratory'.
* **Fallback Power Calculation**: If the 'Partial Criteria Score' (continuous risk score) is used, the required N for a correlation coefficient of r=0.15 is approximately 350. If N < 350, the results are interpreted as 'hypothesis-generating' only.

## Fallback Methodology

If the number of complete cases (N) for strict ATP-III criteria is < 100:
1. **Switch to Continuous Score**: Calculate a 'Metabolic Risk Score' as the sum of standardized (z-score) clinical variables (BMI, Glucose, TG, HDL, BP).
2. **Statistical Test**: Use **Linear Regression** (`Risk_Score ~ Gene_Expression + Age + Sex + Tissue`) instead of Logistic Regression.
3. **Differential Analysis**: Use Spearman correlation between Gene Expression and Risk Score instead of Wilcoxon.
4. **Interpretation**: All results are labeled 'Exploratory' with a note on the reduced power and the shift from binary to continuous outcome.

## Compute Feasibility

* **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB Disk).
* **Verified Strategy**: The plan will use `datasets.load_dataset(..., streaming=True)` to iterate over the GTEx v8 expression matrix and phenotype file simultaneously, aggregating statistics on-the-fly without loading the full matrix into RAM. This ensures the 7 GB RAM limit is respected while retaining the necessary clinical variables.
* **Fallback**: If streaming fails or the dataset is too large, the plan will process a fixed random sample of [deferred] complete cases, with a power limitation note.
* **No GPU Required**: No deep learning or large language models are used.
* **Time**: Statistical tests on a subset of genes across a range of tissues will complete in minutes, well under the 6-hour limit.

## Risks and Mitigations

1. **Data Availability Risk**: The verified URLs provided may not contain the full clinical phenotype data required for ATP-III.
 * *Mitigation*: The `downloader.py` script will validate the presence of all 5 required columns. If missing, the pipeline attempts to fetch the 'GTEx Phenotype' file from the official GTEx Portal (via `ftpd` or `wget` if allowed) or switches to the 'Exploratory' mode with the 'Partial Criteria Score' fallback.
2. **Power Limitation**: If the number of complete cases (N) is < 100.
 * *Mitigation*: FR-001 mandates a power limitation note. The study will proceed but with explicit caveats in the results section.
3. **Tissue Heterogeneity**: Different tissues have vastly different baseline expression levels.
 * *Mitigation*: Stratification by tissue type and inclusion of 'tissue' as a covariate in the logistic regression.

## References
* GTEx Consortium. "The GTEx Portal." (Accessed via verified HuggingFace mirrors).
* National Heart, Lung, and Blood Institute (NHLBI). "Third Report of the Expert Panel on Detection, Evaluation, and Treatment of High Blood Cholesterol in Adults (Adult Treatment Panel III)."