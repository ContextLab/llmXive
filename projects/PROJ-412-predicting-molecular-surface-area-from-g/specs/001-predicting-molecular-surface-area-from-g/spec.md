# Feature Specification: Predicting Molecular Surface Area from Graph Convolutional Networks

**Feature Branch**: `001-predict-molecular-surface-area`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Surface Area from Graph Convolutional Networks"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system must ingest a dataset of molecular data (SMILES strings) from a public repository (e.g., ZINC15 or OpenDataPubChem), convert these into 2D molecular graph representations using RDKit, and generate ground-truth 3D surface area labels for a training set. This forms the foundational dataset required for any model training.

**Why this priority**: Without a validated, paired dataset of 2D graphs and 3D surface areas, no prediction model can be trained or evaluated. This is the prerequisite for all downstream analysis.

**Independent Test**: A researcher can run the data pipeline script and verify that a CSV/Parquet file is produced containing SMILES, node/edge feature matrices, and a numeric surface area column, with no missing values in the target column for the training set.

**Acceptance Scenarios**:

1. **Given** a list of SMILES strings from the ZINC15 subset, **When** the ingestion script is executed, **Then** the system outputs a processed dataset file containing 2D graph features and 3D surface area labels for a sufficient number of molecules to train a GCN model, with no NaN values in the target column for the training set.
2. **Given** a molecule with invalid SMILES syntax, **When** the ingestion script processes the list, **Then** the molecule is excluded from the training set, and a warning log entry is generated with the specific SMILES string.
3. **Given** the processed dataset, **When** the system splits the data into training and testing sets, **Then** the split is performed by randomly partitioning the data and iterating until the Kolmogorov-Smirnov (KS) test p-value comparing the molecular weight distributions of the training and testing sets is ≥ 0.05.

---

### User Story 2 - GCN Model Training and Baseline Comparison (Priority: P2)

The system must train a lightweight Graph Convolutional Network (GCN) on the 2D graph features to predict surface area, while simultaneously training a **Descriptor-Based Baseline** defined as a **linear regression model on 2D molecular descriptors (molecular weight, atom counts)**. The system must compare the Mean Absolute Error (MAE) of both models on the held-out test set.

**Why this priority**: This user story directly addresses the research question by quantifying the predictive power of 2D topology against a baseline that uses only 2D-derived descriptors. This isolates the value of the GCN's graph structure learning against a simple linear model, avoiding the circularity of using 3D geometry for both ground truth and baseline features.

**Independent Test**: The training script runs to completion within the ≤ 60 minutes CI limit, producing two model artifacts (GCN and Descriptor-Based Baseline) and a results report showing MAE, RMSE, and R² for both, along with a statistical significance test (paired t-test or Wilcoxon signed-rank test).

**Acceptance Scenarios**:

1. **Given** the preprocessed training dataset, **When** the GCN training job starts, **Then** the model trains for ≤50 epochs with early stopping (patience=5) and completes within ≤ 60 minutes on a CPU-only runner.
2. **Given** the trained GCN and **Descriptor-Based Baseline** models, **When** evaluated on the test set, **Then** the system outputs a comparison table showing MAE, RMSE, and R² for both models.
3. **Given** the prediction errors from both models, **When** a statistical test is performed, **Then** the system first runs a Shapiro-Wilk test on the error differences; if p > 0.05, it reports a paired t-test p-value and effect size (Cohen's d), otherwise it reports a Wilcoxon signed-rank test p-value.

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

The system must perform a sensitivity analysis on the model's performance metrics by varying the decision threshold (MAE cutoff) to ensure results are robust. Additionally, it must justify any thresholds used based on community standards or the magnitude of the target variable.

**Why this priority**: To satisfy methodological soundness, the spec requires that any cutoff or decision boundary be justified and tested for sensitivity. This prevents "cherry-picking" results and ensures the findings are reproducible.

**Independent Test**: The analysis script re-runs the evaluation with modified thresholds (e.g., varying the MAE cutoff for "success" by a percentage of the mean surface area) and generates a report showing how the false-positive/negative rates or success rates change.

**Acceptance Scenarios**:

1. **Given** the trained GCN model, **When** the sensitivity analysis script runs, **Then** it evaluates performance across a fixed set of absolute error thresholds: {0.01, 0.05, 0.1} Å², and reports the variation in the percentage of molecules predicted within the threshold.
2. **Given** the threshold sweep results, **When** the final report is generated, **Then** it explicitly states the justification for the chosen thresholds by citing a specific source (DOI, URL, or standard document) supporting the values, or explicitly stating that the thresholds are arbitrary and selected for sensitivity analysis purposes.
3. **Given** the analysis results, **When** the system checks for multiplicity, **Then** it applies a Bonferroni or False Discovery Rate correction if multiple hypothesis tests were run (e.g., testing multiple thresholds), reporting the adjusted p-values.

---

### Edge Cases

- **What happens when** a molecule in the dataset has no valid 3D conformation generated by RDKit?
  - **System handles**: The molecule is excluded from the training set, and the count of excluded molecules is logged. The dataset size is reduced, but the pipeline continues.
- **How does system handle** a memory overflow during graph feature extraction for very large molecules?
  - **System handles**: The system implements a chunked processing strategy or a maximum atom count filter (e.g., exclude molecules > 100 atoms) to stay within the 7 GB RAM constraint, logging the excluded count.
- **What happens when** the 3D conformation generation fails for a significant portion (>10%) of the dataset?
  - **System handles**: The pipeline halts with a critical error, prompting a review of the input data quality or the conformation generation parameters.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest SMILES strings from a public repository and convert them to 2D graph features (atom type, hybridization, charge) using RDKit. (See US-1)
- **FR-002**: System MUST generate 3D surface area labels for a subset of molecules using RDKit's 3D geometry functions. (See US-1)
- **FR-003**: System MUST train a lightweight GCN model on CPU-only hardware with a maximum of 50 epochs and early stopping (patience=5). (See US-2)
- **FR-004**: System MUST train a **Descriptor-Based Baseline** using linear regression on 2D molecular descriptors (molecular weight, atom counts) for comparison. (See US-2)
- **FR-005**: System MUST perform a statistical comparison (paired t-test or Wilcoxon signed-rank test) to compare the MAE of the GCN and baseline models, reporting p-value and effect size. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis by sweeping a decision threshold (MAE cutoff) over the specific absolute values {0.01, 0.05, 0.1} Å² and report the variation in success rates. (See US-3)
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) when multiple hypothesis tests are performed during the sensitivity analysis. (See US-3)

### Key Entities

- **Molecule**: Represents a chemical compound with a unique SMILES string, 2D graph features, 3D surface area value, and **molecular_weight (computed)**.
- **Graph**: Represents the 2D molecular topology with nodes (atoms) and edges (bonds) containing feature vectors.
- **Model**: Represents the trained GCN or Descriptor-Based Baseline model, including weights and hyperparameters.
- **EvaluationResult**: Represents the outcome of model evaluation, containing MAE, RMSE, R², and statistical test results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation (R²) between GCN predictions and computed surface area is measured against the baseline Descriptor-Based R². (See US-2)
- **SC-002**: The Mean Absolute Error (MAE) of the GCN model is measured against the MAE of the Descriptor-Based Baseline. (See US-2)
- **SC-003**: The statistical significance of the performance difference is measured via a paired t-test or Wilcoxon signed-rank test p-value and effect size. (See US-2)
- **SC-004**: The robustness of the results is measured by the variation in success rates across the sensitivity analysis threshold sweep. (See US-3)
- **SC-005**: The computational feasibility is measured by the total runtime on a CPU-only runner, ensuring it completes within ≤ 60 minutes. (See US-2)

## Assumptions

- **Assumption about data**: The ZINC15 or OpenDataPubChem subset contains sufficient molecules with valid 3D conformations and surface area values to train a GCN model.
- **Assumption about scope**: The study is limited to molecules that can be represented by standard 2D SMILES and for which RDKit can generate a 3D conformation; molecules requiring complex stereochemistry or non-standard valences are excluded.
- **Assumption about environment**: The GitHub Actions runner provides at least 2 CPU cores, ~7 GB RAM, and ~14 GB disk space, which is sufficient for the proposed GCN architecture and dataset size.
- **Assumption about methodology**: The relationship between 2D topology and 3D surface area is assumed to be associative; no causal claims are made regarding the effect of specific structural motifs on surface area without further experimental validation.
- **Assumption about ground truth**: The "ground truth" surface area is explicitly defined as the **Solvent Accessible Surface Area (SASA)** computed by RDKit's 3D geometry functions using the **ETKDGv3 algorithm** with **maxAttempts=1000** and **randomSeed=42** to generate the **lowest-energy conformer**. This is a computed value subject to the heuristics of the conformer generation algorithm, not an experimental measurement.
- **Assumption about threshold justification**: The project will evaluate performance at absolute thresholds {0.01, 0.05, 0.1} Å²; **no single threshold is assumed to be the correct one a priori**. These values are chosen as **concrete sensitivity points** to approximate the range of typical experimental error and will be validated via sensitivity analysis. The value 0.05 Å² is treated as one of several points in the sweep, not as a fixed primary ground truth.