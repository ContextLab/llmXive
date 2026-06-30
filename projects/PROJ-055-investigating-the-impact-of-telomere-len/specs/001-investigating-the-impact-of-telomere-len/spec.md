# Feature Specification: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Feature Branch**: `001-telomere-lifespan-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Integration and Cleaning Pipeline (Priority: P1)

The researcher needs to automatically download raw telomere length data from Dryad and species longevity/ecological data from AnAge, then merge them into a single, standardized analysis-ready dataset. This is the foundational step; without a clean, merged dataset, no statistical modeling can occur.

**Why this priority**: This is the prerequisite for all subsequent analysis. If data cannot be retrieved or merged due to format mismatches or missing identifiers, the entire project halts.

**Independent Test**: Can be fully tested by running the data ingestion script against a known subset of Dryad/AnAge entries and verifying the output CSV contains >90% of unique species in the source datasets with valid identifiers, standardized units (kb), and no duplicate species IDs.

**Acceptance Scenarios**:

1. **Given** a list of valid Dryad dataset IDs and AnAge species names, **When** the ingestion script executes, **Then** a single CSV file is generated containing merged rows with columns for `telomere_length`, `lifespan`, `species`, `migration_status`, and `body_mass`.
2. **Given** a Dryad dataset with inconsistent units (e.g., some in kb, some in relative units), **When** the cleaning step runs, **Then** all values are converted to kilobases (kb) using documented conversion factors, and a log of converted rows is produced.
3. **Given** a species present in AnAge but missing from the Dryad data, **When** the merge completes, **Then** the row is excluded from the primary analysis dataset but recorded in a `missing_data_log.csv` for auditability.

---

### User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

The researcher needs to fit a Phylogenetic Generalized Least Squares (PGLS) model to quantify the association between early-life telomere length and lifespan, using a phylogenetic tree to account for evolutionary non-independence.

**Why this priority**: This addresses the core research question. It determines whether the primary hypothesis (telomere length predicts lifespan) is supported by the aggregated data while correctly modeling phylogenetic covariance.

**Independent Test**: Can be fully tested by running the modeling script on the cleaned dataset and verifying the output includes a fixed-effect coefficient for telomere length and its p-value, and that the p-value matches a manual calculation within epsilon (1e-6) for a synthetic dataset with known parameters.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with a valid phylogenetic tree and >15 species, **When** the PGLS is fitted (`lifespan ~ telomere_length + phylogenetic_covariance`), **Then** the model converges without errors and outputs a summary table with the fixed effect estimate, standard error, and p-value.
2. **Given** a dataset where telomere length and lifespan are uncorrelated, **When** the model is fitted, **Then** the p-value for the telomere length coefficient is > 0.05, correctly indicating no significant association.
3. **Given** the model output, **When** the results are saved, **Then** a forest plot is generated showing the fixed effect estimate with 95% confidence intervals, saved as `results/association_forest.png`.

---

### User Story 3 - Ecological Moderator Analysis (Priority: P3)

The researcher needs to test whether the telomere-lifespan relationship varies based on ecological factors (specifically migratory behavior) by including an interaction term in the PGLS model.

**Why this priority**: This addresses the secondary research question regarding environmental modulation. It adds depth to the findings but is dependent on the primary model being stable.

**Independent Test**: Can be fully tested by running the extended model with the interaction term and verifying the model fits and outputs the interaction coefficient and its standard error, regardless of the coefficient's sign or significance.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with a `migration_status` column (e.g., "Migratory", "Resident") and a phylogenetic tree, **When** the extended model (`lifespan ~ telomere_length * migration_status + phylogenetic_covariance`) is fitted, **Then** the output includes the interaction coefficient and its standard error.
2. **Given** a scenario where migratory species show a stronger telomere-lifespan slope, **When** the model is fitted, **Then** the interaction term coefficient is reported with its p-value (regardless of whether p < 0.05).
3. **Given** the model results, **When** the visualization step runs, **Then** a grouped scatter plot is generated showing separate regression lines for "Migratory" and "Resident" species, saved as `results/moderator_plot.png`.

---

### Edge Cases

- **What happens when** a species in the Dryad dataset has no corresponding entry in the AnAge database for lifespan?
  - **Handling**: The record is excluded from the analysis, and a warning is logged with the species name. The pipeline continues without crashing.
- **How does the system handle** a Dryad dataset where telomere length is reported in relative units (qPCR Ct values) without a standard curve reference?
  - **Handling**: The pipeline flags these records as "unconvertible" and excludes them from the primary analysis, logging them to `unconvertible_units.csv`.
- **What happens when** the dataset size exceeds the 7 GB RAM limit of the free-tier runner?
  - **Handling**: The pipeline automatically detects memory pressure (RAM usage > 6 GB) and switches to a chunked processing mode or subsamples the dataset to a substantial majority of the original size (preserving species representation) to ensure completion within the designated time window.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw CSV data from Dryad and AnAge using a Python script (e.g., `requests` or `urllib`) and parse them into pandas DataFrames (See US-1).
- **FR-002**: System MUST standardize all telomere length measurements to kilobases (kb) and filter for wild-caught individuals only (See US-1).
- **FR-003**: System MUST merge telomere data with ecological covariates (migration, body mass) based on species name matching, excluding unmatched records (See US-1).
- **FR-004**: System MUST fit a Phylogenetic Generalized Least Squares (PGLS) model with `lifespan` as the response, `telomere_length` as the fixed effect, and a phylogenetic covariance matrix derived from a bird tree (See US-2). If the number of species is < 15, the system MUST report "Low Power: Phylogenetic inference unreliable" instead of halting.
- **FR-005**: System MUST calculate and report the interaction effect between `telomere_length` and `migration_status` (a species-level fixed effect) in the PGLS framework to test for ecological modulation (See US-3).
- **FR-006**: System MUST perform a leave-one-out cross-validation (LOOCV) sensitivity check by species, or a jackknife by study if species count is < 10, to ensure results are not driven by a single high-impact study (See US-2). The system MUST log the justification for the chosen method.
- **FR-007**: System MUST generate a forest plot of the fixed effects and a scatter plot of the moderator interaction, saving them as PNG files (See US-2, US-3).

### Key Entities

- **SpeciesRecord**: Represents a single observation in the merged dataset. Key attributes: `species_id`, `telomere_length_kb`, `max_lifespan_years`, `migration_status`, `body_mass_g`.
- **ModelResult**: Represents the output of the statistical fit. Key attributes: `fixed_effect_estimate`, `p_value`, `confidence_interval`, `phylogenetic_signal_lambda`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of successfully merged records (Dryad + AnAge match) is measured against the total number of unique species in the source datasets with valid identifiers (See US-1).
- **SC-002**: The system correctly applies the alpha threshold of 0.05 to flag significance in the PGLS output (See US-2).
- **SC-003**: The AIC difference between the base model and the interaction model is calculated and reported without error (See US-3).
- **SC-004**: The stability of the telomere-lifespan coefficient is measured against the range of coefficients obtained from the leave-one-out or jackknife sensitivity analysis (See US-2).
- **SC-005**: The statistical power to detect a moderate effect size (Cohen's d = 0.5) at alpha = 0.05 is calculated and reported based on the number of species in the dataset (See US-2).

## Assumptions

- **Data Availability**: The Dryad and AnAge databases contain sufficient overlapping records (>500 individuals across >15 species) to achieve statistical power for the proposed PGLS.
- **Unit Consistency**: The majority of Dryad datasets provide telomere length in absolute units (kb) or provide sufficient metadata to convert relative qPCR values to kb; records without this metadata will be excluded.
- **Observational Framing**: The analysis will frame all findings as **associational** rather than causal, as the data is observational (wild populations) without random assignment of telomere length.
- **Compute Constraints**: The 7 GB RAM limit of the GitHub Actions free-tier runner is the hard ceiling; the expected usage is <2 GB. If usage exceeds a defined threshold, the system triggers chunked processing.
- **Methodological Validity**: The use of Phylogenetic Generalized Least Squares (PGLS) is required to account for phylogenetic non-independence; a simple LMM with species as a random intercept is scientifically insufficient for this inference.
- **Threshold Justification**: The alpha threshold for significance is set to 0.05, consistent with standard ecological literature; no multiple-comparison correction is applied as the primary analysis focuses on a single fixed effect of interest.
- **Measurement Validity**: The telomere length measurements in the source datasets are derived from validated methods (qPCR or TRF) and are comparable across studies for the purpose of this meta-analysis.