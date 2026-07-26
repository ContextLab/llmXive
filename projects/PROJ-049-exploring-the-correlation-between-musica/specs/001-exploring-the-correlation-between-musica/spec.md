# Feature Specification: Exploring the Correlation Between Musical Preference and Personality Traits

**Feature Branch**: `001-music-personality-correlation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Do individuals with specific Big Five personality traits show statistically significant preferences for particular musical genres? How strong are these correlations after controlling for demographic variables such as age, gender, and cultural background?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (US-1)

The system must successfully ingest the Big Five Inventory (BFI-2) dataset from OpenML and Last.fm listening data, cleaning and merging them into a unified analysis-ready dataframe.

**Why this priority**: Without a clean, merged dataset containing both personality scores and genre preferences, no statistical analysis can be performed. This is the foundational step for the entire research pipeline.

**Independent Test**: The pipeline can be tested by executing the data loading script and verifying the output dataframe contains non-null values for all personality traits and at least 10 standardized genre categories (plus 'Other') for a sample of at least 100 users, with no missing demographic covariates. Verification must reference the specific lookup table defined in FR-002.

**Acceptance Scenarios**:

1. **Given** the OpenML BFI-2 dataset and Last.fm archive are accessible, **When** the ingestion script runs, **Then** the system outputs a merged CSV where every row has valid scores for Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism.
2. **Given** raw genre tags from Last.fm, **When** the mapping logic executes, **Then** the system outputs a standardized genre column where ambiguous tags (e.g., "alt", "rock") are correctly consolidated into one of 10 predefined categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other) via the lookup table defined in FR-002.
3. **Given** a user record with missing demographic data (e.g., age), **When** the preprocessing step runs, **Then** that record is either imputed using a defined strategy (mean/median for numeric, mode for categorical) or excluded, and a log entry records the count of excluded rows and the strategy used.

---

### User Story 2 - Statistical Correlation and Regression Analysis (US-2)

The system must compute Pearson correlation coefficients between each Big Five trait and genre preference scores (log‑transformed listening minutes), and run multiple linear regression models controlling for age, gender, and country (encoded as dummy variables or regions).

**Why this priority**: This is the core analytical engine that directly answers the research question. It must handle the statistical logic correctly to produce valid results, accounting for skewed data distributions and high‑cardinality categorical variables.

**Independent Test**: The analysis can be tested by running the script on a known synthetic dataset with pre‑calculated correlation values and verifying the output matches the expected coefficients within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** the cleaned merged dataset, **When** the correlation matrix is computed, **Then** the system outputs a 5×N matrix of Pearson r‑values with p‑values for each trait‑genre pair, where N is the number of genres present.
2. **Given** the correlation results, **When** the regression models run, **Then** the system outputs a table of coefficients (beta), standard errors, and p‑values for each trait, adjusted for the three demographic covariates (country encoded via one‑hot or regional grouping).
3. **Given** the dataset contains >100 hypothesis tests (5 traits × N genres), **When** the significance testing completes, **Then** the system applies a Bonferroni correction (α = 0.05/50 ≈ 0.001) and flags results as "significant" only if adjusted p < 0.001.
4. **Given** the final correlation table, **When** the flagging step runs, **Then** the system records a Boolean flag `high_correlation` for any trait‑genre pair where |r| > 0.3 and stores this flag in the results CSV. (Implemented by FR‑008.)

---

### User Story 3 - Visualization and Reporting (US-3)

The system must generate visualizations of the correlation matrix and regression coefficients, and export a summary report containing Cohen’s d effect sizes (derived from Pearson r) and confidence intervals.

**Why this priority**: While the analysis produces raw numbers, the visualizations and report are required for human interpretation and validation of the "Expected results" (e.g., verifying practical importance via Cohen’s d).

**Independent Test**: The reporting module can be tested by executing the script and verifying the existence of a `results_report.csv` and a `correlation_heatmap.png` file, ensuring the heatmap correctly displays the sign and magnitude of Pearson correlations and that the report includes Cohen’s d with 95 % confidence intervals.

**Acceptance Scenarios**:

1. **Given** the regression results, **When** the visualization script runs, **Then** the system generates a heatmap image where the color intensity corresponds to the absolute value of the Pearson correlation coefficient.
2. **Given** the statistical outputs, **When** the report is generated, **Then** the system exports a CSV containing Cohen’s d effect sizes for all significant correlations and confidence intervals derived from Fisher’s z‑transformation of the underlying Pearson r.
3. **Given** a non‑significant trait‑genre pair, **When** the report is generated, **Then** the system explicitly labels that pair as "Non‑significant (adjusted p ≥ 0.001)" rather than omitting it.

---

### Edge Cases

- What happens if the OpenML or Last.fm datasets are unavailable or return HTTP 404 errors during the CI run? (System must fail gracefully with a clear error message and not hang).
- How does the system handle users who have listened to zero songs in the Last.fm dataset? (These users must be excluded prior to correlation to avoid division by zero or NaN scores).
- What if the demographic data (e.g., country) has too many unique categories to be used as a single covariate? (The system must group rare countries into an "Other" category or exclude them).
- How does the system handle perfect collinearity if a genre is perfectly predicted by a demographic variable? (The regression model must detect and drop the collinear predictor, logging a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the BFI-2 dataset from OpenML and the Last.fm archive, validating that the download completes within 300 seconds. (See US-1)
- **FR-002**: System MUST map raw genre tags to a fixed set of standardized categories using a predefined lookup table, ensuring no raw tags remain in the final analysis dataset. (See US-1)
- **FR-003**: System MUST compute Pearson correlation coefficients for all trait‑genre pairs (using log‑transformed listening minutes) and calculate associated p‑values. (See US-2)
- **FR-004**: System MUST execute multiple linear regression models for each trait with age, gender, and country as covariates (country encoded via one‑hot encoding or regional grouping), returning beta coefficients and standard errors. (See US-2)
- **FR-005**: System MUST apply a Bonferroni correction (α = 0.05/50 ≈ 0.001) to adjust p‑values for the 5 × N comparisons before determining significance. (See US-2)
- **FR-006**: System MUST generate a correlation heatmap visualization and a summary CSV report containing Cohen’s d effect sizes (derived from Pearson r) and 95 % confidence intervals. (See US-3)
- **FR-007**: System MUST handle missing demographic data by either excluding rows with missing covariates or imputing them using a defined strategy (mean/median for numeric, mode for categorical), logging the count of excluded rows and the strategy used. (See US-1)
- **FR-008**: System MUST flag any trait‑genre pair where |Pearson r| > 0.3 and record this Boolean flag in the results table. (See US-2)

### Key Entities

- **UserRecord**: Represents a single participant, containing attributes: `user_id`, `openness_score`, `conscientiousness_score`, `extraversion_score`, `agreeableness_score`, `neuroticism_score`, `age`, `gender`, `country`.
- **GenrePreference**: Represents the aggregated listening data for a user, containing attributes: `user_id`, `genre_name`, `listening_minutes`, `genre_score` (normalized).
- **AnalysisResult**: Represents the output of the statistical tests, containing attributes: `trait`, `genre`, `correlation_r`, `p_value`, `adjusted_p_value`, `is_significant`, `cohens_d`, `ci_lower`, `ci_upper`, `high_correlation_flag`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The absolute Pearson correlation coefficient |r| is calculated for each trait‑genre pair; a Boolean flag `high_correlation` is set to True when |r| > 0.3. (See US-2)
- **SC-002**: Statistical significance is measured against a Bonferroni‑adjusted p‑value threshold of 0.001 to control the family‑wise error rate. (See US-2)

## Assumptions

- **Assumption about data availability**: The OpenML BFI-2 dataset and the Last.fm public archive are accessible without authentication and contain sufficient user overlap or sample sizes to perform correlation analysis.
- **Assumption about computational constraints**: The combined size of the downloaded datasets and the intermediate processed dataframe will fit within the available RAM limit of the GitHub Actions free‑tier runner, allowing for in‑memory processing without disk‑swap.
- **Assumption about methodological framing**: The study is observational; therefore, all reported relationships are framed as associational correlations, not causal effects, as the data lacks random assignment.
- **Assumption about genre mapping**: The predefined lookup table for mapping raw genre tags to standardized categories covers >95 % of all unique tags found in the Last.fm dataset; the remaining tags are grouped into an "Other" category.
- **Assumption about sensitivity analysis**: A sensitivity analysis for the significance threshold will be performed by sweeping the α level across {0.01, 0.005, 0.001} to verify result stability, as no specific cutoff was mandated beyond the Bonferroni‑controlled 0.001.
- **Assumption about measurement validity**: The BFI-2 instrument used in the dataset is treated as a validated measure of the Big Five traits, requiring no further psychometric validation within this scope.
- **Assumption about collinearity**: Demographic variables (age, gender, country) are assumed to have low multicollinearity with personality traits; if Variance Inflation Factor (VIF) > 5 is detected, the model will drop the offending covariate and log a warning.
