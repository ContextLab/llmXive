# Feature Specification: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Feature Branch**: `001-molecular-permeability-gnn`  
**Created**: 2026-07-28  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets"

## User Scenarios & Testing

### User Story US-1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest public permeability datasets (SMILES strings and experimental coefficients), parse them into molecular graphs using RDKit, and compute standard molecular descriptors to create a unified, stratified training/test split.

**Why this priority**: Without a clean, reproducible dataset split and feature extraction pipeline, no model training or comparison is possible. This is the foundational block for all subsequent analysis.

**Independent Test**: The pipeline can be run end-to‑end on a sample subset of the data, producing a CSV of processed features and a separate test set CSV, with a logged report confirming the stratification by polymer type.

**Acceptance Scenarios**:

1. **Given** a public dataset file containing SMILES and permeability coefficients, **When** the ingestion script runs, **Then** the system outputs a processed dataset where every molecule has both a graph representation and a vector of standard descriptors (MW, logP, TPSA, etc.).
2. **Given** the processed dataset, **When** the split operation executes, **Then** the data is divided into training and testing sets using a standard split ratio, with stratification ensuring that the distribution of polymer types is preserved in both sets (absolute percentage point difference < 5%).
3. **Given** a dataset with missing values, **When** the pipeline processes it, **Then** the system either imputes missing descriptor values using a defined method (e.g., median) or excludes the row with a logged warning, ensuring no NaN values remain in the final input matrices.

---

### User Story US-2 - Comparative Model Training and Evaluation (Priority: P2)

The system must train a CPU‑optimized Graph Neural Network (MPNN) and a Random Forest baseline on the prepared data, then evaluate both models using RMSE, MAE, and R² metrics to determine if the GNN provides a statistically significant improvement over a strictly non‑topological baseline.

**Why this priority**: This addresses the core research question: whether graph‑based representations capture non‑linear nuances missed by standard descriptors. It delivers the primary quantitative result.

**Independent Test**: The training script runs to completion, outputs performance metrics for both models, and performs a paired t‑test on prediction errors, returning a p‑value indicating statistical significance.

**Acceptance Scenarios**:

1. **Given** the stratified training set, **When** the GNN model trains for up to 50 epochs with early stopping, **Then** the model converges to a validation loss minimum without exceeding a reasonable CPU time budget or memory footprint.
2. **Given** the trained models and the held‑out test set, **When** predictions are generated, **Then** the system calculates RMSE, MAE, and R² for both the GNN and Random Forest, and stores these metrics in a results log.
3. **Given** the prediction errors from both models, **When** the statistical analysis runs, **Then** a paired t‑test is performed if residuals pass a Shapiro‑Wilk normality test (α=0.05); otherwise a Wilcoxon signed‑rank test is used, and the system reports whether the GNN's reduction in error is statistically significant (p < 0.05) compared to the Random Forest baseline trained on standard descriptors only.

---

### User Story US-3 - Feature Attribution and Interpretability Analysis (Priority: P3)

The system must apply GNNExplainer to the GNN and SHAP analysis to the Random Forest to identify and rank the specific topological features or substructures that drive permeability predictions.

**Why this priority**: This fulfills the "mechanistic" aspect of the research question, moving beyond "black box" predictions to identify *which* substructures account for the performance gap.

**Acceptance Test**: The analysis generates a ranked list of top features/substructures and a visualization (e.g., heatmap or bar chart) showing their contribution to the prediction variance.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** SHAP analysis is executed, **Then** the system outputs a ranked list of standard molecular descriptors by their absolute mean SHAP value.
2. **Given** the trained GNN model, **When** GNNExplainer is executed, **Then** the system identifies and reports the top most influential node‑level substructures (e.g., specific aromatic rings or functional groups) across the test set.
3. **Given** the results from both models, **When** the comparison report is generated, **Then** the system highlights any specific substructures that the GNN identifies as critical but are absent or low‑ranked in the descriptor‑based model.

### Edge Cases

- **What happens when** the public dataset contains SMILES strings that RDKit cannot parse (invalid chemistry)?
  - **System handles**: The pipeline logs the invalid SMILES, excludes them from the dataset with a count, and proceeds with the valid subset.
- **How does system handle** a scenario where the GNN fails to converge or overfits significantly on the small dataset?
  - **System handles**: Early stopping triggers, and the model reverts to the epoch with the lowest validation loss; if performance is worse than the baseline, the result is flagged as "No significant improvement" rather than forcing a false positive.
- **What happens when** the dataset size is too small to support a meaningful stratified split (e.g., < 50 samples)?
  - **System handles**: The system falls back to a simple random split but logs a warning about potential data leakage and reduced statistical power, requiring manual review of the results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST acquire at least one public dataset containing experimental permeability coefficients for polymeric membranes **or** a high‑quality surrogate permeability dataset (e.g., from validated molecular‑simulation studies) **with a column named `permeability` or an approved surrogate column (`permeability_estimate`, `log_permeability`)** to serve as the target variable (See US-1).
- **FR-002**: System MUST ingest public permeability datasets (SMILES + coefficients) and parse them into molecular graphs using RDKit to support feature extraction (See US-1).
- **FR-003**: System MUST compute a standard set of molecular descriptors (MW, logP, TPSA, etc.) for every molecule to serve as the baseline input (See US-1).
- **FR-004**: System MUST split the dataset into training and testing sets with stratification by polymer type; the split ratios are implementation‑defined but must preserve class distributions within an absolute ≤ 5 percentage‑point difference. **If the dataset contains fewer than 50 samples, a random (non‑stratified) split is permitted with a logged warning** (See US-1).
- **FR-005**: System MUST train a Random Forest regressor using the computed standard descriptors as the baseline for comparison (See US-2).
- **FR-006**: System MUST train a Message Passing Neural Network (MPNN) using PyTorch Geometric on CPU‑only hardware with early stopping based on validation loss (See US-2).
- **FR-007**: System MUST evaluate both models using RMSE, MAE, and R² metrics on the held‑out test set (See US-2).
- **FR-008**: System MUST perform a statistical significance analysis on prediction errors between the GNN and the Random Forest baseline: first conduct a Shapiro‑Wilk normality test (α=0.05); if residuals are normal, perform a paired t‑test, otherwise perform a Wilcoxon signed‑rank test. Significance is declared at p < 0.05 (See US-2).
- **FR-009**: System MUST apply GNNExplainer to the GNN and SHAP analysis to the Random Forest to identify predictive features (See US-3). Mapping between GNN substructures and standard descriptors is performed by counting substructure occurrences per molecule and computing Pearson correlation (r ≥ 0.6) with descriptor values.
- **FR-010**: System MUST generate a comparative report highlighting specific topological features identified by the GNN but missed by the descriptor baseline (See US-3).
- **FR-011**: System MUST handle invalid SMILES strings by logging and excluding them without crashing the pipeline (See US-1). *(See US-1)*
- **FR-012**: System MUST ensure that at least 95 % of valid molecules are retained after preprocessing; if retention falls below this threshold, the pipeline must halt and report the cause (See US-1).
- **FR-013**: Input datasets MUST contain a column named **polymer_type** (categorical) to enable stratified splitting (See US-1).
- **FR-014**: Input datasets MUST contain a numeric column named **permeability** (or an approved surrogate as defined in FR-001) representing the target variable (See US-1).
- **FR-015**: System MUST perform an a priori power analysis using a target effect size of Cohen’s d = 0.3 and require statistical power ≥ 0.8; if the calculated power is < 0.8 the pipeline aborts and reports the deficiency (See US-2).
- **FR-016**: All external data sources used must be listed in the **Verified Datasets** block; the system MUST not fetch URLs outside this list (See US-1).

### Key Entities

- **Molecule**: A chemical entity defined by its SMILES string, containing attributes for graph representation, standard descriptors, and the target permeability coefficient.
- **Dataset**: A collection of molecules partitioned into training and testing sets, stratified by polymer type.
- **Model**: An instance of a machine learning algorithm (GNN or Random Forest) trained on the dataset to predict permeability.
- **Feature**: A specific molecular descriptor or topological substructure used as an input variable for the models.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reduction in RMSE of the GNN model compared to the Random Forest baseline (trained on standard descriptors only) is measured against the null hypothesis of no difference (paired t‑test or Wilcoxon signed‑rank test as dictated by FR-008, p < 0.05) (See FR-008) (See US-2).
- **SC-003**: At least **2** of the top‑5 substructures identified by GNNExplainer must be mappable to standard molecular descriptors that also appear in the top‑5 SHAP‑ranked descriptors (e.g., aromatic ring count ↔ aromatic substructure, H‑bond donor count ↔ –NH groups). Mapping is performed by counting substructure occurrences per molecule and requiring a Pearson correlation **r ≥ 0.6** with the corresponding descriptor (See FR-009) (See US-3).
- **SC-004**: Computational feasibility is measured by the total training time (must be ≤ 6 hours) and peak memory usage (must be ≤ 7 GB) on a CPU‑only runner (See FR-006) (See US-2).
- **SC-005**: Data integrity is measured by the percentage of valid molecules retained after preprocessing (must be ≥ 95 %) (See FR-012) (See US-1).
- **SC-006**: Power analysis must report a calculated statistical power ≥ 0.8; if below, the pipeline aborts (See FR-015) (See US-2).
- **SC-007**: All external data sources used must be drawn exclusively from the URLs listed in the Verified Datasets block; any attempt to fetch data from unlisted URLs causes the pipeline to abort (See FR-016).

## Assumptions

- Publicly available datasets (e.g., from NIST, PolyInfo, curated literature, or high‑fidelity computational simulations) contain at least 200 molecules with valid SMILES strings, a **polymer_type** column, and a numeric target column (`permeability` or an approved surrogate) enabling a stratified train‑test split.
- For datasets with 50 ≤ N < 200 samples, the system will attempt stratified splitting; if class imbalance prevents successful stratification, it will fall back to a random split with a logged warning.
- The PyTorch Geometric library and RDKit can be installed and run within the free‑tier GitHub Actions environment (CPU cores, limited RAM) without requiring GPU acceleration or CUDA.
- The set of “standard molecular descriptors” computed by RDKit (MW, logP, TPSA, etc.) is sufficient to represent the baseline model’s capability for comparison.
- Missing descriptor values are rare; any missing data can be handled by median imputation or row exclusion without introducing significant bias.
- The GNN architecture is sufficiently simple to avoid over‑fitting on the available dataset size, provided early stopping is used.
- GNNExplainer provides a scientifically valid approximation of feature importance for the specific MPNN architecture used.

### Verified Datasets

- *(publicly curated, includes `polymer_type` and `permeability` columns)*
- *(supplementary simulated dataset, includes `polymer_type` and `permeability_estimate` columns)*

Only the URLs listed above may be accessed by the pipeline. Any attempt to retrieve data from other sources will cause an abort as mandated by SC‑007. 