# Feature Specification: Identifying Structure-Property Relationships in Polymer Blends

**Feature Branch**: `001-structure-property-relationships`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Identifying Structure-Property Relationships in Polymer Blends Using Public Databases"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Harmonization (Priority: P1)

A researcher needs to aggregate polymer blend data from disparate public sources (Polymer Database, NIST, Materials Project) into a single, clean, and unit-harmonized dataset containing SMILES strings, composition vectors, and measured macroscopic properties (Tg, Young's modulus).

**Why this priority**: Without a unified, high-quality dataset, no predictive modeling or analysis is possible. This is the foundational block of the entire research pipeline.

**Independent Test**: Can be fully tested by running the data ingestion script on a known dataset and verifying that: (1) all non-null SMILES strings are parsed correctly by RDKit, (2) all units are converted to Kelvin and GPa without error, (3) entries failing the weight-fraction sum check (|sum - 1.0| > 0.02) are correctly flagged and excluded, AND (4) the system reports a success rate of ≥80% of raw records successfully harmonized (as defined in SC-006). The test validates the *correctness* of the processing logic AND the *success rate metric*.

**Acceptance Scenarios**:

1. **Given** raw CSV/JSON files from Polymer Database and NIST with mixed units, **When** the ingestion script processes them, **Then** the output dataset must have all Tg values converted to Kelvin and Modulus values converted to GPa, with no missing values in the target columns.
2. **Given** a blend entry where the weight fractions of components do not sum to 1.0 (within a tolerance of ±0.02), **When** the script processes the row, **Then** the row must be flagged and excluded from the final dataset, logging the specific discrepancy.
3. **Given** a component with a malformed SMILES string, **When** the script attempts to parse it with RDKit, **Then** the row must be excluded, and a count of excluded rows due to invalid chemistry must be recorded in the execution log.

---

### User Story 2 - Feature Engineering and Descriptor Generation (Priority: P2)

A materials scientist needs to automatically generate molecular descriptors (e.g., molecular weight, fractional free volume, Hansen solubility parameters) from SMILES strings and compute blend-specific interaction features (weighted averages, differences, and non-linear mixing rules) to serve as predictors for machine learning models.

**Why this priority**: Raw SMILES strings are not directly usable by regression models; this step transforms structural data into the quantitative features required to answer the research question regarding structure-property relationships.

**Independent Test**: Can be fully tested by running the feature engineering module on a small sample of known polymers and verifying that the generated feature matrix has the expected dimensions, that ≥95% of rows have ≥15 non-null descriptors (as defined in SC-007), and that specific derived features (e.g., "difference in H-bonding capacity", "Fox equation Tg residual") are mathematically consistent with the input monomer descriptors.

**Acceptance Scenarios**:

1. **Given** a valid SMILES string for a monomer, **When** the descriptor generator runs, **Then** it must produce at least 15 distinct molecular descriptors (including MW, TPSA, rotatable bonds, and calculated free volume) with no NaN values.
2. **Given** a blend composition with two components and their respective monomer descriptors, **When** the interaction features are computed, **Then** the system must compute: (a) the weighted average of descriptors, (b) the absolute difference between component descriptors, AND (c) non-linear mixing rule predictions (specifically the Fox equation and Gordon-Taylor equation) to derive the Tg_residual target (Tg_measured - Tg_Fox).
3. **Given** a dataset where two predictors are definitionally related (e.g., a derived parameter bounded by a base parameter), **When** the collinearity diagnostic runs, **Then** the system must flag pairs with a Variance Inflation Factor (VIF) > 5.0, perform a sensitivity analysis by excluding the predictor with the highest VIF, and report the impact of this exclusion on model performance metrics (MAE, R²), WITHOUT automatically excluding the predictor from the primary model input unless VIF > 10.

---

### User Story 3 - Model Training and Statistical Validation (Priority: P3)

A researcher needs to train Random Forest and XGBoost models to predict Tg_residual and Young's modulus, evaluate their performance against a linear baseline, and generate interpretable feature importance rankings, all within the constraints of a CPU-only CI environment.

**Why this priority**: This delivers the core scientific output (predictive accuracy and key driver identification) and validates the hypothesis that public databases suffice for accurate prediction.

**Independent Test**: Can be fully tested by executing the full training pipeline on a subset of the data and verifying that: (1) if N < 100, the system halts with "Data Insufficiency" error; (2) if N ≥ 100, the model reports the MAE for Tg_residual and Modulus; (3) a paired t-test is performed to compare errors with a linear baseline, with the p-value reported regardless of the outcome; (4) the timer starts at the beginning of `01_ingest.py` and ends at the write of `final_report.json`, completing within 5 hours on `ubuntu-latest`.

**Acceptance Scenarios**:

1. **Given** the dataset is partitioned into training, validation, and test sets using a random split with a fixed seed (if N≥500) OR Stratified Repeated K-Fold (5 folds, 3 repeats) (if N<500), **When** the Random Forest and XGBoost models are trained with hyperparameter tuning on the validation set (or inner fold), **Then** the selected best model must report the test-set MAE for Tg_residual and Young's modulus, and these values must be compared against the linear baseline.
2. **Given** the test-set predictions from the best ML model and a linear regression baseline (trained on the same features), **When** a paired t-test is performed on the absolute errors, **Then** the system must report the p-value of the test and state whether the null hypothesis is rejected or not, regardless of whether p < 0.05.
3. **Given** the final trained model, **When** SHAP values are computed for the top-ranked predictions, **Then** the output must include a ranked list of feature importances and a visualization showing how specific descriptors (e.g., "fractional free volume") drive the predicted Tg_residual for individual samples.

---

### Edge Cases

- What happens when the public API (Materials Project) returns a rate-limit error during data acquisition? (System must implement exponential backoff with initial=1s, multiplier=2, max=5 retries before failing the job).
- How does the system handle polymer blends with more than 3 components where the SMILES strings are missing for minor constituents? (Rows with missing SMILES for any component > 0.05 weight fraction are excluded).
- How does the system handle datasets where the number of samples is too small (< 100) to perform a meaningful 5-fold cross-validation? (The system must halt training and raise a "Data Insufficiency" error).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse polymer blend data from the Polymer Database, NIST WebBook, and Materials Project APIs, harmonizing units to Kelvin and GPa, and validate against `contracts/dataset.schema.yaml`. (See US-1)
- **FR-002**: The system MUST validate that weight fractions in every blend entry sum to 1.0 ± 0.02, excluding any entries that fail this check. (See US-1)
- **FR-003**: The system MUST generate a minimum of 15 molecular descriptors per monomer using RDKit, including molecular weight, topological polar surface area, and fractional free volume. (See US-2)
- **FR-004**: The system MUST compute blend-specific interaction features, specifically: (a) weighted averages of monomer descriptors, (b) absolute differences between component descriptors, and (c) non-linear mixing rule predictions using the Fox equation and Gordon-Taylor equation to derive the target variable `Tg_residual` (Tg_measured - Tg_Fox) for model training. (See US-2)
- **FR-005**: The system MUST train Random Forest and XGBoost regressors using a 70/15/15 split if N≥500, OR Stratified Repeated K-Fold (5 folds, 3 repeats) if N<500. The validation set (or inner fold) is strictly for hyperparameter tuning; the test set is held out until the final evaluation. (See US-3)
- **FR-006**: The system MUST perform a paired t-test comparing the test-set errors of the best ML model against a linear regression baseline (trained on the same features and target) and report the resulting p-value. (See US-3)
- **FR-007**: The system MUST generate SHAP values for the top-ranked predictions to provide interpretability of feature contributions. (See US-3)
- **FR-008**: The system MUST detect predictor pairs with a Variance Inflation Factor (VIF) > 5.0. If VIF > 5.0, the system MUST perform a sensitivity analysis by re-training the model excluding the predictor with the highest VIF and reporting the delta in MAE and R². If N<100, this is a sensitivity analysis only; if VIF > 10, the system MUST exclude the predictor. (See US-2)
- **FR-009**: The system MUST execute the training loop times with seeds {1, 2, 3, 4, 5} to assess stability of feature importance rankings. (See US-3)
- **FR-010**: The system MUST implement exponential backoff with initial=1s, multiplier=2, max=5 retries for API rate-limit errors. (See Edge Cases)
- **FR-011**: The system MUST exclude rows with missing SMILES for any component > 0.05 weight fraction. (See Edge Cases)
- **FR-012**: The system MUST halt training and raise a "Data Insufficiency" error if N < 100. (See Edge Cases)
- **FR-013**: The system MUST implement a fallback to "component-level prediction mode" if the "perfect join" of SMILES + Composition + Tg + Modulus fails for >50% of records, provided a verified source for the combined data exists. (See Edge Cases)
- **FR-014**: The system MUST validate the weight-fraction tolerance by performing a sensitivity sweep over a range of small values and reporting the impact on data quality. (See Assumptions)
- **FR-015**: The system MUST verify the existence of a specific, accessible dataset URL containing SMILES, Composition, Tg, and Modulus before ingestion. If no verified source is found, the system MUST halt. (See Assumptions)
- **FR-016**: The system MUST implement "Source Stratification" in the validation strategy (stratified by source) to address domain shift. (See Assumptions)
- **FR-017**: The system MUST implement "Stratified Random Sampling" if the raw dataset exceeds available RAM, targeting [deferred] of max RAM capacity. (See Assumptions)
- **FR-018**: The system MUST track content hashes of all `data/` artifacts in a `state.json` file. (See Constitution)
- **FR-019**: The system MUST use the Reference-Validator Agent to verify all cited URLs against a `CITATION_TITLE_OVERLAP_THRESHOLD` check. (See Constitution)

### Key Entities

- **PolymerBlend**: Represents a specific blend entry, containing attributes for components (SMILES, weight fraction), measured Tg (K), and measured Young's Modulus (GPa).
- **MolecularDescriptor**: Represents a computed property of a monomer (e.g., MW, TPSA, H-bonding capacity) derived from its SMILES string.
- **InteractionFeature**: Represents a derived feature for a blend, calculated as a function (average, difference, Fox, Gordon-Taylor) of the constituent MolecularDescriptors.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the best predictive model is measured against the linear baseline MAE on a held-out test set (70/15/15 split if N≥500, OR Stratified Repeated K-Fold if N<500). (See US-3)
- **SC-002**: The statistical significance of the ML model's improvement over the linear baseline is measured by reporting the p-value from a paired t-test. (See US-3)
- **SC-003**: The feature importance rankings are measured against the requirement to identify at least 3 distinct molecular descriptors that appear in the top-10 list for ≥ 80% of 5 independent training runs (seeds 1-5), aggregated by frequency. (See US-3)
- **SC-004**: The data quality is measured against the requirement that ≥ 95% of the union (deduplicated by SMILES+Composition) of all successfully fetched records (HTTP 200 + valid JSON parse) from Polymer Database, NIST, and Materials Project pass the unit harmonization and weight-fraction validation checks. (See US-1)
- **SC-005**: The computational feasibility is measured against the constraint that the entire pipeline (ingest, engineering, training) completes within 5 hours on a GitHub Actions `ubuntu-latest` runner (2 CPU, 7 GB RAM), measured from `01_ingest.py` start to `final_report.json` write. (See Assumptions)
- **SC-006**: The ingestion success rate is measured as the percentage of raw records successfully harmonized (passed all validation checks) out of total fetched records, with a target of ≥ 80%. (See US-1)
- **SC-007**: The feature generation utility is measured as the percentage of rows with ≥ 15 non-null descriptors, with a target of ≥ 95%. (See US-2)
- **SC-008**: The stability of feature importance is measured by the frequency of top-10 features across 5 runs, with a target of ≥ 80% consistency. (See US-3)
- **SC-009**: The rate-limit handling is measured by the system's ability to recover from 5 consecutive rate-limit errors within 30 seconds. (See Edge Cases)
- **SC-010**: The small dataset handling is measured by the system's ability to halt with "Data Insufficiency" error when N < 100. (See Edge Cases)
- **SC-011**: The fallback logic is measured by the system's ability to switch to "component-level prediction mode" if the "perfect join" fails for >50% of records. (See Edge Cases)

## Assumptions

- **Assumption about data availability**: It is assumed that the Polymer Database, NIST WebBook, and Materials Project APIs remain accessible and that the public datasets contain sufficient entries to support training.
- **Assumption about dataset-variable fit**: It is assumed that the available public datasets contain the necessary molecular descriptors (or data to compute them via RDKit) and that no critical predictor variables (e.g., specific processing history parameters) are missing; if a required variable is found to be absent, the analysis will be restricted to available descriptors.
- **Assumption about inference framing**: Since the data is observational (no random assignment of molecular structures), all findings regarding structure-property relationships will be framed as associational, not causal. Feature importance reflects *predictive contribution* in the presence of correlation, not causal mechanism.
- **Assumption about compute resources**: The entire analysis is assumed to run on a CPU-only environment (no GPU); therefore, no 8-bit quantization or large-model training is permitted, and data must be sampled or subsetted if it exceeds available RAM capacity.
- **Assumption about threshold justification**: The tolerance for weight-fraction summation (±0.02) is based on standard experimental measurement error in polymer synthesis; this threshold will be subject to a sensitivity analysis sweeping values of {0.01, 0.02, 0.05} to ensure robustness.
- **Assumption about measurement validity**: The molecular descriptors generated by RDKit (e.g., TPSA, MW) are assumed to be validated and standard in the materials science community, requiring no further experimental validation.
- **Assumption about multiplicity**: When testing multiple hypotheses (e.g., different models, different descriptors), a correction for multiple comparisons (e.g., Bonferroni or False Discovery Rate) will be applied to the p-values to control family-wise error.