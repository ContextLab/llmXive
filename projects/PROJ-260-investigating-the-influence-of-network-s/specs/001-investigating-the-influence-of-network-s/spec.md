# Feature Specification: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Feature Branch**: `001-investigate-network-heat-conduction`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Network Topology Extraction (Priority: P1)

**Description**: The researcher uploads or points the system to a pre-computed molecular dynamics (MD) trajectory file (e.g., from Materials Cloud or Zenodo). The system parses atomic coordinates, constructs a bond network based on the first minimum of the radial distribution function (RDF), and computes local graph-theoretic metrics (coordination number, bond angle variance) for every atom.

**Why this priority**: This is the foundational step. Without a correctly parsed network and computed topological metrics, no correlation analysis can occur. It validates the "predictor" variable extraction.

**Independent Test**: The system can process a single, small amorphous silicon trajectory file and output a CSV containing atomic IDs, coordination numbers, and local bond angle variance without requiring thermal conductivity data or VDOS calculation.

**Acceptance Scenarios**:
1. **Given** a valid MD trajectory file of amorphous silicon (Reference: Materials Cloud ID: aSi-2023-Ref), **When** the user triggers the "Extract Topology" function, **Then** the system outputs a CSV where every atom has a coordination number ≥ 1 and ≤ 6. If any atom has a coordination > 6, the system flags a "Physical Anomaly" but does not halt. The average coordination number must match the reference value (4.00) with an absolute difference ≤ 0.05.
2. **Given** a trajectory file with a missing or corrupted header, **When** the user triggers extraction, **Then** the system halts and returns a specific error code indicating "Invalid File Format" rather than crashing or producing NaN values.
3. **Given** a trajectory with a known RDF minimum at 2.5 Å, **When** the bond network is constructed, **Then** the system uses a cutoff distance of 2.5 Å ± 0.1 Å to define bonds, and the resulting network density matches the density value found in the input file's header metadata.

---

### User Story 2 - Vibrational Mode Analysis and Bottleneck Identification (Priority: P2)

**Description**: The system calculates the Vibrational Density of States (VDOS) via velocity autocorrelation functions and computes the participation ratio to identify localized vibrational modes. It aggregates these into a "density of localized modes" metric per simulation box and identifies "topological bottlenecks" (under-coordinated regions).

**Why this priority**: This extracts the "outcome" variables (localized modes, bottlenecks) required to test the research hypothesis. It depends on the successful completion of User Story 1.

**Independent Test**: The system can take the output of User Story 1 (network topology) and a velocity dump, compute the VDOS, and output a scalar value representing the "density of localized modes" for that specific simulation box.

**Acceptance Scenarios**:
1. **Given** a velocity dump file and a corresponding network topology, **When** the VDOS is calculated, **Then** the resulting spectrum shows a non-zero density in the low-frequency range (acoustic modes) and a distinct peak in the high-frequency range (10.0–15.0 THz) consistent with the reference dataset (Materials Cloud ID: aSi-VDOS-Ref).
2. **Given** a simulation box with a known cluster of under-coordinated atoms (coordination < 3), **When** the bottleneck density is calculated, **Then** the system flags this region. The system MUST also perform a sensitivity analysis by sweeping the under-coordination threshold by ±0.5 and report the stability of the bottleneck density metric (coefficient of variation < 0.1).
3. **Given** a system where all atoms are perfectly coordinated, **When** the localized mode density is calculated, **Then** the participation ratio indicates a lower density of localized modes compared to a disordered system of the same size.

---

### User Story 3 - Statistical Correlation and Robustness Validation (Priority: P3)

**Description**: The system aggregates the topological metrics and bottleneck densities with pre-recorded thermal conductivity values from an *independent* source. It performs Spearman and Pearson correlation analyses across at least three distinct system sizes (e.g., N=1000, N=2000, N=4000) and reports the correlation coefficients with significance testing using Bootstrap Resampling.

**Why this priority**: This delivers the final research answer (the correlation) and validates the finding against the "finite-size effects" requirement. It is the culmination of the pipeline.

**Independent Test**: The system can ingest three datasets with distinct system sizes and pre-computed topology, run the correlation analysis, and output a summary table showing the correlation coefficient, p-value, and 95% confidence interval for each dataset.

**Acceptance Scenarios**:
1. **Given** three datasets of varying sizes (e.g., 1000, 2000, 4000 atoms) with known thermal conductivities from independent sources, **When** the correlation analysis is run, **Then** the system outputs the Spearman correlation coefficient and a 95% confidence interval derived from 1000 bootstrap iterations. The system verifies the calculation accuracy by comparing the output to a manual calculation (|output - manual| < 1e-6).
2. **Given** a dataset where the topological metrics are randomized, **When** the correlation is run, **Then** the system reports a correlation coefficient near 0 (|r| < 0.1) and a p-value > 0.5, confirming the signal is not random.
3. **Given** a scenario where the sample size is insufficient for standard significance testing, **When** the analysis runs, **Then** the system flags a "Low Power" warning and reports the calculated statistical power (or notes it as a limitation) but does not fail the test.

### Edge Cases

- **What happens when** the RDF minimum is ambiguous (e.g., in highly disordered systems with a broad first peak)? The system must default to the first local minimum or allow a user-specified override, but must log the decision.
- **How does the system handle** MD trajectories with missing velocity data? The system must fail gracefully for the VDOS calculation step but allow the topology extraction (User Story 1) to proceed.
- **What happens when** the dataset contains only one system size, making finite-size validation impossible? The system must flag this as a limitation in the output report rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse atomic coordinates from standard MD trajectory formats (e.g., LAMMPS dump, XYZ) and construct a bond network using a distance cutoff derived from the first minimum of the radial distribution function (See US-1).
- **FR-002**: System MUST compute local graph-theoretic metrics (coordination number, bond angle variance) for every atom in the network and aggregate them into global topology descriptors (See US-1).
- **FR-003**: System MUST calculate the Vibrational Density of States (VDOS) via velocity autocorrelation functions and derive the participation ratio to quantify the density of localized vibrational modes (See US-2).
- **FR-004**: System MUST identify and quantify "topological bottlenecks" (regions with under-coordinated atoms, e.g., coordination < 3) and report their density per simulation box (See US-2).
- **FR-005**: System MUST perform statistical correlation analysis (Spearman and Pearson) between the extracted topological metrics/bottleneck densities and the provided thermal conductivity values across multiple datasets using Bootstrap Resampling (1000 iterations) to estimate confidence intervals (See US-3).
- **FR-006**: System MUST validate robustness by repeating the correlation analysis across at least three distinct system sizes (e.g., N=1000, N=2000, N=4000) and reporting any finite-size effects observed (See US-3).
- **FR-007**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) if more than one hypothesis test is performed. The unit of testing is defined as "per metric per system-size comparison" (See US-3).
- **FR-008**: System MUST verify that the thermal conductivity values used as the outcome variable are derived from an independent source (e.g., experimental measurement or a distinct simulation run) and not the same trajectory used for topology extraction. If the source is not independent, the system MUST halt with an error (See US-3).

### Key Entities

- **SimulationBox**: Represents a single MD snapshot containing atomic positions, velocities, and metadata (system size, temperature, known thermal conductivity).
- **BondNetwork**: A graph representation of the atoms where nodes are atoms and edges are bonds defined by the RDF cutoff.
- **TopologicalMetric**: Aggregated values (e.g., mean coordination, variance, bottleneck density) derived from the BondNetwork.
- **VibrationalSpectrum**: The calculated VDOS and associated participation ratio data for a specific SimulationBox.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Spearman correlation coefficient calculation accuracy is measured against a manual reference calculation (tolerance ≤ 1e-6) across at least three distinct datasets (See US-3).
- **SC-002**: The statistical power of the correlation test is calculated and reported for the observed effect size. If the power is < 0.8, the system flags a "Low Power" warning (See US-3).
- **SC-003**: The consistency of the correlation coefficient across three different system sizes is calculated and reported (variance value), allowing the researcher to assess finite-size effects (See US-3).
- **SC-004**: The application of multiple-comparison correction is verified, and the corrected p-value is reported (See US-3).
- **SC-005**: The computational runtime for the full pipeline (topology + VDOS + correlation) on a 4000-atom system is measured against a threshold of ≤ 30 minutes on a standard 4-core CPU environment (See US-2).

## Assumptions

- **Dataset Availability**: Public repositories (Materials Cloud, Zenodo) contain at least three distinct amorphous silicon datasets with pre-computed thermal conductivity values and velocity trajectories compatible with the analysis pipeline.
- **Methodological Framing**: The study is observational; therefore, all correlation findings are framed as associational relationships between topology and thermal properties, not causal mechanisms, unless randomization is explicitly introduced in a future iteration.
- **Compute Constraints**: The analysis is restricted to CPU-only execution (no GPU/CUDA). All molecular dynamics post-processing (VDOS, RDF) and statistical analysis must complete within 6 hours on a standard CI runner with ~7 GB RAM. Large-scale simulations (>100k atoms) are assumed to be downsampled or excluded to fit memory constraints.
- **Threshold Justification**: The cutoff for defining "under-coordinated" atoms (coordination < 3) is based on the standard tetrahedral coordination of amorphous silicon (coordination ~4); this threshold is justified by the community standard for identifying defects in tetrahedral networks (Wooten-Winer-Weaire model).
- **Sensitivity Analysis**: A sensitivity analysis will be performed by sweeping the bond cutoff distance by ±0.1 Å around the identified RDF minimum to ensure the correlation is robust to small variations in network definition.
- **Measurement Validity**: The thermal conductivity values provided in the metadata MUST be derived from validated methods (e.g., Green-Kubo or Non-Equilibrium MD) on a *distinct* trajectory or experimental source, ensuring independence from the predictor variables.
- **Independence of Variables**: The system assumes the researcher provides thermal conductivity data that is not derived from the same atomic trajectory used to calculate the topological metrics, preventing circular validation.