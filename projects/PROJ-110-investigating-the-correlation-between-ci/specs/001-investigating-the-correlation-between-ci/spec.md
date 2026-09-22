# Feature Specification: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

**Feature Branch**: `001-circadian-metabolic-correlation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Metabolic Syndrome Status from Clinical Variables (Priority: P1)

The researcher must be able to programmatically classify **METSIM** donors as "Metabolic Syndrome" (MetS) or "Control" based on the ATP‑III criteria using available clinical phenotype data (BMI, fasting glucose, blood pressure, triglycerides, HDL). GTEx samples are **only** used for exploratory expression profiling where phenotype data are unavailable and are **not** used for primary MetS labeling.

**Why this priority**: This is the foundational step; without a binary or ordinal label for the outcome variable, no correlation analysis can be performed. METSIM provides in‑vivo clinical measurements, ensuring construct validity of the MetS label, while GTEx is relegated to exploratory use.

**Independent Test**: Can be fully tested by running the classification script on a known subset of METSIM data and verifying that the output matches manual calculation of ATP‑III criteria for those specific samples. The script also validates its output against `classification.schema.yaml`; any mismatch aborts the pipeline.

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
4. **Given** a tissue with fewer than 20 samples in either the MetS or Control group, **When** the test runs, **Then** the system either applies the hierarchical mixed‑effects ANCOVA fallback (see FR‑020) if pooled tissues reach the sample minimum, otherwise the tissue is excluded from the analysis and logs a "low power" warning to stderr with level WARNING.

### User Story 3 - Build Predictive Logistic Regression Model with Covariates (Priority: P3)

The researcher must be able to fit a multivariate logistic regression model predicting MetS status using circadian gene expression levels and key covariates (age, sex, tissue type, PMI, Time of Death), and evaluate its performance via cross‑validation.

**Why this priority**: This moves beyond simple association to multivariate prediction, controlling for confounders. It provides a more robust test of the hypothesis but relies on the successful completion of US‑01 and US‑02.

**Independent Test**: Can be fully tested by training the model on a training split, evaluating on a validation split, and verifying that the Area Under the Curve (AUC) and confidence intervals are calculated and reported.

**Acceptance Scenarios**:

1. **Given** the expression data and labels, **When** the logistic regression model is trained with k‑fold cross‑validation, **Then** the system reports an average AUC score and 95% confidence intervals.
2. **Given** the trained model, **When** the odds ratios for each gene are extracted, **Then** the output includes the odds ratio, standard error, and p‑value for each predictor.
3. **Given** a model with collinear predictors (if any), **When** the diagnostic check runs, **Then** the system flags the collinearity (VIF > 5) and reports the joint descriptive relationship rather than claiming independent effects.
4. **Given** the inclusion of sequencing batch as a covariate, **When** the batch‑sensitivity analysis runs, **Then** the model coefficients are compared with and without batch; stability ≥ 90% is required for reporting.

### User Story 4 - External Validation in an Independent Cohort (Priority: P4)

The researcher must validate the key differential‑expression and predictive‑model findings in an independent public dataset (e.g., METSIM muscle RNA‑seq cohort) to confirm generalizability.

**Why this priority**: External validation addresses the methodological requirement for independent confirmation and mitigates the limitation of GTEx’s case scarcity.

**Independent Test**: Can be fully tested by reproducing the DE and logistic‑regression pipelines on the METSIM dataset and checking that the direction of effects and predictive performance are consistent with GTEx results.

**Acceptance Scenarios**:

1. **Given** the METSIM expression matrix and MetS phenotype data, **When** the DE pipeline (FR‑013) is applied, **Then** the system reports concordant significant genes with **gene‑level overlap ≥ 15%** of GTEx hits and provides a replication p‑value.
2. **Given** the trained GTEx logistic model, **When** it is applied to METSIM samples, **Then** the system reports an AUC that is not significantly lower than the GTEx cross‑validated AUC (ΔAUC ≤ 0.05, two‑sided test, α = 0.05).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the METSIM muscle RNA‑seq TPM matrices **and** associated phenotype files that contain all five ATP‑III clinical variables (BMI, fasting glucose, blood pressure, triglycerides, HDL). GTEx v8 TPM matrices may be downloaded as *exploratory* supplementary expression data only. All raw input files MUST be validated against `dataset.schema.yaml`. Samples with missing, null, NaN, or numerically invalid values (e.g., < ‑1) for any of the five ATP‑III clinical variables **AND** with post‑mortem interval (PMI) > 24 h MUST be excluded from the analysis cohort with a log entry. If the number of complete METSIM cases is < 100, the system MUST set `study_status=exploratory`, write a warning “Insufficient METSIM sample size (N < 100) for robust power; study limited to exploratory analysis”, and **optionally** supplement the cohort with GTEx Normal Tissue samples for tissues lacking metabolic‑trait annotations (see FR‑011). (See US‑01)

- **FR-002**: System MUST classify each donor into "MetS" or "Control" groups strictly according to the ATP‑III criteria (≥ 3 of the 5 thresholds met). The ATP‑III definition is verified by the National Cholesterol Education Program Adult Treatment Panel III guideline. Classification output MUST be validated against `classification.schema.yaml`. (See US‑01)

- **FR-003**: System MUST perform covariate‑adjusted differential expression analysis (ANCOVA) comparing each core circadian gene between MetS and Control groups, **stratified by tissue**, and including age, sex, PMI, and Time‑of‑Death as covariates. **If a tissue has < 20 samples per group**, the system MAY apply a hierarchical mixed‑effects ANCOVA that pools biologically similar tissues (see FR‑020) to retain power; otherwise the tissue is excluded with a WARNING. (See US‑02)

- **FR-004**: System MUST apply a **global** Benjamini‑Hochberg False Discovery Rate correction across **all** gene‑tissue tests generated by FR‑003, controlling the overall FDR at q < 0.05. (See US‑02)

- **FR-005**: System MUST fit a multivariate logistic regression model predicting MetS status using **the most variable core circadian genes** (pre‑selected by coefficient of variation) **plus** covariates age, sex, tissue, PMI, Time‑of‑Death, and batch. The total number of predictors (≤ 10) must respect a predictor‑to‑sample ratio ≤ 1:10 (enforced by FR‑021). The model MUST incorporate L2 regularization (λ = 1.0) to mitigate over‑fitting. The model MUST also include a continuous severity score (sum of 5 ATP‑III criteria) as an alternative outcome variable for auxiliary association checks. Metabolic‑trait variables (BMI, glucose, BP, triglycerides, HDL) are **NOT** used as predictors to avoid circular validation. (See US‑03)

- **FR-006**: System MUST perform k‑fold (default 5‑fold) cross‑validation to evaluate model performance (AUC) and prevent overfitting. (See US‑03)

- **FR-007**: System MUST compute tissue‑specific correlations between each core circadian gene and continuous metabolic traits (BMI, glucose, etc.) using Spearman’s ρ by default; Pearson’s r is used only if Shapiro‑Wilk normality test p > 0.05 for the trait‑gene pair. Correlations are modeled with a mixed‑effects linear model with a random intercept for tissue. Benjamini‑Hochberg correction is applied **globally** across all gene‑trait tests. Genes with adjusted p < 0.05 **and** |ρ| ≥ 0.2 are highlighted as significant; non‑significant genes are reported with raw ρ and p‑value. Hypothesis testing against the null ρ = 0 is performed (see FR‑024). (See US‑02)

- **FR-008**: System MUST generate diagnostic plots (heatmap of DE results, ROC curve for the logistic model, scatter plots of significant correlations) for significant findings. (See US‑02, US‑03)

- **FR-009**: System MUST report odds ratios **only for the gene‑expression predictors** from the logistic regression model (see FR‑005). For each metabolic trait (BMI, glucose, BP, triglycerides, HDL) the system MUST also provide a separate **descriptive** univariate logistic regression summary (odds ratio, 95% CI, p‑value); these summaries are **not** part of the multivariate model and do not influence its predictions. (See US‑03)

- **FR-010**: System MUST reproduce the DE pipeline (FR‑013) and logistic‑regression evaluation (FR‑005) on an independent solid‑tissue cohort (e.g., METSIM muscle RNA‑seq dataset) and report replication metrics (gene‑overlap proportion, AUC comparison). Gene‑level overlap of significant DE genes must be ≥ 15% of GTEx hits, and AUC difference ≤ 0.05 (two‑sided test, α = 0.05). (See US‑04)

- **FR‑011**: System MUST conduct an a priori power analysis for the logistic regression using α = 0.05, desired power ≥ 0.80, expected odds ratio > 1, and 15 predictors (genes + covariates). If the calculated required sample size exceeds the available complete donors, the system flags the study as exploratory and records the power estimate. (See US‑01)

- **FR‑012**: System MUST apply a **global** Benjamini‑Hochberg FDR correction across **all** correlation tests (gene‑trait pairs) to control the overall false discovery rate at q < 0.05. (See US‑02)

- **FR‑013**: System MUST perform covariate‑adjusted differential expression (ANCOVA) per tissue, including age, sex, PMI, and Time‑of‑Death as covariates, and output effect sizes (β) with 95% CI. Output MUST be validated against `de_results.schema.yaml`. (See US‑02)

- **FR‑014**: System MUST fit a mixed‑effects model for gene‑trait correlations with tissue as a random effect, as described in FR‑007. Correlation output files MUST conform to `correlation_results.schema.yaml`. (See US‑02)

- **FR‑015**: System MUST run a batch‑effect sensitivity analysis by refitting the logistic regression with and without a sequencing‑batch covariate; coefficient stability ≥ 90 % is required for reporting. (See US‑03)

- **FR‑016**: System MUST perform an a priori power analysis for tissue‑stratified differential expression (ANCOVA) using a medium effect size f = 0.25, α = 0.05, power ≥ 0.80. Required sample size per group is logged; if insufficient, the hierarchical fallback in FR‑003 is activated. (See US‑02)

- **FR‑017**: System MUST perform an a priori power analysis for gene‑trait correlations targeting a correlation coefficient r = 0.3, α = 0.05, power ≥ 0.80. Required sample size is logged; if insufficient, results are labeled exploratory. (See US‑02)

- **FR‑018**: All input and output files (raw METSIM‑MetS data, donor classification files, DE results, correlation results, logistic‑regression coefficients, cross‑validation performance, and external‑validation metrics) MUST be validated against their respective schema contracts (`dataset.schema.yaml`, `classification.schema.yaml`, `de_results.schema.yaml`, `correlation_results.schema.yaml`, `logistic_regression.schema.yaml`, `model.schema.yaml`, `validation_results.schema.yaml`). Validation failures abort the pipeline. (See US‑01‑US‑04)

- **FR‑019**: System MUST compute statistical power for tissue‑stratified differential expression and gene‑trait correlation analyses accounting for the multiple‑testing burden (Bonferroni‑adjusted α) and report whether the planned sample size meets the ≥ 0.80 power threshold. (See US‑02)

- **FR‑020**: When a tissue does not meet the per‑group sample minimum (≥ 20), the system SHALL apply a hierarchical mixed‑effects ANCOVA pooling biologically similar tissues (e.g., brain sub‑regions) to increase effective sample size, provided the pooled group reaches ≥ 20 samples per condition; otherwise the tissue is excluded with a logged warning. (See US‑02)

- **FR‑021**: Prior to fitting the logistic regression, the system SHALL compute the maximum allowable number of predictors as floor(N_cases / 10) and truncate the predictor list accordingly to maintain a predictor‑to‑sample ratio ≤ 1:10, ensuring model stability. (See US‑03)

- **FR‑022**: After DE analysis, the system SHALL report (a) the count and (b) the proportion of core circadian genes that are significant (FDR < 0.05) **per tissue** and **overall**, and store these metrics for SC‑002 evaluation. (See US‑02)

- **FR‑023**: System MUST compare the logistic‑regression AUC against a random‑classifier baseline (AUC = 0.5) using a DeLong test; the improvement must be statistically significant (two‑sided p < 0.05) and reported alongside the raw AUC. (See US‑03)

- **FR‑024**: For each gene‑trait correlation, the system SHALL perform a hypothesis test of ρ = 0, report the p‑value, and require |ρ| ≥ 0.2 for biological relevance, satisfying SC‑004. (See US‑02)

- **FR‑025**: System MUST conduct a sensitivity analysis by varying each ATP‑III threshold independently by ±5 % and recomputing donor labels; ≥ 90 % of labels must remain unchanged. The stability proportion is reported as part of SC‑005. (See US‑01)

- **FR‑026**: System MUST use a primary cohort that provides both RNA‑seq expression and the full set of ATP‑III clinical measurements (e.g., METSIM muscle cohort). GTEx data may be used only for exploratory expression profiling where phenotype data are unavailable. (See US‑01)

- **FR‑027**: Correlation results files (`correlation_results.csv`) MUST conform to `correlation_results.schema.yaml`; validation failures abort the pipeline. (See US‑02)

- **FR‑028**: Logistic‑regression output files (`logistic_model_coefficients.csv`, `cv_performance.csv`) MUST conform to `logistic_regression.schema.yaml` and `model.schema.yaml`; validation failures abort the pipeline. (See US‑03)

- **FR‑029**: Validation‑step output (`validation_results.csv`) MUST conform to `validation_results.schema.yaml`; validation failures abort the pipeline. (See US‑04)

- **FR‑030**: System MUST perform a post‑mortem interval (PMI) sensitivity analysis by comparing MetS classification results for donors with PMI ≤ 12 h versus PMI ≤ 24 h; ≥ 95 % label concordance is required to confirm robustness of ATP‑III criteria on post‑mortem samples. (See US‑01)

- **FR‑031**: System MUST document any observed systematic shifts in clinical variables due to PMI and, if detected, apply an adjustment model (linear regression of variable on PMI) before classification. (See US‑01)

### Key Entities *(include if feature involves data)*

- **Donor**: Represents a human subject; attributes include ID, age, sex, tissue source, clinical measurements (BMI, BP, lipids, glucose), Post‑Mortem Interval (PMI), and Time of Death.
- **GeneExpression**: Represents the transcript abundance; attributes include Gene Symbol, TPM value, and log‑transformed value.
- **MetabolicStatus**: Represents the binary classification; attributes include Label ("MetS" or "Control") and CriteriaCount (0‑5).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of donors successfully classified as MetS or Control is measured against the total number of METSIM‑MetS samples with complete phenotype data. (See US‑01)

- **SC-002**: The number and proportion of core circadian genes showing statistically significant differential expression (FDR < 0.05, global correction) is measured per tissue and overall; these metrics are produced by FR‑022. (See US‑02)

- **SC-003**: The Area Under the Curve (AUC) of the logistic regression model is measured against a baseline random classifier (AUC = 0.5); the model must achieve AUC ≥ 0.6 **and** the improvement over baseline must be statistically significant (DeLong two‑sided p < 0.05) as required by FR‑023. (See US‑03)

- **SC-004**: The magnitude of the correlation coefficient (ρ) between gene expression and continuous metabolic traits is measured against the null hypothesis of no correlation (ρ = 0) by requiring two‑sided p < 0.05 **and** |ρ| ≥ 0.2 for a result to be considered biologically meaningful, as enforced by FR‑024. (See US‑02)

- **SC-005**: Sensitivity analysis varying each ATP‑III threshold independently by ±5 % must result in ≥ 90 % of donor labels remaining unchanged; the stability proportion is reported as required by FR‑025. (See US‑01)

- **SC-006**: Replication success is measured as (a) ≥ 15 % gene‑level overlap of significant DE genes between METSIM and GTEx (adjusted for tissue mismatch) and (b) AUC difference ≤ 0.05 (two‑sided test, α = 0.05). (See US‑04)

- **SC-007**: Power analysis results for logistic regression (FR‑011), DE (FR‑016, FR‑019), and correlation (FR‑017, FR‑019) are reported, including required sample sizes and whether the study meets the ≥ 0.80 power threshold. (See US‑01‑US‑03)

- **SC-008**: All generated files are confirmed to pass schema validation (FR‑018); validation pass rates are reported as [deferred] for a successful run. (See US‑01‑US‑04)

## Assumptions

- The primary dataset is the METSIM muscle RNA‑seq cohort, which includes measured fasting glucose, triglycerides, HDL, blood pressure, and BMI, enabling direct application of ATP‑III criteria.
- GTEx v8 TPM matrices are used only for exploratory supplementary expression analyses where phenotype data are unavailable; they are not the source of MetS labels.
- The "Core Circadian Genes" list (PER1‑3, CRY1‑2, BMAL1, CLOCK, NR1D1, RORα) is sufficient to capture the relevant biological signal; other circadian genes may be omitted.
- Post‑mortem interval (PMI) ≤ 24 h is required to limit artefactual shifts; literature (Brown et al., Nat Commun 2020) supports that ATP‑III criteria remain valid within this PMI window, and FR‑030/FR‑031 explicitly test robustness to PMI.
- The analysis will run on a CPU‑only environment (GitHub Actions free tier); therefore, only classical statistical methods (ANCOVA, mixed‑effects models, Logistic Regression) and standard Python libraries (scikit‑learn, statsmodels, pandas) are employed.
- Benjamini‑Hochberg correction is appropriate for the moderate number of tests; a global correction across all gene‑tissue (or gene‑trait) tests is applied to control the overall false discovery rate.
- The ATP‑III criteria are considered valid proxies for MetS status in a research setting using post‑mortem tissue, provided the sensitivity analysis (SC‑005) confirms label stability and the PMI robustness checks (FR‑030, FR‑031) demonstrate no systematic bias.
- The a priori power analyses (FR‑011, FR‑016, FR‑017, FR‑019) assume α = 0.05, power ≥ 0.80, expected odds ratio ≈ 1.5 for logistic regression, effect size f = 0.25 for ANCOVA, and correlation coefficient r = 0.3 for gene‑trait tests; if required sample sizes exceed available donors, results are interpreted as exploratory with documented power limitations.
- Tissue‑specific stratification in FR‑003 and mixed‑effects modeling in FR‑007 are sufficient to control for batch effects and residual confounding; additional batch‑sensitivity analysis (FR‑015) will assess robustness to unmeasured confounders.
- All processed artifacts are stored under `data/processed/` in compliance with Constitution Principle IV (Single Source of Truth).
- FR‑009 reports odds ratios for individual metabolic traits only as descriptive, univariate summaries; they are **not** used as predictors in the multivariate logistic model, preserving independence between predictors and outcome.