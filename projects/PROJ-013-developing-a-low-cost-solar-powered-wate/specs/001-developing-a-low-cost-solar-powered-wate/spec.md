# Feature Specification: Developing a Low-Cost Solar-Powered Water Purification System

**Feature Branch**: `001-solar-purification-tradeoff`  
**Created**: 2026-07-27  
**Status**: Draft  
**Input**: User description: "Developing a Low-Cost Solar-Powered Water Purification System"

## User Scenarios & Testing

### User Story 1 - Data Retrieval and Cost Function Construction (Priority: P1)

The system must retrieve thermal properties (conductivity, emissivity, specific heat) for a defined set of low-cost materials (aluminum, copper, black-painted steel, plastic) from NIST databases and scrape current market prices to construct a deterministic cost function $C = \sum (mass_i \times price_i)$.

**Why this priority**: Without accurate material data and a defined cost model, no simulation or optimization can proceed. This is the foundational data layer required for all subsequent physics calculations.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying that the output CSV contains a representative set of material-geometry combinations with non-null thermal properties and valid positive cost values derived from the latest scraped market prices.

**Acceptance Scenarios**:

1. **Given** the NIST Chemistry WebBook and a public market price API are accessible, **When** the ingestion script runs, **Then** the output file contains thermal conductivity, emissivity, and specific heat for at least 4 distinct materials with no missing values.
2. **Given** market price data is retrieved, **When** the cost function is calculated for a specific geometry, **Then** the total cost is a positive scalar value in USD, calculated strictly as the sum of (mass × price) for all components.

---

### User Story 2 - 1D Transient Heat Transfer Simulation (Priority: P1)

The system must implement a 1D transient heat transfer model in Python using `scipy.integrate` to simulate the thermal dynamics of three specific still geometries (flat-plate, single-slope, double-slope) under solar irradiance profiles from the NASA POWER API. The model assumes uniform cross-section and models slope variations via effective projected area. The system calculates the time-averaged thermal efficiency ($\eta$) over a designated final period of the simulation to approximate quasi-steady state performance.

**Why this priority**: This is the core scientific engine that answers the research question. It transforms the static material data into dynamic performance metrics ($\eta$) required for the trade-off analysis.

**Independent Test**: Can be fully tested by running the simulation with a fixed set of inputs (e.g., Aluminum, single-slope) and verifying that the output efficiency $\eta$ falls within the physically plausible range of 0.0 to 0.8, and that the simulation completes within 60 seconds on a standard CPU.

**Acceptance Scenarios**:

1. **Given** valid material properties and a solar irradiance profile, **When** the simulation runs for the single-slope geometry, **Then** the calculated time-averaged thermal efficiency $\eta$ (final interval) is a float between 0.0 and 0.8.
2. **Given** the same inputs, **When** the simulation runs for the double-slope geometry, **Then** the resulting efficiency differs from the flat-plate result by a non-zero margin, demonstrating geometry sensitivity.
3. **Given** a standard GitHub Actions runner (2 CPU, 7GB RAM), **When** the full batch of 20 simulations is executed, **Then** the total runtime remains within an acceptable duration for iterative experimentation..

---

### User Story 3 - Pareto Frontier Optimization and Visualization (Priority: P2)

The system must perform a multi-objective optimization to identify the Pareto frontier of efficiency ($\eta$) vs. cost ($C$) and generate a scatter plot highlighting the "knee point". The knee point is defined mathematically as the point on the Pareto frontier that minimizes the Euclidean distance to the ideal point (max efficiency, min cost).

**Why this priority**: This delivers the primary research output: the visual and quantitative identification of the optimal design trade-off, directly addressing the literature gap.

**Independent Test**: Can be fully tested by executing the optimization script and verifying that the generated plot contains a representative set of data points, a clearly highlighted Pareto frontier subset, and a marked "knee point" that represents a non-dominated solution.

**Acceptance Scenarios**:

1. **Given** the matrix of (Efficiency, Cost) pairs, **When** the optimization algorithm runs, **Then** the output identifies a subset of non-dominated solutions forming the Pareto frontier.
2. **Given** the Pareto frontier, **When** the knee point is calculated (minimizing distance to ideal point), **Then** the plot explicitly marks this point and reports its coordinates (Efficiency, Cost).
3. **Given** the visualization, **When** a user inspects the plot, **Then** the curve clearly demonstrates the trade-off relationship (e.g., diminishing returns) rather than a linear or random scatter.

---

### Edge Cases

- What happens if the NASA POWER API returns missing or zero irradiance data for a specific date/location? (System must default to a representative average or raise a specific error).
- How does the system handle a material price that is unavailable or zero in the scraped data? (System must exclude that material from the simulation or flag it as invalid).
- What occurs if the heat transfer simulation fails to converge for a specific geometry-material combination? (System must log the failure, exclude the point, and continue with the remaining valid combinations).

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve thermal conductivity, specific heat, and emissivity for at least 4 low-cost materials from the NIST Chemistry WebBook or equivalent verified engineering handbook. (See US-1)
- **FR-002**: System MUST construct a cost function $C$ for each design by summing the product of component mass and current market price, ensuring all costs are strictly positive. (See US-1)
- **FR-003**: System MUST simulate 1D transient heat transfer for three distinct geometries (flat-plate, single-slope, double-slope) using `scipy.integrate` under solar irradiance boundary conditions, modeling slope variations via effective projected area. (See US-2)
- **FR-004**: System MUST calculate time-averaged thermal efficiency $\eta$ over the final 30 minutes of the transient simulation for every valid material-geometry combination without requiring GPU acceleration. (See US-2)
- **FR-005**: System MUST identify the Pareto frontier of $\eta$ vs. $C$ and mark the "knee point" defined as the point on the frontier minimizing the Euclidean distance to the ideal point (max $\eta$, min $C$). (See US-3)
- **FR-006**: System MUST validate simulation outputs by ensuring the calculated efficiency $\eta$ falls within ±10% of the mean efficiency (0.45) reported in standard passive solar still literature (Ref: Duffie & Beckman, "Solar Engineering of Thermal Processes", 2020). (See US-2)
- **FR-007**: System MUST generate a scatter plot of efficiency vs. cost with the Pareto frontier highlighted, suitable for publication-quality export. (See US-3)

### Key Entities

- **MaterialProfile**: Represents a construction material with attributes: thermal conductivity (W/m·K), emissivity (0-1), specific heat (J/kg·K), density (kg/m³), and unit price (USD/kg).
- **GeometryConfig**: Represents a still design with attributes: type (flat-plate, single-slope, double-slope), inclination angle (degrees), and surface area (m²).
- **SimulationResult**: Represents the output of a run with attributes: material_id, geometry_id, steady_state_efficiency ($\eta$), total_cost ($C$), and convergence_status.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The number of valid (Efficiency, Cost) data points generated is measured against the target of a diverse set of material-geometry combinations. (See FR-004)
- **SC-002**: The physical plausibility of the simulation is measured by verifying that $\eta$ falls within an acceptable range consistent with passive solar still performance in standard literature. (See FR-006)
- **SC-003**: The identification of the Pareto frontier is measured by the presence of a distinct "knee point" on the generated plot, where the coefficient of determination ($R^2$) of a linear fit to the frontier points is < 0.95. (See FR-005)
- **SC-004**: The computational feasibility is measured by the total runtime of the simulation batch, which must not exceed a practical threshold on a CPU-only runner. (See FR-004)
- **SC-005**: The reproducibility of the data pipeline is measured by the successful execution of the full script from raw API calls to final plot generation without manual intervention. (See US-1, US-2, US-3)

## Assumptions

- The NIST Chemistry WebBook and NASA POWER API are accessible without authentication or with standard public access keys during the CI run.
- The "low-cost" materials (aluminum, copper, black-painted steel, plastic) are sufficiently represented by the data available in standard engineering handbooks for the purpose of this comparative study.
- The solar irradiance profiles from NASA POWER for Sub-Saharan Africa are representative of the target deployment region and sufficient for a steady-state efficiency approximation.
- The 1D transient heat transfer model is a valid approximation for the system geometry, ignoring 2D/3D edge effects which are assumed to be negligible for the comparative optimization. Slope geometries are modeled via effective projected area.
- The GitHub Actions free-tier runner (multi-core CPU, sufficient RAM) provides sufficient memory to hold the simulation matrices and Python environment without swapping.
- Market prices for construction materials are assumed to be static for the duration of the study, derived from the most recent public scrape.
- The "knee point" on the Pareto frontier is mathematically identifiable using the distance-to-ideal-point heuristic, as no specific algorithm was mandated in the idea.