# Feature Specification: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

**Feature Branch**: `001-molecular-topology-selectivity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Molecular Topology and Reaction Selectivity"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Reaction Filtering (Priority: P1)

The system MUST successfully download the USPTO-50k dataset, parse the SMILES strings, and filter the dataset to retain only electrophilic aromatic substitution (EAS) reactions with identifiable aromatic rings.

**Why this priority**: Without a clean, relevant dataset, no statistical analysis can be performed. This is the foundational step that enables all subsequent modeling and validation.

**Independent Test**: The system can be tested by running the ingestion pipeline on a small subset of the data and verifying that the output CSV contains only reactions matching the EAS pattern and that the row count matches the expected subset size.

**Acceptance Scenarios**:

1. **Given** the USPTO-50k dataset file is accessible at the specified URL, **When** the ingestion script executes, **Then** the system downloads the file and parses all SMILES strings without crashing.
2. **Given** a parsed list of reactions, **When** the EAS pattern matcher runs, **Then** the system outputs a filtered dataset containing exclusively EAS reactions. **If** the number of retained reactions is ≥ 100, the pipeline proceeds; **Else**, the system MUST log a critical error and halt with the status "Insufficient Data" to prevent downstream modeling on empty sets.
3. **Given** a reaction with missing or malformed SMILES data, **When** the parser processes it, **Then** the system logs the error and excludes the row from the final dataset without terminating the job.

---

### User Story 2 - Topological Descriptor Calculation (Priority: P2)

The system MUST compute Wiener, Balaban, and Zagreb indices for the reactant molecules in the filtered dataset using the `rdkit` library, ensuring all calculations complete within the CPU-only resource constraints.

**Why this priority**: These indices are the primary predictors for the research question. Their accurate and efficient computation is necessary to test the hypothesis that topology predicts selectivity.

**Independent Test**: The system can be tested by running the descriptor calculation on a known set of 10 molecules with pre-calculated values. Specifically, the system must calculate the Wiener index for **benzene** (expected: 5), **toluene** (expected: 9), and **nitrobenzene** (expected: 13). The calculated values must match these reference values within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** a valid reactant SMILES string, **When** the descriptor calculator runs, **Then** it outputs the Wiener, Balaban, and Zagreb indices as floating-point numbers.
2. **Given** a molecule with a disconnected graph or invalid valence, **When** the calculator processes it, **Then** the system flags the record as "invalid topology" and excludes it from the regression analysis without halting execution.
3. **Given** the full filtered dataset, **When** the calculation runs on a standard CI runner, **Then** the total computation time for descriptor generation is ≤ 15 minutes. This 15-minute limit is a strict sub-budget for descriptors only, ensuring sufficient time remains for the modeling phase within the total 6-hour pipeline limit.

---

### User Story 3 - Statistical Modeling and Validation (Priority: P3)

The system MUST perform Poisson Regression and Random Forest regression to correlate topological indices with the **selectivity target** (Regioisomer Diversity Count), applying 5-fold cross-validation and reporting R² (pseudo-R² for Poisson) and RMSE metrics.

**Why this priority**: This is the core analytical step that answers the research question. It validates whether the topological features have predictive power for regioisomer diversity.

**Independent Test**: The system can be tested by running the modeling pipeline on a synthetic dataset with a known linear relationship between input and output. The synthetic data is generated with seed=42, noise=0.1, and known coefficients β=[1.0, -0.5, 0.2]. The system must recover these known coefficients within a tolerance of ±0.1 for at least two of the three coefficients.

**Acceptance Scenarios**:

1. **Given** the dataset with computed descriptors and **selectivity target** values, **When** the regression models are trained, **Then** the system outputs R² and RMSE values for both Poisson Regression and Random Forest.
2. **Given** the 5-fold cross-validation setup, **When** the validation completes, **Then** the system reports the mean and standard deviation of the performance metrics across the folds.
3. **Given** the model results, **When** the analysis completes, **Then** the system generates a summary report indicating whether any topological index shows a statistically significant correlation (p < 0.05) with the **selectivity target**.

### Edge Cases

- **What happens when** the USPTO-50k dataset contains no EAS reactions? The system MUST log a critical error, set the output dataset to zero rows, and exit gracefully, preventing downstream modeling failures.
- **How does the system handle** molecules where the Balaban index calculation fails due to graph connectivity issues? The system MUST skip the specific index for that molecule, log the warning, and proceed with the other indices to maximize data retention.
- **What happens when** the dataset is too small to perform 5-fold cross-validation (e.g., < 20 samples)? The system MUST automatically switch to a leave-one-out (LOO) cross-validation strategy to ensure validation is always performed, as mandated by FR-005.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the USPTO-50k dataset from the specified URL and parse the SMILES strings to identify electrophilic aromatic substitution reactions (See US-1).
- **FR-002**: System MUST compute the Wiener index, Balaban index, and Zagreb indices for all valid reactant molecules using CPU-efficient graph algorithms (See US-2).
- **FR-003**: System MUST extract the **selectivity target** defined as the "Regioisomer Diversity Count" (integer: number of distinct regioisomeric products formed) from the product SMILES metadata to serve as the dependent variable (See US-1).
- **FR-004**: System MUST perform Poisson Regression and Random Forest regression to model the relationship between topological indices and the **selectivity target** (See US-3).
- **FR-005**: System MUST apply 5-fold cross-validation to the trained models; if the sample size N < 20, the system MUST automatically switch to leave-one-out (LOO) cross-validation and calculate R² (pseudo-R²) and RMSE metrics (See US-3).
- **FR-006**: System MUST handle missing or malformed SMILES data by logging errors and excluding affected records without terminating the pipeline (See US-1).

### Key Entities

- **ReactionRecord**: Represents a single chemical reaction from the USPTO-50k dataset, containing fields for reactant SMILES, product SMILES, and the derived **selectivity target** (Regioisomer Diversity Count).
- **TopologicalDescriptor**: Represents the computed values (Wiener, Balaban, Zagreb) for a specific reactant molecule.
- **ModelResult**: Represents the output of the statistical analysis, including regression coefficients, R² (pseudo-R²), RMSE, and p-values for the **selectivity target**.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of successfully parsed EAS reactions is measured against the total number of reactions in the downloaded USPTO-50k dataset. **Pass condition**: The proportion must be ≥ 90% (See US-1).
- **SC-002**: The predictive performance (R²) of the topological models is measured against a baseline null model (intercept-only) to determine if topology adds value. **Pass condition**: The model's R² must be > 0.05 (See US-3).
- **SC-003**: The computational efficiency of descriptor calculation is measured against the 15-minute threshold on a **GitHub Actions free-tier runner (2-core, 7GB RAM)** to ensure the analysis fits within the CI time budget (See US-2).
- **SC-004**: The statistical significance of the correlation between topological indices and the **selectivity target** is measured against the p < 0.05 threshold defined in the research hypothesis (See US-3).

## Assumptions

- **Dataset Variable Fit**: It is assumed that the USPTO-50k dataset contains sufficient metadata to distinguish regioisomers in the product SMILES. The **selectivity target** is defined as the count of distinct regioisomers formed. If the metadata is insufficient to distinguish regioisomers for a specific reaction, the count defaults to 0 (no diversity), ensuring the target variable retains variance across the dataset.
- **Inference Framing**: Since the USPTO-50k dataset is observational and lacks random assignment, all findings regarding the relationship between topology and selectivity will be framed as **associational** rather than causal.
- **Multiplicity & Power**: The analysis will test three primary topological indices. To control for family-wise error, a Bonferroni correction (adjusted alpha = 0.05/3 ≈ 0.0167) will be applied when assessing statistical significance. The sample size is assumed to be sufficient for regression analysis given the dataset size (N > 1000 expected), but power limitations will be acknowledged if the filtered EAS subset is small.
- **Threshold Justification & Sensitivity**: The p < 0.05 threshold is standard in chemical literature. A sensitivity analysis will be performed by sweeping the significance threshold across {0.01, 0.05, 0.10} to verify that the headline findings (which indices are significant) remain robust.
- **Measurement Validity**: The topological indices (Wiener, Balaban, Zagreb) are well-established, validated graph-theoretic descriptors with citable validation in the literature (e.g., Balaban, [year]; Wiener, 1947).
- **Predictor Collinearity**: The Wiener, Balaban, and Zagreb indices are definitionally related as they all derive from the molecular graph structure. The analysis will include a collinearity diagnostic (Variance Inflation Factor, VIF) to ensure that regression coefficients are not inflated by multicollinearity; if VIF > 5, the indices will be analyzed jointly or sequentially rather than in a single multivariate model.
- **Compute Feasibility**: The entire pipeline (download, parsing, descriptor calculation, modeling) is assumed to run within the available RAM and time limit of a GitHub Actions free-tier runner. using `rdkit` and `scikit-learn` on CPU. No GPU acceleration or large language models are required.
- **Data Availability**: The USPTO-50k dataset is assumed to be accessible via the provided Figshare URL without authentication barriers.
- **Target Independence**: The **selectivity target** (Regioisomer Diversity Count) is derived from the *product* graph topology, while predictors are derived from the *reactant* graph topology. This ensures the target is not trivially determined by the reactant's indices, avoiding circular validation.