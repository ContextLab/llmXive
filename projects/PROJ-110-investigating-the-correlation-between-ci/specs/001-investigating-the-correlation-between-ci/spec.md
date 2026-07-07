# Feature Specification: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Feature Branch**: `001-circadian-metabolic-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Metabolic Syndrome Status from Clinical Variables (Priority: P1)

The researcher must be able to programmatically classify GTEx donors as "Metabolic Syndrome" (MetS) or "Control" based on the ATP-III criteria using available clinical phenotype data (BMI, fasting glucose, blood pressure, triglycerides, HDL).

**Why this priority**: This is the foundational step; without a binary or ordinal label for the outcome variable, no correlation analysis can be performed. It directly addresses the core research question.

**Independent Test**: Can be fully tested by running the classification script on a known subset of GTEx data and verifying that the output matches manual calculation of ATP-III criteria for those specific samples.

**Acceptance Scenarios**:

1. **Given** a donor with BMI ≥ 30, fasting glucose ≥ 100, and triglycerides ≥ 150 (3 criteria met), **When** the classification script runs, **Then** the donor is labeled "MetS".
2. **Given** a donor with only 2 criteria met (e.g., BMI ≥ 30 and HDL < 40), **When** the classification script runs, **Then** the donor is labeled "Control".
3. **Given** a donor with missing data for one of the five criteria (e.g., fasting glucose), **When** the script runs, **Then** the donor is excluded from the analysis with a log entry indicating the missing variable.

---

### User Story 2 - Perform Differential Expression Analysis on Core Circadian Genes (Priority: P2)

The researcher must be able to compare the expression levels (TPM) of a predefined list of core circadian genes (e.g., *PER1*, *BMAL1*, *CLOCK*) between the "MetS" and "Control" groups using non-parametric statistical tests, with appropriate multiple-comparison correction.

**Why this priority**: This directly tests the primary hypothesis (association between gene expression and syndrome status). It is the core analytical engine of the study.

**Independent Test**: Can be fully tested by executing the statistical analysis pipeline on the pre-processed data and verifying that the output includes a table of p-values, adjusted p-values (FDR), and effect sizes for each gene.

**Acceptance Scenarios**:

1. **Given** the expression matrix and group labels for a specific tissue, **When** the Wilcoxon rank-sum test is executed (stratified by tissue), **Then** the system outputs a p-value for each of the ~15 core circadian genes for that tissue.
2. **Given** the raw p-values from the previous step, **When** the Benjamini-Hochberg procedure is applied, **Then** the system outputs adjusted p-values (FDR) where the number of false discoveries is controlled at q < 0.05.
3. **Given** a gene with no expression difference between groups, **When** the test runs, **Then** the adjusted p-value is > 0.05, and the gene is not flagged as significant.
4. **Given** a tissue with fewer than 20 samples in either the MetS or Control group, **When** the test runs, **Then** the system excludes that tissue from the analysis and logs a "low power" warning.

---

### User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

The researcher must be able to fit a multivariate logistic regression model predicting MetS status using circadian gene expression levels and key covariates (age, sex, tissue type), and evaluate its performance via cross-validation.

**Why this priority**: This moves beyond simple association to multivariate prediction, controlling for confounders. It provides a more robust test of the hypothesis but relies on the successful completion of US-01 and US-02.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

**Acceptance Scenarios**:

1. **Given** the expression data and labels, **When** the logistic regression model is trained with 5-fold cross-validation, **Then** the system reports an average AUC score and 95% confidence intervals.
2. **Given** the trained model, **When** the odds ratios for each gene are extracted, **Then** the output includes the odds ratio, standard error, and p-value for each predictor.
3. **Given** a model with collinear predictors (if any), **When** the diagnostic check runs, **Then** the system flags the collinearity (VIF > 5) and reports the joint descriptive relationship rather than claiming independent effects.

---

### Edge Cases

- What happens when a tissue type has fewer than 20 samples in either the MetS or Control group? (System must exclude the tissue or flag it for insufficient power).
- How does the system handle donors with borderline metabolic syndrome status (e.g., BMI = 29.9 vs 30.0)? (System must strictly adhere to the integer count rule: ≥3 for MetS; 29.9 is treated as < 30, thus failing that specific criterion).
- How does the system handle zero-count genes (TPM = 0) after log transformation? (System must apply a pseudocount of 1 before log transformation to avoid NaN values).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse GTEx v8 RNA-seq TPM matrices and associated phenotype files. The system MUST attempt to classify every sample; samples with missing, null, NaN, or numerically invalid values (e.g., < -1) for any of the five clinical variables (BMI, fasting glucose, systolic/diastolic BP, triglycerides, HDL) MUST be excluded from the analysis cohort with a log entry. If the number of complete cases in GTEx is < 100, the system MUST attempt to supplement with TCGA data (if available) or flag the study as exploratory with a power limitation note. (See US-01)
- **FR-002**: System MUST classify each donor into "MetS" or "Control" groups based strictly on the ATP-III criteria (≥3 of 5 thresholds met). (See US-01)
- **FR-003**: System MUST perform Wilcoxon rank-sum tests comparing expression of each core circadian gene between MetS and Control groups, stratified by tissue type, only for tissues with ≥20 samples per group. (See US-02)
- **FR-004**: System MUST apply Benjamini-Hochberg False Discovery Rate (FDR) correction to all p-values generated in FR-003 to control for multiple comparisons. (See US-02)
- **FR-005**: System MUST fit a multivariate logistic regression model (`MetS ~ gene_expression + age + sex + tissue`) and calculate odds ratios with 95% confidence intervals. (See US-03)
- **FR-006**: System MUST perform 5-fold cross-validation to evaluate model performance (AUC) and prevent overfitting. (See US-03)
- **FR-007**: System MUST compute correlations between gene expression and continuous metabolic traits (BMI, glucose, etc.) for ALL core circadian genes. Correlation method MUST be Spearman by default; Pearson MUST be used only if normality is confirmed (Shapiro-Wilk p > 0.05). Genes with adjusted p-value (FDR) < 0.05 (as determined in FR-004) are highlighted as significant; correlations for non-significant genes are reported as exploratory severity indicators. Note: Correlations with traits used to define MetS are descriptive of severity, not independent validation. (See US-02)
- **FR-008**: System MUST generate diagnostic plots (heatmap, ROC curve, correlation scatter plots) for significant findings. (See US-02, US-03)

### Key Entities

- **Donor**: Represents a human subject; attributes include ID, age, sex, tissue source, and clinical measurements (BMI, BP, lipids, glucose).
- **GeneExpression**: Represents the transcript abundance; attributes include Gene Symbol, TPM value, and log-transformed value.
- **MetabolicStatus**: Represents the binary classification; attributes include Label ("MetS" or "Control") and CriteriaCount (0-5).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of donors successfully classified as MetS or Control is measured against the total number of GTEx v8 samples with complete phenotype data. (See US-01)
- **SC-002**: The number of core circadian genes showing statistically significant differential expression (FDR < 0.05) is measured against the total number of core circadian genes tested (~15). (See US-02)
- **SC-003**: The Area Under the Curve (AUC) of the logistic regression model is measured against a baseline random classifier (AUC = 0.5) to determine predictive utility. (See US-03)
- **SC-004**: The magnitude of the correlation coefficient (r) between gene expression and continuous metabolic traits is measured against the null hypothesis of no correlation (r = 0). (See US-02)
- **SC-005**: The sensitivity of the classification results is measured against a sensitivity analysis where the ATP-III thresholds are varied by ±5% to assess robustness. (See US-01)

## Assumptions

- The GTEx v8 dataset contains the specific clinical variables (fasting glucose, triglycerides, HDL, blood pressure) required to apply ATP-III criteria; if any variable is missing for a large portion of samples, the sample size will be significantly reduced, potentially affecting power.
- If GTEx v8 lacks sufficient complete cases (N < 100), the TCGA dataset will be available as a supplementary source, or the study will be interpreted as exploratory with a noted power limitation.
- The "Core Circadian Genes" list (PER1-3, CRY1-2, BMAL1, CLOCK, NR1D1, RORα) is sufficient to capture the relevant biological signal; other circadian genes may be omitted.
- The GTEx tissue samples, though not time-stamped, contain sufficient biological variance in gene expression to detect associations with metabolic status, assuming the metabolic syndrome itself induces a disruption in circadian rhythm detectable in bulk tissue.
- The analysis will run on a CPU-only environment (GitHub Actions free tier); therefore, no GPU-accelerated deep learning models or 8-bit quantization will be used; only classical statistical methods (Wilcoxon, Logistic Regression) and standard libraries (scikit-learn, statsmodels, pandas) will be employed.
- The Benjamini-Hochberg correction is appropriate for the multiple testing burden of ~15 genes; if the list of genes were expanded to thousands, a more conservative method or different correction strategy would be needed.
- The ATP-III criteria, originally designed for clinical diagnosis, are valid proxies for "Metabolic Syndrome" in a research setting using post-mortem tissue samples.
- The sample size of available GTEx samples with complete metabolic phenotypes will be sufficient (N > 100) to achieve statistical power > 0.8 for detecting moderate effect sizes (OR ≈ 1.5). If not, the results will be interpreted as exploratory with a noted power limitation.
- Tissue-specific stratification in FR-003 is sufficient to control for batch effects; if tissue composition differs significantly between MetS and Control groups, the logistic regression (FR-005) will account for residual confounding via the 'tissue' covariate.