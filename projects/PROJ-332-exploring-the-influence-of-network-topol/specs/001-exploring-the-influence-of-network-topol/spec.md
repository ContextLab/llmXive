# Feature Specification: Influence of Network Topology on Thermal Conductivity in Nanomaterials

**Feature Branch**: `001-network-topology-thermal`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description:  
> How does the connectivity distribution of randomly assembled nanowire networks modulate effective thermal conductivity?  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Generate Topology‑Specific Nanowire Networks (Priority: P1)

A researcher wants to create synthetic nanowire network graphs with a prescribed average node degree (or connection probability) and obtain the corresponding effective thermal conductivity.

**Why this priority**: This is the core data‑generation step; without reliable networks the downstream analysis cannot proceed.

**Independent Test**: Run the generator for a single target degree (e.g., 4) and verify that the produced graph’s measured average degree is within ±5 % of the target and that an effective conductivity value is produced.

**Acceptance Scenarios**:

1. **Given** a request for a graph with 1 000 nodes and target average degree = 4, **When** the system generates the graph, **Then** the measured average degree is 3.8 – 4.2 and a conductivity estimate is produced.  
2. **Given** an invalid target degree (e.g., negative or > N‑1), **When** the request is submitted, **Then** the system raises a clear validation error.

---

### User Story 2 – Quantify Scaling Between Topology and Conductivity (Priority: P2)

A researcher wants to fit a scaling law between graph‑theoretic metrics (average degree, average path length, clustering coefficient) and the effective thermal conductivity, identify a percolation threshold, and report statistical significance after correcting for multiple comparisons.

**Why this priority**: This delivers the scientific insight required to answer the research question.

**Independent Test**: Execute the full pipeline on a small parameter grid (e.g., 5 connectivity levels, 20 simulations each) and verify that regression outputs include calculated scaling exponents, confidence intervals, and p-values, and that the system correctly reports the correlation matrix of the metrics.

**Acceptance Scenarios**:

1. **Given** simulation results across connectivity levels, **When** the regression module runs, **Then** it returns scaling exponents, confidence intervals, and p-values for the primary metric (average degree), along with a correlation matrix of all metrics.  
2. **Given** a set of results where all mean degrees are below the percolation threshold, **When** the regression runs, **Then** it reports “no significant scaling detected” without error.

---

### User Story 3 – Perform Sensitivity & Robustness Checks (Priority: P3)

A researcher wants to assess how sensitive the conductivity estimates are to the assumed thermal‑resistor parameters and to the chosen percolation‑threshold cutoff, and obtain a concise report.

**Why this priority**: Sensitivity analysis safeguards against over‑interpretation of results and satisfies methodological soundness requirements.

**Independent Test**: Run the sensitivity sweep over the resistor scaling factor {0.9, 1.0, 1.1} and verify that reported conductivity variations stay within ±10 % and that the final report lists the observed range.

**Acceptance Scenarios**:

1. **Given** a completed set of simulations, **When** the sensitivity module is invoked, **Then** it produces a table showing conductivity for each scaling factor and confirms that the maximum deviation is ≤ 10 %.  
2. **Given** missing material‑property inputs, **When** the sensitivity module starts, **Then** it aborts with a clear error message indicating the missing material.

---

### Edge Cases

- **Disconnected Graph**: If the generated graph is disconnected (no path between source and sink nodes), the system MUST return an effective conductivity of zero. and log a warning "Graph disconnected; conductivity set to 0.0". This graph is excluded from regression analysis.
- **Zero-Resistance Edge**: If an edge resistance is calculated as zero (infinite conductivity), the system MUST clamp the resistance to a minimum non-zero value. to prevent division-by-zero errors in the solver.
- **Missing Material Properties**: If the material database lacks a requested value, the system MUST default to the NIST standard value for standard materials (Si, CNT, Ag, Au) as defined in FR-010. For non-standard materials, the system MUST raise a clear error unless a value is provided via the CLI argument defined in FR-016.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate random geometric graphs with user‑specified node count *N* (default 1000) and target average degree using a fixed spatial domain size of 10 µm × 10 µm. The connection probability *p* is derived from the target average degree and domain size using the standard RGG formula for a fixed area. If the user provides *p*, the system MUST convert it to the equivalent target average degree using the fixed domain size. *(See US-1)*
- **FR-002**: The system MUST assign a thermal resistance to each edge based on the material’s bulk thermal conductivity (adjusted by a size-correction factor for d < 100nm using the Fuchs-Sondheimer model with parameters p=0.5, lambda=40nm), and a user‑provided wire diameter *d* (default 50 nm) and length *ℓ* (R_wire = ℓ/(k_eff·A), where A = π(d/2)²). The total edge resistance MUST include a series junction resistance component as defined in FR-012. *(See US-1)*
- **FR-003**: The system MUST solve the linear Kirchhoff heat‑flow equations for the network to obtain the effective thermal conductivity between the two designated boundary nodes defined in FR-013. Convergence is achieved when the residual norm (L2) ≤ 1e‑6. If the graph is disconnected, the system MUST return 0.0 W/(m·K) without attempting the solve. *(See US-1)*
- **FR-004**: The system MUST compute the following graph‑theoretic metrics for every generated network: average degree, average shortest‑path length (set to infinity if disconnected), and clustering coefficient. For disconnected graphs, the average shortest-path length MUST be set to infinity and excluded from the correlation matrix calculation in FR-006. *(See US-2)*
- **FR-005**: The system MUST perform a power-law regression on the subset of connected graphs (k_eff > 0) using the model: k_eff = A * (<k> - <k>_c)^t. The system MUST output the scaling exponent *t*, 95 % confidence intervals, and p-values. This regression MUST exclude all graphs where k_eff = 0.0 (disconnected). The regression serves to validate the solver's numerical stability and characterize the synthetic relationship, not to discover novel empirical laws. *(See US-2)*
- **FR-006**: The system MUST report the Pearson correlation matrix of all computed metrics (average degree, path length, clustering) to demonstrate their collinearity, and MUST use average degree as the primary metric for regression to avoid multiple-comparison issues. *(See US-2)*
- **FR-007**: The system MUST conduct a sensitivity analysis by sweeping the edge‑resistance scaling factor over a range of values near unity (applied to both wire and junction resistance) and report the resulting conductivity range. *(See US-3)*
- **FR-008**: The system MUST enforce a total runtime ceiling of 6 hours on a 2‑CPU‑core, ≤ 7 GB RAM CI runner for the default grid (100 simulations × 10 connectivity levels); if exceeded, the job aborts with a timeout error as enforced by the watchdog process in FR-015. *(See US-1)*
- **FR-009**: The system MUST log all simulation parameters (graph seed, *N*, *p*, material k, d, ℓ, scaling factor, percolation_threshold, convergence_rate, total_runtime) and results to a CSV file at `data/processed/simulation_results.csv` for reproducibility. The CSV MUST include columns: `seed`, `N`, `p`, `avg_degree`, `percolation_threshold`, `convergence_rate`, `total_runtime`, `k_eff`, `scaling_exponent_t`, `p_value`. *(See US-1, US-2)*
- **FR-010**: The system MUST validate that required material thermal‑conductivity values are present in the local data store. If a required value for a standard material (Si, CNT, Ag, Au) is absent, the system MUST default to the NIST standard value at 300K: Silicon = 149 W/(m·K), Carbon Nanotube = 3500 W/(m·K), Silver = 429 W/(m·K), Gold = 318 W/(m·K). If a non-standard material is requested, the system MUST raise a clear error unless a value is provided via the CLI argument `--material-override <name>=<value>` defined in FR-016. *(See Edge Cases)*
- **FR-011**: The system MUST apply a size-correction factor (Fuchs-Sondheimer model) to bulk thermal conductivity values when calculating edge resistances for nanowires with diameter *d* < 100nm to ensure physical validity in the nanoscale regime. *(See US-1)*
- **FR-012**: The system MUST model junction (Kapitza) resistance as a series component to the wire resistance. The default junction resistance MUST be K·m²/W. The system MUST perform a sensitivity sweep on this parameter over a representative range of low thermal conductance values. *(See US-1)*
- **FR-013**: The system MUST select source and sink nodes as follows: source = node with minimum x-coordinate (if ties, select node with maximum y-coordinate); sink = node with maximum x-coordinate (if ties, select node with minimum y-coordinate). *(See US-1)*
- **FR-014**: The system MUST use a fixed spatial domain size for all graph generation. Node density is therefore fixed at 10 nodes/µm² for N=1000. *(See US-1)*
- **FR-015**: The system MUST include a watchdog process in the CI pipeline to enforce a bounded runtime ceiling. If the timeout is hit, the watchdog MUST terminate the job and log the exit code and duration to the CSV file. *(See US-1)*
- **FR-016**: The system MUST accept non-standard material values via a CLI argument `--material-override <name>=<value>`, where `<value>` is a floating-point number representing the thermal conductivity in W/(m·K). *(See US-1)*
- **FR-017**: The system MUST estimate the percolation threshold using linear interpolation on the sorted (average_degree, connectivity_probability) data to find the degree where P(connected) = 0.80. If P=0.80 is not in the range, the system MUST report the closest value and a warning. *(See US-2)*

### Key Entities

- **NetworkGraph**: Represents a synthetic nanowire assembly; attributes include node list, edge list, and computed metrics.
- **ThermalResistorModel**: Encapsulates the mapping from graph edges to thermal resistances based on material properties and geometry.
- **SimulationResult**: Stores effective conductivity, regression outputs, and sensitivity‑analysis summaries for a given parameter set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For ≥ 95 % of generated graphs, the measured average degree must be within ±5 % of the user‑specified target. *(See US-1)*
- **SC-002**: The heat‑flow solver must achieve convergence (residual ≤ 1e‑6) for ≥ 99 % of simulations. *(See US-1)*
- **SC-003**: The system MUST correctly calculate the percolation threshold (defined as the smallest average degree where ≥ 80% of graphs are connected, estimated via linear interpolation as per FR-017) and report a statistically significant scaling exponent *t* (p < 0.05) for the average degree metric when the mean degree exceeds this calculated threshold, using the model k_eff ∝ (<k> - <k>_c)^t. This calculation MUST be performed only on the subset of connected graphs (k_eff > 0). *(See US-2)*
- **SC-004**: The sensitivity sweep must show that conductivity variation across the scaling‑factor set {0.9, 1.0, 1.1} does not exceed ±10 % of the baseline (1.0) estimate. *(See US-3)*
- **SC-005**: The complete pipeline (graph generation, solver, regression, sensitivity) must finish within 6 hours on the CI runner for the default grid (100 simulations × 10 connectivity levels, ranging from p=0.01 to p=0.10 in steps of 0.01), as measured by the CI watchdog process in FR-015. *(See US-1)*

## Assumptions

- The CI environment provides **CPU cores**, **≈ 7 GB RAM**, **≈ 14 GB disk**, and **no GPU**. All code must run in pure‑CPU mode.
- Material thermal conductivities are taken from publicly available NIST tables. For standard materials (Si, CNT, Ag, Au), if a value is missing from the local store, the system defaults to the NIST standard value at 300K (Si=149, CNT=3500, Ag=429, Au=318 W/(m·K)). For non-standard materials, the user must provide a value via the CLI argument defined in FR-016.
- Wire geometry is approximated as cylinders with a **default** diameter *d* = 50 nm and length *ℓ* = 1 µm unless the user overrides them via FR-002. This default follows standard nanowire‑fabrication literature, but the system accepts user-provided values.
- The percolation threshold is operationally defined as the smallest average degree at which ≥ 80 % of generated graphs yield a finite effective conductivity (i.e., a connected source‑sink path), estimated via linear interpolation. This definition is a practical metric for the specific N=1000 simulation size and is not a universal physical constant.
- All random processes are seeded for reproducibility; the seed is logged in the CSV output.  
- No external GPU‑accelerated libraries (e.g., CUDA, bitsandbytes) are used; all numerical linear algebra relies on NumPy / SciPy which are CPU‑compatible.  
- The analysis treats the relationship between topology and conductivity as **associational**; causal claims are avoided because the data are synthetic and no random assignment of physical parameters occurs.  
- A bounded runtime limit and 100x10 grid size are defined as necessary feasibility constraints for the CI environment; larger grids are subject to user-defined timeouts.
- The node count is fixed at N=1000 for all simulations to ensure consistent scaling analysis.