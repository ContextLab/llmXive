# Feature Specification: Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

**Feature Branch**: `001-predicting-seebeck-alloying`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Compositional Feature Engineering (Priority: P1)

The system MUST download the electronic transport database, filter for thermoelectric-relevant alloy families (e.g., bismuth telluride, lead telluride, skutterudites), and engineer specific compositional descriptors (mean atomic radius, electronegativity variance, valence electron concentration) for every valid record. Where data permits, the system MUST attempt to filter by specific stoichiometry ranges (e.g., Bi2Te3 vs Bi2Se3) to reduce noise from crystallographic phase differences.

**Why this priority**: Without a clean, feature-engineered dataset, no analysis can occur. This is the foundational step that transforms raw database dumps into the input required for the research question.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the expected number of rows, no null values in the engineered feature columns, and that the calculated feature values match manual calculations for a known sample material.

**Acceptance Scenarios**:

1. **Given** the raw electronic transport database is available at the specified DOI, **When** the ingestion script runs, **Then** the output dataset contains only records from the predefined thermoelectric families (bismuth telluride, lead telluride, skutterudites) with complete composition data.
2. **Given** a valid alloy composition entry, **When** the feature engineering module processes it, **Then** the output includes calculated values for mean atomic radius, electronegativity variance, valence electron concentration, and atomic number variance, with no missing values.
3. **Given** a record with missing Seebeck coefficient or elemental composition, **When** the pipeline runs, **Then** that record is excluded from the final dataset without causing a script crash.

---

### User Story 2 - Predictive Modeling and Feature Importance Analysis (Priority: P2)

The system MUST train a gradient boosting regressor (scikit-learn, ≤100 trees) on the engineered dataset using 5-fold cross-validation, evaluate performance on a hold-out test set, and extract the top 5 most predictive compositional descriptors. The system MUST include 'material family' as a categorical feature to control for crystallographic phase differences and report the 95% confidence interval for the R² score. The system MUST also report the individual Pearson correlation coefficient (r) for each engineered descriptor against the Seebeck coefficient to allow post-hoc hypothesis testing regarding VEC or electronegativity.

**Why this priority**: This directly addresses the core research question of identifying which compositional features correlate with Seebeck coefficient. It provides the primary scientific output of the project. This analysis is exploratory; due to the physical limitations of compositional descriptors (which do not capture band structure), the goal is to identify significant correlations rather than definitive predictive rules.

**Independent Test**: Can be fully tested by running the training script and verifying that the model achieves an R² score (even if low), that the cross-validation loop completes without error, that a 95% confidence interval is reported, and that a ranked list of feature importances and individual correlations is generated.

**Acceptance Scenarios**:

1. **Given** the engineered dataset with train/test split (80/20 stratified by material family), **When** the gradient boosting model is trained with 5-fold cross-validation, **Then** the model completes training and reports mean cross-validated R², the 95% confidence interval for R², and Mean Absolute Error (MAE).
2. **Given** a trained model, **When** evaluated on the hold-out test set, **Then** the system outputs the test set R² score, MAE, and identifies the top 5 features by importance score.
3. **Given** the test set results, **When** compared against a linear regression baseline, **Then** the system logs whether the gradient boosting model outperformed the linear baseline in terms of R².
4. **Given** the feature set, **When** the correlation analysis runs, **Then** the system outputs a table of Pearson r values for each descriptor against the Seebeck coefficient.

---

### User Story 3 - Visualization and Reporting of Composition-Property Relationships (Priority: P3)

The system MUST generate visualizations plotting the top predictive descriptors against the Seebeck coefficient and produce a summary report documenting the findings. The report MUST explicitly state the test set R² and classify the result as: "Success" if R² > 0.2, "Inconclusive" if 0.2 ≤ R² < 0.4, or "Failure" if R² < 0.2.

**Why this priority**: Visualization is required to interpret the feature importance results and communicate the "compositional rules" identified in the research question to the materials science community. The lowered threshold (R² > 0.2) reflects the scientific reality that simple descriptors are weak predictors of transport properties.

**Independent Test**: Can be fully tested by running the reporting script and verifying that output images (PNG/SVG) exist, contain valid axes labels, and that the text report contains the calculated R², its classification (Success/Inconclusive/Failure), and the 95% confidence interval.

**Acceptance Scenarios**:

1. **Given** the feature importance rankings from the trained model, **When** the visualization module runs, **Then** scatter plots are generated for the top 3 descriptors vs. Seebeck coefficient with clear axis labels and trend lines.
2. **Given** the model performance metrics, **When** the summary report is generated, **Then** the report explicitly states the test set R², classifies it as "Success" if > 0.2, "Inconclusive" if 0.2 ≤ R² < 0.4, or "Failure" if < 0.2, and includes the 95% confidence interval.
3. **Given** the analysis results, **When** the README is updated, **Then** it includes a link to the generated figures and a summary of the top 2-3 compositional descriptors found to be most predictive.

### Edge Cases

- What happens if the downloaded database contains alloy compositions that do not match the predefined thermoelectric families? (System filters them out and logs a count).
- How does the system handle materials with missing elemental electronegativity values in the periodic table reference? (System excludes the record or imputes based on group averages, logging the action).
- What if the dataset size is insufficient to split into a meaningful 80/20 train/test set (e.g., < 50 records)? (System raises a warning and defaults to a 90/10 split or cross-validation only).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the electronic transport database from the specified DOI and parse it into a structured DataFrame (See US-1).
- **FR-002**: System MUST filter records to include only thermoelectric-relevant alloy families (bismuth telluride, lead telluride, skutterudites) and exclude entries with missing Seebeck coefficients or composition data (See US-1).
- **FR-003**: System MUST calculate compositional descriptors (mean atomic radius, electronegativity variance, valence electron concentration, atomic number variance) for every valid record using standard periodic table data (See US-1).
- **FR-004**: System MUST train a gradient boosting regressor (max 100 trees) using 5-fold cross-validation and evaluate on an 80/20 stratified train/test split. The model MUST include 'material family' as a categorical feature to control for crystallographic phase differences (See US-2).
- **FR-005**: System MUST extract and rank feature importance scores to identify the top 5 compositional descriptors predicting Seebeck coefficient and calculate the Pearson correlation coefficient (r) for each descriptor individually (See US-2).
- **FR-006**: System MUST generate scatter plots of the top 3 descriptors against the Seebeck coefficient and a summary report containing the test set R², its classification (Success/Inconclusive/Failure), and the 95% confidence interval (See US-3).
- **FR-007**: System MUST operate entirely within CPU-only constraints (no GPU/CUDA), ensuring the analysis runs within 6 hours on a standard GitHub Actions free-tier runner (See Assumptions).
- **FR-008**: System MUST report the 95% confidence interval for the R² score derived from the cross-validation folds (See US-2).

### Key Entities

- **MaterialRecord**: Represents a single entry in the electronic transport database, containing composition (elemental list), Seebeck coefficient, and material family.
- **CompositionalDescriptor**: A derived numeric feature representing a specific physicochemical property of the alloy (e.g., electronegativity variance).
- **ModelOutput**: The result of the training process, containing R² score, MAE, feature importance rankings, and confidence intervals.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance explained (R²) by the compositional descriptors is measured against the expected threshold of > 0.2 for significant correlation (See US-2).
- **SC-002**: The feature importance ranking is measured against the requirement that the top-ranked feature must have an importance score > 0.0 and the model must demonstrate a statistically significant improvement (p < 0.05) over a null model (See US-2).
- **SC-003**: The model performance (R²) is measured against a linear regression baseline to determine if non-linear relationships exist (See US-2).
- **SC-004**: The computational feasibility is measured against the constraint of ≤ 6 hours runtime and ≤ 7 GB RAM on a CPU-only runner (See Assumptions).
- **SC-005**: The dataset completeness is measured against the requirement that the pipeline must retain ≥ 95% of the filtered input records with no nulls in the 4 engineered descriptor columns (See US-1).

## Assumptions

- The electronic transport database (DOI: 10.1038/sdata.2017.85) is accessible via public URL and the data format (JSON/CSV) remains stable.
- Standard periodic table data (electronegativity, atomic radius, valence electrons) is available via a standard Python library (e.g., `mendeleev` or `pymatgen`) without requiring external API calls that might fail in CI.
- The gradient boosting implementation in scikit-learn (`GradientBoostingRegressor`) is sufficient for the dataset size and does not require GPU acceleration or 8-bit quantization.
- The "thermoelectric-relevant" classification can be reliably determined by string matching material names or formulas against the predefined list (bismuth telluride, lead telluride, skutterudites) without complex crystallographic analysis.
- The dataset size is sufficient to support an 80/20 stratified split; if the dataset is very small (< 50 records), the analysis will rely heavily on cross-validation metrics rather than a hold-out test set.
- The compositional descriptors (e.g., mean atomic radius) are calculated as simple arithmetic means/variances of the constituent elements, ignoring complex crystal structure effects or defect concentrations which are not available in the source database.
- The physical limitations of compositional descriptors (inability to capture band structure) mean that R² values are expected to be low; a threshold of > 0.2 is considered scientifically significant for this feature set.