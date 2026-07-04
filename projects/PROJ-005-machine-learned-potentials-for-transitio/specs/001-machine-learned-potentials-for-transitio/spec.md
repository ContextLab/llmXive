# Feature Specification: Machine-Learned Potentials for Transition-Metal Catalysis

**Feature Branch**: `001-machine-learned-potentials`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "How do graph‑neural‑network potentials generalize across ligand environments in Pd, Ni, and Cu catalytic cycles, and which structural features of the transition state dominate deviations from DFT reference values?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Graph Construction (Priority: P1)

As a computational chemist, I need to ingest literature DFT transition-state data for Pd, Ni, and Cu complexes and OC20 ground-state relaxation trajectories, converting them into graph representations with atomic features, so that I can prepare a valid input for the GNN model.

**Why this priority**: Without a correctly formatted and filtered dataset, no model training or analysis can occur. This is the foundational step.

**Independent Test**: Can be fully tested by running the data pipeline script on the provided dataset subset and verifying that the output graph files contain valid reaction geometries with correct atomic node features (atomic number, charge) and edge attributes (distance-based cutoff), and that the pipeline handles cases where the target count is not met by flagging the data scarcity.

**Acceptance Scenarios**:

1. **Given** the literature DFT transition-state data and OC20 ground-state relaxations, **When** the ingestion script filters for Pd, Ni, and Cu elementary steps, **Then** the output contains a target of a substantial number of reactions, or fewer if data is unavailable (flagged as data scarcity).
2. **Given** a filtered set of transition states, **When** the graph conversion process runs, **Then** each node is annotated with atomic number, formal charge, and local coordination environment, and edges are defined by a distance-based cutoff.

---

### User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

As a researcher, I need to train an ensemble of SchNet-style GNNs on the prepared dataset to predict energies and forces, and subsequently generate barrier height predictions for a held-out test set, so that I can evaluate the model's accuracy against DFT references and estimate uncertainty.

**Why this priority**: This delivers the core predictive capability and the necessary ensemble structure for uncertainty quantification. The model must be trained and capable of inference to assess generalization.

**Independent Test**: Can be fully tested by training the ensemble of 5 models for ≤ 30 epochs (base training) on the [deferred] training split and generating predictions for the [deferred] held-out test set, verifying that the model outputs scalar energy values with finite variance and no NaN/Inf values, and that the ensemble variance is calculable.

**Acceptance Scenarios**:

1. **Given** the training split ([deferred] of data), **When** the GNN ensemble (5 seeds) is trained with Adam optimization (learning rate 1e-4) for ≤ 30 epochs on a CPU-only environment, **Then** the training completes successfully within the specified time limit, the models converge to finite losses, and the ensemble variance is non-zero.
2. **Given** the trained ensemble and the held-out test set, **When** the model predicts barrier heights, **Then** the output is a set of scalar energy values corresponding to the transition states, the Mean Absolute Error (MAE) against DFT references is calculable, and the prediction variance is recorded.

---

### User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

As a domain expert, I need to perform feature-importance analysis (SHAP/Integrated Gradients) and statistical testing on the prediction errors across different ligand families (Group 13 vs. conventional), so that I can identify the structural determinants of model deviation and quantify error distribution differences.

**Why this priority**: This addresses the specific research question regarding *why* the model fails or succeeds, providing the scientific insight sought by the project.

**Independent Test**: Can be fully tested by running the analysis scripts on the prediction results to generate feature importance scores, statistical test p-values, and uncertainty correlation metrics, verifying that the output includes a ranked list of descriptors, a comparison of error distributions, and a recorded uncertainty correlation.

**Acceptance Scenarios**:

1. **Given** the model predictions and the DFT reference values, **When** the feature-importance analysis runs, **Then** the system identifies a subset of geometric/electronic descriptors and records the percentage of variance explained by each.
2. **Given** the error distributions for Group 13 ligands and conventional ligands, **When** a paired statistical test (t-test or Wilcoxon) is performed, **Then** the output includes a p-value indicating the statistical significance of the difference in error distributions (p < 0.05) and records the result.

---

### Edge Cases

- **What happens when** the dataset contains transition states with unusual coordination numbers (e.g., > 6) not seen in training?
  - **System handles** this by flagging the sample as an outlier during the preprocessing stage and excluding it from the training set but including it in the test set to evaluate generalization limits.
- **How does system handle** cases where the DFT reference energy is missing for a specific ligand in the literature data?
  - **System handles** this by logging a warning and skipping the specific data point, ensuring the remaining dataset integrity is maintained without crashing the pipeline.
- **What happens when** the GNN training loss fails to decrease after 10 epochs?
  - **System handles** this by implementing an early stopping mechanism with a patience of 5 epochs to prevent wasted compute time and potential overfitting.

## Requirements

### Functional Requirements

- **FR-001**: System MUST target a minimum of 120 valid reactions involving Pd, Ni, and Cu transition metals from literature DFT data and OC20 relaxations. (See US-1)
- **FR-001b**: If fewer than 120 valid reactions are available, the system MUST proceed with the available data, flagging the data scarcity in the output logs, and proceed with training. (See US-1)
- **FR-002**: System MUST convert DFT geometries into graph representations where nodes include atomic number, formal charge, and coordination number, and edges are defined by a distance-based cutoff. (See US-1)
- **FR-003**: System MUST train a SchNet-style GNN using PyTorch Geometric on CPU-only hardware, optimizing with Adam (learning rate 1e-4) for a maximum of 30 epochs (base training). (See US-2)
- **FR-004**: System MUST predict barrier heights for the held-out test set and compute the Mean Absolute Error (MAE), Root Mean Square Error (RMSE), and Pearson correlation coefficient against DFT references. (See US-2)
- **FR-005**: System MUST perform feature-importance analysis using Integrated Gradients and SHAP values to quantify the contribution of structural descriptors to prediction errors and record the variance explained. (See US-3)
- **FR-006**: System MUST execute a paired statistical test (t-test or Wilcoxon signed-rank) to compare error distributions between reactions containing Group 13 ligands and those with conventional ligands, recording the p-value. (See US-3)
- **FR-007**: System MUST train an ensemble of 5 GNNs with different random seeds to enable calculation of prediction variance via prediction variance. (See US-3)
- **FR-008**: System MUST perform leave-one-out cross-validation (LOOCV) or bootstrapping to validate generalization performance on the small dataset, recording the cross-validated error metrics. (See US-2)

### Key Entities

- **TransitionStateGraph**: Represents a chemical reaction transition state as a graph. Attributes: `nodes` (atomic features), `edges` (distance-based connectivity), `energy_dft` (reference value), `barrier_height`.
- **PredictionResult**: Stores the output of the GNN inference. Attributes: `energy_ml` (predicted value), `error` (difference from DFT), `ligand_class` (Group 13 or Conventional).
- **EnsemblePredictionResult**: Stores the output of the GNN ensemble inference. Attributes: `mean_energy` (average prediction), `variance` (prediction uncertainty), `individual_predictions` (list of 5 model outputs).
- **FeatureImportance**: Maps structural descriptors to their contribution to error. Attributes: `descriptor_name`, `importance_score`, `variance_explained`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the GNN predictions for barrier heights is measured against the DFT reference values for the held-out test set and recorded. (See FR-004)
- **SC-001b**: The MAE value is recorded in the results table for comparison against community standards (e.g., 2 kcal mol⁻¹). (See FR-004)
- **SC-002**: The percentage of variance in prediction deviations explained by the top structural descriptors is measured against the total variance of the error distribution and recorded. (See FR-005)
- **SC-003**: The statistical significance of the difference in error distributions between Group 13 and conventional ligands is measured via the p-value from a paired t-test or Wilcoxon signed-rank test and recorded. (See FR-006)
- **SC-004**: The computational speed-up factor of the GNN prediction versus a single-point DFT calculation is measured by comparing wall-clock times on the same CPU hardware and recorded. (See FR-004)
- **SC-005**: The correlation between prediction uncertainty (ensemble variance) and observed error magnitude is measured via Pearson correlation coefficient and recorded. (See FR-007)

## Assumptions

- **Assumption about data**: The literature DFT datasets and OC20 ground-state relaxations contain sufficient samples of Pd, Ni, and Cu elementary steps to support the training of a GNN, with a target of 120 reactions after filtering.
- **Assumption about method**: The SchNet architecture is capable of running within the available RAM and time limits. of the GitHub Actions free-tier runner for the *base* training (≤ 30 epochs) on a subset of reactions. Leave-one-out cross-validation is performed as a separate analysis step.
- **Assumption about variables**: The literature DFT data and OC20 data contain all necessary geometric and electronic variables (atomic positions, charges, coordination numbers) required to construct the graph representations and calculate barrier heights.
- **Assumption about inference**: The GNN predictions are purely associational; no causal claims are made about the effect of ligands on barrier heights, only the model's ability to predict DFT values based on structural features.
- **Assumption about sensitivity**: The sensitivity analysis for any decision cutoffs (e.g., distance-based edge cutoff) will be performed by sweeping the cutoff value over a range of near-neighbor distances to ensure robustness of the graph construction.