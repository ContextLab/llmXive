# Feature Specification: Investigating Microbial Community Succession in Constructed Wetlands

**Feature Branch**: `001-microbial-succession`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Investigating Microbial Community Succession in Constructed Wetlands"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retrieve and Preprocess Public 16S Datasets (Priority: P1)

The research pipeline MUST successfully retrieve pre-processed 16S rRNA feature tables and associated metadata from public repositories (NCBI SRA, Zenodo) and filter them to constructed wetland samples with reported nitrogen and phosphorus removal performance metrics.

**Why this priority**: This forms the foundational data layer without which no downstream analysis is possible. If data retrieval fails, the entire project cannot proceed.

**Independent Test**: Can be fully tested by executing the data retrieval script against a known public dataset and verifying that output feature tables and metadata files exist with ≥90% of expected samples retained after filtering.

**Acceptance Scenarios**:

1. **Given** a list of public dataset identifiers from NCBI SRA or Zenodo, **When** the retrieval script executes, **Then** feature tables and metadata files are saved to `data/raw/` with ≥95% of requested datasets successfully downloaded.
2. **Given** downloaded datasets, **When** filtering is applied for constructed wetlands with nutrient removal data, **Then** ≥10 samples with both 16S data and N/P removal rates are retained for analysis.
3. **Given** samples exceeding 5,000 reads per sample, **When** subsampling is applied, **Then** all samples are standardized to [deferred] reads and no sample is discarded due to low initial depth.

---

### User Story 2 - Calculate Diversity Metrics and Test Community Differences (Priority: P2)

The research pipeline MUST calculate alpha diversity (Shannon, Simpson) and beta diversity (Bray-Curtis) for each sample, then apply PERMANOVA to test for significant differences in community composition between wetland establishment stages (e.g., early vs. mature).

**Why this priority**: Diversity metrics and community comparisons are core ecological analyses that directly address the research question about succession patterns. This analysis is independent of network construction.

**Independent Test**: Can be fully tested by running diversity calculations on a subset of 20 samples and verifying that alpha diversity indices are computed and PERMANOVA p-values are generated with documented effect sizes.

**Acceptance Scenarios**:

1. **Given** ≥10 samples with valid 16S counts, **When** alpha diversity is calculated, **Then** Shannon and Simpson indices are computed for all samples with no NaN values.
2. **Given** samples grouped by wetland stage (e.g., establishment vs. mature), **When** PERMANOVA is executed, **Then** a p-value ≤0.05 indicates significant community differences, OR p>0.05 with effect size (R²) documented.
3. **Given** multiple wetland stage comparisons, **When** PERMANOVA is run, **Then** multiple-comparison correction (Benjamini-Hochberg FDR) is applied and adjusted p-values are reported.

---

### User Story 3 - Construct Co-occurrence Networks and Correlate Taxa with Nutrient Removal (Priority: P3)

The research pipeline MUST construct microbial co-occurrence networks using Spearman correlations, calculate network stability metrics (modularity), and run regression/Spearman correlation to link specific taxon abundances with nitrogen and phosphorus removal efficiency.

**Why this priority**: Network analysis and taxa-performance correlations address the predictive component of the research question. This builds on diversity analysis but can be developed independently.

**Independent Test**: Can be fully tested by constructing a network from 15 samples and verifying that modularity scores are computed and at least 3 taxa show significant correlation (|r|≥0.5, p≤0.05) with nutrient removal rates.

**Acceptance Scenarios**:

1. **Given** ≥15 samples with taxa abundance data, **When** co-occurrence network is constructed, **Then** edges are retained only for Spearman |ρ|≥0.6 with p≤0.01 after multiple-comparison correction.
2. **Given** a constructed network, **When** modularity is calculated, **Then** the value is reported with comparison between early vs. mature stages (Δmodularity ≥0.1 indicates increased stability).
3. **Given** taxon abundance and nutrient removal data, **When** correlation analysis is run, **Then** ≥3 taxa with |r|≥0.5 and p≤0.05 are identified as predictive of N/P removal efficiency.

---

### Edge Cases

- **Given** a dataset where 16S data exists but nutrient removal measurements are missing, **When** filtering is applied, **Then** samples are excluded and a count of excluded samples is logged.
- **Given** samples with <5,000 initial reads, **When** subsampling threshold is applied, **Then** those samples are excluded and a warning is raised (≥5 samples must remain).
- **Given** highly correlated predictor taxa (e.g., definitionally related abundances), **When** regression is executed, **Then** variance inflation factor (VIF) is calculated and taxa with VIF>5 are flagged for collinearity diagnostics.
- **Given** a PERMANOVA result with p≤0.05 but R²<0.1, **When** interpreting effect size, **Then** the small effect is documented as statistically significant but ecologically weak.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve pre-processed 16S rRNA feature tables and metadata from NCBI SRA or Zenodo repositories via HTTP download (See US-001)
- **FR-002**: System MUST filter datasets to constructed wetlands with reported nitrogen and phosphorus removal performance metrics (See US-001)
- **FR-003**: System MUST subsample all samples to [deferred] reads per sample to fit memory constraints (See US-001)
- **FR-004**: System MUST calculate alpha diversity (Shannon, Simpson) and beta diversity (Bray-Curtis) for all samples (See US-002)
- **FR-005**: System MUST apply PERMANOVA to test for significant differences in community composition between wetland establishment stages (See US-002)
- **FR-006**: System MUST construct co-occurrence networks using Spearman correlations with edge retention threshold |ρ|≥0.6, p≤0.01 (See US-003)
- **FR-007**: System MUST calculate network modularity and compare between early vs. mature wetland stages (See US-003)
- **FR-008**: System MUST run linear regression or Spearman correlation to link taxon abundances with nutrient removal rates (See US-003)
- **FR-009**: System MUST apply Benjamini-Hochberg FDR correction for multiple hypothesis tests (See US-002, US-003)
- **FR-010**: System MUST calculate variance inflation factor (VIF) for predictor taxa and flag collinearity when VIF>5 (See US-003)

### Key Entities

- **Sample**: A single wetland observation with 16S rRNA feature counts and associated metadata (wetland stage, N/P removal rates, location)
- **Taxon**: A microbial operational taxonomic unit (OTU) or amplicon sequence variant (ASV) with abundance counts across samples
- **Network**: A co-occurrence graph where nodes are taxa and edges represent significant Spearman correlations
- **Stage**: A categorical wetland establishment phase (e.g., early, intermediate, mature) used for group comparisons

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Number of samples with both 16S data and nutrient removal metrics is measured against the minimum threshold of 10 samples required for statistical power (See US-001)
- **SC-002**: Alpha diversity index completeness (Shannon, Simpson computed for all retained samples) is measured against [deferred] target (See US-002)
- **SC-003**: PERMANOVA effect size (R²) and adjusted p-value are measured against statistical significance threshold (p≤0.05, FDR-corrected) (See US-002)
- **SC-004**: Network modularity difference between early vs. mature stages is measured against Δ≥0.1 threshold for increased stability (See US-003)
- **SC-005**: Number of taxa with |r|≥0.5 and p≤0.05 correlating with nutrient removal is measured against minimum of 3 predictive taxa (See US-003)
- **SC-006**: Multiple-comparison correction coverage (percentage of hypothesis tests with FDR-adjusted p-values) is measured against [deferred] target (See US-002, US-003)

## Assumptions

- Public datasets from NCBI SRA and Zenodo contain both 16S rRNA feature tables AND associated water chemistry measurements (nitrogen/phosphorus removal rates); [NEEDS CLARIFICATION: does the selected dataset contain both variable types?]
- [deferred] reads per sample subsampling preserves sufficient ecological signal for diversity and correlation analyses
- Spearman correlation (|ρ|≥0.6, p≤0.01) is an appropriate threshold for co-occurrence network edge retention based on community standards in microbial ecology literature
- Benjamini-Hochberg FDR correction at α=0.05 is sufficient for multiple-comparison control across all hypothesis tests
- VIF>5 threshold for collinearity flagging aligns with standard regression diagnostics in ecological modeling
- All analyses complete within 6 hours on CPU-only GitHub Actions runner (2 cores, ~7 GB RAM, ~14 GB disk)
- No GPU or CUDA acceleration is required; scikit-bio, pandas, scipy, and networkx are CPU-tractable
- Sample sizes from available public datasets are sufficient for PERMANOVA and regression analyses (≥10 samples minimum)
- No new field sampling or wetland construction is required; all data is from existing public repositories
- Network modularity increase (Δ≥0.1) between early and mature stages indicates ecological succession toward stability
