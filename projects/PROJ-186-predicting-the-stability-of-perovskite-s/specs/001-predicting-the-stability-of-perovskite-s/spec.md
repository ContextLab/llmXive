# Feature Specification: Predicting the Stability of Perovskite Structures Using Machine Learning

**Feature Branch**: `001-gene-regulation` (Note: Branch name derived from mechanical step output; actual feature name is Perovskite Stability)  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting the Stability of Perovskite Structures Using Machine Learning"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1)

A materials scientist needs to ingest a raw list of ABX₃ compositions from the Materials Project and Open Quantum Materials Database (OQMD) and automatically calculate the Goldschmidt tolerance factor, octahedral factor, ionic radius mismatch, and electronegativity differences to prepare a feature matrix for modeling.

**Why this priority**: Without a clean, calculated dataset containing the specific physical descriptors requested in the research question, no machine learning model can be trained. This is the foundational data engineering step.

**Independent Test**: Can be fully tested by running the data pipeline script against a small, known subset of Materials Project IDs and verifying that the output CSV contains exactly the required columns with no null values for the target stability metric.

**Acceptance Scenarios**:

1. **Given** a list of 50 valid ABX₃ composition IDs from the Materials Project, **When** the data ingestion script is executed, **Then** a CSV file is generated containing columns for `tolerance_factor`, `octahedral_factor`, `ionic_radius_mismatch`, `electronegativity_diff`, and `decomposition_energy` with zero missing values in the target column.
2. **Given** a composition with an ambiguous oxidation state, **When** the descriptor calculator runs, **Then** the entry is flagged or excluded from the final dataset, and a log entry records the exclusion reason.

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

A researcher needs to train a RandomForestRegressor on the prepared dataset and validate its performance using 5-fold cross-validation to ensure the model generalizes before being used for prediction on novel compounds.

**Why this priority**: This step establishes the scientific validity of the model. If the model does not achieve the target RMSE (≤ 0.15 eV/atom) on held-out data, the subsequent screening of novel compounds is scientifically unsound.

**Independent Test**: Can be fully tested by executing the training script on the designated training split and verifying that the cross-validated RMSE is calculated and logged, and that the model object is serialized to disk.

**Acceptance Scenarios**:

1. **Given** a prepared training dataset with [deferred] of the data, **When** the training script executes a 5-fold grid search over `max_depth ∈ {10, 15, 20}` and `min_samples_leaf ∈ {1, 2, 4}`, **Then** the system selects the best hyperparameters based on the lowest cross-validation error, re-trains the model on the full training set, and saves the trained model artifact (`.pkl`) to the `results/` directory.
2. **Given** a hyperparameter grid search configuration, **When** the grid search runs, **Then** the system selects the best parameters based on the lowest cross-validation error and logs the specific `max_depth` and `min_samples_leaf` chosen.

### User Story 3 - Virtual Screening and Candidate Ranking (Priority: P3)

A discovery engineer needs to screen a combinatorial library of hypothetical ABX₃ compositions to identify the top candidates with the highest predicted thermodynamic stability for experimental follow-up.

**Why this priority**: This is the primary output of the research: a ranked list of novel materials. It directly answers the research question regarding generalization to uncharacterized compositions.

**Independent Test**: Can be fully tested by running the screening script on a mock combinatorial library and verifying that the output table lists exactly 20 candidates sorted by predicted stability, with all required descriptor summaries included.

**Acceptance Scenarios**:

1. **Given** a combinatorial library of [deferred] hypothetical ABX₃ formulas and a trained model, **When** the screening script is executed, **Then** a Markdown table is generated containing the top 20 candidates ranked by predicted decomposition energy, with values < -0.1 eV/atom highlighted.
2. **Given** a candidate with a predicted decomposition energy > -0.1 eV/atom, **When** the screening filter is applied, **Then** the candidate is excluded from the top 20 list and not flagged for experimental follow-up.

### Edge Cases

- What happens when the Materials Project API returns a 429 (Too Many Requests) error during data ingestion? The system must implement a retry mechanism with exponential backoff (a limited number of retries) before failing the job.
- How does the system handle hypothetical compositions where the ionic radii are undefined (e.g., a rare earth element not in the `pymatgen` periodic table)? The system must skip the calculation for that specific feature, log the warning, and either impute with a mean value or exclude the row, depending on the strictness flag.
- What if the cross-validated RMSE exceeds 0.20 eV/atom? The system must flag the model as "low confidence" in the results log, preventing automatic flagging of top candidates without manual review.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download up to 10,000 ABX₃ entries from the Materials Project REST API. If fewer than 5,000 valid perovskite entries are retrieved, the system MUST attempt to retrieve additional entries from the Open Quantum Materials Database (OQMD) to reach a minimum of 5,000 entries. All retrieved entries MUST be filtered strictly for those with Space Group (Cubic) or 148 (Rhombohedral) to ensure structural validity, ensuring the dataset contains the specific predictor variables (tolerance factor, ionic radii, electronegativity) required for the analysis (See US-1).
- **FR-002**: System MUST calculate the Goldschmidt tolerance factor ($t$) and octahedral factor ($\mu$) for every composition that passed the structural filter in FR-001 using `pymatgen` utilities, storing these as floating-point features in the feature matrix (See US-1).
- **FR-003**: System MUST train a RandomForestRegressor, performing a 5-fold cross-validation grid search over `max_depth ∈ {10, 15, 20}` and `min_samples_leaf ∈ {1, 2, 4}` to optimize hyperparameters. The system MUST then re-train the model with the best selected parameters on the full training dataset before saving the artifact (See US-2).
- **FR-004**: System MUST generate a comprehensive set of hypothetical ABX₃ compositions by combinatorial substitution of defined element sets (A={K,Rb,Cs}, B={Ti,Zr,Hf}, X={F,Cl,Br,I}). The system MUST filter these for geometric feasibility (0.8 ≤ tolerance_factor ≤ 1.1), rank them by predicted decomposition energy, and flag the top candidates with predicted energy below a thermodynamically favorable threshold for experimental follow-up (See US-3).
- **FR-005**: System MUST produce a predicted-vs-true scatter plot and a feature-importance bar chart, saving both as PNG files in the `results/` directory for visual inspection (See US-2).
- **FR-006**: System MUST enforce a CPU-only execution environment, prohibiting any GPU-specific libraries (e.g., CUDA, bitsandbytes) to ensure compatibility with the GitHub Actions free-tier runner (See Assumptions).

### Key Entities

- **CompositionRecord**: Represents a single ABX₃ entry; attributes include `formula`, `tolerance_factor`, `ionic_radius_mismatch`, `electronegativity_diff`, `decomposition_energy` (target), and `source_id`.
- **TrainedModel**: Represents the serialized RandomForestRegressor; attributes include `hyperparameters`, `feature_importances`, and `cross_validation_score`.
- **ScreeningCandidate**: Represents a hypothetical composition; attributes include `formula`, `predicted_stability_score`, `descriptor_values`, and `rank`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The model's cross-validated RMSE on decomposition energy is measured against the target threshold of ≤ 0.15 eV/atom to determine if the model is sufficiently accurate for virtual screening (See US-2, FR-003).
- **SC-002**: The feature importance analysis is measured against the hypothesis that tolerance factor, ionic radius mismatch, and electronegativity differences are top predictors, confirmed via a permutation-based sensitivity analysis to detect non-linear interactions beyond known geometric rules (See US-2, FR-005).
- **SC-003**: The virtual screening output is measured against the requirement to produce a ranked list of [deferred] hypothetical compositions, with the top 20 flagged for experimental follow-up (See US-3, FR-004).
- **SC-004**: The data pipeline runtime is measured against a concrete threshold of ≤ 6 hours to ensure the full analysis (ingestion, training, screening) completes without timeout (See Assumptions).
- **SC-005**: The memory usage of the data processing and model training steps is measured against a concrete limit of ≤ 7 GB to ensure no out-of-memory errors occur (See Assumptions).

## Assumptions

- The Materials Project REST API and OQMD provide sufficient access to download the required ABX₃ dataset within the rate limits of the free-tier API without requiring an institutional key that expires during the CI job.
- The `pymatgen` library contains accurate ionic radii and electronegativity values for all elements (including post-transition metals and rare earths) required to construct the hypothetical ABX₃ library.
- The decomposition energy (eV/atom) is the primary proxy for thermodynamic stability, and a threshold of -0.1 eV/atom is a defensible community standard for "stable enough" for initial screening.
- The hypothetical compositions generated by combinatorial substitution fit entirely within the available RAM limit of the CI runner, allowing for in-memory feature calculation and prediction.
- The RandomForest algorithm, with the specified hyperparameters, will complete training and cross-validation on the CPU-only runner within the allocated time limit.
- No GPU acceleration is required; the model complexity is low enough that CPU-only inference and training yield results within the project's compute constraints.
- The `decomposition_energy` values from the Materials Project and OQMD are treated as ground truth for training, assuming the DFT calculations used to generate them are consistent and accurate enough for the regression task.