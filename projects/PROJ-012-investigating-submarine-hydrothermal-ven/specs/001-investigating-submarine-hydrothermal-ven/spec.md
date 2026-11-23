# Feature Specification: Submarine Hydrothermal Vent Microbial Communities as Indicators of Ocean Acidification

**Feature Branch**: `001-submarine-hydrothermal-vent-microbial-communities`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "How do shifts in microbial community composition within submarine hydrothermal vents correlate with localized pH reductions driven by ocean acidification?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I need to ingest raw 16S rRNA sequencing data (FASTQ files), autonomous pH sensor logs, and autonomous temperature sensor logs, then preprocess them into a unified analysis-ready table, so that I can begin statistical analysis without manual data wrangling.

**Why this priority**: Without clean, aligned data (including temperature for collinearity checks), no statistical correlation can be computed. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by providing a mock dataset of FASTQ files, a CSV of pH readings, and a CSV of temperature readings with timestamps and coordinates, running the pipeline, and verifying the output is a single CSV with microbial OTU/ASV counts aligned to specific pH and temperature measurements and sampling locations.

**Acceptance Scenarios**:

1. **Given** a directory containing raw 16S rRNA FASTQ files, a CSV of pH sensor readings, and a CSV of temperature sensor readings with timestamps and coordinates, **When** the preprocessing pipeline is executed, **Then** the system outputs a single CSV file where each row represents a sample with columns for pH value, temperature value, Shannon diversity index, and normalized microbial abundance counts.
2. **Given** a sample in the input data where the pH sensor timestamp has no matching 16S sequencing sample within a ±15 minute window, **When** the pipeline runs, **Then** that sample is flagged in a `rejected_samples.log` file with the reason "temporal mismatch" and excluded from the main analysis table.

---

### User Story 2 - Diversity Analysis and pH Correlation (Priority: P2)

As a researcher, I need to calculate alpha diversity indices (Shannon, Simpson) for each sample and run a linear mixed-effects model to correlate these indices with pH levels, while explicitly acknowledging that diversity is a summary statistic of composition, so that I can quantify the associational relationship between community health metrics and acidification.

**Why this priority**: This directly addresses the core research question regarding the correlation between community composition shifts and pH, with necessary caveats regarding circularity.

**Independent Test**: Can be tested by running the analysis on a pre-calculated diversity table and a corresponding pH table, verifying that the output includes a regression coefficient, p-value, and a visualization of the diversity vs. pH trend, alongside a note on the exploratory nature of the test.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with per-sample Shannon diversity indices and corresponding pH values, **When** the correlation module is executed, **Then** the system outputs a summary table containing the fixed effect estimate for pH, the standard error, and the p-value from a linear mixed-effects model (with site as a random effect), and includes a metadata flag indicating this is an associational analysis of a summary statistic.
2. **Given** a dataset where the relationship between pH and diversity is non-linear, **When** the model fitting runs, **Then** the system automatically detects the non-linearity (via residual analysis) and outputs a warning suggesting a polynomial term, while still providing the linear model results for comparison.

---

### User Story 3 - Multivariate Community Clustering (Priority: P3)

As a researcher, I need to perform PERMANOVA and ordination (PCoA/NMDS) to test if microbial communities cluster significantly based on pH gradients, ensuring that dispersion effects are controlled for, so that I can visualize and statistically validate distinct community structures in acidified vs. neutral zones.

**Why this priority**: This provides a holistic view of community shifts (beta diversity) rather than just single metrics, offering deeper ecological insight.

**Independent Test**: Can be tested by providing a distance matrix and pH metadata, running the PERMANOVA test (after a betadisper check), and verifying the output includes the R-squared value, F-statistic, a p-value, and a dispersion flag.

**Acceptance Scenarios**:

1. **Given** a Bray-Curtis dissimilarity matrix of microbial communities and a metadata table with pH levels, **When** the PERMANOVA test is executed, **Then** the system outputs a statistical summary indicating whether pH significantly explains community variation (p < 0.05) and the percentage of variance explained (R²), provided the homogeneity of dispersions test (betadisper) is not significant.
2. **Given** a dataset where the number of samples per pH gradient is highly unbalanced (defined as a >2x difference in sample counts between groups), **When** the clustering analysis runs, **Then** the system applies a rarefaction or subsampling step to balance the groups before calculating the PERMANOVA statistic to avoid bias; otherwise, it proceeds without subsampling.

---

### Edge Cases

- **What happens when** the pH sensor data contains extreme outliers (e.g., sensor malfunction reading pH 14 in a marine vent)? **The system** must detect values outside the biologically plausible range for marine vents (pH 1.0 to 10.0) and automatically exclude them. Values in the lower and upper ranges must be flagged for manual review.
- **How does the system handle** a scenario where the 16S sequencing depth varies by an order of magnitude between samples? **The system** must apply rarefaction to a common sequencing depth of [deferred] reads before calculating diversity indices to ensure comparability, unless an alternative normalization method (e.g., CSS, TMM) is explicitly configured in the pipeline settings.
- **What happens when** the number of samples is too low (< 10) to support a robust linear mixed-effects model? **The system** must output a warning regarding low statistical power and switch to a simpler linear regression or non-parametric test (Spearman correlation) with a clear note in the results.
- **What happens when** the pH measurement within the sampling window is highly heterogeneous? **The system** must calculate the standard deviation of pH values within the ±15 minute alignment window. If the standard deviation exceeds 0.2 pH units, the sample must be flagged as "highly heterogeneous" and excluded from the primary correlation analysis to prevent spurious results from spatially/temporally unstable measurements.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw 16S rRNA FASTQ files, autonomous pH sensor logs, and autonomous temperature sensor logs into a unified temporal-spatial index (See US-1).
- **FR-001.1**: System MUST calculate the standard deviation of pH values within the ±15 minute alignment window for each sample to characterize temporal stability (See Edge Cases).
- **FR-002**: System MUST calculate alpha diversity indices (Shannon, Simpson) for each sample on data rarefied to a minimum depth of [deferred] reads (See US-2).
- **FR-003**: System MUST fit a linear mixed-effects model with pH as a fixed effect and sampling site as a random effect to test the correlation between diversity and pH. If the dataset contains fewer than 2 distinct sites, the system MUST fallback to a fixed-effects linear regression (See US-2).
- **FR-003.1**: System MUST include a metadata flag in the output of FR-003 explicitly stating that the diversity-pH correlation is an associational analysis of a summary statistic and not a causal proxy (See US-2).
- **FR-004**: System MUST perform a test for homogeneity of multivariate dispersions (betadisper) prior to PERMANOVA. If dispersions are significantly different (p < 0.05), the system MUST flag the subsequent PERMANOVA result as potentially confounded by heteroscedasticity. Then, the system MUST perform PERMANOVA on a Bray-Curtis distance matrix to test for significant differences in community composition across pH gradients (See US-3).
- **FR-005**: System MUST generate an ordination plot visualizing community clustering colored by pH levels. The system MUST use NMDS if the stress value of the initial PCoA is > 0.2, otherwise it MUST use PCoA (See US-3).
- **FR-006**: System MUST flag and exclude samples where pH values fall outside the biologically plausible range of 1.0 to 10.0 for hydrothermal vents. Values between 1.0–2.0 and 8.5–10.0 must be flagged for manual review (See Edge Cases).

### Key Entities

- **Sample**: Represents a specific collection event at a vent site, containing attributes for location, timestamp, pH value, temperature value, pH variance, and raw sequencing data.
- **OTU/ASV**: Operational Taxonomic Unit or Amplicon Sequence Variant representing a distinct microbial taxon, with attributes for taxonomy and abundance per sample.
- **DiversityMetric**: A computed value (e.g., Shannon Index) associated with a specific Sample, derived from its OTU/ASV distribution.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance in microbial community composition explained by pH is measured against the PERMANOVA R² statistic (See US-3).
- **SC-002**: The statistical significance of the relationship between pH and alpha diversity is measured against the p-value from the linear mixed-effects model (See US-2).
- **SC-003**: The robustness of the diversity-pH correlation is measured against a sensitivity analysis sweeping the rarefaction depth threshold across {5,000, 10,000, [deferred]} reads (See US-2, FR-002).
- **SC-004**: The validity of the pH-diversity link is measured against a collinearity diagnostic (VIF) to ensure pH is not confounded by other environmental variables like temperature (See Methodological Soundness).
- **SC-005**: The computational feasibility is measured against the total runtime on a standard 'ubuntu-latest' GitHub Actions runner (2 CPU, 7GB RAM) not exceeding 6 hours (See Compute Feasibility).

## Assumptions

- **Assumption about data availability**: The input dataset contains 16S rRNA sequencing data, concurrent pH measurements, and concurrent temperature measurements for the same sampling events; if these are decoupled in time, the analysis will be limited to samples within a ±15 minute window.
- **Assumption about statistical framing**: The study is observational; therefore, all results will be framed as associational correlations rather than causal effects of acidification on microbial communities.
- **Assumption about computational resources**: The total size of the raw sequencing data and intermediate matrices will fit within the ~7 GB RAM and ~14 GB disk limits of the GitHub Actions free-tier runner; if larger, the pipeline will automatically subsample or use out-of-core processing.
- **Assumption about method validity**: The 16S rRNA gene region sequenced is appropriate for resolving the taxonomic groups of interest in hydrothermal vent environments (e.g., V4 region for broad bacterial diversity).
- **Assumption about threshold justification**: The rarefaction depth of [deferred] reads is chosen based on community standards for amplicon sequencing to balance depth and sample retention, and a sensitivity analysis will be performed to confirm results are stable across this threshold.
- **Assumption about temperature data**: Temperature data is available and required for the VIF collinearity diagnostic; if missing, SC-004 cannot be fully evaluated.