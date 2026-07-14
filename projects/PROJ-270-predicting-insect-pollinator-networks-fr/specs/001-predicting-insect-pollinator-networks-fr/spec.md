# Feature Specification: Predicting Insect Pollinator Networks from Floral Trait Data

**Feature Branch**: `001-predict-pollinator-networks`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Predicting Insect Pollinator Networks from Floral Trait Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest bipartite interaction matrices from the Web of Life database and corresponding floral trait metadata, preprocessing them into a unified feature matrix ready for model training. This is the foundational step; without clean, aligned data, no predictive analysis can occur.

**Why this priority**: This is the prerequisite for all downstream modeling. If data cannot be retrieved, aligned, or cleaned, the research question cannot be addressed.

**Independent Test**: Can be fully tested by running the data ingestion script against a small, fixed set of 3 Web of Life ecosystems and verifying the output feature matrix dimensions and data types match the expected schema (rows: plant-pollinator pairs, columns: encoded traits + binary link label).

**Acceptance Scenarios**:

1. **Given** a list of 10 Web of Life ecosystem IDs, **When** the ingestion script runs, **Then** it successfully downloads interaction matrices and trait metadata for at least 8 ecosystems with complete trait data (handling network errors gracefully).
2. **Given** raw trait data with missing values (e.g., missing scent profiles), **When** the preprocessing step executes, **Then** missing continuous values are imputed via median imputation, continuous traits are normalized via Z-score (after winsorizing outliers at the 1st and 99th percentiles), and missingness is measured and reported; if missingness exceeds 15%, the system flags the ecosystem for manual review.
3. **Given** categorical traits (e.g., color: "blue", "white", "yellow"), **When** encoding is applied, **Then** they are converted to one-hot vectors without data leakage between training and test splits.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

The system must train a Random Forest classifier on the prepared feature matrix using stratified 5-fold cross-validation to predict the probability of plant-pollinator links, ensuring robustness against class imbalance. Negative samples must be restricted to biologically plausible non-interactions (co-occurring species).

**Why this priority**: This implements the core analytical engine. It allows the user to quantify the predictive power of static traits and is the primary mechanism for answering the research question.

**Independent Test**: Can be fully tested by training the model on a subset of the data (e.g., 1 ecosystem) and verifying that the cross-validation loop completes, produces consistent AUC-ROC scores across folds, and that the model object is serializable.

**Acceptance Scenarios**:

1. **Given** a stratified training set with a 1:10 positive-to-negative link ratio (where negatives are co-occurring unobserved pairs), **When** the Random Forest model is trained with 5-fold CV, **Then** the mean AUC-ROC and standard deviation across folds are calculated and reported.
2. **Given** the training data, **When** the model is fit, **Then** it completes without OOM errors.
3. **Given** the model, **When** permutation importance is calculated, **Then** the top 3 most influential traits are identified and ranked by their impact on model accuracy.

---

### User Story 3 - Generalization Validation and Reporting (Priority: P3)

The system must evaluate the trained model against a held-out, independent ecosystem (not seen during training) to assess generalizability, and generate visualizations comparing predicted vs. observed network structures. Validation must use a degree-preserving null model.

**Why this priority**: This validates the external validity of the findings, ensuring the model captures general biological principles rather than overfitting to specific local datasets. It provides the final evidence for the "trait gap" hypothesis.

**Independent Test**: Can be fully tested by running the evaluation script on a single held-out ecosystem and verifying that an AUC-ROC score is generated, a network comparison plot is saved, and the results are logged to a summary report.

**Acceptance Scenarios**:

1. **Given** a model trained on a subset of ecosystems, **When** evaluated on one held-out independent ecosystem, **Then** the AUC-ROC is reported and compared against a bipartite configuration model null (preserving degree distribution) to confirm it exceeds the null with statistical significance (p < 0.05 via permutation test).
2. **Given** the predicted link probabilities, **When** visualized against the observed network, **Then** a networkx plot is generated showing nodes (plants/pollinators) and edges (observed vs. predicted), highlighting discrepancies where high-probability predicted links are absent in reality.
3. **Given** the full analysis, **When** the final report is generated, **Then** it includes the AUC-ROC, precision-recall curves, and a ranked list of trait importance, formatted as a Markdown summary.

### Edge Cases

- What happens when a specific ecosystem in Web of Life has no corresponding trait metadata in Dryad or literature? (System must skip that ecosystem and log a warning, proceeding with the remaining valid set).
- How does the system handle extreme class imbalance (e.g., <1% positive links) in a specific ecosystem? (System must apply stratified sampling and potentially adjust class weights in the Random Forest).
- What if the held-out ecosystem is too small to provide a statistically meaningful validation? (System must flag the sample size as insufficient for robust validation and report the limitation).

### Risks

- **Risk about data availability**: The Web of Life database and associated Dryad repositories may contain sufficient floral trait metadata (color, corolla depth, scent) for fewer than 8 of the requested ecosystems. The system is designed to proceed with whatever valid data is available (minimum 8 required for statistical power), but results may be limited if this threshold is not met.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download bipartite interaction matrices and floral trait metadata from Web of Life and associated repositories for a target of 10 distinct ecosystems, but must succeed with at least 8 ecosystems containing complete trait data. (See US-1)
- **FR-002**: System MUST preprocess data by encoding categorical traits via one-hot encoding, normalizing continuous traits via Z-score (after winsorizing outliers at 1st/99th percentiles), and imputing missing values using median imputation. (See US-1)
- **FR-003**: System MUST train a Random Forest classifier using `scikit-learn` with 5-fold stratified cross-validation to address class imbalance. (See US-2)
- **FR-004**: System MUST evaluate model performance using AUC-ROC and precision-recall curves against a held-out independent ecosystem, comparing results against a bipartite configuration model null hypothesis. (See US-3)
- **FR-005**: System MUST perform permutation importance testing to rank floral traits by their contribution to prediction accuracy. (See US-2)
- **FR-006**: System MUST generate network visualizations comparing observed vs. predicted links using `networkx`. (See US-3)
- **FR-007**: System MUST generate negative training samples (unobserved links) only from plant-pollinator pairs that are spatially and temporally co-occurring in the same ecosystem to prevent the model from learning co-occurrence patterns instead of trait matching. (See US-2)

### Key Entities

- **Ecosystem**: A distinct geographic region with a specific plant-pollinator community.
- **Plant-Pollinator Pair**: A potential interaction unit defined by a specific plant species and a specific pollinator species.
- **Floral Trait**: A measurable characteristic of a plant (e.g., corolla depth, color, scent compound) used as a predictor variable.
- **Link**: A binary variable (0 or 1) indicating the presence or absence of an observed interaction between a plant and pollinator.
- **Co-occurring Pair**: A plant-pollinator pair where both species are known to exist in the same ecosystem at the same time, regardless of observed interaction.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (AUC-ROC) of the trait-based model is measured against a bipartite configuration model null (preserving degree distribution) to confirm it exceeds the null with statistical significance (p < 0.05). (See US-3)
- **SC-002**: The relative importance of floral traits (morphology, scent, color) is measured via permutation importance to determine which physical constraints drive network specificity. (See US-2)
- **SC-003**: The generalizability of the model is measured by comparing AUC-ROC scores on the held-out ecosystem against the cross-validation mean to assess overfitting. (See US-3)
- **SC-004**: The "trait gap" is quantified by measuring the difference between the AUC-ROC of a saturated model (using all known interaction features) and the observed AUC-ROC, indicating the portion of link variance unexplained by static traits. (See US-3)
- **SC-005**: The computational feasibility is measured by ensuring the entire training and evaluation pipeline completes without OOM errors on a CPU-only runner with ≤7 GB RAM. (See US-2)

## Assumptions

- **Assumption about methodological framing**: Since the data is observational (no random assignment of traits to pollinators), all findings regarding "determination" of links are framed as associational correlations, not causal effects.
- **Assumption about trait validity**: The floral traits retrieved from literature and databases are validated measurements (e.g., standard color scales, calibrated scent analysis) and are comparable across different ecosystems.
- **Assumption about class imbalance**: The inherent sparsity of ecological networks (few observed links vs. many possible pairs) will be adequately addressed by stratified 5-fold cross-validation and class weighting, without requiring synthetic data generation.
- **Assumption about co-occurrence**: Spatial and temporal metadata in the source databases is sufficient to accurately determine which plant-pollinator pairs are co-occurring, allowing for the construction of a valid negative sample set.