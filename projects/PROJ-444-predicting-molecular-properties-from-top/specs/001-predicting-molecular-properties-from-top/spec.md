# Feature Specification: Predicting Molecular Properties from Topological Data Analysis

**Feature Branch**: `001-predict-molecular-properties-tda`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Properties from Topological Data Analysis of Molecular Structures"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute TDA Features for Molecular Dataset (Priority: P1)

As a researcher, I want to ingest a dataset of small organic molecules (SMILES) and compute their topological descriptors (persistence images/Betti curves) so that I can establish the baseline topological feature set for the study.

**Why this priority**: This is the foundational data engineering step. Without valid topological feature vectors, no modeling or comparison can occur. It validates the pipeline's ability to handle the specific dataset and graph construction logic.

**Independent Test**: Run the data processing script on a fixed subset of molecules.; verify that the output CSV contains a row for each molecule with a valid vector of topological features and no NaN values in the computed columns.

**Acceptance Scenarios**:

1. **Given** a CSV file containing 100 valid SMILES strings, **When** the TDA computation script is executed, **Then** a feature matrix is generated where every row corresponds to a molecule and contains non-null topological descriptors derived from persistent homology.
2. **Given** a SMILES string representing a disconnected molecular graph, **When** the graph construction and filtration steps are applied, **Then** the system correctly handles the disconnected components in the persistence diagram calculation without crashing.
3. **Given** a molecule with a complex ring system, **When** the shortest-path distance filtration is applied, **Then** the resulting Betti curves accurately reflect the birth and death of topological holes corresponding to the ring structures.

---

### User Story 2 - Train and Compare Predictive Models (Priority: P2)

As a researcher, I want to train regression models using (a) traditional descriptors, (b) topological features, and (c) a combination of both, so that I can quantify whether topology adds predictive signal beyond standard QSPR methods.

**Why this priority**: This directly addresses the core research question. It requires the successful integration of the feature sets from US-1 and the execution of the comparative modeling logic.

**Independent Test**: Execute the training pipeline on a split dataset; verify that three distinct models are trained and that the cross-validated R² and RMSE scores are reported for each model configuration.

**Acceptance Scenarios**:

1. **Given** the computed feature matrices (traditional and topological) and experimental property values, **When** the 5-fold cross-validation training loop runs, **Then** the system outputs performance metrics (R², RMSE) for the "Traditional Only," "Topological Only," and "Combined" models.
2. **Given** the performance metrics from the cross-validation, **When** the statistical comparison step runs, **Then** a paired t-test or Wilcoxon signed-rank test is performed, and a p-value indicating the significance of the difference between models is recorded.
3. **Given** a specific property (e.g., logP), **When** the combined model is trained, **Then** the system correctly identifies and reports the feature importance contributions from the topological features.

---

### User Story 3 - Validate Methodological Rigor and Sensitivity (Priority: P3)

As a reviewer, I want to verify that the study design includes sensitivity analyses for decision thresholds, accounts for multiple hypothesis testing, and quantifies feature redundancy, so that the findings are methodologically defensible.

**Why this priority**: This ensures the scientific validity of the results. It verifies that the implementation adheres to the methodological soundness constraints (multiplicity correction, threshold justification, redundancy analysis) before the project is considered complete.

**Independent Test**: Inspect the output logs or report artifacts to confirm that a sensitivity sweep was performed on the persistence diagram vectorization parameters, a multiple-comparison correction was applied to the statistical tests, and a mutual information analysis was conducted.

**Acceptance Scenarios**:

1. **Given** the persistence image generation parameters, **When** the sensitivity analysis script runs, **Then** the system re-runs the prediction with at least three different grid resolutions (e.g., 10x10, 20x20, 30x30) and reports the variance in R² scores across these configurations.
2. **Given** a set of N hypothesis tests (where N is the count of successfully modeled properties), **When** the final statistical reporting step executes, **Then** the p-values are adjusted using the Bonferroni method to control the family-wise error rate.
3. **Given** the correlation matrix of the input features, **When** the collinearity diagnostic runs, **Then** the system flags any pairs of predictors with a Variance Inflation Factor (VIF) > 5 and reports them in the final analysis summary.
4. **Given** the feature sets (traditional and topological), **When** the redundancy analysis runs, **Then** the system calculates and reports the mutual information between the two sets to quantify feature overlap.

---

### Edge Cases

- What happens when a SMILES string is invalid or cannot be converted to a valid graph by RDKit? (System must log the error and skip the molecule, continuing with the rest of the batch).
- How does the system handle molecules with extremely large molecular weights that might cause the shortest-path matrix to exceed RAM limits? (System must implement chunking or subsampling logic).
- What occurs if the persistent homology computation yields an empty diagram for a simple linear chain molecule? (System must handle empty diagrams gracefully, outputting a zero-vector or default baseline).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute persistent homology diagrams from molecular graphs using a shortest-path distance filtration, explicitly citing the topological features used. This filtration is selected as the standard baseline for graph connectivity analysis, acknowledging that while it may not capture 3D conformational volume, it is the canonical method for pure topological graph descriptors (See US-1).
- **FR-002**: System MUST convert persistence diagrams into vector representations (e.g., persistence images) with a grid resolution of exactly 10x10 for the primary experiment. This resolution is established as the baseline for comparison against sensitivity sweeps (See US-1).
- **FR-003**: System MUST train regression models on three feature sets: traditional descriptors only, topological features only, and combined features. The models must use fixed hyperparameters: Linear Regression with L2 regularization (alpha=1.0) and Random Forest with 100 trees and a maximum depth of 10 (See US-2).
- **FR-004**: System MUST perform 5-fold cross-validation using scaffold-based splits (Bemis-Murcko frameworks) to prevent data leakage from structural similarity. The split must use a fixed random seed of 42 to ensure reproducibility. The system must calculate R² and RMSE for each fold (See US-2).
- **FR-005**: System MUST apply the Bonferroni multiple-comparison correction to the p-values generated from comparing model performance across the N successfully modeled properties (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the vectorization grid resolution (e.g., {10, 20, 30}) and report the impact on prediction stability (See US-3).
- **FR-007**: System MUST detect and report multicollinearity among predictors using Variance Inflation Factor (VIF) diagnostics, flagging any VIF > 5 and including them in the final analysis summary (See US-3).
- **FR-008**: System MUST not require GPU acceleration or CUDA libraries; it must run entirely on CPU resources (See US-2).
- **FR-009**: System MUST calculate and report the mutual information between the traditional descriptor set and the topological feature set to quantify feature redundancy before claiming added signal (See US-3).

### Key Entities

- **Molecule**: Represents a chemical entity with attributes: SMILES string, molecular weight, and computed property values (solubility, logP, boiling point).
- **TopologicalDescriptor**: Represents the vectorized output of persistent homology, containing Betti curves or persistence image values derived from the molecular graph.
- **ModelPerformance**: Represents the aggregate metrics (R², RMSE, p-value) resulting from a specific training configuration and cross-validation fold.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive performance (R²) of the combined model is measured against the baseline traditional-only model to determine if topological features provide a statistically significant improvement, contingent upon the mutual information analysis (FR-009) confirming non-trivial redundancy (See US-2).
- **SC-002**: The stability of the model performance is measured across the sensitivity sweep of vectorization resolutions to ensure results are not artifacts of a single grid choice (See US-3).
- **SC-003**: The family-wise error rate is measured against the nominal alpha level (0.05) after applying the Bonferroni correction to ensure the validity of the N hypothesis tests, acknowledging the conservative nature of this method for correlated properties (See US-3).
- **SC-004**: The computational resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier limits. and must complete within 90% of these limits (< 6.3GB RAM, < 5.4 hours) to confirm feasibility with a safety margin (See US-2).
- **SC-005**: The collinearity diagnostics are measured against the VIF threshold of 5 to determine if any predictors need to be excluded or combined (See US-3).

## Assumptions

- The PubChem or ChEMBL dataset contains sufficient molecules with experimentally verified solubility, logP, and boiling point values to support a k-fold cross-validation split (minimum sufficient molecules per property).
- The RDKit and GUDHI/Dionysus libraries can be installed and run within the CPU-only environment of the GitHub Actions free tier without requiring proprietary licenses or GPU-specific builds.
- The "shortest-path distance" filtration on molecular graphs is sufficient to capture the relevant topological features for these physicochemical properties as a baseline graph descriptor; more complex filtrations (e.g., based on atomic charges) are out of scope for this initial study.
- The relationship between molecular topology and properties is associative; the study design does not claim causal inference from the observational data.
- The dataset provided does not require pre-filtering for stereochemistry or tautomers beyond standard canonicalization, as the topological features are intended to be robust to minor isomeric variations.
- While solubility, logP, and boiling point are highly correlated, the Bonferroni correction is applied to the N modeled properties to maintain a conservative Type I error rate, accepting the potential for increased Type II error in this exploratory context.