# Project Specification: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Version History
- v1.0: Initial draft
- v1.1: Updated based on Plan Corrections (T045, T046, T047)

## Functional Requirements

### Data Ingestion and Preprocessing
- **FR-001**: System MUST load raw microbiome and cognitive data from `data/raw/` and merge by participant ID column `participant_id`.
- **FR-002**: System MUST compute alpha diversity (Shannon index) using `scikit-bio` on the OTU/ASV tables **using raw counts** (not CLR-transformed).
- **FR-003**: System MUST apply Centered Log-Ratio (CLR) transformation **only** to taxa abundance matrices, not alpha diversity values.
- **FR-004**: System MUST perform multivariate linear regression with predictors: `shannon_index`, Age, Sex, BMI, DQS.
- **FR-005**: System MUST apply False Discovery Rate (FDR) correction (Benjamini-Hochberg) to p-values from multiple tests.
- **FR-006**: System MUST generate publication-quality scatter and histogram plots.
- **FR-007**: System MUST impute missing numeric covariate values (age, BMI, DQS) using the median of the available data, and missing categorical values (sex) using the mode.
- **FR-008**: System MUST calculate Diet Quality Score (DQS) using the HEI-2015 standard formula if raw dietary data is present.

### Data Validation and Error Handling
- **FR-009**: System MUST fail loudly if required input files are missing or empty.
- **FR-010**: System MUST validate that DQS calculation is possible if dietary data is required.

## Success Criteria

- **SC-001**: The correlation coefficient and p-value between **Raw Shannon Index** and fluid intelligence are measured against the Spearman rank correlation test results.
- **SC-002**: The regression coefficient for `shannon_index` in the multivariate model is statistically significant (p < 0.05) after controlling for covariates.
- **SC-003**: All reported significant findings have q-values < 0.05 after FDR correction.
- **SC-004**: The cleaned dataset has >95% completeness for primary outcomes and covariates.

## Data Model

### Input Data
- **Microbiome Data**: Wide-format matrix of OTU/ASV counts (rows: participants, columns: taxa).
- **Cognitive Data**: DataFrame with `participant_id` and `fluid_intelligence`.
- **Covariates**: DataFrame with `participant_id`, `age`, `sex`, `bmi`, `dietary_data`.

### Output Data
- **cleaned_data.csv**: Merged, filtered, and imputed dataset.
- **correlation_results.csv**: Spearman correlation results.
- **regression_results.csv**: Multivariate regression coefficients and statistics.
- **plots/**: Visualization artifacts.

## Constraints
- **Memory Safety**: `SAMPLE_LIMIT=50000` must be enforced for all data loading operations.
- **Reproducibility**: `RANDOM_SEED=42` must be used for all stochastic operations.
- **Data Integrity**: No synthetic data generation is permitted for final analysis.