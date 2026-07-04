# Feature Specification: Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

**Feature Branch**: `001-predict-plant-stress-resilience`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Resilience from Publicly Available Metabolomic Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest raw plant metabolomic datasets from public repositories (NCBI GEO, Zenodo), filter for relevant stress conditions, and normalize the data for analysis. This is the foundational step; without clean, structured input data, no predictive modeling can occur.

**Why this priority**: This is the prerequisite for all downstream analysis. If data cannot be retrieved, filtered, or normalized, the project cannot proceed to modeling or validation.

**Independent Test**: Can be fully tested by running the data pipeline script against a known subset of public data and verifying the output is a normalized CSV/Parquet file with no missing critical columns and correct row counts.

**Acceptance Scenarios**:

1. **Given** a list of valid NCBI GEO accession IDs, **When** the pipeline executes, **Then** it successfully downloads the raw metabolomic matrices and associated metadata.
2. **Given** raw metabolomic data with missing values <10%, **When** the preprocessing step runs, **Then** missing values are imputed using the **half-minimum** method, and the data is **log-natural (ln)** transformed and normalized by total ion count.
3. **Given** a dataset containing mixed stress types, **When** the filter logic runs, **Then** only samples with documented recovery rates measured ≥7 days post-stress are retained.

---

### User Story 2 - Predictive Model Training and Feature Importance (Priority: P2)

The system must train Random Forest and Support Vector Machine (SVM) models to predict recovery rates from pre-stress metabolomic profiles and identify the most predictive metabolites. This delivers the core research value: determining if metabolomic signatures carry predictive signal.

**Why this priority**: This is the primary analytical engine. It directly addresses the research question by testing the predictive capability of metabolomics.

**Independent Test**: Can be tested by training a model on a split dataset, evaluating performance metrics (R² or Pearson correlation), and verifying that feature importance rankings are generated for the top 20 metabolites.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset, **When** the Random Forest model is trained with **5-fold cross-validation**, **Then** it outputs a performance metric (R² for individual data, Pearson r for population data) and a ranked list of feature importances.
2. **Given** the same training data, **When** the SVM model is trained, **Then** it produces a comparable performance metric and feature ranking.
3. **Given** a trained model, **When** the analysis completes, **Then** the top predictive metabolites are extracted and mapped to known biochemical pathways (e.g., osmolytes, antioxidants).

---

### User Story 3 - Cross-Stress Generalizability and Statistical Validation (Priority: P3)

The system must evaluate the model's ability to generalize across different stress types (e.g., train on drought, test on salinity) and perform statistical validation via permutation testing to ensure results are not due to chance.

**Why this priority**: This validates the robustness and biological relevance of the findings. It addresses the "gap" regarding cross-stress generalizability and ensures statistical rigor.

**Independent Test**: Can be tested by running the cross-stress evaluation script and the permutation test (n=1000), verifying that p-values are calculated and generalizability scores are reported.

**Acceptance Scenarios**:

1. **Given** a model trained on drought stress data, **When** it is evaluated on a separate salinity stress dataset, **Then** the system reports the drop in performance calculated as **R²_drop = R²_in_dist - R²_out_dist** (or correlation difference for population data) as a generalizability metric.
2. **Given** the trained model's performance score, **When** a permutation test with 1000 iterations is executed, **Then** a p-value is calculated to determine if the performance exceeds random chance (p<0.05).
3. **Given** the top predictive metabolites, **When** the validation check runs, **Then** the system: (a) maps raw metabolite names to **KEGG Compound IDs**, (b) performs an **Enrichment Analysis** against known stress-response pathways, and (c) flags alignment if the **Jaccard similarity ≥ 0.3** or **Enrichment p-value < 0.05**.

### Edge Cases

- What happens when a downloaded dataset has >10% missing values? The system must reject the dataset or flag it for manual review, rather than attempting imputation that could introduce bias.
- How does the system handle datasets where the recovery metric is defined differently (e.g., biomass vs. survival rate)? The system MUST normalize these to a common **Recovery Index (0-1 scale)** before filtering or analysis.
- What if a specific stress type (e.g., heat) has insufficient samples (<50) for training? The system must skip the cross-stress evaluation for that specific pair and report a "insufficient data" warning.
- What if individual-level paired time-series (t=0 vs t>=7d) are unavailable? The system MUST fallback to **population-level aggregation** (mean pre-stress vs mean recovery) and switch the modeling metric from R² to **Pearson correlation coefficient**.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse metabolomic datasets from NCBI GEO and Zenodo based on user-provided accession IDs or search keywords (See US-1).
- **FR-002**: System MUST filter datasets to retain only samples with pre-stress profiles and post-stress recovery metrics measured ≥7 days after stress exposure (See US-1).
- **FR-002.1**: System MUST normalize heterogeneous recovery metrics (e.g., biomass, survival, chlorophyll) to a unified **Recovery Index (0-1 scale)** before applying FR-002 filters (See US-1).
- **FR-003**: System MUST process metabolomic data ONLY IF the proportion of missing entries is <10%. **IF** missing <10%, **THEN** the system MUST: (a) normalize by total ion count, (b) impute missing values using the **half-minimum** method, and (c) apply **natural log (ln)** transformation. **ELSE**, the system MUST reject the dataset (See US-1).
- **FR-004**: System MUST train Random Forest and SVM models using **5-fold cross-validation** to predict continuous recovery rates (or correlation) from pre-stress metabolite profiles (See US-2).
- **FR-005**: System MUST compute and output feature importance scores for all metabolites to identify the top predictive variables (See US-2).
- **FR-006**: System MUST perform a permutation test with n=1000 iterations to assess statistical significance (p<0.05) of model performance against random chance (See US-3).
- **FR-007**: System MUST evaluate cross-stress generalizability by training on one stress type and testing on a distinct stress type (See US-3).
- **FR-008**: System MUST validate top predictive metabolites against a database of known stress-response pathways (e.g., proline, ABA, glutathione) (See US-3).
- **FR-009**: System MUST verify data pairing. **IF** individual-level paired time-series (t=0 vs t>=7d) are available, **THEN** use individual-level supervised learning. **ELSE**, the system MUST fallback to **population-level aggregation** (mean pre vs mean post) and switch the modeling objective to **group-level correlation** (See US-2, US-3).
- **FR-010**: System MUST validate model generalizability using **Leave-One-Dataset-Out (LODO)** cross-validation, where the model is trained on N-1 datasets and tested on the held-out dataset, to ensure independence without requiring external data (See US-3).
- **FR-011**: System MUST switch the performance metric from **R²** to **Pearson correlation coefficient (r)** if the data is processed in population-level mode (See FR-009).
- **FR-012**: System MUST map raw metabolite names to **KEGG Compound IDs** using a standard mapping table before performing any pathway alignment or validation (See US-3).

### Key Entities

- **MetabolomicProfile**: Represents a single sample's pre-stress state, containing metabolite concentrations and metadata (species, stress type).
- **RecoveryMetric**: Represents the outcome variable, quantifying the plant's recovery (e.g., biomass ratio, chlorophyll retention) measured ≥7 days post-stress.
- **RecoveryIndex**: A normalized scalar value (0-1) derived from heterogeneous recovery metrics to enable cross-stress comparison.
- **ModelResult**: Contains performance metrics (R², RMSE, or Pearson r), feature importance rankings, and statistical validation results (p-values).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: Model performance (R² or Pearson r) is measured against the baseline of a null model (predicting the mean recovery rate) to determine predictive signal (See US-2).
- **SC-002**: Statistical significance is measured against the null hypothesis of random chance via permutation testing (n=1000) to validate that performance is not spurious (See US-3).
- **SC-003**: Cross-stress generalizability is measured against the in-distribution performance to quantify the drop in predictive accuracy (R²_drop or r_drop) when applied to unseen stress types (See US-3).
- **SC-004**: Biological validity is measured against the **Enrichment Analysis** of top predictive metabolites, requiring a **Jaccard similarity ≥ 0.3** or **Enrichment p-value < 0.05** against established stress-response pathways (See US-3).
- **SC-005**: Computational feasibility is measured against the constraint of running the full pipeline (training, cross-validation, permutation) within 6 hours on a CPU-only runner with ≤7GB RAM (See Assumptions).

## Assumptions

- **Dataset Availability**: Publicly available datasets (NCBI GEO, Zenodo) contain both pre-stress metabolomic profiles and post-stress recovery metrics for the same samples, allowing for direct pairing. If a dataset lacks recovery metrics, it is excluded.
- **Data Quality**: Missing values in the raw metabolomic data are <10% for the majority of samples, allowing for standard imputation without significant bias.
- **Observational Nature**: The analysis is strictly observational; findings will be framed as associational correlations between pre-stress metabolites and recovery rates, not causal effects, due to the lack of random assignment in public datasets.
- **Compute Constraints**: The entire analysis (including 5-fold cross-validation and 1000-permutation tests) will fit within the GitHub Actions free-tier limits (2 CPU cores, ~7 GB RAM, ≤6 hours) by using CPU-tractable models (Random Forest, SVM) and potentially subsampling data if necessary.
- **Metric Standardization**: Recovery metrics (biomass, chlorophyll, survival) can be normalized to a comparable scale (e.g., percentage of control) for cross-dataset analysis.
- **Threshold Justification**: The p<0.05 threshold for statistical significance and the <10% missing value threshold for imputation are based on standard community practices in biological data analysis.
- **Sensitivity Analysis**: A sensitivity analysis will be performed on the missing value imputation threshold (e.g., testing 5%, 10%) to ensure model robustness.