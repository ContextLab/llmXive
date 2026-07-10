# Feature Specification: Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data

**Feature Branch**: `001-predict-plant-metabolite-profiles`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "To what extent does the presence and diversity of biosynthetic gene clusters explain variation in quantitative secondary metabolite profiles across plant species?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Alignment and Feature Extraction (Priority: P1)

The researcher needs to automatically download genomic assemblies and metabolite abundance tables for a matched set of plant species, run antiSMASH 7.0 to predict BGCs, and generate a single aligned matrix of BGC features (presence/counts) and metabolite targets (log-transformed abundance).

**Why this priority**: This is the foundational step; without a clean, aligned dataset where species match between genomic and metabolomic sources, no statistical modeling can occur. It delivers the primary data asset required for the entire study.

**Independent Test**: Can be fully tested by executing the data pipeline on a small subset (e.g., 5 species) and verifying that the output CSV contains a sufficient number of rows with non-null values for both BGC counts and metabolite abundances, and that the pipeline completes within 30 minutes on a standard CPU (2 vCPUs, 7GB RAM).

**Acceptance Scenarios**:

1. **Given** a list of valid species names in the configuration, **When** the pipeline executes, **Then** it successfully retrieves genome assemblies from NCBI RefSeq and metabolite tables from PMDB/MetaboLights, matching them by species name.
2. **Given** a genome assembly file (FASTA) and annotation (GFF), **When** antiSMASH 7.0 is executed, **Then** the system parses the JSON output to generate a binary presence matrix for BGC types and a count matrix for BGC diversity per species, mapping specific BGC types to metabolite classes using the MIBiG 3.0 ontology (if no match, assign to 'unknown' class).
3. **Given** raw metabolite abundance values, **When** the data processor runs, **Then** it harmonizes identifiers using InChIKeys, adds a pseudo-count of 1 to all values, applies log-transformation to normalize distributions, and filters out any species missing either genomic or metabolomic data.

---

### User Story 2 - Predictive Modeling and Validation (Priority: P2)

The researcher needs to train regression models (Random Forest, Elastic Net) on the aligned dataset to predict metabolite abundance from BGC features, perform k-fold cross-validation, and validate performance against a phylogenetic permutation baseline to ensure the signal is not an artifact.

**Why this priority**: This addresses the core research question by quantifying the relationship between BGCs and metabolites. It validates whether genomic potential has predictive power for chemical phenotype.

**Independent Test**: Can be fully tested by running the training script on the P1 dataset and verifying that the PGLS model achieves an R² > 0.0 AND the standard deviation of R² across 5 bootstrap resamples is ≤ 0.1, while the phylogenetic permutation baseline yields an R² near zero, confirming the model learns a real signal.

**Acceptance Scenarios**:

1. **Given** the aligned feature-target matrix, **When** the model training script runs, **Then** it splits the data into training and test sets with a [deferred] ratio, stratified by phylogenetic clade to prevent overfitting.
2. **Given** the training set, **When** Cross-validation is performed, **Then** the system reports mean R² and Pearson correlation scores for each model (Random Forest, Elastic Net, Gradient Boosting).
3. **Given** the trained models, **When** evaluated on the hold-out set, **Then** the system compares the model's R² against a baseline where metabolite labels are shuffled via Phylogenetic Permutation (multiple iterations), ensuring the model's performance is statistically significant (p < 0.05).

---

### User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

The researcher needs to perform a sensitivity analysis on any decision cutoffs (e.g., BGC detection confidence thresholds) to ensure the results are robust, and document the justification for these thresholds based on community standards.

**Why this priority**: This ensures the methodological soundness of the study by demonstrating that findings are not dependent on arbitrary parameter choices, addressing the "threshold justification" requirement for publication-quality research.

**Independent Test**: Can be fully tested by re-running the analysis with varied thresholds (e.g., low, medium, and high values) and verifying that the reported R² values vary within 0.05 (measured as max absolute difference across sweep), with results logged.

**Acceptance Scenarios**:

1. **Given** a primary BGC detection threshold (0.5), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over a set of representative values and reports the resulting R² and false-positive rates for each sweep.
2. **Given** the sensitivity analysis results, **When** the final report is generated, **Then** it includes a justification for the primary threshold citing community standards (e.g., "antiSMASH default confidence") and explicitly states the variation in headline rates across the sweep.
3. **Given** the final results, **When** the researcher reviews the report, **Then** they can confirm that the model's predictive power is stable across the tested threshold range, validating the robustness of the conclusion.

---

### Edge Cases

- What happens when a species has a genome assembly but no corresponding metabolite data (or vice versa)? The system must exclude such species from the final aligned matrix and log a warning, ensuring no partial rows exist.
- How does the system handle species with zero predicted BGCs? The system must treat these as valid data points (zero counts) rather than excluding them, as this is a biologically meaningful state (lack of biosynthetic potential).
- What happens if the public data sources (PMDB, MetaboLights) are temporarily unavailable? The pipeline must fail gracefully with a clear error message indicating which source failed, rather than hanging or producing incomplete data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download genome assemblies and GFF annotation files from NCBI RefSeq or Phytozome for a user-defined list of plant species. (See US-1)
- **FR-002**: System MUST execute antiSMASH 7.0 on each genome to predict BGCs and parse the JSON output to generate a binary presence matrix and a count matrix for BGC diversity. (See US-1)
- **FR-003**: System MUST download metabolite abundance tables from PMDB or MetaboLights, harmonize identifiers using InChIKeys, add a pseudo-count of 1, and apply log-transformation to normalize distributions. (See US-1)
- **FR-004**: System MUST align genomic features and metabolite targets into a single matrix, filtering out any species that lack data in either modality. (See US-1)
- **FR-005**: System MUST train regression models (Random Forest, Elastic Net, Gradient Boosting) using scikit-learn with 5-fold cross-validation and stratified splitting by phylogenetic clade. (See US-2)
- **FR-006**: System MUST evaluate model performance on a hold-out test set using R² and Pearson correlation, and compare results against a Phylogenetic Permutation baseline (multiple iterations). (See US-2)
- **FR-007**: System MUST perform a sensitivity analysis by sweeping BGC detection thresholds over a set of representative values and report the variation in R² and error rates. (See US-3)
- **FR-008**: System MUST generate a final report that includes model performance metrics, feature importance rankings, and the sensitivity analysis results with threshold justifications. (See US-3)
- **FR-009**: System MUST map specific BGC types to metabolite classes using the MIBiG 3.0 ontology; if no match is found, assign the feature to the 'unknown' class. (See US-1)
- **FR-010**: System MUST implement Phylogenetic Generalized Least Squares (PGLS) as the primary regression model to account for phylogenetic non-independence. (See US-2)

### Key Entities

- **Species**: A biological entity representing a plant species, with attributes including species name, phylogenetic clade, and links to genomic and metabolomic data.
- **BGC Feature**: A genomic feature representing a biosynthetic gene cluster, with attributes including type (e.g., terpenoid, alkaloid), presence (binary), and count per species.
- **Metabolite**: A chemical entity representing a secondary metabolite, with attributes including InChIKey, log-transformed abundance, and compound class.
- **Model**: A predictive entity representing a trained regression model, with attributes including algorithm type, hyperparameters, R² score, and feature importance rankings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance in metabolite abundance explained by BGC diversity is measured against the null hypothesis (R² = 0) using the Phylogenetic Permutation baseline. (See US-2)
- **SC-002**: The robustness of model performance is measured against the sensitivity analysis sweep, where the variation in R² across threshold changes must be ≤ 0.05. (See US-3)
- **SC-003**: The computational feasibility is measured against the GitHub Actions free-tier constraints (≤6h runtime, 2 CPU cores, 7 GB RAM), ensuring the entire pipeline completes within these limits. (See US-1, US-2, US-3)
- **SC-004**: The data alignment success rate is measured against the user-defined input list, where a [deferred] percentage of species must have valid data in both genomic and metabolomic sources, provided N ≥ 5. (See US-1)

## Assumptions

- The public data sources (NCBI RefSeq, Phytozome, PMDB, MetaboLights) will remain accessible and provide stable APIs or download links for the duration of the project.
- The antiSMASH 7.0 command-line tool can be executed within the GitHub Actions free-tier environment (CPU-only, ≤6h, 7 GB RAM) without requiring GPU acceleration or specialized hardware.
- The dataset of matched species (with both genomic and metabolomic data) will be large enough (≥ 20 species) to perform meaningful regression analysis and cross-validation, though this number may be `[deferred]` if public data is sparse.
- The log-transformation of metabolite abundance values (with pseudo-count of 1) will sufficiently normalize the distributions for linear and tree-based regression models.
- The phylogenetic clade information for each species will be available and accurate enough to enable stratified splitting of the dataset.
- The BGC detection confidence thresholds (e.g., 0.5) are based on community standards for antiSMASH and will be justified in the final report.
- The Phylogenetic Permutation baseline will effectively serve as a null model to distinguish real signal from phylogenetic artifacts.
- The scikit-learn regression models (Random Forest, Elastic Net) will converge within the specified time limit on the available CPU resources.