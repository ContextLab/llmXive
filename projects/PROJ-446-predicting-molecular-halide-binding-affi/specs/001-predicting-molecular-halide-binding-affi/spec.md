# Feature Specification: Predicting Molecular Halide Binding Affinities with Machine Learning

**Feature Branch**: `001-predicting-halide-binding-affinities`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Halide Binding Affinities with Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

A researcher downloads experimental halide binding constants from NIST Chemistry WebBook and PubChem, parses molecular structures from SMILES/InChI records, generates molecular fingerprints and descriptors, and filters the dataset to hosts with ≥3 different halide measurements for within-host comparison.

**Why this priority**: This is the foundational data layer; without a clean, validated dataset, no modeling or analysis can proceed. It delivers the core research asset.

**Independent Test**: Can be fully tested by running the data pipeline on a small sample subset and verifying the output CSV contains valid binding constants, halide identities, and molecular descriptors for ≥3 halides per host.

**Acceptance Scenarios**:

1. **Given** a query for "halide binding constant" on NIST/PubChem, **When** the pipeline downloads and parses records, **Then** the output CSV contains columns for host SMILES, halide identity (F⁻/Cl⁻/Br⁻/I⁻), binding constant (log K or ΔG), and source reference
2. **Given** a host molecule with measurements for F⁻, Cl⁻, and Br⁻, **When** the filtering step runs, **Then** the host is retained in the dataset; hosts with only 1-2 halide measurements are excluded
3. **Given** a host molecule record without a valid SMILES string, **When** the pipeline validates molecular structures, **Then** the record is logged as invalid and excluded from the final dataset

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

A researcher trains random forest and gradient boosting models using scikit-learn to predict binding affinity from structural features, with 5-fold cross-validation split by host molecule (not by measurement) to avoid data leakage.

**Why this priority**: This delivers the core predictive capability and model performance metrics that answer the research question. It depends on US-1 but is independently testable once data exists.

**Independent Test**: Can be fully tested by training a random forest model on the preprocessed dataset and verifying that cross-validation produces R² and RMSE metrics without data leakage (i.e., same host does not appear in both train and test folds).

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with ≥3 halides per host, **When** the 5-fold cross-validation split runs, **Then** no host molecule appears in both training and validation sets within the same fold
2. **Given** a trained random forest model, **When** cross-validation completes, **Then** the output includes R² and RMSE metrics for each fold and their mean/std across folds
3. **Given** the full dataset, **When** model training completes, **Then** the process finishes within ≤6 hours on a CPU-only runner with ≤7 GB RAM peak usage

---

### User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

A researcher performs permutation importance analysis to identify top structural determinants of halide selectivity, generates partial dependence plots showing affinity trends across the halide series (F⁻→Cl⁻→Br⁻→I⁻), and produces interpretable insights into which molecular features correlate with halide preference.

**Why this priority**: This delivers the mechanistic insights that answer "what structural features determine affinity" and "how does this vary across halide identity." It depends on US-2 but can be independently tested once models exist.

**Independent Test**: Can be fully tested by running permutation importance on a trained model and verifying the output includes a ranked list of top 10 features with importance scores, plus partial dependence plots for at least 2 key features.

**Acceptance Scenarios**:

1. **Given** a trained gradient boosting model, **When** permutation importance analysis runs, **Then** the output includes a ranked list of features with importance scores where the top 3 features explain ≥40% of total importance
2. **Given** the fitted model and test set, **When** partial dependence plots are generated, **Then** the plots show affinity trends for at least 2 features (e.g., hydrogen-bond donor count, cavity size) across the halide series
3. **Given** the feature importance results, **When** the researcher reviews the top determinants, **Then** the output includes a summary table mapping features to their hypothesized chemical interpretation (e.g., "cationic center density → electrostatic attraction")

---

### Edge Cases

- What happens when NIST/PubChem records have inconsistent units for binding constants (some report log K, others ΔG in kcal/mol)?
- How does the system handle host molecules with ambiguous halide identity labels (e.g., "halide" without specifying F⁻/Cl⁻/Br⁻/I⁻)?
- What happens when the dataset contains fewer than 50 host molecules after filtering (insufficient for 5-fold cross-validation)?
- How does the system handle duplicate records for the same host-halide pair with different reported binding constants?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse experimental halide binding constants from NIST Chemistry WebBook and PubChem using search terms "halide binding constant", "anion recognition", and "ionophore affinity" (See US-1)
- **FR-002**: System MUST generate molecular fingerprints (ECFP4) and RDKit descriptors from SMILES/InChI records for each host molecule (See US-1)
- **FR-003**: System MUST filter the dataset to retain only host molecules with ≥3 different halide measurements (F⁻, Cl⁻, Br⁻, I⁻) for within-host comparison (See US-1)
- **FR-004**: System MUST split data by host molecule (not by measurement) during 5-fold cross-validation to prevent data leakage (See US-2)
- **FR-005**: System MUST train random forest and gradient boosting models using scikit-learn with default hyperparameters, without GPU/CUDA acceleration (See US-2)
- **FR-006**: System MUST perform permutation importance analysis to identify top structural determinants of halide selectivity (See US-3)
- **FR-007**: System MUST generate partial dependence plots for at least 2 key features showing affinity trends across the halide series (See US-3)
- **FR-008**: System MUST frame all predictive findings as associational (not causal) in documentation, given the observational nature of the dataset (See US-2)
- **FR-009**: System MUST apply family-wise error rate correction (e.g., Bonferroni or Benjamini-Hochberg) when reporting significance across multiple halide-specific model comparisons (See US-2)
- **FR-010**: System MUST validate that all molecular descriptor variables are available in the NIST/PubChem source before proceeding; if any required variable is missing, record a `[NEEDS CLARIFICATION: does <dataset> contain <variable>?]` marker (See US-1)

### Key Entities *(include if feature involves data)*

- **HostMolecule**: Represents an organic host compound with attributes SMILES, InChI, molecular descriptors (ECFP4 fingerprint, RDKit descriptors), and associated binding measurements
- **BindingMeasurement**: Represents a single experimental measurement with attributes host_id, halide_identity (F⁻/Cl⁻/Br⁻/I⁻), binding_constant (log K or ΔG), units, source (NIST/PubChem), and reference DOI
- **ModelRun**: Represents a trained model instance with attributes model_type (random_forest/gradient_boosting), cross_validation_folds, R²_mean, R²_std, RMSE_mean, RMSE_std, and feature_importance_ranking

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Out-of-sample R² is measured against the 5-fold cross-validation held-out host molecules to assess predictive performance on unseen hosts (See US-2)
- **SC-002**: Feature importance ranking is measured against permutation importance scores to identify structural determinants of halide selectivity (See US-3)
- **SC-003**: Model training runtime is measured against the 6-hour CPU-only runner time budget to verify compute feasibility (See US-2)
- **SC-004**: Dataset completeness is measured against the required variables (host SMILES, halide identity, binding constant) to verify dataset-variable fit (See US-1)
- **SC-005**: Multiple-comparison correction is measured against the number of halide-specific hypothesis tests performed to control family-wise error rate (See US-2)

## Assumptions

- NIST Chemistry WebBook and PubChem contain binding constants for all four halide ions (F⁻, Cl⁻, Br⁻/I⁻) for a sufficient number of host molecules (≥50 hosts with ≥3 halides each) to support 5-fold cross-validation
- The filtering threshold of ≥3 different halide measurements per host is justified by the need for within-host comparison across the halide series, enabling analysis of how affinity varies by halide identity for the same receptor
- All molecular structure data in NIST/PubChem records is provided in valid SMILES or InChI format parseable by RDKit; records with invalid structures are excluded from the dataset
- The scikit-learn random forest and gradient boosting implementations can complete training on the full dataset within ≤6 hours on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM) without GPU acceleration
- Binding constants in NIST/PubChem records are reported in consistent units (log K or ΔG) that can be standardized; any records with ambiguous or non-standard units are excluded
- The observational nature of the dataset (no random assignment of hosts to halides) means all reported structure-affinity relationships are associational, not causal; no identification strategy or randomization is available to support causal claims
- Molecular descriptors (ECFP4 fingerprints, RDKit descriptors) may exhibit collinearity; the analysis will report joint relationships descriptively and include a collinearity diagnostic (e.g., variance inflation factor) rather than claiming independent predictive effects for definitionally related descriptors
- The dataset size after filtering will fit within available RAM and disk on the GitHub Actions runner.; if the full dataset exceeds this, a representative subset will be sampled and the scoping decision will be documented
- No validated questionnaires or psychometric instruments are used in this study (chemistry domain), so the measurement validity requirement for citable validation does not apply; molecular descriptors are standard computational chemistry tools with established community usage
