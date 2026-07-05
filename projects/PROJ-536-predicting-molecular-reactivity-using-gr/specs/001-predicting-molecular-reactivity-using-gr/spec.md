# Feature Specification: Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets

**Feature Branch**: `001-predict-molecular-reactivity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Reactivity Using Graph Neural Networks and Reaction Datasets"

## User Scenarios & Testing

### User Story 1 - Core Yield Prediction Pipeline (Priority: P1)

The researcher downloads a subset of the USPTO reaction dataset, parses the molecular structures into graphs, and trains a lightweight Message Passing Neural Network (MPNN) to predict reaction yield. The system must successfully output a regression model that can predict yields for a held-out test set with quantified error metrics (MAE, RMSE).

**Why this priority**: This is the foundational capability. Without a working prediction model, no comparative analysis or feature importance study is possible. It establishes the baseline functionality of the research tool.

**Independent Test**: The pipeline can be fully tested by running the training script on a small, fixed subset of the USPTO data and verifying that the output includes a model file and a JSON report containing MAE and RMSE values that are finite numbers (not NaN or Infinity).

**Acceptance Scenarios**:

1. **Given** a valid USPTO subset CSV file with SMILES and yield columns, **When** the data ingestion and graph conversion script is executed, **Then** the system produces a graph dataset object where every molecule has valid atom and bond feature vectors, and no parsing errors occur for >95% of the input rows.
2. **Given** the converted graph dataset split into train/validation/test sets, **When** the MPNN model is trained using early stopping (patience=5) or a maximum of 200 epochs on a CPU-only environment, **Then** the training loss shows a general downward trend (non-increasing moving average over 5 epochs) and the final validation loss is recorded in the log.
3. **Given** a trained MPNN model and a test set, **When** the inference step is executed, **Then** the system outputs a JSON file containing predicted yields for all test samples, and the calculated Mean Absolute Error (MAE) is a positive number ≤ 15.0 (assuming yield is 0-100%).

---

### User Story 2 - Baseline Comparison and Variance Analysis (Priority: P2)

The researcher compares the GNN model's performance against traditional baselines (Random Forest on Morgan fingerprints and Linear Regression on molecular descriptors). The system must calculate and report the R² improvement of the GNN over the best baseline, determining if the structural topology adds predictive value.

**Why this priority**: The research question specifically asks whether graph topology explains yield variability *better* than traditional descriptors. This comparison is the core scientific validation step.

**Independent Test**: The analysis can be tested by running the comparison module on a fixed dataset and verifying that the output report explicitly lists the R² scores for the GNN, Random Forest, and Linear Regression models, and calculates the delta.

**Acceptance Scenarios**:

1. **Given** the same test set used in User Story 1, **When** the baseline models (RF with Morgan fingerprints, LR with MW/logP/TPSA) are trained and evaluated on the same stratified split, **Then** the system generates a comparison table showing R², MAE, and RMSE for all three models (GNN, RF, LR).
2. **Given** the performance metrics from all models, **When** the variance analysis is computed, **Then** the system outputs a specific value for "R² Improvement" calculated as (R²_GNN - R²_Baseline), where R²_Baseline is the maximum of the two baseline scores.
3. **Given** the comparison results, **When** the significance check is performed, **Then** the system flags the result as "Practically Significant" (if R² improvement ≥ 0.10) or "No Significant Improvement" (otherwise), based on the researcher-defined threshold of 0.10. This flag is a reporting item for researcher interpretation, not an automated pass/fail gate.

---

### User Story 3 - Feature Importance and Uncertainty Quantification (Priority: P3)

The researcher identifies which subgraph patterns or graph features drive the predictions using GNNExplainer and generates prediction intervals using conformal prediction to quantify uncertainty.

**Why this priority**: This addresses the "identify specific subgraph patterns" part of the research question and adds necessary rigor regarding confidence in the predictions, which is critical for chemical application.

**Independent Test**: The module can be tested by running the importance and uncertainty scripts on a trained model and verifying that the output includes a ranked list of subgraph patterns and a prediction interval file with valid lower/upper bounds.

**Acceptance Scenarios**:

1. **Given** a trained GNN model, **When** the GNNExplainer algorithm is executed, **Then** the system outputs a ranked list of subgraph patterns (motifs) sorted by their impact on prediction error, with the A representative set of prominent patterns will be clearly identified and visualized..
2. **Given** a set of test predictions, **When** conformal prediction is applied to generate % intervals, **Then** the system produces a CSV file containing the predicted yield, lower bound, and upper bound for each sample, where the upper bound is strictly greater than the lower bound.
3. **Given** the prediction intervals, **When** the coverage rate is calculated, **Then** the system reports the percentage of true yields that fall within the predicted intervals, allowing the researcher to assess if the uncertainty quantification is well-calibrated.

---

### Edge Cases

- What happens when the USPTO dataset contains SMILES strings that RDKit cannot parse (invalid chemical syntax)? The system must log the row ID, skip the entry, and continue processing without crashing, reporting the total count of skipped entries.
- How does the system handle reaction classes with extremely low sample sizes (e.g., < 10 examples)? The system must stratify the split to ensure these classes are not entirely dropped from the test set, or flag them as "insufficient data for stratified evaluation" in the report.
- What happens if the CPU memory limit is exceeded during graph conversion for a large batch? The system must process the data in smaller chunks and aggregate the results, ensuring the job completes within the CI time limit.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse a specified subset of the USPTO reaction dataset, extracting SMILES strings and reaction yields, and skip any rows with invalid chemical syntax while logging the count of skipped entries. (See US-1)
- **FR-002**: System MUST convert molecular SMILES into graph representations using RDKit, extracting atom features (atomic number, charge, hybridization) and bond features (bond type, conjugation) suitable for Message Passing Neural Networks. (See US-1)
- **FR-003**: System MUST train a lightweight MPNN model on CPU-only hardware using early stopping (patience=5) or a maximum of 200 epochs, using mean squared error loss, and save the final model weights and training history. (See US-1)
- **FR-004**: System MUST implement and evaluate two baseline models: a Random Forest regressor using Morgan fingerprints and a Linear Regression model using molecular descriptors (MW, logP, TPSA) on the same stratified test set. (See US-2)
- **FR-005**: System MUST calculate and report the R² improvement of the GNN model over the best-performing baseline, explicitly flagging whether the improvement meets or exceeds the 0.10 researcher-defined threshold. (See US-2)
- **FR-006**: System MUST apply GNNExplainer to the trained GNN to identify the top contributing subgraph patterns and output a ranked list with visualizations. (See US-3)
- **FR-007**: System MUST apply conformal prediction to generate [deferred] prediction intervals for the test set yields and report the empirical coverage rate. (See US-3)
- **FR-008**: System MUST ensure all models (GNN and baselines) are trained and evaluated on data splits stratified by reaction class to prevent confounding due to class imbalance. (See US-2)

### Key Entities

- **ReactionRecord**: Represents a single chemical reaction instance, containing input reactant SMILES, product SMILES, reaction yield (0-100), and reaction class label.
- **MolecularGraph**: A graph data structure derived from a SMILES string, containing nodes (atoms with feature vectors) and edges (bonds with feature vectors).
- **ModelEvaluation**: A result set containing performance metrics (R², MAE, RMSE) for a specific model configuration on a specific dataset split.
- **PredictionInterval**: A tuple (lower_bound, predicted_value, upper_bound) associated with a specific reaction record, representing the uncertainty of the yield estimate.
- **SubgraphPattern**: A localized motif or subgraph identified by GNNExplainer as contributing significantly to the prediction, including atom/bond composition and frequency.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (R², MAE, RMSE) of the GNN model is measured against the performance of the Random Forest and Linear Regression baselines on the same stratified test set. (See FR-005)
- **SC-002**: The improvement in R² score provided by the GNN model is measured against the 0.10 threshold defined in FR-005. (See FR-005)
- **SC-003**: The calibration of the uncertainty estimates is measured by the empirical coverage rate of the [deferred] prediction intervals against the true yield values in the test set. (See FR-007)
- **SC-004**: The computational feasibility is measured by the total wall-clock time of the full pipeline (data parsing to evaluation) against the CI time limit on a 2-core CPU runner. (See Assumption A-003)
- **SC-005**: Data validity is measured by the percentage of successfully parsed reactions, with the target documented in the implementation plan. (See FR-001)
- **SC-006**: The R² improvement is measured against the researcher-defined 0.10 threshold to determine if the GNN provides practical significance for the specific study. (See FR-005, FR-008)

## Assumptions

- **A-001**: The USPTO dataset available via the public repository (Zenodo/PubChem) contains a sufficient number of reactions with explicit yield values and valid SMILES strings to support a standard train/val/test split with stratification by reaction class.
- **A-002**: The "reaction yield" variable in the dataset is a continuous numeric value representing the percentage yield, and does not require conversion from categorical labels or other units.
- **A-003**: The entire dataset (after sampling if necessary) and the MPNN model (with default precision, no reduced-bit quantization) will fit within the RAM and disk constraints of the GitHub Actions free-tier runner.
- **A-004**: The MPNN architecture implemented using PyTorch Geometric will converge within the early stopping criteria (patience=5) or 200 epochs on the CPU-only environment, as deep training on CPU is computationally expensive and the research focus is on feature comparison rather than state-of-the-art accuracy.
- **A-005**: The "reaction class" labels in the dataset are sufficiently distinct to allow for meaningful stratification, and the dataset does not contain excessive noise in the yield values that would render regression impossible.
- **A-006**: The 10% R² improvement threshold is a researcher-defined benchmark for this specific study to evaluate practical significance; it is not a universal community standard, and results should be interpreted within this context.