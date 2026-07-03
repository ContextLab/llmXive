# Feature Specification: Predicting Molecular Reactivity Using Machine Learning and Public Reaction Databases

**Feature Branch**: `001-molecular-reactivity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Reactivity Using Machine Learning and Public Reaction Databases"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Reaction Class Filtering (Priority: P1)

The researcher needs to download a subset of the USPTO reaction dataset (a substantial number of reactions), parse the molecular structures, and filter them into specific reaction classes, including unimolecular nucleophilic substitution, bimolecular nucleophilic substitution, and Diels-Alder, using reaction template matching.

**Why this priority**: Without a clean, filtered dataset of specific reaction mechanisms, no structural analysis or modeling can occur. This is the foundational data pipeline.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains a single `reaction_type` column containing exactly three distinct values ("SN1", "SN2", "Diels-Alder") where present, and that the total row count is ≥ 90% of the input file row count.

**Acceptance Scenarios**:

1. **Given** a raw USPTO JSON dump, **When** the ingestion script runs with the specified reaction templates, **Then** the output file contains only rows matching SN1, SN2, or Diels-Alder patterns, and non-matching rows are excluded.
2. **Given** a raw input file, **When** the script encounters malformed SMILES strings, **Then** those rows are logged to an error file and excluded from the primary dataset without crashing the process.

---

### User Story 2 - Feature Extraction and Model Training (Priority: P2)

The researcher needs to convert the filtered molecular reactants into numerical features (molecular weight, atom counts, bond types, topological indices) using RDKit, and train a lightweight gradient-boosting model (XGBoost) on CPU to predict relative reactivity rankings derived from experimental yield or success data.

**Why this priority**: This implements the core research hypothesis: determining if structural features can predict reactivity. It must run within a feasible CPU budget to be feasible.

**Independent Test**: Can be fully tested by running the training script on a sample of [deferred] reaction records and verifying that the model outputs a prediction file with a Spearman correlation coefficient > 0.5 (indicating scientific validity) and that the total runtime is < 30 minutes on a standard CPU.

**Acceptance Scenarios**:

1. **Given** a filtered dataset of reaction records, **When** the feature extraction and training pipeline runs, **Then** a trained model artifact is saved, and a log file confirms the training completed within 30 minutes on a CPU-only environment.
2. **Given** the trained model, **When** evaluated via 5-fold cross-validation, **Then** the system outputs a confusion matrix and a Spearman correlation value for each reaction class.

---

### User Story 3 - Comparative Analysis and Significance Testing (Priority: P3)

The researcher needs to compare the predictive performance across the three reaction classes and perform a permutation test to determine if the observed correlations are statistically significant (p < 0.01 for the main hypothesis). The validity of this test relies on the target variable being independent of the structural predictors as defined in FR-004.

**Why this priority**: This delivers the final scientific insight: which reaction mechanisms are predictable and whether the results are due to chance.

**Independent Test**: Can be fully tested by running the analysis script on the cross-validation results and verifying that the output report contains a ranked list of reaction classes by Spearman ρ, with SN1/SN2/Diels-Alder labels clearly distinguished, and a p-value < 0.01 for the permutation test.

**Acceptance Scenarios**:

1. **Given** the cross-validation results, **When** the analysis script runs, **Then** it generates a summary report ranking SN1, SN2, and Diels-Alder by Spearman ρ, with SN1/SN2/Diels-Alder labels clearly distinguished.
2. **Given** the observed model performance, **When** the permutation test is executed (shuffling targets [deferred] times), **Then** the system calculates and reports a p-value indicating the probability of the result occurring by chance.

### Edge Cases

- What happens when the USPTO dataset subset is missing specific reaction templates for a class (e.g., when the number of Diels-Alder reactions is limited)? The system must flag a "Low Sample Size" warning and skip that class rather than failing.
- How does the system handle molecules with undefined stereochemistry in SMILES? The system must normalize these to a canonical representation or exclude them with a log entry.
- What happens if the CPU memory limit is exceeded during feature extraction? The system must implement a batch processing strategy to process the data in manageable chunks.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the provided input subset of the USPTO reaction dataset and filter it to include reactions matching the classes SN1, SN2, or Diels-Alder, excluding all others (See US-1).
- **FR-002**: System MUST convert molecular reactants into a feature matrix including molecular weight, atom counts, bond types, and topological indices using RDKit, ensuring no GPU usage (See US-2).
- **FR-003**: System MUST train a gradient-boosting model (XGBoost) using 5-fold cross-validation within a maximum runtime of 30 minutes on a CPU-only environment (See US-2).
- **FR-004**: System MUST compute Spearman rank correlation coefficients between predicted and observed reactivity rankings, where 'observed' rankings are derived strictly from experimental yield values or reaction success flags, not from structural features or reaction class labels (See US-3).
- **FR-005**: System MUST perform a permutation test (A sufficient number of iterations, a community standard for initial significance estimation when power analysis is not feasible) to calculate the statistical significance (p-value) of the observed correlations, explicitly framing results as associational (See US-3).
- **FR-006**: System MUST handle datasets with < 1,000 samples per class by logging a warning and excluding that class from the final comparison report rather than crashing (See US-1).

### Key Entities

- **ReactionRecord**: Represents a single chemical reaction with attributes: `reaction_id`, `smiles_reactants`, `smiles_products`, `reaction_type` (SN1/SN2/Diels-Alder), `reactivity_rank`.
- **FeatureVector**: Represents the numerical encoding of a reactant set, with attributes: `molecular_weight`, `atom_counts`, `bond_types`, `topological_indices`.
- **ModelResult**: Represents the output of a training fold, with attributes: `fold_id`, `spearman_rho`, `p_value`, `training_time`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The Spearman correlation coefficient (ρ) between predicted and observed reactivity rankings is measured against the null hypothesis of ρ = 0 (See US-3).
- **SC-002**: The statistical significance (p-value) of the correlation is measured against the threshold of p < 0.01 for the permutation test (See US-3).
- **SC-003**: The training runtime is measured against the 30-minute CPU budget limit to ensure feasibility on free-tier runners (See US-2).
- **SC-004**: The memory footprint of the feature extraction process is measured against the GB RAM limit to confirm batch processing is effective (See US-2).
- **SC-005**: The proportion of reactions successfully classified into SN1, SN2, or Diels-Alder is measured against the total input size to assess data quality (See US-1).

## Assumptions

- The USPTO public repository provides a downloadable subset of at least 100,000 reactions that includes sufficient examples of SN1, SN2, and Diels-Alder mechanisms (minimum 1,000 per class) to enable statistical analysis.
- The "reactivity ranking" target variable is derived by sorting reactions by their reported experimental yield (descending) or by a binary success flag if yield is missing, ensuring the target is independent of the structural predictors used in the model.
- The RDKit library and XGBoost (CPU version) can be installed and run within the disk and RAM constraints of the GitHub Actions free-tier runner.
- Reaction template matching is sufficiently accurate to classify reactions into the three target classes without manual curation; ambiguous reactions will be excluded.
- The analysis is observational; therefore, all conclusions regarding structure-reactivity relationships will be framed as associational, not causal, as no random assignment of molecular structures is performed.
- The dataset contains all necessary structural variables (predictors) and outcome variables (reactivity) required for the analysis; if specific covariates (e.g., solvent effects) are missing, they will be treated as unobserved confounders and not included in the model.