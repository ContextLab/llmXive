# Feature Specification: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Feature Branch**: `001-quantify-topology-confinement`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Quantify the impact of magnetic field topology on plasma confinement using DIII-D public archives."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1)

As a plasma physicist, I need to automatically retrieve 10 specific DIII-D discharge datasets (EFIT equilibria and Thomson scattering profiles) and parse them into a unified analysis-ready format, so that I can begin the topological analysis without manual data handling.

**Why this priority**: This is the foundational step. Without clean, parsed data containing both magnetic topology metrics and confinement time, no correlation analysis can occur. It is the Minimum Viable Product (MVP) for the data ingestion layer.

**Independent Test**: The pipeline can be tested by running the retrieval script against the public MDSplus archive and verifying that a single CSV file is produced containing 10 rows (discharges) with columns for `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `te_profile`, and `ne_profile`.

**Acceptance Scenarios**:

1. **Given** a list of 10 valid DIII-D discharge numbers, **When** the retrieval script is executed via the CI runner, **Then** the system downloads the corresponding EFIT and Thomson scattering files and parses them into a single structured dataset without manual intervention.
2. **Given** a discharge with missing Thomson scattering data, **When** the retrieval script processes it, **Then** the system logs a warning and excludes that specific discharge from the final analysis dataset, ensuring the correlation step only receives valid data pairs.

---

### User Story 2 - Topological Metric Calculation (Priority: P2)

As a researcher, I need the system to calculate magnetic island widths and resonant surface densities from the parsed EFIT equilibrium data, so that I have the specific topological predictors required for the correlation study.

**Why this priority**: This transforms raw magnetic data into the specific scientific variables defined in the research question. It is the core scientific computation of the feature.

**Independent Test**: The calculation module can be tested by feeding it a known EFIT file with a manually verified island width and verifying that the output matches the expected value within a 5% tolerance.

**Acceptance Scenarios**:

1. **Given** a parsed EFIT equilibrium file, **When** the topology calculator runs, **Then** it outputs a numerical value for the magnetic island width at the primary resonant surface (q=2 or q=3) and the density of resonant surfaces.
2. **Given** an equilibrium with no distinct magnetic islands detected, **When** the calculator runs, **Then** it outputs a zero or negligible value for island width and flags the discharge as "low-topology" for downstream filtering.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

As an analyst, I need the system to compute the Spearman rank correlation between the calculated topological metrics and energy confinement time, generate a scatter plot, and output the p-value, so that I can determine if the hypothesis is supported.

**Why this priority**: This delivers the final research result. While the previous stories provide data and metrics, this story answers the specific research question and produces the evidence required for the project's success.

**Independent Test**: The analysis module can be tested by running it on a small synthetic dataset with a known negative correlation and verifying that the output p-value is < 0.05 and the correlation coefficient matches the synthetic ground truth within statistical noise.

**Acceptance Scenarios**:

1. **Given** a dataset of 10 discharges with calculated topology metrics and confinement times, **When** the analysis script runs, **Then** it outputs a Spearman correlation coefficient and a p-value, and generates a `topology_vs_confinement.png` scatter plot.
2. **Given** a dataset where the correlation is statistically insignificant (p > 0.05), **When** the analysis script runs, **Then** it explicitly flags the result as "No significant correlation found" in the summary report.

---

### Edge Cases

- What happens when the MDSplus archive is temporarily unreachable or returns a timeout error during the `wget` attempt? (System must retry 3 times with 10-second intervals before failing the job).
- How does the system handle discharges where the safety factor profile (q-profile) does not cross integer values (no resonant surfaces)? (The system must assign a default "zero" density and exclude from island-width specific metrics).
- How does the system handle a scenario where the calculated island width exceeds the physical minor radius of the tokamak (indicating a reconstruction error)? (The system must flag the data point as an outlier and exclude it from the correlation calculation).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve exactly 10 pre-reconstructed equilibrium (EFIT) and Thomson scattering profile datasets from the DIII-D public MDSplus archive using `wget` or equivalent HTTP client. (See US-1)
- **FR-002**: System MUST parse the downloaded equilibrium data to calculate the magnetic island width at the primary resonant surface and the density of resonant surfaces using Python libraries (e.g., `numpy`, `scipy`). (See US-2)
- **FR-003**: System MUST extract electron temperature and density profiles to compute the energy confinement time ($\tau_E$) for each discharge. (See US-2)
- **FR-004**: System MUST compute the Spearman rank correlation coefficient between the calculated topological metrics (island width, resonant surface density) and the energy confinement time. (See US-3)
- **FR-005**: System MUST perform bootstrap resampling with exactly 1000 iterations to estimate 95% confidence intervals for the calculated correlation coefficients. (See US-3)
- **FR-006**: System MUST generate a diagnostic scatter plot (topology metric vs. confinement time) using `matplotlib` and save it as a PNG file. (See US-3)
- **FR-007**: System MUST enforce a strict execution time limit of 6 hours and memory limit of 7 GB RAM on the CI runner, aborting any operation that exceeds these bounds. (See US-1)

### Key Entities

- **Discharge**: A single tokamak shot containing time-series data for magnetic equilibrium and plasma profiles.
- **TopologicalMetric**: A derived scalar value representing magnetic island width or resonant surface density for a specific discharge.
- **ConfinementTime**: A derived scalar value ($\tau_E$) representing the energy confinement time for a specific discharge.
- **CorrelationResult**: A structured object containing the Spearman coefficient, p-value, and confidence intervals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The correlation coefficient between magnetic island density and energy confinement time is measured against the hypothesis threshold of > 0.5 (in magnitude) to determine statistical significance. (See US-3)
- **SC-002**: The p-value of the correlation test is measured against the significance level of 0.05 to validate the rejection of the null hypothesis. (See US-3)
- **SC-003**: The total execution time of the data retrieval, parsing, and analysis pipeline is measured against the 6-hour CI runner limit to ensure compute feasibility. (See US-1)
- **SC-004**: The memory footprint of the analysis process is measured against the 7 GB RAM limit to ensure the dataset fits within the free-tier runner constraints. (See US-1)

## Assumptions

- The DIII-D public MDSplus archive is accessible via standard HTTP/HTTPS protocols without requiring authentication credentials beyond public read access.
- The 10 selected discharges contain valid EFIT reconstructions and Thomson scattering data; if a discharge lacks one, it is excluded rather than causing a pipeline failure.
- The "magnetic island width" can be reliably estimated from the EFIT q-profile and magnetic shear without running a full, computationally expensive MHD stability solver.
- The relationship between topology and confinement in this dataset is purely associational; no causal claims are made, and no randomization is assumed.
- The free-tier GitHub Actions runner (2 CPU, ~7 GB RAM) is sufficient to process 10 discharges and perform 1000 bootstrap iterations within the 6-hour window.
- The `wget` tool and Python scientific stack (`numpy`, `scipy`, `matplotlib`) are pre-installed and available in the CI environment.
