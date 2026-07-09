# Feature Specification: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

**Feature Branch**: `001-molecular-structure-dssc-performance`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

The system must successfully ingest the Nazeer et al. DSSC dataset, parse SMILES strings, and generate standardized molecular graph representations (nodes/edges with features) ready for model input. This is the foundational step; without clean, standardized data, no modeling or analysis can occur.

**Why this priority**: Data integrity is the prerequisite for all subsequent analysis. If the dataset cannot be loaded or molecules standardized, the entire research question is unanswerable. This is the highest priority as it enables all other stories.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output is a valid `pandas` DataFrame containing standardized SMILES, computed graph features (atom/bond arrays), and the target PCE column, with no missing values in critical fields.

**Acceptance Scenarios**:

1. **Given** the raw `dssc_dataset.csv` from Zenodo, **When** the ingestion script runs, **Then** the output DataFrame contains exactly the rows from the source with added columns for atom features (atomic number, hybridization) and bond features (type, aromaticity).
2. **Given** a molecule with a salt counter-ion in the SMILES, **When** the standardization step runs, **Then** the salt is removed, and the resulting SMILES is canonicalized via RDKit without raising an error.
3. **Given** a molecule with ambiguous tautomers, **When** the pre-processing runs, **Then** the canonical tautomer is selected and stored, ensuring consistency across the dataset.

---

### User Story 2 - Model Training and Evaluation on CPU (Priority: P2)

The system must train a Graph Convolutional Network (GCN) and a baseline Random Forest model on the pre-processed data using scaffold-aware k-fold cross-validation, executing entirely on a CPU-only environment within a practical time limit..

**Why this priority**: This delivers the core predictive capability and comparative analysis required to answer the research question. It validates whether the proposed ML approach is feasible on the target hardware and produces the metrics (MAE, R²) needed for evaluation.

**Independent Test**: Can be fully tested by running the training script and verifying that it completes within 6 hours, produces model artifacts (weights), and outputs a JSON report containing MAE, RMSE, and R² for both the GCN and Random Forest models across all 5 folds.

**Acceptance Scenarios**:

1. **Given** the pre-processed graph data, **When** the training loop executes on a CPU-only runner, **Then** the GCN model trains for a sufficient number of epochs per fold without GPU memory errors and finishes within 6 hours total.
2. **Given** the trained models, **When** the evaluation step runs, **Then** the system outputs a paired-t test result comparing the fold-wise MAE of the GCN vs. Random Forest, including the p-value.
3. **Given** a split where the test set contains molecules with unique scaffolds, **When** the scaffold-aware split is applied, **Then** no molecule from the training set shares a scaffold with the test set, preventing data leakage.

---

### User Story 3 - Interpretability and Motif Extraction (Priority: P3)

The system must extract and rank substructures (motifs) contributing to high predicted PCE using integrated gradients or attention weights, and summarize the top recurring motifs.

**Why this priority**: This addresses the "why" behind the predictions, providing the actionable design heuristics mentioned in the motivation. While the model can predict without this, the scientific value lies in identifying the structural drivers.

**Independent Test**: Can be fully tested by running the interpretability script on a held-out high-PCE molecule and verifying that the output lists specific substructures (e.g., donor-π-acceptor motifs) with associated importance scores.

**Acceptance Scenarios**:

1. **Given** a trained GCN model and a high-PCE molecule, **When** the interpretability module runs, **Then** it outputs a ranked list of subgraphs (atoms/bonds) with their contribution scores to the prediction.
2. **Given** the top-5 recurring motifs identified across the dataset, **When** the summary is generated, **Then** the output includes a textual description of each motif and a frequency count.
3. **Given** the identified motifs, **When** the system cross-references them with literature (manual check), **Then** the output format allows a researcher to easily validate the motifs against known high-performance dyes.

### Edge Cases

- What happens when the Zenodo dataset download fails or the file format changes? The system must retry up to 3 times with exponential backoff, then fail gracefully with a clear error message indicating the source URL and expected format.
- How does the system handle molecules with invalid SMILES that cannot be parsed by RDKit? These molecules must be logged in a `failed_molecules.log` file and excluded from the training set, with a count of excluded molecules reported in the final summary.
- What if the CPU-only training exceeds the 6-hour limit? The system must implement a hard timeout (several hours) to allow for cleanup and artifact saving., failing the job with a "Time Limit Exceeded" status rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the DSSC dataset from ` and extract SMILES and PCE values (See US-1).
- **FR-002**: System MUST standardize all molecular structures using RDKit, including tautomer canonicalization and salt removal, to ensure data consistency (See US-1).
- **FR-003**: System MUST implement a Graph Convolutional Network (GCN) with ≤ 2 layers and hidden size 128, trainable on CPU without GPU dependencies (See US-2).
- **FR-004**: System MUST perform scaffold-aware k-fold cross-validation to ensure no structural leakage between training and test sets (See US-2).
- **FR-005**: System MUST compute and report MAE, RMSE, and R² for both the GCN and a baseline Random Forest model on Morgan fingerprints (See US-2).
- **FR-006**: System MUST perform a paired t-test on fold-wise MAE between the GCN and Random Forest to determine statistical significance (See US-2).
- **FR-007**: System MUST extract node-level importance scores using integrated gradients or attention mechanisms to identify predictive substructures (See US-3).
- **FR-008**: System MUST aggregate and summarize the top-5 recurring motifs that correlate with high PCE predictions (See US-3).
- **FR-009**: System MUST verify that all experimental PCE values are normalized to percentage units (%) and AM1.5G illumination conditions, flagging any entries that deviate for manual review (See US-1).

### Key Entities

- **Molecule**: Represents a chemical entity with attributes: SMILES string, standardized graph (nodes/edges), and experimental PCE value.
- **Model**: Represents a trained predictor with attributes: architecture type (GCN/RF), hyperparameters, and performance metrics (MAE, R²).
- **Motif**: Represents a recurring substructure with attributes: graph pattern, frequency in high-PCE predictions, and importance score.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in Mean Absolute Error (MAE) between the GCN and Random Forest models is measured in absolute percentage points of PCE to determine if the GCN outperforms the baseline (See FR-005).
- **SC-002**: The mean coefficient of determination (R²) across the 5 folds for the GCN model is measured against a null model (horizontal line at mean PCE) to validate predictive power (See FR-005).
- **SC-003**: The statistical significance of the performance improvement is measured via a two-tailed paired t-test p-value and Cohen's d effect size (See FR-006).
- **SC-004**: The total execution time of the training and evaluation workflow is measured against the 6-hour limit of the GitHub Actions free-tier runner (See FR-003).
- **SC-005**: The interpretability analysis produces a ranked list of at least 5 distinct (non-isomorphic via graph isomorphism check) substructures with quantified contribution scores (See FR-008).

## Assumptions

- The Nazeer et al. Zenodo dataset contains all necessary variables (SMILES strings and experimental PCE values) to perform the analysis; if specific metadata (e.g., electrolyte type) is missing, it will be treated as a constant or ignored, as the primary focus is molecular structure.
- The dataset size is small enough (< 1 GB) to fit entirely into the 7 GB RAM limit of the GitHub Actions free-tier runner without requiring chunking or sampling.
- The GCN implementation in PyTorch Geometric can run efficiently on CPU with the specified hyperparameters (multiple layers, appropriate hidden size, a sufficient number of training epochs) within the 6-hour time limit. for the given dataset size.
- The "scaffold" definition for the cross-validation split is based on the Bemis-Murcko scaffold framework, which is the standard in cheminformatics for ensuring structural diversity between folds.
- The experimental PCE values in the dataset are reported in consistent units (%), requiring no unit conversion. *Note: FR-009 adds a verification step to handle cases where this assumption may not hold.*
- The interpretability method (integrated gradients) is computationally feasible on CPU for the model size and dataset; if not, the method will fall back to simpler feature importance from the Random Forest baseline.
- The identified motifs are correlational; the study does not claim causal relationships between specific substructures and PCE, acknowledging that device fabrication variables (e.g., layer thickness, annealing) may confound the results.