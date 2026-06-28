# Feature Specification: Statistical Properties of Simulated Black Hole Mergers

**Feature Branch**: `001-statistical-properties-black-hole-mergers`
**Created**: 2024-01-15
**Status**: Draft
**Input**: User description: "Investigating the Statistical Properties of Simulated Black Hole Mergers"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and preprocess GWTC observational catalogs (Priority: P1)

As a researcher, I want to download the GWTC-1 and GWTC-2 posterior samples and extract component masses, mass ratios, and effective spins so that I have the observational dataset for statistical comparison with simulation predictions.

**Why this priority**: This is the foundational data acquisition step; without the observational catalog data, no statistical comparison can be performed. It is the most critical dependency for all downstream analysis.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads both GWTC-1 and GWTC-2 posterior sample files from the Zenodo repositories and produces a preprocessed CSV containing ≥100 merger events with mass_ratio, effective_spin, and component_mass attributes.

**Acceptance Scenarios**:

1. **Given** the Zenodo repository URLs for GWTC-1 and GWTC-2 are accessible, **When** the download script executes, **Then** the posterior sample files are saved to the local data directory with ≥95% file integrity checksum verification.
2. **Given** the raw posterior samples are downloaded, **When** the preprocessing script runs, **Then** the output CSV contains ≥100 valid merger events with non-null mass_ratio, effective_spin, and component_mass_1 values.
3. **Given** a corrupted or incomplete download, **When** the pipeline detects the integrity failure, **Then** the system retries up to 3 times before failing with an explicit error message identifying the affected file.

---

### User Story 2 - Compute statistical distributions and perform KS tests (Priority: P2)

As a researcher, I want to compute kernel density estimates for the observational and simulation datasets and apply Kolmogorov-Smirnov tests to compare the empirical cumulative distribution functions so that I can determine whether the distributions align or diverge.

**Why this priority**: This is the core scientific analysis that directly answers the research question. It depends on US-1 for data but can be tested independently once data is available.

**Independent Test**: Can be fully tested by running the statistical comparison module on the preprocessed data and verifying that the output includes KS test statistics and p-values for mass_ratio and effective_spin distributions.

**Acceptance Scenarios**:

1. **Given** the preprocessed observational and simulation datasets, **When** the KDE computation runs, **Then** 1D KDEs are generated for mass_ratio and effective_spin with bandwidth selected via Scott's rule or Silverman's rule.
2. **Given** the empirical cumulative distribution functions, **When** the KS test executes, **Then** the output includes a KS statistic and p-value for each parameter dimension (mass_ratio, effective_spin).
3. **Given** multiple hypothesis tests are performed (≥2 parameter dimensions), **When** the analysis completes, **Then** the output includes a family-wise error rate correction (e.g., Bonferroni-adjusted p-values) for the multiple-comparison problem.

---

### User Story 3 - Generate visualization report with divergence regions (Priority: P3)

As a researcher, I want to visualize the distributions and highlight regions where simulation-based population models diverge from GWTC observational posteriors so that I can document and communicate the statistical findings.

**Why this priority**: This provides the final deliverable for communication and interpretation but depends on US-1 and US-2 for data and analysis. It is the least critical for the core statistical validity.

**Independent Test**: Can be fully tested by running the visualization module and verifying that the output includes ≥2 plots (1D mass_ratio distribution, 1D effective_spin distribution) with annotated divergence regions.

**Acceptance Scenarios**:

1. **Given** the KDE and KS test results, **When** the visualization module executes, **Then** the output includes a 1D KDE plot for mass_ratio with simulation and observational distributions overlaid.
2. **Given** the KS test p-values, **When** the report is generated, **Then** regions where p < 0.05 are annotated as statistically significant divergence.
3. **Given** the full analysis pipeline completes, **When** the final report is saved, **Then** the report includes ≥2 figures saved as PNG files with resolution ≥300 DPI.

---

### Edge Cases

- What happens when a Zenodo repository URL becomes unavailable or returns a 404 error? → The pipeline retries up to 3 times with exponential backoff (1s, 2s, 4s delays) before failing with an explicit error message.
- How does the system handle posterior samples with missing or NaN values for key parameters? → Rows with NaN in mass_ratio, effective_spin, or component_mass are filtered out with a warning logged; the pipeline proceeds only if ≥50 valid events remain.
- What happens when the KS test returns a p-value exactly at the α=0.05 threshold? → The result is recorded as p=0.05 with an explicit note that this is a boundary case requiring sensitivity analysis at α ∈ {0.04, 0.05, 0.06}.
- How does the system handle simulation datasets with significantly smaller sample sizes than the observational catalog? → A power limitation is recorded in the output report, and the KS test proceeds with a note that Type II error risk is elevated for undersampled parameters.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download GWTC-1 posterior samples from Zenodo DOI 10.5281/zenodo.3966973 and GWTC-2 posterior samples from Zenodo DOI (See US-1)
- **FR-002**: System MUST download merger rate data from IllustrisTNG public release Zenodo DOI 10.5281/zenodo.3566863 (See US-1)
- **FR-003**: System MUST extract component masses, mass ratios, and effective spins from the posterior samples into a preprocessed CSV with ≥100 valid merger events (See US-1)
- **FR-004**: System MUST compute 1D kernel density estimates for mass_ratio and effective_spin using bandwidth selected via Scott's rule (See US-2)
- **FR-005**: System MUST apply the Kolmogorov-Smirnov test to compare empirical CDFs for at least 2 parameter dimensions (mass_ratio, effective_spin) (See US-2)
- **FR-006**: System MUST apply Bonferroni correction for multiple-comparison control when ≥2 hypothesis tests are performed (See US-2)
- **FR-007**: System MUST generate 1D KDE plots for mass_ratio and effective_spin with simulation and observational distributions overlaid (See US-3)
- **FR-008**: System MUST annotate regions where p < 0.05 as statistically significant divergence in the final report (See US-3)
- **FR-009**: System MUST perform sensitivity analysis on the α=0.05 threshold by sweeping α ∈ {0.04, 0.05, 0.06} and report how divergence rates vary (See US-2)
- **FR-010**: System MUST log a power limitation note when simulation dataset sample size is <50% of the observational catalog sample size (See US-2)

### Key Entities *(include if feature involves data)*

- **GWTC_Catalog**: Represents the observational gravitational-wave transient catalog; key attributes include event_id, component_mass_1, component_mass_2, mass_ratio, effective_spin, posterior_samples.
- **Simulation_Dataset**: Represents the merger population predictions from IllustrisTNG or EAGLE; key attributes include event_id, component_mass_1, component_mass_2, mass_ratio, effective_spin, formation_channel.
- **Statistical_Test_Result**: Represents the output of a KS test comparison; key attributes include parameter_name, ks_statistic, p_value, bonferroni_adjusted_p_value, significance_flag.
- **Visualization_Output**: Represents the generated plots and figures; key attributes include figure_id, parameter_name, format (PNG), resolution_dpi, file_path.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: KS test p-value for mass_ratio distribution is measured against the α=0.05 significance threshold (See US-2)
- **SC-002**: KS test p-value for effective_spin distribution is measured against the α=0.05 significance threshold (See US-2)
- **SC-003**: Family-wise error rate is measured against the Bonferroni-corrected α threshold (See US-2)
- **SC-004**: Computational runtime is measured against the 6-hour GitHub Actions free-tier limit (See US-1)
- **SC-005**: Memory usage is measured against the limited RAM constraint of the free-tier runner (See US-1)
- **SC-006**: Disk usage is measured against the disk constraint of the free-tier runner (See US-1)

---

## Assumptions

- The GWTC-1 and GWTC-2 posterior sample files are publicly accessible via the Zenodo repository URLs without requiring authentication.
- The IllustrisTNG merger rate data contains the necessary subgrid physics parameters for population prediction comparison; [NEEDS CLARIFICATION: does the IllustrisTNG release contain component mass and spin distributions for binary black hole mergers, or only galaxy/halo merger rates?]
- The observational posterior samples contain ≥100 valid merger events after filtering for NaN values and missing parameters.
- The Kolmogorov-Smirnov test is appropriate for the sample sizes available (n ≥ 30 per distribution) and the data is treated as independent and identically distributed within each catalog.
- The analysis is observational (no random assignment); therefore, all findings are framed as ASSOCIATIONAL comparisons rather than causal claims.
- The GitHub Actions free-tier runner provides ≥2 CPU cores and ≥7 GB RAM; the pipeline is designed to complete within 6 hours on this hardware.
- No GPU, CUDA, or hardware accelerators are required; all computations use CPU-tractable methods (scipy.stats, numpy, matplotlib).
- The Zenodo download rate limits allow completion of the data transfer within the 6-hour CI window; if rate-limited, the pipeline will queue retries rather than fail immediately.
- The posterior samples represent independent merger events; hierarchical Bayesian correlations between events are not modeled in this analysis.
- The sensitivity analysis on α thresholds (α ∈ {0.04, 0.05, 0.06}) is computationally trivial and will not exceed the 6-hour CI budget.
