# Feature Specification: Predicting Material Degradation Pathways from Compositional Data

**Feature Branch**: `001-predict-degradation-pathways`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Material Degradation Pathways from Compositional Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest raw corrosion datasets from public repositories, filter for metallic alloys, and encode elemental compositions into machine-readable feature vectors.

**Why this priority**: Without clean, encoded data, no model training or analysis can occur. This is the foundational step that transforms raw literature data into a usable research artifact.

**Independent Test**: The pipeline can be executed end-to-end on a sample dataset, producing a clean CSV file with encoded features and valid degradation labels, verifiable by checking the output file dimensions and label distribution.

**Acceptance Scenarios**:

1. **Given** a raw CSV file from Zenodo containing mixed materials (polymers, composites, alloys), **When** the ingestion script runs, **Then** the output dataset contains ONLY records identified as metallic alloys, with polymers and composites removed.
2. **Given** a record with missing elemental weight percentages, **When** the preprocessing step runs, **Then** the record is handled as follows: if missing values constitute < 5% of the elemental fields, they are imputed using the **median value per element**; if missing values constitute ≥ 5%, the record is excluded. No NaN values exist in the final feature matrix.
3. **Given** the raw composition data, **When** the feature encoder runs, **Then** each record includes derived atomic properties (electronegativity, atomic radius) mapped from the periodic table for post-hoc analysis, while the primary training vector contains only elemental weight percentages.

---

### User Story 2 - Model Training and Evaluation (Priority: P2)

The system must train a multi-label classifier on the processed data and evaluate its performance against a held-out test set using macro-F1 score and confusion matrix analysis.

**Why this priority**: This step validates the core research hypothesis by determining if a statistical signal exists between composition and degradation mode.

**Independent Test**: The training script executes on a CPU-only environment, produces a trained model artifact, and generates a report containing the macro-F1 score and confusion matrix, which can be compared against a stratified random baseline.

**Acceptance Scenarios**:

1. **Given** the stratified train/test split, **When** the Random Forest classifier trains, **Then** the process completes within 6 hours on a standard CPU runner without GPU errors.
2. **Given** the trained model and test set, **When** evaluation runs, **Then** the output report displays a macro-F1 score that is statistically distinguishable from a **stratified random baseline** (preserving class distribution) via a **permutation test (n=1,000 iterations, p < 0.05)** AND exceeds the baseline macro-F1 by a margin of **≥ 0.05**.
3. **Given** the evaluation results, **When** the confusion matrix is generated, **Then** it clearly identifies which degradation modes (e.g., pitting vs. SCC) are most frequently confused by the model.

---

### User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

The system must identify which alloying elements drive specific degradation predictions and perform a sensitivity analysis on the classification threshold to ensure robustness.

**Why this priority**: This step provides scientific interpretability, allowing researchers to understand *why* the model makes predictions and verifying that results are not artifacts of arbitrary cutoffs.

**Independent Test**: The analysis script generates a ranked list of feature importances (via SHAP) and a plot showing model performance stability across a range of threshold values.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** feature importance analysis runs, **Then** the output lists the top elemental contributors (features) for each degradation pathway (e.g., Cr for pitting, Ni for SCC) using **SHAP values** to mitigate multicollinearity bias.
2. **Given** the model's probability outputs, **When** sensitivity analysis runs, **Then** the system sweeps the **decision probability threshold** (baseline 0.5) by applying deltas Δ ∈ {, 0.05, 0.1} (i.e., testing thresholds 0.49, 0.51, 0.45, 0.55, etc.) and reports how the false-positive and false-negative rates vary.
3. **Given** the sensitivity results, **When** the final report is generated, **Then** it explicitly states whether the headline performance metrics remain stable (within 5% variance) across the tested threshold range.

---

### Edge Cases

- What happens when a dataset contains records with only one or two elemental components (binary alloys) versus complex multi-component alloys?
- How does the system handle degradation labels that are ambiguous or contain multiple overlapping modes (e.g., "pitting + stress corrosion")?
- How does the system behave if the public dataset lacks specific environmental context variables (e.g., temperature, pH) that might be confounding factors?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest and parse raw corrosion datasets from Zenodo, filtering for metallic alloys only, to ensure dataset-variable fit for the analysis (See US-1).
- **FR-002**: The system MUST encode elemental weight percentages into feature vectors for training, ensuring all required variables are present. Derived atomic properties (electronegativity, radius) MUST be calculated but excluded from the primary training vector to prevent multicollinearity, though retained for post-hoc correlation analysis (See US-1).
- **FR-003**: The system MUST train a Random Forest multi-label classifier on CPU hardware, ensuring the analysis remains feasible within free-tier compute constraints (See US-2).
- **FR-004**: The system MUST evaluate model performance using macro-F1 score and confusion matrix to identify dominant error modes, providing a measurable success metric (See US-2).
- **FR-005**: The system MUST perform feature importance analysis using **SHAP values** and threshold sensitivity sweeps (sweeping decision threshold baseline with deltas Δ ∈ {small, 0.05, 0.1}) to justify decision boundaries and ensure robustness (See US-3).
- **FR-006**: The system MUST explicitly frame all findings as associational rather than causal, acknowledging the observational nature of the dataset (See US-2).
- **FR-007**: The system MUST split the dataset into a training set and an **Out-of-Distribution (OOD) test set** based on alloy class (e.g., holding out high-entropy alloys or specific alloy families) to validate generalization beyond the training distribution (See US-3).
- **FR-008**: The system MUST document the mitigation of multicollinearity by using elemental weight percentages as primary features and SHAP for importance, rather than impurity-based metrics (See US-3).
- **FR-009**: If the dataset lacks explicit environmental variables (pH, temperature, stress), the system MUST flag this limitation and widen the reported confidence intervals for predictions by **[deferred]** to account for unobserved confounding (See Assumptions).

### Key Entities

- **AlloyRecord**: A data entity representing a specific material sample, containing attributes for elemental composition (weight %), derived atomic properties, and the target degradation pathway label.
- **FeatureVector**: A data structure containing the **elemental weight percentages** used as the primary input for the Random Forest model.
- **DegradationPathway**: A categorical entity representing the mode of failure (e.g., pitting, stress corrosion cracking, fatigue, none), used as the target variable for classification.
- **ModelArtifact**: The output entity containing the trained classifier, SHAP-based feature importance rankings, and performance metrics, stored for reproducibility.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The macro-F1 score of the trained classifier is measured against a **stratified random baseline** (preserving class distribution) via a **permutation test (n=1,000 iterations)**. Success is defined as p < 0.05 AND a macro-F1 margin of **≥ 0.05** over the baseline (See US-2).
- **SC-002**: The stability of performance metrics (false-positive/false-negative rates) is measured across the decision threshold sweep range (baseline standard, deltas Δ ∈ {0.01, 0.05, 0.1}) to validate the robustness of the classification boundary (See US-3).
- **SC-003**: The feature importance rankings (SHAP values) are measured against a **Reference Importance Vector** derived from key metallurgical review papers (listed in Assumptions) using **Spearman rank correlation (ρ)**. Success is defined as **ρ ≥ 0.6** (See US-3).
- **SC-004**: The total compute time for the full pipeline (ingestion, training, evaluation) is measured against the 6-hour limit of the free-tier CI runner to ensure feasibility (See US-2).
- **SC-005**: The dataset coverage (number of valid alloy records) is measured against the total records in the source Zenodo datasets. Success is defined as **≥ 70% retention** of source records AND an absolute count of **≥ 200 valid records** to ensure statistical power (See US-1).
- **SC-006**: The model's generalization capability is measured by the macro-F1 score on the **Out-of-Distribution (OOD) test set** (held-out alloy classes). Success is defined as a macro-F1 score **≥ 0.5** on the OOD set (See US-3).

## Assumptions

- The public corrosion datasets available on Zenodo contain sufficient records of metallic alloys with both elemental composition and discrete degradation pathway labels to train a statistical model.
- The "standardized electrochemical conditions" mentioned in the research question are either implicit in the dataset metadata or sufficiently uniform that environmental noise does not completely obscure the compositional signal. *Note: If environmental variables are missing, FR-009 mandates a 20% confidence interval widening.*
- The Random Forest algorithm, running in default precision on a CPU, is sufficient to capture the non-linear relationships between elemental composition and degradation modes without requiring deep learning architectures.
- The dataset does not require GPU-accelerated libraries (e.g., PyTorch with CUDA, 8-bit quantization) to process the feature matrix, ensuring compatibility with the free-tier runner.
- Any missing environmental variables (e.g., specific pH or temperature) are treated as unobserved confounders, and the resulting analysis is strictly limited to reporting associations, not causal mechanisms.
- **Reference Importance Vector Sources**: The validation in SC-003 relies on a curated vector derived from the following review papers (or their most recent equivalents):
  1. [Specific Review Paper 1 on Corrosion Mechanisms]
  2. [Specific Review Paper 2 on Alloying Effects]
  3. [Specific Review Paper 3 on Pitting Resistance]
  4. [Specific Review Paper 4 on Stress Corrosion Cracking]
  5. [Specific Review Paper 5 on High-Entropy Alloy Corrosion]
  *(Note: The exact titles will be populated during the data ingestion phase based on the most cited literature for the specific dataset used.)*