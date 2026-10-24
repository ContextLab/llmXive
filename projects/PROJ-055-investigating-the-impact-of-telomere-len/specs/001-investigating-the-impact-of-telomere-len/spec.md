# Feature Specification: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Feature Branch**: `001-telomere-lifespan-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Integration and Cleaning Pipeline (US-1)

The researcher needs to automatically download raw telomere length data from Dryad and individual‑level lifespan data from published field studies (e.g., MARK‑recapture datasets) and merge them into a single, standardized analysis‑ready dataset. This is the foundational step; without a clean, merged dataset, no statistical modeling can occur.

**Why this priority**: This is the prerequisite for all subsequent analysis. If data cannot be retrieved or merged due to format mismatches or missing identifiers, the entire project halts.

**Independent Test**: Can be fully tested by running the data ingestion script against a known subset of Dryad entries and the lifespan study CSVs and verifying the output CSV contains >90 % of unique individual records in the source datasets with valid identifiers, standardized units (kb), and no duplicate individual IDs.

**Acceptance Scenarios**:

1. **Given** a list of valid Dryad dataset IDs and a list of individual‑level lifespan CSVs, **When** the ingestion script executes, **Then** a single CSV file is generated containing merged rows with columns for `telomere_length_kb`, `lifespan_days`, `species`, `migration_status`, `breeding_latitude`, and `body_mass_g`.
2. **Given** a Dryad dataset with inconsistent units (e.g., some in kb, some in relative units), **When** the cleaning step runs, **Then** all values are converted to kilobases (kb) using documented conversion factors, and a log of converted rows is produced.
3. **Given** an individual record whose species is present in the lifespan studies but missing from the Dryad telomere data, **When** the merge completes, **Then** the row is excluded from the primary analysis dataset but recorded in a `missing_data_log.csv` for auditability.

---

### User Story 2 - Statistical Modeling and Association Analysis (US-2)

The researcher needs to fit a **Linear Mixed‑Effects Model (LMM)** to quantify the association between early‑life telomere length (kb) and individual lifespan (days), using species as a random intercept to account for non‑independence among individuals of the same taxon.

**Why this priority**: This addresses the core research question while satisfying Constitution Principle VII, which mandates an LMM in R for transparency.

**Independent Test**: Can be fully tested by running the modeling script on the cleaned dataset and verifying the output includes a fixed‑effect coefficient for telomere length and its p‑value, and that the p‑value matches a manual calculation within ε = 1e‑6 for a synthetic dataset with known parameters.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with ≥ 15 species represented, **When** the LMM is fitted (`lifespan_days ~ telomere_length_kb + (1|species)`), **Then** the model converges without errors and outputs a summary table with the fixed‑effect estimate, standard error, and p‑value.
2. **Given** a dataset where telomere length and lifespan are uncorrelated, **When** the model is fitted, **Then** the p‑value for the telomere length coefficient is > 0.05, correctly indicating no significant association.
3. **Given** the model output, **When** the results are saved, **Then** a forest plot is generated showing the fixed‑effect estimate with 95 % confidence intervals, saved as `results/association_forest.png`.

---

### User Story 3 - Ecological Moderator Analysis (US-3)

The researcher needs to test whether the telomere‑lifespan relationship varies based on two ecological factors: **migration status** and **breeding latitude**. Both factors are included as interaction terms with telomere length in the LMM.

**Why this priority**: This addresses the secondary research question regarding environmental modulation and fulfills the idea’s hypothesis about latitude.

**Independent Test**: Can be fully tested by running the extended model with interaction terms and verifying the model fits and outputs the interaction coefficients and their standard errors, regardless of the coefficients’ sign or significance.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset with `migration_status` (e.g., “Migratory”, “Resident”) and `breeding_latitude` (numeric degrees), **When** the extended model (`lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + (1|species)`) is fitted, **Then** the output includes both interaction coefficients and their standard errors.
2. **Given** a scenario where migratory species show a stronger telomere‑lifespan slope, **When** the model is fitted, **Then** the migration interaction term coefficient is reported with its p‑value (regardless of whether p < 0.05).
3. **Given** the model results, **When** the visualization step runs, **Then** a grouped scatter plot is generated showing separate regression lines for “Migratory” vs “Resident” species and a latitude‑gradient plot, saved as `results/moderator_plot.png`.

---

### Edge Cases

- **What happens when** a species in the Dryad dataset has no corresponding individual lifespan record?  
  **Handling**: The individual record is excluded from the analysis, and a warning is logged with the species name. The pipeline continues without crashing.

- **How does the system handle** a Dryad dataset where telomere length is reported in relative units (qPCR Ct values) without a standard curve reference?  
  **Handling**: The pipeline flags these records as “unconvertible” and excludes them from the primary analysis, logging them to `unconvertible_units.csv`.

- **What happens when** the dataset size exceeds the 7 GB RAM limit of the free‑tier runner?  
  **Handling**: The pipeline automatically detects memory pressure (RAM usage > 6 GB) and switches to a chunked processing mode or subsamples the dataset to a substantial majority of the original size (preserving species representation) to ensure completion within the designated time window.

- **How are records with `migration_status = "Unknown"` handled in the interaction analysis?**  
  **Handling**: Records with “Unknown” migration are retained in the base LMM but are **excluded** from the interaction term estimation. A note summarizing the number of excluded records is added to the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw CSV data from Dryad and individual‑level lifespan CSVs using a Python script (e.g., `requests` or `urllib`) and parse them into pandas DataFrames (See US-1).
- **FR-002**: System MUST standardize all telomere length measurements to kilobases (kb) and filter for wild‑caught individuals only (See US-1).
- **FR-003**: System MUST merge telomere data with ecological covariates (`migration_status`, `breeding_latitude`, `body_mass_g`) based on species name matching, excluding unmatched records (See US-1).
- **FR-004**: System MUST fit a **Linear Mixed‑Effects Model (LMM)** with `lifespan_days` as the response, `telomere_length_kb` as the fixed effect, and a random intercept for `species` (See US-2). If the number of distinct species is **< 15**, the system MUST log a low‑power warning “Low Power: species‑level inference unreliable” but continue execution.
- **FR-005**: System MUST calculate and report the interaction effects between `telomere_length_kb` and **both** `migration_status` (categorical) **and** `breeding_latitude` (continuous) within the LMM framework (See US-3). Records with `migration_status = "Unknown"` are excluded from the interaction term but retained in the base model; the exclusion count is reported.
- **FR-006**: System MUST perform a sensitivity check:  
  • If distinct species count **≥ 10**, perform leave‑one‑out cross‑validation (LOOCV) by species.  
  • If species count **< 10**, perform a jackknife by study (or by data source) instead.  
  The system MUST log the chosen method and its justification (See US-2).
- **FR-007**: System MUST generate a forest plot of the fixed effects and a set of interaction visualizations (migration‑status grouped scatter plot and latitude gradient plot), saving them as PNG files (See US-2, US-3).
- **FR-008**: System MUST include `breeding_latitude` as a covariate in all models and test its interaction with telomere length, reporting the coefficient, standard error, and p‑value (See US-3).

### Key Entities

- **SpeciesRecord**: Represents a single observation in the merged dataset. Key attributes: `species`, `telomere_length_kb`, `lifespan_days`, `migration_status`, `breeding_latitude`, `body_mass_g`.
- **ModelResult**: Represents the output of the statistical fit. Key attributes: `fixed_effect_estimate`, `p_value`, `confidence_interval`, `variance_components`, `icc`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of successfully merged individual records (Dryad + lifespan studies match) is measured against the total number of unique individuals in the source datasets with valid identifiers (See US-1).
- **SC-002**: The system correctly applies the alpha threshold of **0.05** to flag significance in the LMM output (See US-2).
- **SC-003**: The AIC difference between the base LMM and each interaction‑augmented LMM (migration and latitude) is calculated and reported without error (See US-3).
- **SC-004**: The stability of the telomere‑lifespan coefficient is measured against the range of coefficients obtained from the LOOCV or jackknife sensitivity analysis (See US-2).
- **SC-005**: Statistical power to detect a **standardized regression slope of 0.2** (equivalent to partial‑R² ≈ 0.04) at α = 0.05 is calculated via 1,000 simulated LMM datasets that mirror the observed species count, covariance structure, and covariates (See US-2).

## Assumptions

- **Data Availability**: The Dryad and published lifespan datasets contain sufficient overlapping records (> 500 individuals across > 15 species) to achieve statistical power for the proposed LMM.
- **Unit Consistency**: The majority of Dryad datasets provide telomere length in absolute units (kb) or provide sufficient metadata to convert relative qPCR values to kb; records without this metadata will be excluded.
- **Observational Framing**: The analysis will frame all findings as **associational** rather than causal, as the data are observational (wild populations) without random assignment of telomere length.
- **Compute Constraints**: The RAM limit of the GitHub Actions free‑tier runner constitutes a hard ceiling.; the expected usage is < 2 GB. If usage exceeds a defined threshold, the system triggers chunked processing.
- **Methodological Validity**: The use of a Linear Mixed‑Effects Model (LMM) with species as a random intercept satisfies the constitutional requirement for model transparency and is scientifically appropriate for individual‑level comparative data.
- **Threshold Justification**: The alpha threshold for significance is set to **0.05**, consistent with standard ecological literature; no multiple‑comparison correction is applied as the primary analysis focuses on a single fixed effect of interest.
- **Measurement Validity**: The telomere length measurements in the source datasets are derived from validated methods (qPCR or TRF) and are comparable across studies for the purpose of this meta‑analysis.
