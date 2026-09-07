# Feature Specification: Predicting Material Properties from Compositional Data with Graph Neural Networks

**Feature Branch**: `001-predict-material-properties-compositional-gnn`
**Created**: 2026-06-28
**Status**: Draft
**Input**: User description: "Predicting Material Properties from Compositional Data with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Prediction Pipeline (Priority: P1)

The researcher needs to load a subset of the Materials Project Open Data, construct a composition-only graph representation for each material, train a lightweight GNN on CPU, and generate predictions for band gap and hardness to establish a baseline performance metric.

**Why this priority**: This is the foundational capability. Without the ability to ingest data, build the specific "composition-only" graph, train the model, and produce predictions, no comparison or information-loss analysis can occur. It delivers the primary research output for the composition-only hypothesis.

**Independent Test**: The pipeline can be fully tested by running the training script on a small, fixed subset of 500 materials and verifying that it outputs a JSON file containing R², MAE, and RMSE metrics for both target properties without requiring structural data or GPU resources.

**Acceptance Scenarios**:

1. **Given** the Materials Project data subset (≤10,000 records) is available locally, **When** the composition-only graph builder and GNN trainer are executed on a CPU-only environment, **Then** the system outputs a `results_composition_only.json` file containing R² > 0.0, MAE, and RMSE for band gap and hardness.
2. **Given** a new chemical formula not in the training set, **When** the trained model performs inference, **Then** it returns a predicted band gap and hardness value with a timestamp and confidence interval derived from the 5-fold cross-validation variance.
3. **Given** the training process exceeds 30 minutes per epoch or 6 hours total runtime, **When** the job is monitored, **Then** the system logs a timeout warning and halts execution to prevent CI resource exhaustion.

---

### User Story 2 - Structure-Aware Baseline Comparison (Priority: P2)

The researcher needs to construct a full crystal graph for a smaller, representative subset (≤2,000 materials), train a structure-aware GNN, and compute the performance gap (ΔR²) between the composition-only and structure-aware models to quantify information loss.

**Why this priority**: This story provides the critical comparative analysis required to answer the research question ("how much information is lost"). It is dependent on the P1 pipeline but adds the necessary structural context to validate the hypothesis about information loss.

**Independent Test**: The comparison can be tested by running the baseline training on the [deferred]-material subset, generating a `results_structure_aware.json` file, and verifying that the system correctly calculates and logs the ΔR² between the two model outputs.

**Acceptance Scenarios**:

1. **Given** the composition-only model results and the structure-aware model results, **When** the comparison utility is executed, **Then** it outputs a `comparison_summary.csv` containing the ΔR², ΔMAE, and ΔRMSE for both band gap and hardness.
2. **Given** a specific crystal system (e.g., monoclinic), **When** the error analysis is run, **Then** the system isolates the error metrics for that system and reports whether the ΔR² exceeds 0.15 for hardness.
3. **Given** the structural data files (CIFs) are missing for a material in the subset, **When** the graph builder processes the list, **Then** it skips that material, logs a warning, and continues processing the remaining valid entries without crashing.

---

### User Story 3 - Interpretability & Embedding Analysis (Priority: P3)

The researcher needs to extract the learned node embeddings from the composition-only GNN, perform PCA, and correlate the principal components with known periodic properties (electronegativity, atomic radius) to verify that the model learned chemically meaningful representations.

**Why this priority**: This story addresses the "why" behind the predictions, ensuring the model isn't just a black box. While not strictly necessary for the primary performance metrics (P1/P2), it validates the scientific soundness of the representation learning approach.

**Independent Test**: The analysis can be tested by running the embedding extraction script on the trained P1 model and verifying that the output includes a correlation matrix showing significant Pearson correlations (p < 0.05) between at least one principal component and a periodic property.

**Acceptance Scenarios**:

1. **Given** the trained GNN weights and the validation set, **When** the embedding extractor runs, **Then** it outputs a `node_embeddings.npy` file containing vectors for each element in the composition.
2. **Given** the embeddings and a lookup table of periodic properties, **When** the PCA and correlation analysis are performed, **Then** the system generates a `interpretability_report.md` listing principal components with |Pearson r| > 0.3 and p-value < 0.05.
3. **Given** the correlation analysis shows no significant relationship between embeddings and periodic properties, **When** the report is generated, **Then** it explicitly flags the result as "Low Interpretability" and suggests potential causes (e.g., overfitting, insufficient training).

---

### Edge Cases

- What happens when the input dataset contains a chemical formula with an element not present in the periodic table feature lookup (e.g., a typo or hypothetical element)?
- How does the system handle materials with zero band gap (metals) where the regression target is exactly 0, potentially skewing MAE/RMSE?
- How does the system handle the case where the composition-only and structure-aware models yield identical performance (ΔR² ≈ 0), contradicting the hypothesis?
- What happens if the chunked loading logic fails to deduplicate materials with the same formula but different crystal structures (polymorphs)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load Materials Project data in chunks to ensure peak RAM usage does not exceed 6 GB during the ingestion of ≤10,000 records (See US-1).
- **FR-002**: System MUST construct a composition-only graph where nodes represent unique elements with features [atomic number, electronegativity, valence electrons, atomic radius] and edges represent all pairwise connections weighted by periodic table distance (See US-1).
- **FR-003**: System MUST implement a lightweight GNN with ≤3 graph convolution layers, hidden dimension ≤128, and train exclusively on CPU using Adam optimizer (lr=1e-3) with early stopping patience=10 (See US-1).
- **FR-004**: System MUST perform a stratified 80/10/10 train/validation/test split by crystal system and ensure no material ID appears in both training and test sets (See US-1).
- **FR-005**: System MUST construct a structure-aware graph for a subset of ≤2,000 materials using atom positions and coordination information from CIF files for baseline comparison (See US-2).
- **FR-006**: System MUST calculate and output R², MAE, and RMSE for both band gap and hardness, and explicitly compute the performance gap (ΔR²) between composition-only and structure-aware models (See US-2).
- **FR-007**: System MUST perform 5-fold cross-validation to estimate variance and report the standard deviation of R² across folds (See US-1).
- **FR-008**: System MUST extract node embeddings and perform PCA, then calculate Pearson correlation coefficients between principal components and periodic properties with a significance threshold of p < 0.05 (See US-3).
- **FR-009**: System MUST enforce a hard runtime limit of 6 hours total for the entire pipeline and 30 minutes per epoch to ensure CI feasibility (See US-1).
- **FR-010**: System MUST handle missing structural data for specific materials by logging a warning and excluding them from the structure-aware analysis without terminating the job (See US-2).

### Key Entities

- **Material**: A crystalline compound identified by a unique ID, containing a chemical formula, crystal system, band gap (eV), hardness (GPa), and optional structural coordinates.
- **CompositionGraph**: A graph representation derived solely from the chemical formula, containing element nodes and periodic-distance edges.
- **StructureGraph**: A graph representation derived from the full crystal structure, containing atom nodes with 3D coordinates and coordination edges.
- **ModelMetrics**: A record containing R², MAE, RMSE, and fold-variance for a specific model (composition-only or structure-aware) and target property.
- **EmbeddingVector**: A numeric vector representing the learned latent representation of an element or material node.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The R² score of the composition-only model for band gap prediction is measured against the baseline Random Forest model trained on the same compositional features (See FR-006).
- **SC-002**: The performance gap (ΔR²) between the composition-only and structure-aware models is measured against the hypothesis threshold of 0.15 for hardness prediction (See FR-006).
- **SC-003**: The peak memory usage during data loading and training is measured against the 7 GB RAM limit of the CI runner environment (See FR-001).
- **SC-004**: The total execution time of the pipeline is measured against the 6-hour CI job limit (See FR-009).
- **SC-005**: The correlation coefficient between PCA components and periodic properties is measured against the statistical significance threshold of p < 0.05 (See FR-008).
- **SC-006**: The variance of R² across 5 cross-validation folds is measured to ensure the model is not overfitting to a specific data split (See FR-007).

## Assumptions

- The Materials Project Open Data () is accessible via the specified URL and contains valid, parseable CIF files for the structural subset.
- The dataset contains all necessary periodic table properties (electronegativity, valence electrons, atomic radius) for every element present in the [deferred] materials; if an element is missing, the pipeline will skip that material.
- The "hardness" values in the dataset are derived from DFT calculations or experimental data with sufficient consistency to serve as a regression target; no additional cleaning for outliers beyond standard IQR is assumed.
- The PyTorch Geometric library is available in the CI environment and supports CPU-only graph convolution operations without requiring CUDA.
- The "structure-aware" baseline comparison assumes that the subset of [deferred] materials is representative of the full dataset's distribution of crystal systems and properties.
- The inference task does not require real-time latency; batch processing of the test set is acceptable.
