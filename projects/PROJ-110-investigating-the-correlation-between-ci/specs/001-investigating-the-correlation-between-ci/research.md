# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## 1. Dataset Strategy

### 1.1 Primary Data Source: GTEx v8
The study relies on the Genotype-Tissue Expression (GTEx) Project, Version 8. This dataset provides RNA-seq TPM matrices and associated donor phenotype data.

**Verified Datasets**:
The following sources have been verified for programmatic access. The plan utilizes the official GTEx release or a verified full-mirror.

| Dataset Name | Verified URL (Source) | Usage in Plan |
|:--- |:--- |:--- |
| GTEx v8 Phenotype | `https://www.gtexportal.org/home/datasets` (Official Portal) | Primary source for clinical variables (BMI, glucose, lipids, BP) required for ATP-III classification. |
| GTEx v8 Expression | `https://www.gtexportal.org/home/datasets` (Official Portal) | Primary source for RNA-seq TPM matrices. |
| GTEx v8 (Mirror) | ` (If available and verified) | Alternative for programmatic access if official portal is blocked or slow. |
| Invalid Source | ` | **REJECTED**. This is a small/test dataset, not the full GTEx v8. |
| Invalid Source | ` | **REJECTED**. This is a development subset, likely missing full clinical columns. |

**Data Availability & Feasibility Assessment**:
- **Access**: The official GTEx portal requires a simple data use agreement (DUA) for full download, but programmatic access via `gtex` package or verified mirrors is permitted for research. The plan assumes the use of a verified mirror or direct download of the Phenotype TSV which is often publicly available.
- **Variable Fit**: The plan includes a **Phase 0.5 Validation Gate** to confirm the presence of *all* five ATP-III variables: BMI, Fasting Glucose, Systolic BP, Diastolic BP, Triglycerides, and HDL.
 - *Risk*: If "Fasting Glucose" is missing or clearly non-fasting (e.g., random glucose distribution), the ATP-III classification is invalid.
 - *Mitigation*: If the variable is missing, the study is re-framed to use "Probable MetS" (using available proxies like BMI + Lipids) with a reduced confidence flag, or the analysis is halted. No analysis proceeds without this validation.
- **Streaming**: If the full dataset exceeds available system memory, the implementation will use `datasets.load_dataset(..., streaming=True)` or chunked downloading to iterate over samples and compute statistics on-the-fly.

### 1.2 Core Circadian Gene Panel
The analysis is restricted to the following genes to maintain statistical power and biological relevance:
- *PER1, PER2, PER3*
- *CRY1, CRY2*
- *BMAL1 (ARNTL)*
- *CLOCK*
- *NR1D1 (REV-ERBα)*
- *RORα*

### 1.3 Missing Data Strategy
- **Exclusion**: Any donor missing *any* of the five clinical variables is excluded from the classification cohort (FR-001).
- **Logging**: Each exclusion is logged with the specific missing variable.
- **Power Warning**: If N < 100, a warning is emitted, and the `study_status` is set to `exploratory`.

## 2. Statistical Methodology

### 2.1 Metabolic Syndrome Classification (ATP-III)
- **Criteria**: A sample is labeled "MetS" if it meets ≥3 of the following:
 1. BMI ≥ 30 kg/m²
 2. Fasting Glucose ≥ 100 mg/dL
 3. Systolic BP ≥ 130 mmHg OR Diastolic BP ≥ 85 mmHg
 4. Triglycerides ≥ 150 mg/dL
 5. HDL < 40 mg/dL (Male) or < 50 mg/dL (Female)
- **Strictness**: Boundaries are inclusive (e.g., 29.9 is < 30).
- **Severity Score**: A continuous variable (0-5) is also computed for correlation analysis (FR-009).
- **Validation**: Phase 0.5 ensures the "Fasting Glucose" variable is valid. If not, the study is flagged.

### 2.2 Differential Expression Analysis (FR-003, FR-004)
- **Method**: Wilcoxon rank-sum test (non-parametric) comparing MetS vs. Control.
- **Stratification**: Tests are performed *within* each tissue type.
- **Phase Adjustment**: If "Time of Death" metadata is available, expression values are adjusted for circadian phase (using a linear model with time as a covariate or cosinor terms) before the Wilcoxon test. If time metadata is too coarse, tissues are restricted to samples with matched time windows.
- **Power Filter**: Tissues with < 20 samples per group are excluded with a `WARNING` log.
- **Correction**: Benjamini-Hochberg (BH) FDR correction applied to the set of p-values for each tissue.
- **Significance**: q-value < 0.05.

### 2.3 Correlation Analysis (FR-007)
- **Method**: Spearman rank correlation by default. Pearson used only if Shapiro-Wilk test indicates normality (p > 0.05).
- **Targets**: Correlation between gene expression and each continuous trait (BMI, Glucose, etc.).
- **Partial Correlation**: Correlations are computed *controlling for* "Time of Death" (converted to radians) to isolate the metabolic effect from the circadian phase effect.
- **Correction**: BH FDR applied independently to the correlation p-values.
- **Interpretation**: Correlations with traits used to define MetS are descriptive of severity, not independent validation.

### 2.4 Predictive Modeling (FR-005, FR-006, FR-009)
- **Model**: Multivariate Logistic Regression.
- **Outcome**: Binary MetS status (primary) and Severity Score (secondary).
- **Predictors**:
 - Gene expression (log-TPM).
 - Covariates: Age, Sex, PMI.
 - **Time of Death**: Modeled as a continuous circular variable (sine/cosine transformation of time in radians) to capture the sinusoidal nature of circadian rhythms.
 - **Tissue**: Handled via stratified modeling (separate model per tissue) or mixed-effects model if sample size permits. If sample size is low, tissue-specific models are reported separately.
- **Validation**: 5-fold Cross-Validation.
- **Metrics**: AUC (Area Under Curve) with 95% CI; Odds Ratios (OR) with 95% CI.
- **Trait-Specific ORs**: A separate regression is run where the predictors are the individual metabolic traits (BMI, Glucose, etc.) to report their specific Odds Ratios (FR-009).
- **Collinearity Check**: Variance Inflation Factor (VIF) calculated. If VIF > 5, the model flags collinearity and reports joint descriptive relationships rather than independent effects.

### 2.5 Power Analysis (NEW)
- **Method**: Use `statsmodels.stats.power` to estimate the Minimum Detectable Effect Size (MDES) given the expected N (post-filtering).
- **Reporting**: If N < 100, the study is explicitly labeled "Exploratory" with a warning that it is underpowered to detect moderate effect sizes (OR ≈ 1.5).

### 2.6 Sensitivity Analysis (SC-005)
- **Method**: Vary ATP-III thresholds by ±5% (e.g., BMI ≥ 28.5 or ≥ 31.5).
- **Metric**: Measure the proportion of samples that retain their classification label.
- **Target**: ≥ 90% stability.

## 3. Compute Feasibility & Environment

- **Environment**: GitHub Actions Free Tier (limited CPU, 7GB RAM, 14GB Disk).
- **Strategy**: CPU-first.
 - **Why**: The analysis relies on classical statistics (Wilcoxon, Logistic Regression) and standard libraries (`scipy`, `statsmodels`), which are highly optimized for CPU. No deep learning or GPU-accelerated inference is required.
 - **Memory Management**: Data is streamed or processed in chunks to fit within 7GB RAM. If the full GTEx v8 exceeds this, a representative sample (random seed from `config.yaml`) is used, with a power limitation noted.
- **GPU Escape Hatch**: Not applicable for this specific statistical pipeline. If a future expansion requires fine-tuning a transformer, the plan would switch to a scaled-down Kaggle GPU run (8-bit quantization), but the current scope is fully CPU-tractable.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Clinical Variables** | High: N < 100, study becomes exploratory. | Phase 0.5 Validation Gate; explicit flagging; no TCGA fallback. |
| **Circadian Phase Confounding** | High: False positives due to sampling time. | Continuous time modeling (sine/cosine); partial correlation; phase-adjusted DE. |
| **Tissue Imbalance** | Medium: Some tissues have few MetS cases. | Stratified modeling or separate tissue models; low-power exclusion. |
| **Collinearity** | Medium: Age/PMI may correlate with expression. | VIF check; descriptive reporting if VIF > 5. |
| **Data Size** | Medium: GTEx v8 > 7GB RAM. | Streaming mode or random sampling with explicit power limitation note. |
| **Low Power** | High: Inability to detect moderate effects. | Explicit MDES calculation; "Exploratory" label if N < 100. |

## 5. Decision Rationale

- **Why ATP-III?** It is the standard clinical definition for MetS and is explicitly required by the spec (US-01).
- **Why Wilcoxon?** Gene expression data (TPM) is rarely normally distributed; non-parametric tests are more robust.
- **Why BH FDR?** The number of tests (genes × tissues) is moderate; BH controls the false discovery rate effectively without being overly conservative like Bonferroni.
- **Why CPU?** The statistical methods are computationally lightweight; GPU overhead is unnecessary and would complicate the CI environment.
- **Why Continuous Time?** Circadian rhythms are sinusoidal; categorical bins lose resolution and introduce residual confounding.
- **Why Stratified Modeling?** Tissue-specific baselines are distinct; pooling risks overfitting and masking signals.