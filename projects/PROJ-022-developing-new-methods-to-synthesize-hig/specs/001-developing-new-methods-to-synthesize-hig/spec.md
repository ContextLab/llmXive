# Feature Specification: Developing New Methods to Synthesize High-Performance Membranes using Sustainable Materials

**Feature Branch**: `001-sustainable-membrane-synthesis`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Which structural features and material compositions of sustainable polymers determine permeability and selectivity performance comparable to conventional petrochemical-based membrane materials?"

## User Scenarios & Testing

### User Story 1 - Data Aggregation and Standardization (Priority: P1)

The system must aggregate sparse experimental data from literature (arXiv, OpenPolymer) and standardize units (Barrer, LMH/bar) to create a unified dataset linking polymer composition to transport properties.

**Why this priority**: Without a clean, standardized dataset, no machine learning model can be trained. This is the foundational step required to address the "data scarcity" gap identified in the literature.

**Independent Test**: The pipeline can be tested by running the ingestion script against a mock CSV of 10 literature entries and verifying the output dataframe contains standardized units, imputed missing values, and a valid count of non-null performance records.

**Acceptance Scenarios**:

1. **Given** a raw CSV containing mixed units (e.g., some permeability in GPU, some in Barrer), **When** the ingestion script runs, **Then** all permeability values are converted to Barrer and selectivity values are unitless ratios.
2. **Given** a literature entry with missing synthesis conditions, **When** the preprocessing step runs, **Then** the missing values are flagged and handled via multiple imputation without dropping the entire record.
3. **Given** a dataset of 50 literature entries, **When** the aggregation completes, **Then** the output contains at least 30 valid records with both molecular structure and performance metrics.
4. **Given** a dataset where a critical variable (e.g., fractional free volume) is missing from [deferred] of records, **When** the validation step runs, **Then** the system triggers the imputation strategy and logs a warning without halting.
5. **Given** a dataset where a critical variable is missing from >20% of records, **When** the validation step runs, **Then** the system halts execution, outputs `missing_data_report.json`, and emits error code `ERR_DATA_INSUFFICIENT`.

---

### User Story 2 - Feature Engineering and Model Training (Priority: P2)

The system must generate molecular descriptors (e.g., van der Waals volume, H-bond counts) using RDKit and train a Random Forest or Gradient Boosting regressor to map these descriptors to permeability and selectivity.

**Why this priority**: This transforms raw chemical data into predictive insights. It directly addresses the research question of identifying "structural descriptors" that drive performance.

**Independent Test**: The training module can be tested by running on the standardized dataset from US-1 and verifying the model outputs a feature importance ranking and a cross-validated R² score ≥ 0.1.

**Acceptance Scenarios**:

1. **Given** a standardized dataset of polymer structures, **When** the feature engineering step runs, **Then** a feature matrix is generated containing at least 10 molecular descriptors per polymer.
2. **Given** the feature matrix and performance targets, **When** the model trains on a 2-core CPU, **Then** the model completes within 6 hours (hard limit) with a target of 60 minutes; if the target is exceeded, the system reduces tree depth by [deferred] and retries up to 2 times.
3. **Given** a trained model, **When** 5-fold cross-validation is performed, **Then** the mean R² score is reported and stored in the results artifact, and must be ≥ 0.1.

---

### User Story 3 - Candidate Screening and Statistical Validation (Priority: P3)

The system must screen a virtual library of a substantial number of sustainable candidates, rank them by predicted performance, and statistically compare the top candidates against experimental petrochemical benchmarks.

**Why this priority**: This delivers the final research output: a ranked list of promising materials and a statistical validation of whether bio-based materials can theoretically match petrochemical performance.

**Independent Test**: The screening module can be tested by providing a known set of "high-performance" and "low-performance" dummy candidates and verifying the ranking order matches the expected performance distribution.

**Acceptance Scenarios**:

1. **Given** a trained model and a list of 50 virtual candidate SMILES strings, **When** the screening runs, **Then** a ranked list of candidates is generated with predicted permeability and selectivity values.
2. **Given** the predicted performance of top bio-candidates and experimental benchmark data, **When** the Mann-Whitney U test runs, **Then** a p-value is calculated to determine statistical significance.
3. **Given** the final results, **When** the report is generated, **Then** it includes a feature importance plot, a list of the top 3 predicted sustainable materials, and a power analysis report.

### Edge Cases

- What happens when the literature data contains conflicting performance metrics for the same polymer (e.g., different synthesis methods)? The system must flag these as "high variance" entries and exclude them from the primary training set or handle them via a variance-weighted loss.
- How does the system handle polymers with undefined molecular weights in the literature? The system must default to a "polymer class" average or exclude the record if the molecular weight is critical for the specific descriptor calculation.
- What happens if the virtual library contains structures that RDKit cannot parse? The system must log the failure, skip the record, and continue processing the remaining valid structures without crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST aggregate experimental data from at least three distinct sources (arXiv, OpenPolymer, manual literature extraction) and standardize units to Barrer for permeability and dimensionless for selectivity (See US-1).
- **FR-002**: System MUST generate molecular descriptors including molecular weight, H-bond donor/acceptor counts, and estimated van der Waals volume for every polymer in the dataset using RDKit (See US-2). *Note: True Fractional Free Volume (FFV) requires experimental density and is not calculable from SMILES alone.* (See US-2).
- **FR-003**: System MUST train an ensemble regressor (Random Forest or Gradient Boosting) restricted to a maximum tree depth of 10 and ensemble size of 100 to ensure execution within 7GB RAM and 6-hour CPU limits on an AWS c5.large (2 vCPU, 4GB RAM) or equivalent instance. If the target runtime of 60 minutes is exceeded, the system MUST reduce tree depth by [deferred] and retry up to 2 times (See US-2).
- **FR-004**: System MUST perform stratified 5-fold cross-validation and calculate Mean Absolute Error (MAE) and R² scores to assess model generalizability (See US-2).
- **FR-005**: System MUST execute a Mann-Whitney U test to compare the distribution of predicted performances for top-ranked bio-candidates against *experimental* petrochemical benchmarks (See US-3).
- **FR-006**: System MUST flag any dataset variable required for analysis that is missing from the source literature. If a critical variable is missing from ≥5% but ≤20% of records, the system MUST trigger a fallback imputation strategy using polymer-class averages. If a critical variable is missing from >20% of records, the system MUST halt execution, output `missing_data_report.json`, and emit error code `ERR_DATA_INSUFFICIENT` (See US-1).
- **FR-007**: System MUST explicitly frame all model findings as associational rather than causal, given the observational nature of the literature data (See US-2).
- **FR-008**: System MUST encode the 'synthesis method' as a categorical feature in the model input matrix (See US-2).
- **FR-009**: System MUST require experimental validation of the top 3 predicted sustainable candidates to provide ground truth for the statistical comparison (See US-3).
- **FR-010**: System MUST generate a power analysis report calculating the detectable effect size given the sample size (N=30) before finalizing the statistical test plan (See US-3).
- **FR-011**: System MUST perform dimensionality reduction (PCA) or recursive feature elimination (RFE) before model training to mitigate overfitting risks in high-dimensional, low-sample regimes (See US-2).

### Key Entities

- **PolymerRecord**: Represents a single experimental entry; attributes include SMILES string, synthesis method (categorical), permeability (Barrer), selectivity, and source citation.
- **MolecularDescriptor**: Represents a calculated feature; attributes include descriptor name (e.g., "VdW_Volume"), value, and calculation method.
- **ModelPrediction**: Represents a model output; attributes include candidate SMILES, predicted permeability, predicted selectivity, and confidence interval.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Model R² score on 5-fold cross-validation is measured against a baseline of 0.0 (random guess) with a target threshold of ≥ 0.1 to confirm predictive capability (See US-2).
- **SC-002**: The number of successfully screened candidates in the virtual library is measured against the target of 50+ to ensure sufficient statistical power for ranking (See US-3).
- **SC-003**: The p-value from the Mann-Whitney U test is measured against the alpha threshold of 0.05 to determine if bio-candidates statistically outperform benchmarks (See US-3).
- **SC-004**: The runtime of the full pipeline (ingestion to screening) is measured against the 6-hour limit on a 2-core CPU to verify compute feasibility (See US-2).
- **SC-005**: The number of missing critical variables (e.g., van der Waals volume) in the source data is measured to ensure dataset-variable fit, triggering a clarification flag if >5% of records are affected (See US-1).

## Assumptions

- **Assumption about data availability**: The "Open Polymer Challenge" report and selected arXiv preprints contain sufficient raw data points (≥30 valid records) to train a Random Forest model without severe overfitting.
- **Assumption about compute constraints**: The virtual library of 50+ candidates and the training dataset will fit entirely within 7GB RAM, allowing the use of in-memory dataframes without chunking.
- **Assumption about methodological framing**: Since the data is observational (literature-based), the analysis assumes that controlling for known confounders via feature engineering is sufficient to identify structural drivers, though causality cannot be claimed.
- **Assumption about descriptor validity**: RDKit can successfully calculate van der Waals volume and other steric descriptors for the bio-based polymers (cellulose, chitosan, lignin derivatives) in the dataset. True FFV requires experimental density.
- **Assumption about statistical power**: A sample size of ≥30 valid records is sufficient to detect a *large* effect size in the Mann-Whitney U test; the system acknowledges limited power for medium/small effects and requires a power analysis report (FR-010) to quantify this limitation.