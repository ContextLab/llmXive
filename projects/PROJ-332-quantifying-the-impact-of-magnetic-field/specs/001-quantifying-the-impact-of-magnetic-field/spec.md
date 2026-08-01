# Feature Specification: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Feature Branch**: `001-quantify-topology-confinement`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantify the impact of magnetic field topology on plasma confinement using DIII-D public archives."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1)

As a plasma physicist, I need to automatically retrieve up to 10 specific DIII-D discharge datasets (EFIT equilibria, pre-calculated topology metrics, and confinement time) from the public MDSplus archive and parse them into a unified analysis-ready format, so that I can begin the topological analysis without manual data handling.

**Why this priority**: This is the foundational step. Without clean, parsed data containing both magnetic topology metrics and confinement time, no correlation analysis can occur. It is the Minimum Viable Product (MVP) for the data ingestion layer.

**Independent Test**: The pipeline can be tested by running the retrieval script against the public MDSplus archive and verifying that a single CSV file is produced containing between 5 and 10 rows (discharges) with columns for `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `te_profile`, and `ne_profile`.

**Acceptance Scenarios**:

1. **Given** a list of 10 valid DIII-D discharge numbers, **When** the retrieval script is executed via the CI runner, **Then** the system downloads the corresponding EFIT, island, and tau_e files and parses them into a single structured dataset without manual intervention.
2. **Given** a discharge with missing island width data or missing tau_e data, **When** the retrieval script processes it, **Then** the system logs a warning and excludes that specific discharge from the final analysis dataset, ensuring the correlation step only receives valid data pairs.

---

### User Story 2 - Topological Metric Calculation (Priority: P2)

As a researcher, I need the system to calculate resonant surface densities from the parsed EFIT equilibrium data and retrieve pre-calculated magnetic island widths, so that I have the specific topological predictors required for the correlation study.

**Why this priority**: This transforms raw magnetic data into the specific scientific variables defined in the research question. It is the core scientific computation of the feature.

**Independent Test**: The calculation module can be tested by feeding it a provided reference CSV file containing known values for 3 test discharges and verifying that the output matches the expected values within a 5% tolerance.

**Acceptance Scenarios**:

1. **Given** a parsed EFIT equilibrium file, **When** the topology calculator runs, **Then** it outputs a numerical value for the density of resonant surfaces and retrieves the pre-calculated magnetic island width for the primary resonant surface (the lowest integer q value, e.g., q=2, that lies within the plasma minor radius).
2. **Given** an equilibrium where the pre-calculated island width is not available in the `islands` MDSplus tree, **When** the calculator runs, **Then** it flags the discharge as "missing topology data" and excludes it from the final dataset.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

As an analyst, I need the system to compute the Spearman rank correlation between the calculated topological metrics and energy confinement time, generate a scatter plot, and output the p-value, so that I can determine if the hypothesis is supported.

**Why this priority**: This delivers the final research result. While the previous stories provide data and metrics, this story answers the specific research question and produces the evidence required for the project's success.

**Independent Test**: The analysis module can be tested by running it on a small synthetic dataset with a known negative correlation and verifying that the output p-value is < 0.05 and the correlation coefficient matches the synthetic ground truth within statistical noise. Additionally, if the dataset contains known L-mode and H-mode discharges, the system must correctly identify the expected lower confinement in L-mode as a sanity check.

**Acceptance Scenarios**:

1. **Given** a dataset of 5-10 discharges with calculated topology metrics and confinement times, **When** the analysis script runs, **Then** it outputs a Spearman correlation coefficient and a p-value, and generates a `topology_vs_confinement.png` scatter plot.
2. **Given** a dataset where the correlation is statistically insignificant (p > 0.05) or does not meet the directional hypothesis (r > -0.5), **When** the analysis script runs, **Then** it explicitly flags the result as "Hypothesis not supported" in the summary report.

---

### Edge Cases

- What happens when the MDSplus archive is temporarily unreachable or returns a timeout error during the `wget` attempt? (System must retry 3 times with 10-second intervals before failing the job).
- How does the system handle discharges where the safety factor profile (q-profile) does not cross integer values (no resonant surfaces)? (The system must assign a default "zero" density and exclude from island-width specific metrics).
- How does the system handle a scenario where the retrieved island width exceeds the physical minor radius of the tokamak (indicating a reconstruction error)? (The system must flag the data point as an outlier and exclude it from the correlation calculation).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve up to 10 pre-reconstructed equilibrium (EFIT), island width, and confinement time datasets from the DIII-D public MDSplus archive using `wget` or equivalent HTTP client. The system MUST ensure a minimum of 5 valid discharges are available for analysis; if fewer than 5 valid datasets are retrieved, the pipeline MUST fail. (See US-1)
- **FR-002**: System MUST retrieve the pre-calculated magnetic island width from the DIII-D `islands` or `3d` MDSplus tree for the primary resonant surface (defined as the lowest integer q value, e.g., q=2, within the minor radius). If this data is missing, the discharge MUST be excluded. Additionally, the system MUST calculate the resonant surface density as the count of rational surfaces (q=m/n) per unit minor radius using the EFIT q-profile. (See US-2)
- **FR-003**: System MUST retrieve the pre-calculated energy confinement time ($\tau_E$) from the DIII-D `taue` MDSplus tree or derived fields (`W_MHD`/`P_input`). If pre-calculated values are missing, the discharge MUST be excluded. (See US-1)
- **FR-004**: System MUST compute the Spearman rank correlation coefficient between the calculated topological metrics (island width, resonant surface density) and the energy confinement time. (See US-3)
- **FR-005**: System MUST perform bootstrap resampling with exactly 1000 iterations to estimate 95% confidence intervals for the calculated correlation coefficients. (See US-3)
- **FR-006**: System MUST generate a diagnostic scatter plot (topology metric vs. confinement time) using `matplotlib` and save it as a PNG file. (See US-3)
- **FR-007**: System MUST enforce a strict execution time limit of 6 hours and memory limit of 7 GB RAM on the CI runner, aborting the entire pipeline immediately if any single operation exceeds these bounds. (See US-1)

### Key Entities

- **Discharge**: A single tokamak shot containing time-series data for magnetic equilibrium and plasma profiles.
- **TopologicalMetric**: A derived scalar value representing magnetic island width (retrieved) or resonant surface density (calculated) for a specific discharge.
- **ConfinementTime**: A derived scalar value ($\tau_E$) representing the energy confinement time for a specific discharge (retrieved).
- **CorrelationResult**: A structured object containing the Spearman coefficient, p-value, and confidence intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The correlation coefficient between magnetic island width and energy confinement time is measured against the directional hypothesis threshold of r < -0.5 to determine if the degradation hypothesis is supported. (See US-3)
- **SC-002**: The p-value of the correlation test is measured against the significance level of 0.05 to validate the statistical rejection of the null hypothesis. (See US-3)
- **SC-003**: The total execution time of the data retrieval, parsing, and analysis pipeline is measured against the 6-hour CI runner limit to ensure compute feasibility. (See US-1)
- **SC-004**: The memory footprint of the analysis process is measured against the 7 GB RAM limit to ensure the dataset fits within the free-tier runner constraints. (See US-1)
- **SC-005**: The magnitude of the effect size (|r|) is reported for all valid datasets, regardless of statistical significance, to assess the strength of the relationship. (See US-3)

## Assumptions

- The DIII-D public MDSplus archive is accessible via standard HTTP/HTTPS protocols without requiring authentication credentials beyond public read access.
- The selected discharges contain valid EFIT reconstructions and pre-calculated island width and tau_e data in the MDSplus archive; if a discharge lacks one, it is excluded rather than causing a pipeline failure.
- The "magnetic island width" is available as a pre-calculated metric in the `islands` MDSplus tree for the selected discharges; if not, the discharge is excluded to avoid physical impossibilities.
- The relationship between topology and confinement in this dataset is purely associational; no causal claims are made, and no randomization is assumed.
- The free-tier GitHub Actions runner (2 CPU, ~7 GB RAM) is sufficient to process 5-10 discharges and perform 1000 bootstrap iterations within the 6-hour window.
- The `wget` tool and Python scientific stack (`numpy`, `scipy`, `matplotlib`) are pre-installed and available in the CI environment.