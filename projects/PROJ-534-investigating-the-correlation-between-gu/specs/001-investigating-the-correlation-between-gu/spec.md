# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

**Feature Branch**: `001-gut-microbiome-cognitive-flexibility`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Cohort Filtering (Priority: P1)

The system MUST ingest 16S rRNA sequencing data and linked cognitive assessment data, then filter the cohort to include only participants aged 65+ with complete data for both modalities.

**Why this priority**: This is the foundational step. Without a valid, filtered dataset containing both microbiome and cognitive metrics for the target demographic, no analysis can proceed. It represents the "Minimum Viable Product" of the data pipeline.

**Independent Test**: The system can be tested by running the ingestion script on a small, synthetic dataset containing mixed ages and missing values, verifying that the output CSV contains exactly the rows matching the age ≥ 65 criteria and non-null values for Shannon diversity and cognitive flexibility scores.

**Acceptance Scenarios**:

1. **Given** a raw dataset containing participants aged 20-80 with microbiome and cognitive data, **When** the filtering module runs, **Then** the output dataset contains ONLY participants aged 65 or older.
2. **Given** a participant record with valid microbiome data but missing cognitive flexibility scores, **When** the filtering module runs, **Then** that participant is excluded from the final analysis cohort.
3. **Given** a participant record with missing age data, **When** the filtering module runs, **Then** that participant is excluded to prevent age-group misclassification.

---

### User Story 2 - Diversity Metric Calculation and Correlation Analysis (Priority: P2)

The system MUST calculate alpha diversity (Shannon, Simpson, Chao1) and beta diversity (Bray-Curtis, UniFrac) metrics, then perform Pearson/Spearman correlation and linear regression to quantify the relationship with cognitive flexibility.

**Why this priority**: This constitutes the core scientific contribution of the project. It directly addresses the research question by generating the primary statistical evidence (effect sizes, p-values) linking the two phenomena.

**Independent Test**: The system can be tested by providing a pre-calculated matrix of diversity metrics and cognitive scores, verifying that the correlation coefficients match expected values derived from a manual calculation on a small subset, and that the linear regression model converges without error.

**Acceptance Scenarios**:

1. **Given** a filtered dataset with calculated alpha diversity scores, **When** the correlation analysis runs, **Then** the system outputs a correlation coefficient (Pearson or Spearman) and a p-value for each diversity metric against cognitive flexibility.
2. **Given** the same dataset, **When** the linear regression model runs, **Then** the system outputs the regression coefficients for diversity metrics while controlling for age, sex, and BMI.
3. **Given** multiple hypothesis tests (e.g., testing 3 diversity metrics), **When** the analysis completes, **Then** the system applies Benjamini-Hochberg correction and reports adjusted p-values.

---

### User Story 3 - Visualization and Power Estimation (Priority: P3)

The system MUST generate visualizations of diversity distributions across cognitive performance quartiles and estimate statistical power/effect sizes for future intervention studies.

**Why this priority**: While the correlation analysis provides the primary answer, these outputs are essential for interpreting the biological significance and planning future research, fulfilling the "Expected Results" and "Methodology" sections of the idea.

**Independent Test**: The system can be tested by running the visualization module on a sample dataset, verifying that the generated plots (e.g., boxplots of diversity by quartile) are rendered correctly and that the power estimation output includes a reported effect size and required sample size for [deferred] power.

**Acceptance Scenarios**:

1. **Given** the analysis results, **When** the visualization module runs, **Then** the system generates a plot showing alpha diversity distributions stratified by cognitive flexibility performance quartiles (Q1-Q4).
2. **Given** the observed effect size from the correlation analysis, **When** the power estimation module runs, **Then** the system outputs the minimum sample size required to achieve 80% power at α = 0.05 for a future study.
3. **Given** the regression results, **When** the report generation runs, **Then** the system produces a summary table containing the effect sizes, confidence intervals, and adjusted p-values.

---

### Edge Cases

- What happens when the dataset contains zero-inflated diversity metrics (e.g., all samples have identical diversity)? The system MUST handle this by flagging the dataset as having no variance and skipping correlation calculations to avoid division-by-zero errors.
- How does the system handle missing covariates (age, sex, BMI) for a subset of participants? The system MUST either exclude those specific participants from the regression analysis (listwise deletion) or impute them using a specified method, with the choice logged.
- What if the cognitive flexibility score distribution is heavily skewed? The system MUST detect non-normality and automatically switch from Pearson correlation to Spearman rank correlation, logging the switch.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest 16S rRNA sequencing data and linked cognitive assessment data from the specified public repository (e.g., American Gut Project) and merge them on a unique participant ID (See US-1).
- **FR-002**: System MUST filter the merged dataset to include ONLY participants aged ≥ 65 years with non-null values for at least one alpha diversity metric and one cognitive flexibility score (See US-1).
- **FR-003**: System MUST calculate alpha diversity metrics (Shannon, Simpson, Chao1) and beta diversity metrics (Bray-Curtis, UniFrac) for the filtered cohort (See US-2).
- **FR-004**: System MUST perform Pearson or Spearman correlation analysis between each alpha diversity metric and cognitive flexibility scores, including p-values and confidence intervals (See US-2).
- **FR-005**: System MUST execute a linear regression model with cognitive flexibility as the outcome and diversity metrics as predictors, controlling for age, sex, and BMI, and apply Benjamini-Hochberg correction for multiple comparisons (See US-2).
- **FR-006**: System MUST generate visualizations showing the distribution of diversity metrics across cognitive flexibility performance quartiles (See US-3).
- **FR-007**: System MUST calculate and report the statistical power and required sample size for a future intervention study based on the observed effect size (See US-3).

### Key Entities

- **Participant**: Represents an individual in the study, with attributes: `participant_id`, `age`, `sex`, `bmi`, `cognitive_flexibility_score`, `microbiome_sample_id`.
- **MicrobiomeProfile**: Represents the microbial composition of a sample, with attributes: `sample_id`, `shannon_diversity`, `simpson_diversity`, `chao1`, `bray_curtis_distance`.
- **AnalysisResult**: Represents the output of a statistical test, with attributes: `test_type`, `metric_name`, `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient magnitude and direction between alpha diversity and cognitive flexibility are measured against the null hypothesis of zero correlation to determine statistical significance (See US-2).
- **SC-002**: The variance explained (R-squared) by the linear regression model (diversity + covariates) is measured against the baseline model (covariates only) to assess the incremental predictive value of microbiome diversity (See US-2).
- **SC-003**: The statistical power of the study is measured against the standard threshold of 0.80 to determine if the sample size is sufficient to detect the observed effect size (See US-3).
- **SC-004**: The false discovery rate (FDR) after Benjamini-Hochberg correction is measured against the significance threshold of 0.05 to ensure robust identification of significant associations (See US-2).

## Assumptions

- **Assumption about data availability**: The American Gut Project (or the selected public repository) contains a sufficient number of participants in the older adult demographic with both 16S rRNA sequencing data and linked cognitive flexibility scores (e.g., NIH Toolbox or CANTAB) to achieve a minimum sample size of 100 for meaningful statistical power.
- **Assumption about data quality**: The public dataset provides pre-calculated alpha/beta diversity metrics or raw sequences that can be processed using standard, CPU-tractable tools (e.g., QIIME or phyloseq) within the 6-hour CI time limit and 7GB RAM constraint.
- **Assumption about cognitive measures**: The cognitive flexibility scores in the dataset are derived from validated instruments (e.g., NIH Toolbox Cognition Battery) that have established reliability and validity for use in aging populations.
- **Assumption about confounding**: The available covariates (age, sex, BMI) are sufficient to control for major confounding factors in the relationship between gut microbiome and cognitive flexibility; unmeasured confounders (e.g., diet, medication use) are assumed to be either negligible or partially captured by the microbiome profile itself.
- **Assumption about computational feasibility**: The dataset size (number of samples and features) will fit within the RAM limit of the GitHub Actions free-tier runner, allowing for in-memory processing of diversity calculations and regression models without requiring disk-based spillover or sampling.
- **Assumption about statistical framing**: The analysis is framed as observational and associational; no causal claims are made regarding the direction of the relationship between microbiome diversity and cognitive flexibility.
