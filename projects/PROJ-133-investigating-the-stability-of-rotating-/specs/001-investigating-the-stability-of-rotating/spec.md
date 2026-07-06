# Feature Specification: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions"

## User Scenarios & Testing

### User Story 1 - Compute Stability Phase Diagram (Priority: P1)

As a physics researcher, I need to run the time-dependent Gross-Pitaevskii (GPE) solver across a defined grid of rotation frequencies (Ω), dipolar strengths (ε_dd), and particle numbers (N) to generate the raw simulation data required for the stability phase diagram.

**Why this priority**: This is the core computational engine of the project. Without generating the time-evolution data for the parameter grid, no stability metrics can be calculated, and the primary research question cannot be answered.

**Independent Test**: Can be fully tested by executing the simulation script for a single parameter set (e.g., Ω=0.5, ε_dd=0.5, N=10^4) and verifying that it completes within the 6-hour CI limit without GPU errors, producing density and phase snapshot files.

**Acceptance Scenarios**:

1. **Given** a valid parameter set (Ω, ε_dd, N) from the input grid, **When** the simulation script is executed on a CPU-only runner with ω⊥ = 2π × 100 Hz, **Then** the GPE solver propagates the wavefunction for 200ms physical time and outputs density/phase snapshots every 1ms.
2. **Given** the simulation grid parameters (3 N values × 5 Ω values × 4 ε_dd values), **When** the batch job runs, **Then** the system completes all 60 grid points within the 6-hour GitHub Actions timeout.

### User Story 2 - Detect Vortices and Calculate Stability Metrics (Priority: P2)

As a researcher, I need the system to automatically detect vortex positions via phase winding analysis and calculate stability metrics (vortex retention, radial variance, structure factor) for each simulation run to quantify the transition from stable to unstable regimes.

**Why this priority**: Raw simulation data is uninterpretable without quantification. This step transforms the physics simulation into the specific metrics (retention fraction, lattice order) defined in the expected results.

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated "stable" and "unstable" snapshot file and verifying that it correctly counts vortices and outputs the three defined metrics.

**Acceptance Scenarios**:

1. **Given** a density and phase snapshot file from the simulation, **When** the vortex detection algorithm runs, **Then** it identifies vortex cores by computing phase winding around each plaquette and outputs a count and (x,y) coordinates.
2. **Given** a time-series of vortex counts, **When** the stability analysis runs, **Then** it calculates the vortex-number retention fraction, radial distribution variance, and structure factor sharpness, storing these in a results CSV.

### User Story 3 - Generate Statistical Phase Maps and Visualizations (Priority: P3)

As a researcher, I need the system to aggregate results from the 5 repeated simulations per parameter point, apply statistical tests (ANOVA, one-sample t-test), and generate contour maps and representative plots to visualize the stability landscape.

**Why this priority**: This delivers the final "product" of the research (the phase diagram) and validates the robustness of the findings through statistical repetition, fulfilling the "Expected Results" section.

**Independent Test**: Can be fully tested by running the visualization script on a mock dataset of 5 repeats per point and verifying that it produces a contour map distinguishing stable/unstable regions and a summary table of ANOVA p-values.

**Acceptance Scenarios**:

1. **Given** the aggregated metrics from 5 noise-seed repeats for a parameter point, **When** the statistical analysis runs, **Then** it performs a one-sample t-test against a stable baseline and a one-way ANOVA across grid points, flagging significance at α=0.05.
2. **Given** the full set of statistical results, **When** the plotting module runs, **Then** it generates a 3D parameter space contour map (Ω vs ε_dd vs Stability) and saves representative density/phase plots for the stable, metastable, and unstable regimes.

### Edge Cases

- What happens when the vortex detection algorithm encounters a "vortex-antivortex pair" that annihilates rapidly during the time step? The system must handle zero-crossing ambiguities by checking phase continuity over a larger neighborhood or skipping the frame if the pair count is below the noise threshold.
- How does the system handle the "metastable" boundary where the vortex count drops by >30% relative to the initial count? The system must treat this as a binary threshold for classification but record the exact percentage for the sensitivity analysis.
- What if the simulation crashes due to numerical instability before 200ms? The system must log the failure time, treat the run as "unstable" (retention = 0), and record the crash point to avoid false "stable" classifications.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the time-dependent Gross-Pitaevskii equation with a dipolar interaction term using a split-step Fourier method on a 256×256 grid with a time step of Δt = 0.001 ω⊥⁻¹ (See US-1).
- **FR-002**: System MUST generate initial Thomas-Fermi profiles for N ∈ {10⁴, 5×10⁴, 10⁵} and imprint a solid-body rotation phase for Ω/ω⊥ ∈ [0.3, 0.9] and ε_dd ∈ {0.0, 0.5, 1.0, 1.5} (See US-1).
- **FR-003**: System MUST detect vortices by computing phase winding around each grid plaquette and outputting a count and position list for every saved snapshot (See US-2).
- **FR-004**: System MUST calculate three stability metrics: (a) vortex-number retention fraction, (b) radial distribution variance, and (c) structure factor peak sharpness (See US-2).
- **FR-005**: System MUST repeat each parameter configuration 5 times with different random noise seeds and perform a one-sample t-test against a stable baseline (ε_dd=0, Ω=0.3) and a one-way ANOVA to model stability trends across the grid (See US-3).
- **FR-006**: System MUST define instability as a drop >30% in vortex count or loss of crystalline order, and perform a sensitivity analysis sweeping this threshold over {0.25, 0.30, 0.35} to verify that the classification boundary is robust to ±5% perturbations (See US-2).

### Key Entities

- **SimulationRun**: Represents a single execution of the GPE solver for a specific (Ω, ε_dd, N) configuration and noise seed. Attributes include time-series density data, phase data, and runtime logs.
- **StabilityMetric**: Represents the aggregated quantitative outcome of a simulation run. Attributes include vortex_count, retention_fraction, radial_variance, and structure_factor_sharpness.
- **ParameterGrid**: Represents the input configuration space. Attributes include the set of Ω values, ε_dd values, and N values to be tested.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Vortex-number retention fraction is measured against the initial vortex count at t=0ms to determine stability regimes (See US-2).
- **SC-002**: Radial distribution variance and structure factor sharpness are measured against the theoretical values for a perfect triangular lattice generated by a reference simulation of a non-dipolar (ε_dd=0) condensate at the same Ω (See US-2).
- **SC-003**: The statistical significance of stability differences between parameter points is measured against the null hypothesis using a one-sample t-test and one-way ANOVA with α=0.05 (See US-3).
- **SC-004**: Computational feasibility is measured against the constraint of completing the full parameter grid (60 points × 5 repeats) within 6 hours on a CPU-only GitHub Actions runner (See US-1).
- **SC-005**: The robustness of the instability threshold is measured by sweeping the cutoff over {0.25, 0.30, 0.35} and reporting the variation in false-positive/negative rates (See US-2).

## Assumptions

- **Assumption about computational resources**: The simulation workload for a 256×256 grid with 2×10⁵ time steps fits within the 7 GB RAM and 14 GB disk limits of the GitHub Actions free-tier runner, requiring no GPU acceleration.
- **Assumption about numerical stability**: The split-step Fourier method with Δt = 0.001 ω⊥⁻¹ is numerically stable for the chosen parameter range (Ω up to 0.9, ε_dd up to 1.5) without requiring adaptive time-stepping, validated via a convergence study varying Δt by ±50% and grid size by ±20%.
- **Assumption about dipolar interaction model**: The quasi-2D approximation (weak axial confinement) is valid for the experimental conditions described, allowing the use of a 2D GPE solver with an effective dipolar interaction kernel.
- **Assumption about noise seeding**: Adding small random noise to the initial Thomas-Fermi profile is sufficient to seed the dynamical instabilities observed in rotating dipolar condensates, without needing a more complex perturbation model.
- **Assumption about vortex detection**: The phase-winding method on a 256×256 grid provides sufficient spatial resolution to accurately detect vortices in the expected density profiles.