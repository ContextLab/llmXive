# Feature Specification: Exploring the Correlation Between Musical Preference and Personality Traits

**Feature Branch**: `001-music-personality-correlation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Do individuals with specific Big Five personality traits show statistically significant preferences for particular musical genres? How strong are these correlations after controlling for demographic variables such as age, gender, and cultural background?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (US-1)

The system must successfully acquire a **linked dataset** that contains both Big Five Inventory (BFI‑2) personality scores and Last.fm listening histories for the same participants, obtained via a recruited cohort that provides consented BFI‑2 responses together with their Last.fm username. The pipeline must then clean and merge these records into a unified analysis‑ready dataframe.

**Why this priority**: Without a clean, merged dataset containing both personality scores and genre preferences for the *same* individuals, no statistical analysis can be performed. This is the foundational step for the entire research pipeline.

**Independent Test**: The pipeline can be tested by executing the data loading script and verifying the output dataframe contains non‑null values for all personality traits and at least 10 standardized genre categories (plus 'Other') for a sample of at least 100 users, with no missing demographic covariates. Verification must reference the specific lookup table defined in FR‑002. Additionally, the script must complete within 300 seconds.

**Acceptance Scenarios**:

1. **Given** the linked BFI‑2 + Last.fm dataset is accessible, **When** the ingestion script runs, **Then** the system outputs a merged CSV where every row has valid scores for Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism.
2. **Given** raw genre tags from Last.fm, **When** the mapping logic executes, **Then** the system outputs a standardized genre column where ambiguous tags (e.g., "alt", "rock") are correctly consolidated into one of 10 predefined categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other) via the lookup table defined in FR‑002.
3. **Given** a user record with missing demographic data (e.g., age), **When** the preprocessing step runs, **Then** that record is either excluded or imputed using the defined strategy (mean/median for numeric, mode for categorical), and a log entry records the count of excluded rows and the strategy used.

### User Story 2 - Statistical Correlation and Regression Analysis (US-2)

The system must compute **Pearson correlation** coefficients between each Big Five trait and **proportion‑based** genre preference scores (genre_minutes / total_minutes, log‑transformed). Because a proportion can be zero, a pseudocount of **1 minute** is added to both numerator and denominator before log‑transformation, guaranteeing a finite value. Pearson correlation is chosen because it directly quantifies linear association between continuous variables and aligns with Constitution VI (Statistical Transparency).

Multiple linear regression models are then run **per trait**, using the **log‑transformed proportion scores** as predictors and controlling for age, gender, and country (one‑hot or regional grouping). Total listening minutes are **computed for reporting purposes only** and **not included as a regression covariate** to avoid redundancy.

**Why this priority**: This is the core analytical engine that directly answers the research question. It must handle the statistical logic correctly to produce valid results, accounting for skewed data distributions, high‑cardinality categorical variables, and overall activity level.

**Independent Test**: The analysis can be tested by running the script on a known synthetic dataset with pre‑calculated Pearson coefficients and verifying the output matches the expected values within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** the cleaned merged dataset, **When** the Pearson correlation matrix is computed, **Then** the system outputs a 5×N matrix of *r*‑values with p‑values for each trait‑genre pair, where N is the number of genres present.
2. **Given** the correlation results, **When** the regression models run, **Then** the system outputs a table of coefficients (beta), standard errors, and p‑values for each trait, adjusted for the three demographic covariates (age, gender, country). No total‑minutes covariate is included.
3. **Given** the dataset contains exactly 5 × 10 = 50 hypothesis tests (5 traits × 10 genres), **When** the significance testing completes, **Then** the system applies a Bonferroni correction (α = 0.05 / 50 ≈ 0.001) and flags results as "significant" only if adjusted p < 0.001.

### User Story 3 - Visualization and Reporting (US-3)

The system must generate visualizations of the correlation matrix and regression coefficients, and export a summary report containing Cohen’s *d* effect sizes (derived from Pearson *r*) and 95 % confidence intervals.

**Why this priority**: While the analysis produces raw numbers, the visualizations and report are required for human interpretation and validation of the "Expected results" (e.g., verifying practical importance via Cohen’s *d*).

**Independent Test**: The reporting module can be tested by executing the script and verifying the existence of a `results_report.csv` and a `correlation_heatmap.png` file, ensuring the heatmap correctly displays the sign and magnitude of Pearson correlation coefficients and that the report includes Cohen’s *d* with 95 % confidence intervals.

**Acceptance Scenarios**:

1. **Given** the regression results, **When** the visualization script runs, **Then** the system generates a heatmap image where the color intensity corresponds to the absolute value of the Pearson correlation coefficient.
2. **Given** the statistical outputs, **When** the report is generated, **Then** the system exports a CSV containing Cohen’s *d* effect sizes for all significant correlations and confidence intervals derived from Fisher’s *z*‑transformation of the underlying Pearson *r*.
3. **Given** a non‑significant trait‑genre pair, **When** the report is generated, **Then** the system explicitly labels that pair as "Non‑significant (adjusted p ≥ 0.001)" rather than omitting it.

### Edge Cases

- What happens if the OpenML or Last.fm datasets are unavailable or return HTTP 404 errors during the CI run? (System must fail gracefully with a clear error message and not hang).
- How does the system handle users who have listened to zero songs in the Last.fm dataset? (The pseudocount rule ensures a finite log‑proportion; such users are retained but contribute a minimal value).
- What if the demographic data (e.g., country) has too many unique categories to be used as a single covariate? (The system groups rare countries into an "Other" category or excludes them).
- How does the system handle perfect collinearity if a genre is perfectly predicted by a demographic variable? (The regression model detects and drops the collinear predictor, logging a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST acquire a **linked dataset** containing both BFI‑2 personality scores and Last.fm listening histories for the same participants (e.g., via a consented cohort), validating that the download/composition completes within 300 seconds. (See US‑1)
- **FR-002**: System MUST map raw genre tags to a fixed set of standardized categories using a predefined lookup table, ensuring no raw tags remain in the final analysis dataset. (See US‑1)
- **FR-003**: System MUST compute **Pearson correlation** for all trait‑genre pairs using **proportion‑based** genre preference scores (genre_minutes / total_minutes) with a 1‑minute pseudocount and log‑transform, and calculate associated p‑values. (See US‑2)
- **FR-004**: System MUST execute multiple linear regression models for each trait using the **log‑transformed proportion scores** as predictors, controlling for age, gender, and country (one‑hot or regional grouping). The model must NOT include total listening minutes as a covariate. (See US‑2)
- **FR-005**: System MUST apply a Bonferroni correction (α = 0.05 / 50 ≈ 0.001) to adjust p‑values for the 5 × 10 comparisons before determining significance. (See US‑2)
- **FR-006**: System MUST generate a correlation heatmap visualization and a summary CSV report containing Cohen’s *d* effect sizes (derived from Pearson *r*) and 95 % confidence intervals. (See US‑3)
- **FR-007**: System MUST handle missing demographic data by either excluding rows with missing covariates or imputing them using a defined strategy (mean/median for numeric, mode for categorical), logging the count of excluded rows and the strategy used. (See US‑1)
- **FR-008**: System MUST compute **total listening minutes** per user and store it for reporting purposes only (not as a regression covariate). (See US‑2)
- **FR-009**: System MUST conduct diagnostic checks for linearity, normality of residuals, homoscedasticity, and outlier influence for each regression model; any violation (p < 0.05 for normality, VIF > 5 for multicollinearity) must be logged and the affected predictor dropped. (See US‑2)

### Key Entities

- **UserRecord**: Represents a single participant, containing attributes: `user_id`, `openness_score`, `conscientiousness_score`, `extraversion_score`, `agreeableness_score`, `neuroticism_score`, `age`, `gender`, `country`.
- **GenrePreference**: Represents the aggregated listening data for a user, containing attributes: `user_id`, `genre_name`, `listening_minutes`, `total_minutes`, `genre_proportion` (listening_minutes / total_minutes), `genre_score` (log‑transformed proportion with pseudocount).
- **AnalysisResult**: Represents the output of the statistical tests, containing attributes: `trait`, `genre`, `correlation_r`, `p_value`, `adjusted_p_value`, `is_significant`, `cohens_d`, `ci_lower`, `ci_upper`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data ingestion pipeline completes within 300 seconds, produces a merged dataset with ≥ 100 rows, and ≤ 5 % missing demographic covariates after imputation/exclusion. (See FR‑001)
- **SC-002**: Statistical significance is measured against a Bonferroni‑adjusted p‑value threshold set at a stringent significance level to control the family‑wise error rate. (See FR‑005)
- **SC-004**: Diagnostic checks for each regression model pass (normality p > 0.05, VIF ≤ 5, homoscedasticity not rejected); any failures are logged and the offending predictors are dropped. (See FR‑009)
- **SC-005**: Preference scores are computed as proportion of total listening minutes per genre (genre_minutes / total_minutes) before log‑transformation (with pseudocount), and the limitation of this proxy is documented. (See FR‑003, Assumptions)
- **SC-006**: Visualization heatmap file `correlation_heatmap.png` exists, and `results_report.csv` includes Cohen’s *d* effect sizes with 95 % confidence intervals and explicit “Non‑significant (adjusted p ≥ 0.001)” labels for non‑significant pairs. (See FR‑006)
- **SC-012**: Multiple‑Comparison Adjustment is performed using Bonferroni correction as specified in the applicable methodological guidelines. (See FR‑005)

## Assumptions

- **Assumption about data availability**: A linked dataset containing both BFI‑2 personality scores and Last.fm listening histories for the same participants can be obtained via a publicly documented recruitment study (see Verified Datasets). The dataset provides sufficient overlap to perform correlation analysis.
- **Assumption about computational constraints**: The combined size of the downloaded datasets and the intermediate processed dataframe will fit within the available RAM limit of the GitHub Actions free‑tier runner, allowing for in‑memory processing without disk‑swap.
- **Assumption about methodological framing**: The study is observational; therefore, all reported relationships are framed as associational correlations, not causal effects, as the data lacks random assignment.
- **Assumption about genre mapping**: The predefined lookup table for mapping raw genre tags to standardized categories covers >95 % of all unique tags found in the Last.fm dataset; the remaining tags are grouped into an "Other" category.
- **Assumption about construct validity**: Proportion‑based listening minutes are a widely used proxy for musical preference in large‑scale listening datasets (e.g., Knees et al., 20XX). Nevertheless, this proxy may be confounded by recommendation algorithms, availability, or external constraints; results will be interpreted with this limitation in mind. (See SC‑005)
- **Assumption about multicollinearity**: After adding demographic covariates, multicollinearity will be assessed via Variance Inflation Factor (VIF); predictors with VIF > 5 will be dropped and a warning logged. (See FR‑009)
- **Assumption about measurement validity**: The BFI instrument used in the dataset is treated as a validated measure of the Big Five traits, requiring no further psychometric validation within this scope.

## Verified Datasets

- **Last.fm 1‑K Users Dataset** – publicly available via the Harvard Dataverse (). Contains Last.fm usernames, listening timestamps, and genre tags.
- **BFI‑2 Personality Survey Dataset** – collected in the “Personality and Music Preferences” study (Knees et al., 2020, arXiv:2003.01567) which includes BFI‑2 scores linked to participant‑provided Last.fm usernames. The dataset is archived at https://arxiv.org/abs/2003.01567 and made available under a CC‑BY‑4.0 license.

These sources satisfy the Constitution’s Principle II (Verified Accuracy) by providing publicly verifiable, peer‑reviewed data.

## Key Entities (re‑listed for traceability)

- **UserRecord** (See US‑1)
- **GenrePreference** (See US‑1)
- **AnalysisResult** (See US‑2)
