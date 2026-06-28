# Feature Specification: Gut Microbiome and Cognitive Decline Analysis

**Feature Branch**: `001-gut-microbiome-cognition`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Decline in Aging Populations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST ingest raw 16S rRNA taxonomic data from the American Gut Project (AGP) and cognitive assessment metadata from the Health and Retirement Study (HRS), merge them by participant ID, and filter for the target population (age ≥ 60).

**Why this priority**: Without clean, merged data containing both microbiome and cognitive variables, no analysis can proceed. This is the foundational dependency for all downstream research steps.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output dataframe contains ≥ 500 rows with non-null values for at least 5 microbial genera and 1 cognitive score column.

**Acceptance Scenarios**:

1. **Given** raw AGP and HRS CSV/TSV files exist locally, **When** the ingestion script runs, **Then** a merged dataframe is produced with ≥ 80% overlap on participant IDs.
2. **Given** the merged dataframe, **When** the age filter (≥ 60) is applied, **Then** the resulting subset contains no participants under 60 years old.
3. **Given** missing covariate values (e.g., BMI, education), **When** imputation is applied, **Then** no null values remain in the final analysis dataset.

---

### User Story 2 - Associational Correlation Analysis (Priority: P2)

The system MUST compute Spearman rank correlations between genus-level microbial abundances and cognitive test scores, adjusting for multiple comparisons using the Benjamini-Hochberg FDR method.

**Why this priority**: This directly addresses the core research question regarding associations between taxa and cognition. It provides the initial statistical evidence required before predictive modeling.

**Independent Test**: Can be fully tested by running the correlation module and verifying the output table contains p-values adjusted via FDR, with no unadjusted p-values used for significance claims.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** Spearman correlations are calculated, **Then** the output includes correlation coefficients (rho) and raw p-values for all genus-score pairs.
2. **Given** raw p-values, **When** FDR correction (α = 0.05) is applied, **Then** the final significance table flags only those below the corrected threshold.
3. **Given** significant associations, **When** the results are logged, **Then** they are explicitly labeled as "associational" and not "causal."

---

### User Story 3 - Predictive Modeling and Robustness Validation (Priority: P3)

The system MUST train a Random Forest regressor to predict cognitive scores from microbial taxa, validate against a permutation null distribution, and perform sensitivity analysis on key thresholds.

**Why this priority**: This tests the predictive utility of the microbiome beyond simple correlation. It ensures the findings are robust to hyperparameter choices and not artifacts of the specific data split.

**Independent Test**: Can be fully tested by executing the modeling script and verifying the hold-out R² score exceeds the 95th percentile of the permutation null distribution (multiple iterations).

**Acceptance Scenarios**:

1. **Given** the training set, **When** the Random Forest model is trained, **Then** it runs on CPU-only hardware without GPU acceleration requests.
2. **Given** the hold-out set, **When** performance is evaluated, **Then** the R² score is compared against the permutation null distribution (1000 shuffles).
3. **Given** the rarefaction depth threshold (sufficiently low read depth to minimize sequencing depth as a confounding factor) 

The research question is: How does gut microbiome composition differ between individuals with and without diagnosed autoimmune disease?

The method is: 16S rRNA gene sequencing of fecal samples, followed by compositional analysis.

References: (Segata et al., 2012) https://doi.org/10.1038/nature11230, **When** sensitivity analysis is run, **Then** the model is re-evaluated at multiple depths and the variance in R² is reported.

---

### Edge Cases

- What happens when participant IDs do not match between AGP and HRS datasets? (System MUST log the mismatch count and proceed only if overlap ≥ 500 samples).
- How does system handle insufficient sample size for power? (System MUST output a warning if effective N < 100 for the regression model).
- What happens when memory usage is substantial during permutation testing? (System MUST sample taxa or reduce permutations to maintain execution within CI limits).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest AGP 16S taxonomic tables and HRS cognitive metadata, merging them by participant ID, and verify that all required variables (age, sex, BMI, cognitive score) are present (See US-1).
- **FR-002**: System MUST rarefy taxonomic tables to a uniform depth of [deferred] reads and collapse to genus-level relative abundances before analysis (See US-1).
- **FR-003**: System MUST compute Spearman rank correlations and apply Benjamini-Hochberg FDR correction (α = 0.05) to all p-values, explicitly framing results as associational (See US-2).
- **FR-004**: System MUST train a Random Forest regressor (scikit-learn) using CPU-only execution, with 80/20 train/test split and 5-fold cross-validation (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the rarefaction depth threshold over {5,000, 10,000, [deferred]} reads and report variance in headline performance metrics (See US-3).
- **FR-006**: System MUST calculate Variance Inflation Factors (VIF) for top predictive taxa to check for collinearity, ensuring no two predictors have VIF > 5 without descriptive framing (See US-3).
- **FR-007**: System MUST enforce execution limits of ≤ 6 hours runtime and ≤ 7 GB RAM per job, failing gracefully if exceeded (See US-3).

### Key Entities *(include if feature involves data)*

- **Sample**: Represents a single participant record containing microbiome counts, cognitive scores, and covariates (age, sex, BMI).
- **Taxon**: Represents a microbial genus with relative abundance values across samples.
- **Model**: Represents the trained Random Forest instance and its performance metrics (R², RMSE).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data merge success rate is measured against the total number of unique AGP participant IDs (See US-1).
- **SC-002**: Number of significant genus-cognition associations is measured against the FDR-corrected α = 0.05 threshold (See US-2).
- **SC-003**: Model predictive performance (R²) is measured against the 95th percentile of the permutation-based null distribution (1000 iterations) (See US-3).
- **SC-004**: Memory usage is measured against the 7 GB RAM limit during peak permutation testing (See US-3).

## Assumptions

- The American Gut Project and Health and Retirement Study datasets can be linked via a shared participant identifier or metadata matching key provided in the public repositories.
- A rarefaction depth of [deferred] reads is sufficient to capture diversity without excessive data loss for participants with lower sequencing depth.
- The Python and R libraries required (scikit-learn, statsmodels, qiime2) fit within a specified Docker base image size constraint and 7 GB RAM limit.
- Cognitive scores in the HRS module are comparable across the subset of participants who also provided stool samples in the AGP.
- The relationship between microbiome and cognition is primarily associational due to the observational nature of the public datasets; no causal inference will be claimed.
- The GitHub Actions free-tier runner (limited CPU resources, ~7 GB RAM) is sufficient for the specified Random Forest and permutation tests on the sampled dataset.
