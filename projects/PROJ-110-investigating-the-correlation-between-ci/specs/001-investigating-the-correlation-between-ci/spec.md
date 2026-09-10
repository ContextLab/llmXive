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
2. **Given** a donor with only 2 criteria met (e.g., BMI ≥ 30 and HDL < 40), **When** the script runs, **Then** the donor is labeled "Control".
3. **Given** a donor with missing data for one of the five criteria (e.g., fasting glucose), **When** the script runs, **Then** the donor is excluded from the analysis with a log entry indicating the missing variable.

### User Story 2 - Perform Differential Expression Analysis on Core Circadian Genes (Priority: P2)

The researcher must be able to compare the expression levels (TPM) of a predefined list of core circadian genes (e.g., *PER1*, *BMAL1*, *CLOCK*) between the "MetS" and "Control" groups using covariate‑adjusted statistical tests, with appropriate multiple‑comparison correction.

**Why this priority**: This directly tests the primary hypothesis (association between gene expression and syndrome status). It is the core analytical engine of the study.

**Independent Test**: Can be fully tested by executing the statistical analysis pipeline on the pre‑processed data and verifying that the output includes a table of adjusted p‑values and effect size estimates for each gene.

**Acceptance Scenarios**:

1. **Given** the expression matrix and group labels for a specific tissue, **When** the covariate‑adjusted ANCOVA model (including age, sex, PMI, and Time‑of‑Death) is executed, **Then** the system outputs an adjusted p‑value for each of the core circadian genes for that tissue.
2. **Given** the raw p‑values from the previous step, **When** the global Benjamini‑Hochberg procedure is applied across all gene‑tissue tests, **Then** the system outputs adjusted p‑values (FDR) where the overall false discovery rate is controlled at q < 0.05.
3. **Given** a gene with no expression difference between groups, **When** the test runs, **Then** the adjusted p‑value is > 0.05, and the gene is not flagged as significant.
4. **Given** a tissue with fewer than 20 samples in either the MetS or Control group, **When** the test runs, **Then** the system excludes that tissue from the analysis and logs a "low power" warning to stderr with level WARNING.

### User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

The researcher must be able to fit a multivariate logistic regression model predicting MetS status using circadian gene expression levels and key covariates (age, sex, tissue type, PMI, Time of Death), and evaluate its performance via cross‑validation.

**Why this priority**: This moves beyond simple association to multivariate prediction, controlling for confounders. It provides a more robust test of the hypothesis but relies on the successful completion of US‑01 and US‑02.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

**Acceptance Scenarios**:

1. **Given** the expression data and labels, **When** the logistic regression model is trained with 5‑fold cross‑validation, **Then** the system reports an average AUC score and 95% confidence intervals.
2. **Given** the trained model, **When** the odds ratios for each gene are extracted, **Then** the output includes the odds ratio, standard error, and p‑value for each predictor.
3. **Given** a model with collinear predictors (if any), **When** the diagnostic check runs, **Then** the system flags the collinearity (VIF > 5) and reports the joint descriptive relationship rather than claiming independent effects.
4. **Given** the inclusion of sequencing batch as a covariate, **When** the batch‑sensitivity analysis runs, **Then** the model coefficients are compared with and without batch; stability ≥ 90% is required for reporting.

### User Story 4 - External Validation in an Independent Cohort (Priority: P4)

The researcher must validate the key differential‑expression and predictive‑model findings in an independent public dataset (e.g., MESA RNA‑seq cohort) to confirm generalizability.

**Why this priority**: External validation addresses the methodological requirement for independent confirmation and mitigates the limitation of GTEx’s case scarcity.

**Independent Test**: Can be fully tested by reproducing the DE and logistic‑regression pipelines on the MESA dataset and checking that the direction of effects and predictive performance are consistent with GTEx results.

**Acceptance Scenarios**:

1. **Given** the MESA expression matrix and MetS phenotype data, **When** the DE pipeline (FR‑013) is applied, **Then** the system reports concordant significant genes (overlap ≥ 30% of GTEx hits) and provides a replication p‑value.
2. **Given** the trained GTEx logistic model, **When** it is applied to MESA samples, **Then** the system reports an AUC that is not significantly lower than the GTEx cross‑validated AUC (ΔAUC ≤ 0.05, two‑sided test, α = 0.05).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse GTEx v8 RNA‑seq TPM matrices and associated phenotype files. Samples with missing, null, NaN, or numerically invalid values (e.g., < ‑1) for any of the five ATP‑III clinical variables (BMI, fasting glucose, blood pressure (systolic ≥ 130 mmHg **or** diastolic ≥ 85 mmHg), triglycerides, HDL) MUST be excluded from the analysis cohort with a log entry. If the number of complete GTEx cases is < 100, the system MUST set `study_status=exploratory`, write a warning “Insufficient GTEx sample size (N < 100) for robust power; study limited to exploratory analysis”, and **optionally** supplement the cohort with TCGA Normal Tissue samples for tissues lacking metabolic‑trait annotations (see FR‑011). (See US‑01)
- **FR-002**: System MUST classify each donor into "MetS" or "Control" groups strictly according to the ATP‑III criteria (≥ 3 of the 5 thresholds met). The ATP‑III definition is verified by the National Cholesterol Education Program Adult Treatment Panel III guideline (). (See US‑01)
- **FR-003**: System MUST perform covariate‑adjusted differential expression analysis (ANCOVA) comparing each core circadian gene between MetS and Control groups, **stratified by tissue**, and including age, sex, PMI, and Time‑of‑Death as covariates. Tissues with < 20 samples per group are excluded with a WARNING. (See US‑02)
- **FR-004**: System MUST apply a **global** Benjamini‑Hochberg False Discovery Rate correction across **all** gene‑tissue tests generated by FR‑003, controlling the overall FDR at q < 0.05. (See US‑02)
- **FR-005**: System MUST fit a multivariate logistic regression model (`MetS ~ gene_expression + age + sex + tissue + PMI + Time_of_Death + batch`) and calculate odds ratios with 95% confidence intervals. The model MUST also include a continuous severity score (sum of 5 ATP‑III criteria) as an alternative outcome variable to validate associations against a non‑binary metric. (See US‑03)
- **FR-006**: System MUST perform k‑fold (default 5‑fold) cross‑validation to evaluate model performance (AUC) and prevent overfitting. (See US‑03)
- **FR-007**: System MUST compute tissue‑specific correlations between each core circadian gene and continuous metabolic traits (BMI, glucose, etc.) using Spearman’s ρ by default; Pearson’s r is used only if Shapiro‑Wilk normality test p > 0.05 for the trait‑gene pair. Correlations are modeled with a mixed‑effects linear model with a random intercept for tissue to account for tissue‑level expression differences. Benjamini‑Hochberg correction is applied **globally** across all gene‑trait tests. Genes with adjusted p < 0.05 are highlighted as significant; non‑significant genes are reported with raw ρ and p‑value. (See US‑02)
- **FR-008**: System MUST generate diagnostic plots (heatmap of DE results, ROC curve for the logistic model, scatter plots of significant correlations) for significant findings. (See US‑02, US‑03)
- **FR-009**: System MUST report odds ratios for individual metabolic traits (BMI, glucose, etc.) alongside gene expression odds ratios in the logistic regression output to distinguish between predicting the label and predicting the underlying state. (See US‑03)
- **FR-010**: System MUST reproduce the DE pipeline (FR‑013) and logistic‑regression evaluation (FR‑005) on an independent public cohort (e.g., MESA) and report replication metrics (gene‑overlap proportion, AUC comparison). (See US‑04)
- **FR‑011**: System MUST conduct an a priori power analysis for the logistic regression using α = 0.05, desired power ≥ 0.80, expected odds ratio ≈ moderately elevated (i.e., above unity), and 15 predictors (genes + covariates). If the calculated required sample size exceeds the available complete donors, the system flags the study as exploratory and records the power estimate. (See US‑01)
- **FR‑012**: System MUST apply a **global** Benjamini‑Hochberg FDR correction across **all** correlation tests (gene‑trait pairs) to control the overall false discovery rate at q < 0.05. (See US‑02)
- **FR‑013**: System MUST perform covariate‑adjusted differential expression (ANCOVA) per tissue, including age, sex, PMI, and Time‑of‑Death as covariates, and output effect sizes (β) with 95% CI. (See US‑02)
- **FR‑014**: System MUST fit a mixed‑effects model for gene‑trait correlations with tissue as a random effect, as described in FR‑007. (See US‑02)
- **FR‑015**: System MUST run a batch‑effect sensitivity analysis by refitting the logistic regression with and without a sequencing‑batch covariate; coefficient stability ≥ 90 % is required for reporting. (See US‑03)

### Key Entities *(include if feature involves data)*

- **Donor**: Represents a human subject; attributes include ID, age, sex, tissue source, clinical measurements (BMI, BP, lipids, glucose), Post‑Mortem Interval (PMI), and Time of Death.
- **GeneExpression**: Represents the transcript abundance; attributes include Gene Symbol, TPM value, and log‑transformed value.
- **MetabolicStatus**: Represents the binary classification; attributes include Label ("MetS" or "Control") and CriteriaCount (0‑5).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of donors successfully classified as MetS or Control is measured against the total number of GTEx v8 samples with complete phenotype data. (See US‑01)
- **SC-002**: The number of core circadian genes showing statistically significant differential expression (FDR < 0.05, global correction) is measured against the total number of core circadian genes tested. (See US‑02)
- **SC-003**: The Area Under the Curve (AUC) of the logistic regression model is measured against a baseline random classifier (AUC = 0.5) to determine predictive utility. (See US‑03)
- **SC-004**: The magnitude of the correlation coefficient (ρ) between gene expression and continuous metabolic traits is measured against the null hypothesis of no correlation (ρ = 0). (See US‑02)
- **SC-005**: Sensitivity analysis varies each ATP‑III threshold independently by ±5 % and requires that ≥ 90 % of donor labels remain unchanged. (See US‑01)
- **SC-006**: Replication success is measured as (a) ≥ 30 % overlap of significant DE genes between GTEx and MESA, and (b) AUC difference ≤ 0.05 (two‑sided test, α = 0.05). (See US‑04)

## Assumptions

- The GTEx v8 dataset contains the specific clinical variables (fasting glucose, triglycerides, HDL, blood pressure) required to apply ATP‑III criteria; if any variable is missing for a large portion of samples, the sample size will be significantly reduced, potentially affecting power.
- GTEx donors are predominantly healthy; therefore GTEx is used for **exploratory** analysis only. Primary hypothesis testing will be corroborated with an independent cohort (e.g., MESA) that contains clinically ascertained MetS diagnoses.
- When GTEx yields < 100 complete donors, the study proceeds with `study_status=exploratory` **and** attempts optional supplementation with TCGA Normal Tissue samples for tissues lacking metabolic‑trait annotations, provided those samples have compatible phenotype data.
- The "Core Circadian Genes" list (PER1‑3, CRY1‑2, BMAL1, CLOCK, NR1D1, RORα) is sufficient to capture the relevant biological signal; other circadian genes may be omitted.
- The GTEx tissue samples, though not time‑stamped, contain sufficient biological variance in gene expression to detect associations with metabolic status, assuming the metabolic syndrome itself induces a disruption in circadian rhythm detectable in bulk tissue. PMI and Time‑of‑Death are included as covariates to partially account for circadian phase variance (see Brown et al., Nat. Commun. 2020).
- The analysis will run on a CPU‑only environment (GitHub Actions free tier); therefore, no GPU‑accelerated deep learning models or 8‑bit quantization will be used; only classical statistical methods (ANCOVA, mixed‑effects models, Logistic Regression) and standard libraries (scikit‑learn, statsmodels, pandas) will be employed.
- The Benjamini‑Hochberg correction is appropriate for the moderate number of tests; a global correction across all gene‑tissue (or gene‑trait) tests is applied to control the overall false discovery rate.
- The ATP‑III criteria, originally designed for clinical diagnosis, are valid proxies for "Metabolic Syndrome" in a research setting using post‑mortem tissue samples; the criteria are cited from the NCEP Adult Treatment Panel III guideline (2001).
- The a priori power analysis (FR‑011) assumes α = 0.05, power ≥ 0.80, expected odds ratio ≈ 1.5, and 15 predictors; if the required sample size exceeds available complete donors, results are interpreted as exploratory with a documented power limitation.
- Tissue‑specific stratification in FR‑003 and mixed‑effects modeling in FR‑007 are sufficient to control for batch effects and residual confounding; additional batch‑sensitivity analysis (FR‑015) will assess robustness to unmeasured confounders.