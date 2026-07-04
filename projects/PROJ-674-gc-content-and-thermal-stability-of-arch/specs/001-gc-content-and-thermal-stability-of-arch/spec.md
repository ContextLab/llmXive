# Feature Specification: GC Content and Thermal Stability of Archaeal tRNA Stems

**Feature Branch**: `001-gc-content-thermal-stability`  
**Created**: 2026-06-10  
**Status**: Draft  
**Input**: User description: "GC Content and Thermal Stability of Archaeal tRNA Stems"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Retrieval and Preprocessing (Priority: P1)

The researcher downloads archaeal tRNA sequences from GtRNAdb and retrieves host organism metadata (Optimal Growth Temperature) from BacDive or curated literature, then parses sequences to identify stem regions and compute GC percentages.

**Why this priority**: This is the foundational step—without data retrieval and preprocessing, no analysis can occur. It delivers the dataset needed for all subsequent steps.

**Independent Test**: Can be fully tested by verifying that the script successfully downloads ≥30 archaeal species with documented OGT values and outputs a CSV with stem GC percentages.

**Acceptance Scenarios**:

1. **Given** GtRNAdb and BacDive (or curated literature sources) are accessible, **When** the data retrieval script runs, **Then** it outputs a dataset containing at least 30 archaeal species with both tRNA sequences and OGT values
2. **Given** tRNA sequences are downloaded, **When** stem regions are parsed using cloverleaf secondary structure models, **Then** GC percentage is computed for each stem region (D-stem, Anticodon-stem, etc.) and aggregated per tRNA type
3. **Given** OGT data exists in BacDive or literature, **When** metadata is retrieved, **Then** species with OGT < 45°C and OGT ≥ 45°C are both represented in the dataset

---

### User Story 2 - Statistical Analysis and Correlation Testing (Priority: P2)

The researcher performs linear regression of OGT against mean stem GC content using scipy.stats, applies multiple-comparison correction for >1 hypothesis test, and validates significance via permutation test.

**Why this priority**: This delivers the primary scientific result (correlation coefficient and p-value) but depends on data preprocessing being complete.

**Independent Test**: Can be fully tested by verifying that the permutation test executes ≥1000 iterations and outputs a p-value, regardless of the value.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with stem GC percentages and OGT values, **When** linear regression is executed, **Then** output includes correlation coefficient (r), p-value, and 95% confidence interval
2. **Given** >1 hypothesis test is performed (e.g., per stem type), **When** multiple-comparison correction is applied, **Then** family-wise error rate is controlled using Bonferroni or Benjamini-Hochberg method
3. **Given** the regression results, **When** permutation test runs (shuffling GC values across species to generate the null distribution), **Then** empirical p-value is computed from ≥1000 permutations

---

### User Story 3 - Phylogenetic Controls and Sensitivity Analysis (Priority: P3)

The researcher applies Phylogenetic Independent Contrasts (PIC) if a phylogenetic tree is available to control for shared ancestry, and performs sensitivity analysis sweeping decision thresholds (e.g., minimum sequence length) to verify robustness.

**Why this priority**: This strengthens methodological rigor by addressing confounding from phylogeny and model sensitivity, but is optional if tree data is unavailable.

**Independent Test**: Can be fully tested by verifying that PIC analysis is executed when tree data exists, and sensitivity analysis reports how correlation coefficients vary across threshold sweeps.

**Acceptance Scenarios**:

1. **Given** a phylogenetic tree for the species subset, **When** PIC analysis is executed, **Then** correlation coefficient is recalculated controlling for shared ancestry by transforming both GC content and OGT into contrasts
2. **Given** a decision threshold (e.g., minimum sequence length), **When** sensitivity analysis sweeps the threshold over {10, 20, 30} nt and regression methods over {OLS, Huber}, **Then** output reports variation in Pearson r and p-value across the sweep
3. **Given** no phylogenetic tree is available, **When** the analysis runs, **Then** the system records a marker stating that PIC analysis was skipped due to missing tree data and frames all results as associational only

---

### Edge Cases

- What happens when GtRNAdb lacks stem annotations for certain tRNA types? → The system excludes those tRNA types from analysis and logs the exclusion count.
- How does system handle species with missing OGT values in BacDive or literature? → The system excludes species from analysis and logs the count of excluded species (target: ≥30 valid species after exclusions).
- What happens when the phylogenetic tree does not cover all species in the dataset? → PIC analysis runs on the intersecting subset; results are reported separately for PIC vs. non-PIC analyses.
- If GtRNAdb lacks stem annotations for specific tRNA types, the system MUST exclude those tRNA types from the correlation analysis and log the exclusion count; the analysis proceeds only on the subset of tRNA types with complete stem annotations, ensuring the final dataset contains ≥30 valid species with annotated stems (See US-1).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download tRNA sequences and annotations from GtRNAdb for ≥30 archaeal species with documented OGT values (See US-1)
- **FR-002**: System MUST retrieve host organism OGT metadata from BacDive or curated literature and filter for species with OGT < 45°C and OGT ≥ 45°C (See US-1)
- **FR-003**: System MUST parse sequences using standard cloverleaf secondary structure models to identify stem positions (D-stem, Anticodon-stem, etc.) and compute GC percentage for each stem region (See US-1)
- **FR-004**: System MUST perform linear regression of OGT against mean stem GC content using scipy.stats, outputting correlation coefficient (r), p-value, and 95% confidence interval (See US-2)
- **FR-005**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) when >1 hypothesis test is performed across stem types (See US-2)
- **FR-006**: System MUST validate significance via permutation test with ≥1000 permutations shuffling GC values across species to generate the null distribution (See US-2)
- **FR-007**: System MUST apply Phylogenetic Independent Contrasts (PIC) if a phylogenetic tree is available for the species subset, transforming both GC content and OGT into contrasts before regression (See US-3)
- **FR-008**: System MUST perform sensitivity analysis sweeping decision thresholds (e.g., minimum sequence length ∈ {10, 20, 30} nt and regression method ∈ {OLS, Huber}) and report change in Pearson r and p-value across the sweep (See US-3)
- **FR-009**: System MUST append the specific string "CAUTION: Associational findings only; causality not inferred due to lack of random assignment." to the results JSON when no random assignment or identification strategy is specified (See US-2)
- **FR-010**: System MUST document sample size and power considerations, recording `[deferred]` for exact power calculations but acknowledging power limitation (See US-1)

### Key Entities

- **tRNA_Sequence**: Represents tRNA molecular sequence with attributes: species_id, tRNA_type, stem_regions (D-stem, Anticodon-stem, etc.), GC_percentage_per_stem
- **Species_Metadata**: Represents organism metadata with attributes: species_id, OGT (optimal growth temperature in °C), phylogenetic_lineage
- **Analysis_Result**: Represents statistical output with attributes: correlation_coefficient (r), p_value, confidence_interval_95, permutation_p_value, pic_adjusted_r (null if PIC not run)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Correlation coefficient (r) between stem GC content and OGT is measured against the linear regression model output (See US-2)
- **SC-002**: Statistical significance (p-value) is measured against the permutation test baseline of ≥1000 permutations (See US-2)
- **SC-003**: Sample size is measured against the minimum threshold of ≥30 archaeal species with documented OGT values (See US-1)
- **SC-004**: Sensitivity analysis robustness is measured against the threshold sweep range {10, 20, 30} nt and regression methods {OLS, Huber} reporting variation in Pearson r and p-value (See US-3)
- **SC-005**: Phylogenetic confounding control is measured against PIC-adjusted vs. unadjusted correlation coefficient comparison (See US-3)

## Assumptions

- This project performs computational sequence analysis only; no wet-lab experiments are conducted, so hydration conditions and water activity controls do not apply to the methodology (per reviewer feedback from rosalind-franklin-simulated and linus-pauling-simulated)
- BacDive or curated literature contains sufficient OGT metadata for ≥30 archaeal species with documented tRNA sequences
- The analysis runs on GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, no GPU, ≤6 hours per job)
- Phylogenetic tree data may be unavailable for all species; PIC analysis is optional and results are framed as associational if tree data is incomplete
- Stem region identification uses standard cloverleaf secondary structure models without experimental structural validation
- The dataset contains all required variables (stem GC percentage as predictor, OGT as outcome); if annotations are incomplete, the analysis proceeds on the subset of valid species
- No GPU/CUDA accelerators are required; analysis uses CPU-tractable methods (scipy.stats, permutation tests)
- Multiple hypothesis tests (e.g., per stem type) require family-wise error correction via Bonferroni or Benjamini-Hochberg method
- Power calculations are deferred; sample size target of ≥30 species is based on community-standard minimum for correlation analysis