# Feature Specification: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

**Feature Branch**: `001-submarine-hydrothermal-vent-microbial-communities`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do shifts in microbial community composition within submarine hydrothermal vents correlate with localized pH reductions driven by ocean acidification?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to ingest raw 16S rRNA sequencing data (FASTQ files) and autonomous pH sensor logs, then preprocess them into a unified analysis-ready table, so that I can begin statistical analysis without manual data wrangling.

**Why this priority**: Without clean, aligned data, no statistical correlation can be computed. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by providing a mock dataset of FASTQ files and a CSV of pH readings, running the pipeline, and verifying the output is a single CSV with microbial OTU/ASV counts aligned to specific pH measurements and sampling locations.

**Acceptance Scenarios**:

1. **Given** a directory containing raw 16S rRNA FASTQ files and a CSV of pH sensor readings with timestamps and coordinates, **When** the preprocessing pipeline is executed, **Then** the system outputs a single CSV file where each row represents a sample with columns for pH value, Shannon diversity index, and normalized microbial abundance counts.
2. **Given** a sample in the input data where the pH sensor timestamp has no matching 16S sequencing sample within a ±15 minute window, **When** the pipeline runs, **Then** that sample is flagged in a `rejected_samples.log` file with the reason "temporal mismatch" and excluded from the main analysis table.

---

### User Story 2 - Diversity Analysis and pH Correlation (Priority: P2)

As a researcher, I need to calculate alpha diversity indices (Shannon, Simpson) for each sample and run a linear mixed-effects model to correlate these indices with pH levels, so that I can quantify the relationship between community health and acidification.

**Why this priority**: This directly addresses the core research question regarding the correlation between community composition shifts and pH.

**Independent Test**: Can be tested by running the analysis on a pre-calculated diversity table and a corresponding pH table, verifying that the output includes a regression coefficient, p-value, and a visualization of the diversity vs. pH trend.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with per-sample Shannon diversity indices and corresponding pH values, **When** the correlation module is executed, **Then** the system outputs a summary table containing the fixed effect estimate for pH, the standard error, and the p-value from a linear mixed-effects model (with site as a random effect).
2. **Given** a dataset where the relationship between pH and diversity is non-linear, **When** the model fitting runs, **Then** the system automatically detects the non-linearity (via residual analysis) and outputs a warning suggesting a polynomial term, while still providing the linear model results for comparison.

---

### User Story 3 - Multivariate Community Clustering (Priority: P3)

As a researcher, I need to perform PERMANOVA and ordination (PCoA/NMDS) to test if microbial communities cluster significantly based on pH gradients, so that I can visualize and statistically validate distinct community structures in acidified vs. neutral zones.

**Why this priority**: This provides a holistic view of community shifts (beta diversity) rather than just single metrics, offering deeper ecological insight.

**Independent Test**: Can be tested by providing a distance matrix and pH metadata, running the PERMANOVA test, and verifying the output includes the R-squared value, F-statistic, and a p-value indicating if pH explains a significant portion of the community variance.

**Acceptance Scenarios**:

1. **Given** a Bray-Curtis dissimilarity matrix of microbial communities and a metadata table with pH levels, **When** the PERMANOVA test is executed, **Then** the system outputs a statistical summary indicating whether pH significantly explains community variation (p < 0.05) and the percentage of variance explained (R²).
2. **Given** a dataset where the number of samples per pH gradient is highly unbalanced, **When** the clustering analysis runs, **Then** the system applies a rarefaction or subsampling step to balance the groups before calculating the PERMANOVA statistic to avoid bias.

---

### Edge Cases

- **What happens when** the pH sensor data contains extreme outliers (e.g., sensor malfunction reading pH 14 in a hydrothermal vent)? **The system** must detect values outside the biologically plausible range for marine vents (pH 2–8) and flag them for manual review or automatic exclusion based on a defined threshold.
- **How does the system handle** a scenario where the 16S sequencing depth varies by an order of magnitude between samples? **The system** must apply rarefaction to a common sequencing depth (e.g., [deferred] reads) before calculating diversity indices to ensure comparability.
- **What happens when** the number of samples is too low (< 10) to support a robust linear mixed-effects model? **The system** must output a warning regarding low statistical power and switch to a simpler linear regression or non-parametric test (Spearman correlation) with a clear note in the results.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw 16S rRNA FASTQ files and parse autonomous pH sensor logs into a unified temporal-spatial index (See US-1).
- **FR-002**: System MUST calculate alpha diversity indices (Shannon, Simpson) for each sample after rarefaction to a minimum depth of [deferred] reads (See US-2).
- **FR-003**: System MUST fit a linear mixed-effects model with pH as a fixed effect and sampling site as a random effect to test the correlation between diversity and pH (See US-2).
- **FR-004**: System MUST perform PERMANOVA on a Bray-Curtis distance matrix to test for significant differences in community composition across pH gradients (See US-3).
- **FR-005**: System MUST generate a PCoA or NMDS ordination plot visualizing community clustering colored by pH levels (See US-3).
- **FR-006**: System MUST flag and exclude samples where pH values fall outside the biologically plausible range of 2.0 to 8.5 for hydrothermal vents (See Edge Cases).

### Key Entities

- **Sample**: Represents a specific collection event at a vent site, containing attributes for location, timestamp, pH value, and raw sequencing data.
- **OTU/ASV**: Operational Taxonomic Unit or Amplicon Sequence Variant representing a distinct microbial taxon, with attributes for taxonomy and abundance per sample.
- **DiversityMetric**: A computed value (e.g., Shannon Index) associated with a specific Sample, derived from its OTU/ASV distribution.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance in microbial community composition explained by pH is measured against the PERMANOVA R² statistic (See US-3).
- **SC-002**: The statistical significance of the relationship between pH and alpha diversity is measured against the p-value from the linear mixed-effects model (See US-2).
- **SC-003**: The robustness of the diversity-pH correlation is measured against a sensitivity analysis sweeping the rarefaction depth threshold across {5,000, 10,000, [deferred]} reads (See US-2, FR-002).
- **SC-004**: The validity of the pH-diversity link is measured against a collinearity diagnostic (VIF) to ensure pH is not confounded by other environmental variables like temperature if included (See Methodological Soundness).
- **SC-005**: The computational feasibility is measured against the total runtime on a standard GitHub Actions free-tier runner (2 CPU, 7GB RAM) not exceeding 6 hours (See Compute Feasibility).

## Assumptions

- **Assumption about data availability**: The input dataset contains both 16S rRNA sequencing data and concurrent pH measurements for the same sampling events; if these are decoupled in time, the analysis will be limited to samples within a ±15 minute window.
- **Assumption about statistical framing**: The study is observational; therefore, all results will be framed as associational correlations rather than causal effects of acidification on microbial communities.
- **Assumption about computational resources**: The total size of the raw sequencing data and intermediate matrices will fit within the ~7 GB RAM and ~14 GB disk limits of the GitHub Actions free-tier runner; if larger, the pipeline will automatically subsample or use out-of-core processing.
- **Assumption about method validity**: The 16S rRNA gene region sequenced is appropriate for resolving the taxonomic groups of interest in hydrothermal vent environments (e.g., V4 region for broad bacterial diversity).
- **Assumption about threshold justification**: The rarefaction depth of [deferred] reads is chosen based on community standards for amplicon sequencing to balance depth and sample retention, and a sensitivity analysis will be performed to confirm results are stable across this threshold.
