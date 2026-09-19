# Feature Specification: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-08-07  
**Status**: Draft  
**Input**: User description: "Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher MUST be able to download the ChEMBL dataset, filter for molecules with specific experimental outcomes (oral bioavailability, apparent permeability, or clearance), and sanitize the chemical structures (remove salts, fix valences) to generate a clean, analysis-ready dataset.

**Why this priority**: Without a clean, filtered dataset containing both calculated descriptors and ground-truth experimental values, no statistical modeling or correlation analysis can occur. This is the foundational block.

**Independent Test**: The pipeline can be tested by running the data acquisition script and verifying that the output CSV contains exactly the columns required (SMILES, experimental value, calculated descriptors) with zero rows containing missing values or invalid chemical structures.

**Acceptance Scenarios**:

1. **Given** the ChEMBL FTP server is reachable, **When** the download script executes, **Then** the raw data file is saved locally and the script reports the total number of rows retrieved.
2. **Given** a raw dataset containing molecules with missing experimental data, **When** the preprocessing filter runs, **Then** all rows with missing target variables (bioavailability, permeability, clearance) are removed.
3. **Given** a SMILES string with invalid valence or salt artifacts, **When** the RDKit sanitization step runs, **Then** the molecule is either corrected or removed from the final dataset, and a log entry records the action.

---

### User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

The researcher MUST be able to compute fundamental 2D molecular descriptors (TPSA, logP, MW, rotatable bonds, etc.) for the cleaned dataset and train both Linear Regression and Random Forest models to predict the experimental outcomes.

**Why this priority**: This step generates the predictive models required to test the research hypothesis regarding the strength of correlations between structural features and biological performance.

**Independent Test**: The modeling step is testable by verifying that the training script outputs two distinct model artifacts (one linear, one tree-based) and a feature importance report, without crashing due to memory constraints on the CPU runner.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset of up to 15,000 molecules, **When** the descriptor calculation runs, **Then** a new CSV is produced containing all requested 2D descriptors for every molecule.
2. **Given** the descriptor dataset and a defined target variable, **When** the model training script executes, **Then** a Linear Regression model and a Random Forest model are fitted and saved to disk.
3. **Given** the trained models, **When** feature importance analysis is performed, **Then** a ranked list of descriptors (e.g., logP, TPSA) is generated, identifying the top contributors to prediction accuracy.

---

### User Story 3 - Model Evaluation and Visualization (Priority: P3)

The researcher MUST be able to evaluate the trained models on a hold-out test set using RMSE and Pearson correlation coefficient (r), and generate visualizations (scatter plots of predicted vs. experimental, feature importance bar charts) to interpret the results.

**Why this priority**: This step provides the empirical evidence to answer the research question, allowing the researcher to determine if the observed correlations are strong enough to validate the use of descriptors as proxies for wet-lab assays.

**Independent Test**: The evaluation step is testable by running the script on the test set and verifying that the output includes specific numerical metrics (RMSE, r) and that the generated PNG files are non-empty and correctly labeled.

**Acceptance Scenarios**:

1. **Given** a trained model and a hold-out test set, **When** the evaluation script runs, **Then** the Root Mean Squared Error (RMSE) and Pearson correlation coefficient (r) are calculated and printed to the console.
2. **Given** the predicted and experimental values, **When** the visualization script runs, **Then** a scatter plot (Predicted vs. Experimental) is saved as a PNG file.
3. **Given** the feature importance data, **When** the visualization script runs, **Then** a bar chart showing the contribution of each descriptor is saved as a PNG file.

---

### Edge Cases

- What happens when the ChEMBL dataset contains duplicate SMILES entries with conflicting experimental values? (System must define a strategy: e.g., average the values or keep the most recent).
- How does the system handle molecules where the RDKit sanitizer fails to correct the valence (e.g., exotic elements)? (System must log and exclude these molecules).
- What happens if the sample size after filtering drops below the threshold required for a statistically valid train/test split (e.g., < 100 samples)? (System must halt and report a "Data Insufficiency" error).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the ChEMBL Release 33 dataset via FTP, filtering specifically for entries with experimental measurements for oral bioavailability, apparent permeability (Papp), or clearance. (See US-001)
- **FR-002**: System MUST sanitize molecular structures using RDKit to remove salts, correct non-standard valences, and exclude molecules with missing target variables or invalid chemical structures. (See US-001)
- **FR-003**: System MUST calculate a defined set of 2D molecular descriptors (TPSA, logP, MW, rotatable bonds, H-bond donors/acceptors, ring count) for every retained molecule. (See US-002)
- **FR-004**: System MUST split the processed dataset into a training set and a hold-out test set using stratified sampling by target variable and a fixed random seed of 42. (See US-002)
- **FR-005**: System MUST fit both a Linear Regression model and a Random Forest model to predict the experimental outcome from the descriptor set, ensuring the Random Forest does not exceed memory limits on a 2-core CPU runner. (See US-002)
- **FR-006**: System MUST evaluate model performance on the hold-out set using Root Mean Squared Error (RMSE) and Pearson correlation coefficient (r). (See US-003)
- **FR-007**: System MUST generate a scatter plot of predicted vs. experimental values and a bar chart of feature importances, saving them as PNG files. (See US-003)
- **FR-008**: System MUST limit the dataset size to a computationally feasible subset via stratified random sampling to ensure the entire pipeline completes within the 6-hour, 7GB RAM, 2 CPU core limit of the GitHub Actions runner. (See US-002, US-003)
- **FR-009**: System MUST handle duplicate SMILES entries by retaining the entry with the most recent assay date; if dates match, the system MUST average the conflicting experimental values. (See US-001)

### Key Entities

- **Molecule**: Represents a chemical compound with attributes: SMILES string, calculated descriptors (TPSA, logP, etc.), and experimental target value (bioavailability, permeability, or clearance).
- **Model**: Represents a trained statistical predictor (Linear Regression or Random Forest) with attributes: coefficients/feature importances, training metrics, and prediction capability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient (r) between predicted and experimental values is measured against the hypothesis that logP and TPSA are strong predictors; project succeeds if r >= 0.6, otherwise the measured r-value is reported as evidence of weak correlation. (See FR-006, US-003)
- **SC-002**: The Root Mean Squared Error (RMSE) is measured against a mean predictor baseline (predicting the training set mean for all test samples) to quantify the predictive improvement of the models. (See FR-006, US-003)
- **SC-003**: The feature importance ranking is measured against domain knowledge; success is defined as logP and TPSA both ranking within the top 3 features by importance in the Random Forest model. (See FR-007, US-003)
- **SC-004**: The total pipeline execution time is measured against the 6-hour limit of the GitHub Actions free-tier runner to ensure feasibility. (See FR-008, US-002)
- **SC-005**: The memory usage peak is measured against the 7GB RAM limit of the runner to confirm the dataset size and model complexity are tractable. (See FR-008, US-002)

## Assumptions

- The ChEMBL Release 33 dataset contains a sufficient number of unique molecules with valid experimental measurements for oral bioavailability, permeability, or clearance to support a statistically meaningful analysis (N > 1,000) after filtering.
- The RDKit library installed in the GitHub Actions environment supports the calculation of all required 2D descriptors (TPSA, logP, etc.) without requiring GPU acceleration.
- The experimental values for bioavailability, permeability, and clearance in ChEMBL are measured using standard, comparable assays, allowing for direct correlation analysis across different scaffolds.
- The relationship between molecular descriptors and biological outcomes is primarily linear or captureable by a Random Forest on 2D features, meaning 3D or dynamic features are not strictly required for the initial hypothesis test.
- The GitHub Actions free-tier runner provides consistent 2 CPU cores and ~7GB RAM for the duration of the job, allowing the [deferred]-molecule dataset to fit in memory.