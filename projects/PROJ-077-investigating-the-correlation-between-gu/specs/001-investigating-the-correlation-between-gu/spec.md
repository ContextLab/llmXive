# Specification: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Project Overview
This project investigates the correlation between gut microbiome diversity and cognitive performance using UK Biobank data.

## Research Question
What is the correlation between gut microbiome diversity (measured by Shannon Index) and cognitive performance (measured by fluid intelligence)?

## Data Source
**Primary Source**: UK Biobank
**Access Method**: Local data files in `data/raw/` directory OR verified public URL if available.

**CRITICAL REPRODUCIBILITY CLAUSE**:
To resolve the conflict between "fresh runner" reproducibility and the absence of a public download URL for sensitive biobank data, this specification explicitly allows **local data sources** placed in `data/raw/` as a valid input for the Reproducibility constraint.

- The pipeline MUST support running against local files in `data/raw/` when no public URL is available.
- Data provenance checks (checksums) MUST be performed on local files to ensure integrity.
- The `ALLOW_LOCAL_DATA` configuration flag controls whether local fallback is permitted.
- If `ALLOW_LOCAL_DATA` is True and local files exist, the pipeline proceeds; otherwise, it fails loudly with a clear error directing the user to obtain the data.

**Required Fields**:
- Microbiome: OTU/ASV count tables (participant_id, taxa columns)
- Cognitive: fluid_intelligence_score
- Covariates: age, sex, bmi, dietary components for HEI-2015 calculation

**Data Placement**: All raw data files must be placed in `data/raw/`.

## User Stories

### User Story 1: Data Ingestion and Preprocessing
As a researcher, I want to load and clean the UK Biobank data so that I can perform statistical analysis on a valid dataset.

**Acceptance Criteria**:
- Load data from `data/raw/` (local) or verified URL
- Merge microbiome and cognitive data by participant ID
- Filter out participants with missing primary outcomes
- Impute missing covariates (Median for numeric, Mode for categorical)
- Output: `data/processed/cleaned_data.csv`

### User Story 2: Correlation and Regression Analysis
As an analyst, I want to compute diversity metrics and statistical correlations so that I can quantify the relationship between microbiome and cognition.

**Acceptance Criteria**:
- Calculate Shannon Index from raw counts
- Compute Spearman correlation between Shannon Index and fluid intelligence
- Run multivariate regression with covariates
- Output: `data/processed/correlation_results.csv`, `data/processed/regression_results.csv`

### User Story 3: Statistical Correction and Visualization
As a scientist, I want to apply statistical corrections and generate visualizations so that I can report findings accurately.

**Acceptance Criteria**:
- Apply Benjamini-Hochberg FDR correction
- Generate scatter plots and histograms
- Output: `data/processed/corrected_results.csv`, `data/processed/plots/*.png`

## Technical Requirements

### Data Constraints
- Maximum sample size: a large-scale cohort suitable for streaming enforcement (streaming enforced)
- Memory limit: Pipeline must not exceed 7GB RAM
- Data integrity: Checksum verification required for all input files

### Statistical Methods
- Alpha Diversity: Shannon Index (scikit-bio) on RAW counts
- Correlation: Spearman rank correlation
- Regression: OLS with covariates (Primary Path), Lasso (Secondary Path)
- Correction: Benjamini-Hochberg FDR

### Configuration
- `DQS_REQUIRED`: Boolean flag for dietary quality score requirement (default: False)
- `ALLOW_LOCAL_DATA`: Boolean flag for local data fallback (default: True for this project)
- `SAMPLE_LIMIT`: Maximum rows to process (default: a configurable limit)

## Output Artifacts
1. `data/processed/cleaned_data.csv`
2. `data/processed/correlation_results.csv`
3. `data/processed/regression_results.csv`
4. `data/processed/corrected_results.csv`
5. `data/processed/plots/scatter_shannon_fi.png`
6. `data/processed/plots/diversity_histogram.png`
7. `state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml`