# Research: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## Dataset Strategy

This study relies on the **GTEx v8** dataset for RNA-seq expression and clinical phenotypes. The analysis requires specific clinical variables (BMI, fasting glucose, systolic/diastolic blood pressure, triglycerides, HDL) to apply ATP-III criteria.

### Verified Datasets

| Dataset | Verified URL | Loader Method | Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **GTEx v8 Phenotype** | **NO verified URL found for full Phenotype.tsv.gz with metabolic variables** | `pandas.read_csv` (if provided) | **Critical Gap** | The standard GTEx v8 `Phenotype.tsv.gz` contains the required variables (BMI, Glucose, BP, Lipids). However, the *verified URL block* provided in the project context does not list this specific file. The URLs listed (e.g., `CNX-PathLLM/GTEx-WSI-Description`) appear to be WSI/QA datasets and **do not** contain the required continuous clinical variables. **Action**: The implementation must attempt to load the provided URLs. If the required columns are missing, the pipeline must halt and flag "Data Gap - Study Invalid for Primary Hypothesis". |
| **GTEx v8 RNA-seq** | **NO verified URL found for TPM matrix** | `pandas.read_csv` (if provided) | **Critical Gap** | Similar to Phenotype, the RNA-seq TPM matrix is required. If not provided, the study cannot proceed. |
| **TCGA** | ` | `pandas.read_csv` | **Available (NOT Valid)** | *Critical Check*: TCGA is tissue-specific (Prostate, Ovarian) and cancer-focused. It lacks the systemic metabolic panel (fasting glucose, specific lipid profiles) required for ATP-III in non-cancer controls. **Decision**: TCGA is **NOT** a valid fallback for systemic Metabolic Syndrome. It will be ignored. |

### Dataset Variable Fit Analysis

**Required Variables for ATP-III:**
1. BMI (Body Mass Index)
2. Fasting Glucose (mg/dL)
3. Triglycerides (mg/dL)
4. HDL Cholesterol (mg/dL)
5. Systolic/Diastolic Blood Pressure (mmHg)

**Risk Assessment:**
The verified GTEx URLs provided in the context (`CNX-PathLLM`, `MagicSign`) appear to be derived from WSI (Whole Slide Image) or QA datasets. **It is highly probable these specific files do NOT contain the required continuous clinical variables (Glucose, BP, Lipids).** GTEx v8 *does* contain a `Phenotype` file with these variables, but the *verified URL block* does not list the standard GTEx `Phenotype.tsv.gz`.

**Decision:**
The plan assumes the user must provide the correct GTEx Phenotype file. The implementation code (`data/loader.py`) MUST:
1. Attempt to load the verified URLs.
2. Check for the presence of the 5 required columns.
3. **If columns are missing:** Log a fatal error, exclude the dataset, and flag the study as "Exploratory - Insufficient Phenotype Data" (per FR-001).
4. **If columns are present:** Proceed with classification.

**Fallback:**
If GTEx verified sources fail the variable check, **no suitable alternative dataset exists** for systemic Metabolic Syndrome. TCGA is cancer-specific and lacks the necessary panel. The study will be limited to the "Exploratory" status with a power limitation note, or halted entirely if N=0.

## Statistical Rigor & Methodology

### 1. Differential Expression (FR-003, FR-004)
- **Method:** Wilcoxon rank-sum test (non-parametric) comparing MetS vs. Control.
- **Stratification:** Tests performed **per tissue type** (only if N ≥ 20 per group).
- **Multiple Comparisons:** Benjamini-Hochberg (BH) procedure applied to p-values across the core circadian genes.
- **Rationale:** Wilcoxon is robust to non-normal expression distributions common in RNA-seq. BH controls the False Discovery Rate (FDR) appropriate for a small gene panel.
- **Power Limitation:** If N < 20 per group in a tissue, that tissue is excluded (US-02, FR-003).

### 2. Logistic Regression (FR-005, FR-006)
- **Model:** **Global Model**: `MetS ~ Gene_Expression + Age + Sex + Tissue`.
 - *Note*: Unlike the stratified DE analysis, the regression model is global. 'Tissue' is included as a covariate to control for tissue-specific baselines, avoiding the logical conflict of stratification.
- **Validation:** 5-fold cross-validation.
- **Metric:** AUC-ROC, Odds Ratios (OR) with 95% CI.
- **Collinearity Check:** Variance Inflation Factor (VIF) calculated. If VIF > 5, predictors are flagged, and independent effects are not claimed (US-03, FR-005).
- **Causal Inference:** Observational study. Claims restricted to *association*, not causation.

### 3. Correlation Analysis (FR-007)
- **Method:** Spearman correlation by default. Pearson only if Shapiro-Wilk p > 0.05.
- **Interpretation:** Correlations with traits used to define MetS (e.g., BMI) are descriptive of severity, not independent validation.

### 4. Sensitivity Analysis (SC-005)
- **Method:** Vary ATP-III thresholds by ±5% and re-classify.
- **Metric:** % of samples reclassified compared to baseline.

## Computational Feasibility

- **Hardware:** GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy:**
 - **Gene Filtering**: The expression matrix is filtered to **only** the ~15 core circadian genes **before** loading into memory, reducing dimensionality from [deferred] genes to 15. This prevents memory errors and overfitting.
 - Data loading via `pandas` with chunking if necessary.
 - Statistical tests via `scipy.stats` (CPU native).
 - ML via `scikit-learn` (CPU native).
 - No GPU/CUDA dependencies.
 - No large model inference.
- **Runtime:** Estimated < 1 hour for full pipeline on sampled data.
- **Memory:** Target < 4GB RAM.

## Circadian Phase Confounding (Critical Limitation)

- **Issue**: GTEx samples lack collection timestamps (circadian phase). Circadian gene expression is highly time-dependent.
- **Impact**: A significant difference between MetS and Control groups could simply reflect that MetS donors were sampled at a different time of day than controls, rather than a true metabolic effect.
- **Mitigation**: The study will be framed as investigating "associations with metabolic status in a mixed-phase cohort". Results will not be interpreted as evidence of circadian *disruption* per se, but as associations in a heterogeneous sample.
- **Sensitivity Check**: If possible, the analysis will focus on tissues with known high circadian amplitude (e.g., Liver) as a sensitivity check, acknowledging the limitation remains.

## Limitations

1. **Missing Phenotype Variables**: If GTEx v8 Phenotype lacks fasting glucose or BP, the study cannot proceed with the primary hypothesis.
2. **Sample Size**: Expected N < 100 due to strict ATP-III requirements. This limits statistical power.
3. **Circadian Phase**: Lack of time-of-death metadata makes it impossible to control for circadian phase, a major confounder.
4. **No Valid Fallback**: TCGA is not a valid substitute for systemic Metabolic Syndrome.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Phenotype Variables** | High (Study fails) | Code checks columns at load time; logs fatal error if missing; flags study as exploratory or halts. |
| **Insufficient Sample Size (N < 100)** | Medium (Low Power) | If N < 100, study proceeds with "Exploratory" label; power analysis calculated and reported. |
| **Tissue Heterogeneity** | Medium (Confounding) | Stratified DE analysis; 'tissue' included as covariate in global regression model. |
| **Collinearity in Predictors** | Low (Misinterpretation) | VIF check implemented; joint descriptive reporting if collinear. |
| **Circadian Phase Confounding** | High (Invalid Interpretation) | Explicitly acknowledged in limitations; results framed as associations in mixed-phase cohort. |