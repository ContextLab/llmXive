# Feature Specification: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "How does the topological structure of atomic connectivity networks (e.g., small-world, scale-free, random) influence thermal conductivity in disordered materials, and can specific network motifs predict anomalous heat transport behavior?"

## User Scenarios & Testing

### User Story 1 - Construct and Validate Network Realizations (Priority: P1)

The researcher needs to generate a reproducible ensemble of atomic connectivity network realizations (Small-World, Scale-Free, Random) derived from disordered material structures, ensuring that the network construction parameters (distance cutoffs) are consistent and that the resulting graphs pass topological sanity checks (e.g., connectedness, degree distribution match).

**Why this priority**: Without valid, comparable network realizations, no subsequent transport calculation or correlation analysis is possible. This is the foundational data generation step.

**Independent Test**: Can be fully tested by running the network generation script on a fixed seed and verifying that the output network realizations match the theoretical degree distributions and that the distance-based cutoff yields a connected graph for >95% of realizations.

**Acceptance Scenarios**:

1. **Given** a set of atomic coordinates for a disordered alloy, **When** the system applies a default distance cutoff of a multiple of the nearest-neighbor distance, **Then** the resulting network realization must be connected with a clustering coefficient within 5% of the theoretical Watts-Strogatz target for Small-World ensembles. (Justification: This tolerance ensures the generated network is sufficiently close to the theoretical model for comparative analysis; deviations require re-tuning.)
2. **Given** a request to generate a Scale-Free ensemble, **When** the system applies the Barabási-Albert algorithm with m=2, **Then** the median exponent of the ensemble degree distribution must fall within the theoretical range 2 < γ < 3 across multiple realizations. (Note: This is a unit test for algorithmic correctness.)
3. **Given** a set of atomic coordinates, **When** the system generates a Random (Erdős-Rényi) graph realization matched to the mean degree of the target structure, **Then** the average path length must be within 10% of the theoretical expectation for N nodes and p probability.

### User Story 2 - Compute Phonon Transport and Thermal Conductivity (Priority: P2)

The researcher needs to calculate the effective thermal conductivity (κ) for each generated network realization ensemble using anharmonic lattice dynamics, ensuring the computation runs within CPU constraints (no GPU) and produces valid Green-Kubo or direct transport coefficients.

**Why this priority**: This provides the dependent variable (outcome) required to test the research hypothesis. It is the core physics simulation step.

**Independent Test**: Can be fully tested by running the simulation on a small, known test case (e.g., a 1D chain or simple crystal) and verifying the output κ matches the analytical or literature value within 10%, while confirming the process completes on a CPU-only runner.

**Acceptance Scenarios**:

1. **Given** a valid network realization and atomic force constants, **When** the system executes the anharmonic lattice dynamics solver in CPU-only mode, **Then** the calculation must complete within 45 minutes per network realization on a 2-core runner.
2. **Given** a network realization, **When** the system computes the phonon transmission coefficients, **Then** the resulting thermal conductivity value must be a finite real number and not trigger a "convergence failure" or "singular matrix" error.
3. **Given** a set of 50 network realizations, **When** the system aggregates the conductivity results, **Then** the standard error of the mean must be calculable and reported alongside the mean value.

### User Story 3 - Analyze Topology-Transport Correlations (Priority: P3)

The researcher needs to perform statistical regression analyses between network metrics (clustering, degree variance, spectral gap) and thermal conductivity, including bootstrap resampling to establish confidence intervals and significance levels.

**Why this priority**: This delivers the scientific insight (the "answer" to the research question) by quantifying the relationship between topology and transport.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset with a known correlation (e.g., r=0.8) and verifying that the bootstrapped confidence interval captures the true value and the p-value is < 0.05.

**Acceptance Scenarios**:

1. **Given** a dataset of network metrics and corresponding conductivity values, **When** the system performs linear regression, **Then** the output must include the correlation coefficient (r), p-value, and bootstrap confidence intervals for the slope.
2. **Given** multiple hypothesis tests (one for each network metric), **When** the system evaluates significance, **Then** it must apply a Bonferroni or False Discovery Rate (FDR) correction to the p-values to control for family-wise error.
3. **Given** a detected correlation, **When** the system generates the visualization, **Then** it must produce a publication-ready scatter plot with error bars representing the bootstrap confidence intervals.

### Edge Cases

- **Disconnected Graphs**: What happens if the distance cutoff results in a disconnected network (isolated atoms)? The system must retry with a larger cutoff (up to 2.0×) or flag the realization as invalid and exclude it from the ensemble, logging the exclusion reason.
- **Convergence Failure**: How does the system handle an anharmonic dynamics calculation that fails to converge? The system must catch the exception, retry up to 3 times with adjusted solver parameters, and if it still fails, exclude the realization and report the failure rate to ensure it remains < 5% of the total ensemble.
- **Zero Variance**: What if a network metric (e.g., degree variance) is constant across the ensemble? The system must detect zero variance, skip the regression for that specific metric, and log a warning rather than attempting a division-by-zero operation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate atomic connectivity network realizations using a default distance-based cutoff relative to the nearest-neighbor distance, ensuring the graph is connected for at least 95% of realizations after attempting up to 2.0× the default cutoff, AND ensuring the clustering coefficient is within 5% of the theoretical Watts-Strogatz target for Small-World ensembles (See US-1).
- **FR-002**: System MUST compute effective thermal conductivity using anharmonic lattice dynamics in CPU-only mode, completing each network realization within 45 minutes on a 2-core runner (See US-2).
- **FR-003**: System MUST extract topological metrics including average path length, clustering coefficient, degree variance, spectral gap, and betweenness centrality distribution for every network realization (See US-3).
- **FR-004**: System MUST perform bootstrap resampling with at least 1000 iterations to estimate confidence intervals for all correlation coefficients between network metrics and thermal conductivity, and report the lower and upper percentiles (See US-3).
- **FR-005**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or FDR) to p-values when testing more than one network metric against conductivity to control family-wise error (See US-3).
- **FR-006**: System MUST derive effective force constants via an anharmonic force constant estimation method (e.g., machine-learned potentials or perturbation theory) if explicit force constants are missing from the input dataset (See US-2).
- **FR-007**: System MUST frame all reported statistical relationships as ASSOCIATIONAL and avoid causal language (e.g., "causes," "drives") in the final output, as the design is observational (See US-3).
- **FR-008**: System MUST perform a sensitivity analysis on the distance cutoff by sweeping values across a low-to-moderate range in regular increments to verify the robustness of the topology-transport correlation (See US-1).
- **FR-009**: System MUST derive effective force constants from *ab initio* calculations or established empirical potentials (e.g., EAM) based on atomic species and positions, independent of the abstract graph topology, to prevent circular validation where topology defines the transport outcome (See US-2).
- **FR-010**: System MUST perform a formal statistical power analysis prior to ensemble generation to determine the minimum sample size (N) required to detect a moderate effect size (r ≥ 0.3) with a statistical power ≥ 0.80 (See US-3).
- **FR-011**: System MUST validate the transport regime for each network realization; if the network exhibits high-degree hubs (scale-free) or low clustering indicative of ballistic transport, the system MUST switch to Non-Equilibrium Molecular Dynamics (NEMD) or flag the Green-Kubo formalism as invalid (See US-2).

### Key Entities

- **NetworkRealization**: Represents a single instance of an atomic connectivity graph (Small-World, Scale-Free, or Random) with attributes for node count, edge list, and topological metrics.
- **TransportResult**: Represents the calculated thermal conductivity for a specific realization, including the value, error estimate, and convergence status.
- **CorrelationAnalysis**: Represents the statistical relationship between a specific network metric and thermal conductivity, containing the correlation coefficient, p-value, and confidence intervals.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of valid (connected) network realizations is measured against a target of ≥ 95% (See FR-001, US-1).
- **SC-002**: Total runtime for one full ensemble is measured against a limit of ≤ 6 hours (See FR-002, US-2).
- **SC-003**: The statistical significance of the correlation between the primary topology metric (e.g., clustering coefficient) and thermal conductivity is measured and reported as a p-value < 0.05 after correction (See FR-005, US-3).
- **SC-004**: The width of the 95% bootstrap confidence interval for the correlation slope is measured against a target of ≤ 0.2 to ensure precision (See FR-004, US-3).
- **SC-005**: The system MUST calculate and report the R² value of the power-law fit between network disorder parameters and conductivity reduction, and perform a statistical test against the null hypothesis (R² = 0), rejecting the null at α = 0.05 (See US-3).
- **SC-006**: The executed power analysis is measured against a target statistical power ≥ 0.80 for a moderate effect size (r ≥ 0.3), confirming the sample size N is sufficient (See FR-010, US-3).

## Assumptions

- **Assumption about data availability**: The public datasets (Zenodo, HuggingFace, Materials Project) contain disordered alloy structures with complete atomic positions; if force constants are missing, the assumption is that they can be approximated via a bond-stiffness model based on coordination number and atomic mass.
- **Assumption about computational feasibility**: The `phono3py` or `netph` packages can be run in a CPU-only, non-GPU mode on systems with ≤ 2000 atoms without requiring 8-bit quantization or CUDA acceleration. Systems with larger atom counts require distributed computing or longer time allowances.
- **Assumption about statistical power**: The sample size (N) of network realizations per ensemble type is not fixed a priori but is determined by the power analysis required in FR-010, targeting a moderate effect size (r ≥ 0.3) to achieve power ≥ 0.80.
- **Assumption about methodology**: In disordered materials, anharmonicity is the dominant mechanism for thermal resistance; thus, the use of anharmonic lattice dynamics is required to capture finite, diffusive transport, justifying the methodology over harmonic approximations, unless FR-011 dictates a switch to NEMD.
- **Assumption about threshold justification**: The default distance cutoff of a multiple of the nearest-neighbor distance is based on standard community practices for defining nearest-neighbor bonds in disordered materials; a sensitivity analysis will sweep this cutoff over a range of values to verify robustness.
- **Assumption about inference framing**: Since the study uses generated ensembles rather than randomized controlled trials on physical samples, all conclusions will be strictly framed as associational correlations between topology and transport properties.