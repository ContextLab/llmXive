# Feature Specification: Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "Predicting Plant Secondary Metabolite Profiles from Publicly Available Genomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-Species Data Alignment & Feature Extraction (Priority: P1)

**User Journey**: A researcher needs to construct a unified, analysis-ready dataset by aligning genomic data (for BGC prediction) and metabolomic data (for abundance quantification) across a specific set of plant species. The system must execute the antiSMASH pipeline on provided genomes, parse the results into a binary presence/absence matrix, and harmonize metabolite identifiers to create a single feature-target matrix.

**Why this priority**: This is the foundational step. Without a valid, aligned dataset where every species has both BGC features and metabolite targets, no statistical modeling or correlation analysis can occur. It delivers the raw material for the entire research question.

**Independent Test**: The pipeline can be fully tested by running it on a small, manually curated subset of species. (e.g., *Arabidopsis*, *Rice*, *Maize*) and verifying that the output CSV contains a variable number of rows, with non-null values for both BGC counts and metabolite log-abundances.

**Acceptance Scenarios**:

1. **Given** a list of species IDs and their corresponding genome GFF/FASTA files, **When** the system runs antiSMASH 7.0 and parses the JSON output, **Then** a binary matrix of BGC type presence is generated with no missing columns for the requested BGC classes.
2. **Given** metabolite abundance tables from PMDB/MetaboLights, **When** the system harmonizes identifiers using InChIKeys and applies log-transformation, **Then** a normalized abundance vector is produced where all values are finite numbers (no NaN or Inf).
3. **Given** the two processed datasets, **When** the system performs the species-level join, **Then** the final output matrix contains only species present in both sources, and the row count matches the intersection size (≥ 10 species for statistical validity, specifically to ensure >80% power for permutation tests at α=0.05).

---

### User Story 2 - Regression Modeling & Hypothesis Testing (Priority: P2)

**User Journey**: A researcher needs to quantify the relationship between BGC diversity and metabolite abundance while controlling for phylogenetic non-independence. The system must train regression models (Random Forest, Elastic Net) on the aligned data, perform Leave-One-Clade-Out (LOCO) cross-validation to prevent phylogenetic overfitting, and validate the signal using Phylogenetic Independent Contrasts (PIC) to ensure the correlation is not an artifact of shared evolutionary history.

**Why this priority**: This directly addresses the core research question ("To what extent..."). It transforms the raw data into a statistical answer (R² value) and validates that the finding is robust against phylogenetic confounding.

**Independent Test**: The modeling step can be fully tested by running the training script on the aligned dataset, verifying that the LOCO-CV R² is calculated, and confirming that the PIC-adjusted p-value is < 0.05.

**Acceptance Scenarios**:

1. **Given** the aligned feature-target matrix, **When** the system splits the data using Leave-One-Clade-Out (LOCO) cross-validation, **Then** the training set contains ≥ 80% of distinct phylogenetic clades present in the dataset, and the test set contains ≥ 2 distinct clades (or the full dataset if < 3 clades exist).
2. **Given** the training set, **When** the system performs 5-fold cross-validation with hyperparameter tuning within each LOCO fold, **Then** the best model is selected based on the highest mean cross-validated R² score.
3. **Given** the selected model and the hold-out test set, **When** the system evaluates performance and runs a label-permutation baseline (100 iterations) AND a Phylogenetic Independent Contrasts (PIC) test, **Then** the reported test R² is significantly higher (p < 0.05, calculated as (count of permuted R² ≥ observed R² + 1) / (total permutations + 1)) than the mean R² of the permuted baselines, AND the PIC-adjusted correlation is significant (p < 0.05).

---

### User Story 3 - Sensitivity Analysis & Threshold Justification (Priority: P3)

**User Journey**: A researcher needs to ensure that the conclusions about "predictive power" are not artifacts of arbitrary cutoffs used during data filtering or feature selection. The system must perform a sensitivity analysis sweeping key thresholds (relative to data distribution) and report how the headline correlation rates change.

**Why this priority**: This ensures methodological soundness. Without it, a reviewer could argue that the results are fragile or dependent on arbitrary parameter choices. It validates the robustness of the P2 findings.

**Independent Test**: The sensitivity analysis can be fully tested by running the analysis with three different relative abundance thresholds (e.g., 10th, 25th, 50th percentiles) and verifying that the output includes a table showing the R² variation across these thresholds.

**Acceptance Scenarios**:

1. **Given** the initial filtering parameters, **When** the system sweeps the minimum-abundance threshold across the 10th, 25th, and 50th percentiles of the observed abundance distribution, **Then** the system re-runs the regression model for each threshold and records the resulting R² values.
2. **Given** the sweep results, **When** the system generates the sensitivity report, **Then** it explicitly states the variation in R² (e.g., "R² varied between 0.32 and 0.38") and confirms that the qualitative conclusion (moderate correlation) holds across the range.
3. **Given** the final model, **When** the system analyzes feature importance, **Then** it outputs a ranked list of BGC classes contributing to prediction, with a note on any collinearity diagnostics performed (e.g., VIF scores).

---

### Edge Cases

- **What happens when** a species has a genome assembly but no metabolomic data (or vice versa)?
  - *Handling*: The species is excluded from the final aligned matrix. The system logs a warning with the species ID and the missing data type.
- **How does the system handle** antiSMASH failing to detect any BGCs for a specific genome?
  - *Handling*: The row for that species in the BGC matrix is filled with zeros. The species is retained in the dataset to test if "zero BGCs" correlates with "zero metabolites," but a flag is raised if >50% of species have zero detections.
- **What happens when** the dataset is too small for stratified splitting (e.g., < 10 species)?
  - *Handling*: The system aborts the modeling step with a clear error message: "Insufficient species count for stratified split. Minimum required: 10 species."

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download genome assemblies and GFF files from NCBI RefSeq or Phytozome for the specified species list (See US-1).
- **FR-002**: System MUST execute antiSMASH 7.0 (command-line) and parse the JSON output to generate a binary presence/absence matrix and a diversity count matrix, explicitly acknowledging that the prediction target is "genomic potential vs. observed abundance" rather than direct causality (See US-1).
- **FR-003**: System MUST harmonize metabolite identifiers using InChIKeys and apply log-transformation to abundance values (See US-1).
- **FR-004**: System MUST split the dataset using Leave-One-Clade-Out (LOCO) cross-validation, ensuring the test set contains clades entirely absent from the training set. If the dataset contains < 3 distinct phylogenetic clades, the system MUST fall back to 5-fold stratified cross-validation (See US-2).
- **FR-005**: System MUST train regression models (Random Forest, Elastic Net) with k-fold cross-validation within each LOCO fold and evaluate against a label-permutation baseline (100 iterations). (See US-2).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the minimum-abundance threshold across the 10th, 25th, and 50th percentiles of the observed abundance distribution and report R² variation (See US-3).
- **FR-007**: System MUST output a collinearity diagnostic (e.g., VIF) for predictors that are definitionally related (See US-3).
- **FR-008**: System MUST perform a Phylogenetic Independent Contrasts (PIC) test to validate that the observed correlation persists after controlling for phylogenetic non-independence (See US-2).

### Key Entities

- **Species**: A plant entity with a unique identifier, phylogenetic clade (defined as the taxonomic family level or the lowest resolved monophyletic group above genus), genome assembly path, and metabolite profile ID.
- **BGC Feature**: A binary or count attribute representing the presence or diversity of a specific biosynthetic gene cluster type (e.g., Terpene, Alkaloid) derived from antiSMASH.
- **Metabolite Profile**: A quantitative vector of log-transformed abundance values for specific chemical compounds (InChIKey) measured via mass spectrometry or NMR.
- **Model Result**: An object containing the trained model, cross-validation scores, hold-out R², baseline comparison metrics, and PIC-adjusted correlation statistics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance in metabolite abundance explained by BGC diversity (R²) is measured against the hold-out test set (See US-2).
- **SC-002**: The statistical significance of the predictive signal is measured against the label-permutation baseline distribution (a sufficient number of iterations). (See US-2).
- **SC-003**: The robustness of the correlation is measured against the sensitivity sweep of minimum-abundance thresholds across varying percentiles. (See US-3).
- **SC-004**: The independence of predictor effects is measured against collinearity diagnostics (VIF) for definitionally related BGC classes (See US-3).
- **SC-005**: The computational feasibility is measured against the constraint of completing the full pipeline (data fetch to result, compute time only excluding network I/O latency) within 6 hours on a multi-core, high-memory runner (See US-1, US-2).
- **SC-006**: The phylogenetic independence of the signal is measured against the Phylogenetic Independent Contrasts (PIC) test (p < 0.05) (See US-2).

## Assumptions

- **Dataset-variable fit**: It is assumed that the selected public datasets (PMDB, MetaboLights, RefSeq) contain the necessary variables (BGC presence, metabolite abundance, species phylogeny) for the analysis. If a specific metabolite class lacks genomic correlates in the source data, the species will be filtered, and the analysis will proceed with the remaining valid set.
- **Inference framing**: All findings are framed as associational (correlational) rather than causal, as the study design is observational across species without random assignment.
- **Compute feasibility**: The analysis assumes that the dataset size (number of species × features) will fit within the available RAM limit of the GitHub Actions runner. If the full dataset exceeds this, the system will automatically sample species or features to ensure execution completes within a reasonable time window.
- **Model validity**: It is assumed that validated regression models (Random Forest, Elastic Net) are sufficient to capture the non-linear relationships between BGC diversity and metabolite abundance without requiring GPU-accelerated deep learning.
- **Genotype-Phenotype Gap**: It is assumed that BGC presence is a necessary but insufficient condition for metabolite production. The model tests the correlation of "genomic potential" with "observed abundance," acknowledging that regulatory factors, epigenetics, and pathway fragmentation may create a gap between the two.
- **Threshold Justification**: Thresholds for filtering (e.g., 10th, 25th, 50th percentiles) are selected as relative measures to account for instrument-specific dynamic ranges and detection limits, rather than fixed absolute values which may introduce bias.
- **Collinearity**: It is assumed that some BGC classes may be definitionally related (e.g., subtypes of terpenes), and the analysis will treat them as a joint descriptive relationship rather than claiming independent predictive effects.