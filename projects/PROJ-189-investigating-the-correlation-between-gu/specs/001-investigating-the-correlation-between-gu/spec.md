# Feature Specification: Gut Microbiome and Cognitive Decline Analysis

**Feature Branch**: `001-gut-microbiome-cognition`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Decline in Aging Populations"

## User Scenarios & Testing *(mandatory)*

### User Story US-1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The system MUST ingest raw 16S rRNA taxonomic data from the American Gut Project (AGP) **directly from the Qiita/EBI repository** and cognitive assessment metadata from the Health and Retirement Study (HRS), merge them by participant ID, and filter for the target population (age ≥ 60).

**Why this priority**: Without clean, merged data containing both microbiome and cognitive variables, no analysis can proceed. This is the foundational dependency for all downstream research steps.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output dataframe contains ≥ 500 rows where every row has non‑null values for at least 5 microbial genera and 1 cognitive score column.

**Acceptance Scenarios**:

1. **Given** raw AGP and HRS CSV/TSV files exist locally, **When** the ingestion script runs, **Then** a merged dataframe is produced with ≥ 80 % overlap on participant IDs (calculated as the intersection of unique IDs present in both source datasets).
2. **Given** the merged dataframe, **When** the age filter (≥ 60) is applied, **Then** the resulting subset contains no participants under the specified age threshold.
3. **Given** missing covariate values (e.g., BMI, education), **When** imputation is applied, **Then** no null values remain in the final analysis dataset.

---

### User Story US-2 - Associational Correlation Analysis (Priority: P2)

The system MUST compute Spearman rank correlations between genus‑level microbial abundances and cognitive test scores **adjusting for the covariates age, sex, BMI, and education**. It MUST first regress each microbial genus and each cognitive score on these covariates, use the residuals for correlation, and then apply the Benjamini‑Hochberg FDR method (α = 0.05). The system MUST also perform a linear mixed‑effects regression of cognitive scores on CLR‑transformed genus abundances with random intercepts for participant ID, adjusting for the same covariates, and report fixed‑effect coefficients and associated p‑values. The system MUST apply a Centered Log‑Ratio (CLR) transformation to the taxonomic data prior to the residualisation step to address compositionality.

**Why this priority**: This directly addresses the core research question regarding associations between taxa and cognition while controlling for known confounders, providing valid inferential evidence and a complementary mixed‑effects modeling perspective.

**Independent Test**: Can be fully tested by running the correlation module and verifying the output table contains FDR‑adjusted p‑values, that covariate‑adjusted residuals were used, and that a mixed‑effects results table is produced.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** covariate‑adjusted Spearman correlations are calculated, **Then** the output includes correlation coefficients (rho) and raw p‑values for all genus‑score pairs.
2. **Given** raw p‑values, **When** FDR correction (α = 0.05) is applied, **Then** the final significance table flags only those below the corrected threshold.
3. **Given** the mixed‑effects model run, **When** results are exported, **Then** fixed‑effect coefficients and their p‑values are recorded and labeled as associational.

---

### User Story US-3 - Predictive Modeling, Interpretability, and Robustness Validation (Priority: P3)

The system MUST train a Random Forest regressor to predict cognitive scores from **both microbial taxa (CLR‑transformed) and demographic covariates (age, sex, BMI, education)**, validate against a permutation null distribution, and report interpretability metrics (permutation importance and SHAP values). The model must be evaluated with an A typical train/test split with a larger portion allocated to training and a smaller portion allocated to testing., 5‑fold cross‑validation, and its hold‑out R² score must exceed a high percentile of the permutation null distribution (based on a large number of permutations).

**Why this priority**: This tests the predictive utility of the microbiome while accounting for demographic factors and ensures the findings are robust and interpretable.

**Independent Test**: Can be fully tested by executing the modeling script and verifying that (a) the Random Forest runs on CPU‑only hardware, (b) the hold‑out R² exceeds the 95th percentile of the null distribution, and (c) permutation importance and SHAP plots are generated.

**Acceptance Scenarios**:

1. **Given** the training set, **When** the Random Forest model is trained, **Then** it runs on CPU‑only hardware without GPU acceleration requests.
2. **Given** the hold‑out set, **When** performance is evaluated, **Then** the R² score is compared against a high percentile of the permutation null distribution (1 000 iterations) and must be higher.
3. **Given** the trained model, **When** interpretability analysis is performed, **Then** permutation importance scores and SHAP summary plots are produced and stored.

---

### Edge Cases

- If participant IDs do not match between AGP and HRS datasets, the system MUST log the mismatch count and proceed only if overlap ≥ 500 samples (≈ 80 % of the smaller dataset). Otherwise, it aborts with an error.
- If the effective sample size for the regression model is < 100, the system MUST output a warning indicating limited statistical power.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest AGP 16S taxonomic tables **directly from the American Gut Project via the Qiita/EBI repository** and HRS cognitive metadata, merge them by participant ID, and verify that all required variables (age, sex, BMI, cognitive score) are present (See US-1). The system MUST also compute SHA‑256 checksums of the raw AGP and HRS files and store them as `checksum_agp` and `checksum_hrs` in the `dataset.metadata` section of `unified_results.json` (See US-1).
- **FR-002**: System MUST rarefy taxonomic tables to a uniform depth equal to the minimum read depth observed in the retained samples after quality filtering and collapse to genus‑level relative abundances before analysis (See US-1).
- **FR-003**: System MUST compute covariate‑adjusted Spearman rank correlations on CLR‑transformed genus abundances, applying Benjamini‑Hochberg FDR correction (α = 0.05), and explicitly label results as associational (See US-2). Covariate adjustment is performed by regressing both microbial abundances and cognitive scores on age, sex, BMI, and education and using residuals for correlation.
- **FR-004**: System MUST train a Random Forest regressor (scikit‑learn) using CPU‑only execution, with an 80/20 train‑test split, 5‑fold cross‑validation, inclusion of demographic covariates as predictors (age, sex, BMI, education), and generate interpretability artefacts (see FR-008) (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis sweeping the rarefaction depth threshold over the set `{5,000, min_depth}` in steps of multiple reads, reporting how key association metrics (e.g., number of significant taxa) vary. **Justification**: Sensitivity analysis ensures results are robust to sequencing‑depth choices, a prerequisite for reliable association inference. (See US-1).
- **FR-008**: System MUST generate model interpretability artefacts: permutation importance scores and SHAP summary plots for each predictor (See US-3).
- **FR-009**: System MUST perform a priori power analysis for (a) genus‑level correlation tests (detect effect size |r| ≥ 0.2 with α = 0.05, power = 0.8) and (b) Random Forest regression (detect ΔR² ≥ 0.05 with α = 0.05, power = 0.8), reporting the required sample size and confirming that the actual sample meets or exceeds it (See US-1, US-3).
- **FR-010**: System MUST assess multicollinearity among selected predictors **before CLR transformation** using Variance Inflation Factors; any predictor with VIF > 5 is excluded from the model (See US-3).
- **FR-011**: System MUST document in the unified results JSON the fields `checksum_agp` and `checksum_hrs` containing the SHA‑256 checksums of the source files (See US-1).
- **FR-013**: System MUST perform a linear mixed‑effects regression of cognitive scores on CLR‑transformed genus abundances with random intercepts for participant ID, adjusting for age, sex, BMI, and education, and report fixed‑effect coefficients and associated p‑values (See US-2).

### Key Entities *(include if feature involves data)*

- **Sample**: Represents a single participant record containing microbiome counts, cognitive scores, and covariates (age, sex, BMI, education).
- **Taxon**: Represents a microbial genus with relative abundance values across samples.
- **Model**: Represents the trained Random Forest instance and its performance metrics (R², RMSE, importance scores, SHAP values).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data merge success rate must be ≥ 80 % of AGP participant IDs (See US-1).
- **SC-002**: Number of significant genus‑cognition associations is measured against the FDR‑corrected α = 0.05 threshold (See US-2).
- **SC-003**: Model predictive performance (R²) must exceed a high percentile of the permutation‑based null distribution (1 000 iterations) (See US-3).
- **SC-004**: Memory usage during peak permutation testing must remain ≤ 6 GB; if exceeded, the system reduces permutation count and logs the adjustment (See Edge Cases).

## Assumptions

- The American Gut Project and Health and Retirement Study datasets can be linked via a shared participant identifier or metadata matching key provided in the public repositories.
- A rarefaction depth determined by the minimum read depth of retained samples is sufficient to capture diversity without excessive data loss.
- The required Python and R libraries (scikit‑learn, statsmodels, qiime2) are available in the execution environment.
- Cognitive scores in the HRS module are comparable across the subset of participants who also provided stool samples in the AGP.
- The relationship between microbiome and cognition is primarily associational due to the observational nature of the public datasets; no causal inference will be claimed.
