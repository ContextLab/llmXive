# Feature Specification: Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

**Feature Branch**: `001-md-simulation-params`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity"

## User Scenarios & Testing

### User Story 1 - Reproducible Parameter Sweep Execution (Priority: P1)

As a computational chemist, I need to execute a controlled series of Molecular Dynamics (MD) simulations across varying force fields, durations, and temperatures on a CPU-only environment so that I can generate the trajectory data required for sensitivity analysis without exceeding hardware limits.

**Why this priority**: This is the foundational data generation step. Without successful, reproducible simulations within the 6-hour CPU budget, no analysis can occur. It directly addresses the "compute feasibility" constraint of the project.

**Independent Test**: The system can be tested by running the simulation pipeline on a single complex (e.g., 1J22, ≤200 residues) with a single parameter set (ff14SB, 2ns, 300K) and verifying that the trajectory file is generated and the job completes within 7 minutes without GPU errors.

**Acceptance Scenarios**:

1. **Given** a PDB complex from the PDBbind v2020 subset (≤2.0 Å resolution, ≤200 residues), **When** the simulation script is invoked with parameters `ff14SB`, `2ns`, `300K` on a 2-core CPU runner, **Then** the simulation completes within 7 minutes and produces a valid trajectory file (`.nc` or `.xtc`) and topology file.
2. **Given** a request to run a subsampled factorial design (10 complexes × 2 force fields × 3 durations × 1 temperature), **When** the batch script is executed on the CI runner, **Then** the total wall-clock time does not exceed 6 hours (360 minutes), and all 54 individual simulation jobs complete successfully or are terminated by the 7-minute timeout.
3. **Given** a simulation attempt that fails due to a syntax error in the input file, **When** the error handler is triggered, **Then** the specific complex and parameter set are logged, and the pipeline proceeds to the next valid entry rather than halting the entire batch.

---

### User Story 2 - Automated Affinity Estimation and Error Calculation (Priority: P2)

As a researcher, I need the system to automatically calculate binding free energy estimates (MM-PBSA/MM-GBSA) from the generated trajectories and compute the Root Mean Square Error (RMSE) against experimental values so that I can quantify the accuracy of each parameter combination.

**Why this priority**: This transforms raw trajectory data into the primary metric of interest (prediction error). It bridges the gap between simulation execution and statistical analysis.

**Independent Test**: The system can be tested by providing a pre-generated trajectory and its corresponding experimental binding constant, then verifying that the calculated MM-PBSA value and the resulting RMSE error match expected values within an acceptable tolerance.

**Acceptance Scenarios**:

1. **Given** a valid MD trajectory file and the experimental binding affinity (in kcal/mol) for a specific complex, **When** the analysis module runs MM-PBSA post-processing, **Then** a numerical binding affinity estimate is produced and stored in the results database.
2. **Given** a set of 10 complexes with known experimental affinities, **When** the system processes all generated trajectories for a specific parameter combination, **Then** the Mean Absolute Error (MAE) and Coefficient of Variation (CV) are calculated across the 10 complexes (N=10) and reported for that combination.
3. **Given** a trajectory where the MM-PBSA calculation fails (e.g., due to missing atoms), **When** the error handling routine executes, **Then** the specific complex/parameter combination is flagged as "failed analysis" and excluded from the statistical summary without crashing the pipeline.

---

### User Story 3 - Statistical Sensitivity and Variance Analysis (Priority: P3)

As a methodologist, I need the system to perform a three-way ANOVA and generate variance component plots to determine which simulation parameters (force field, duration, temperature) contribute most to the uncertainty in binding affinity predictions so that I can derive evidence-based protocol recommendations.

**Why this priority**: This delivers the final scientific insight. It answers the research question by quantifying the impact of parameters and identifying the dominant sources of error.

**Independent Test**: The system can be tested by feeding it a synthetic dataset with known variance contributions (e.g., force field accounts for [deferred] of variance) and verifying that the ANOVA output correctly identifies the force field as the most significant factor with a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** the aggregated results of binding affinity errors across all parameter combinations, **When** the statistical analysis module runs a three-way ANOVA, **Then** the output includes F-statistics and p-values for the main effects (force field, length, temperature) and their interactions.
2. **Given** the ANOVA results, **When** the variance decomposition is calculated, **Then** a report is generated identifying the percentage of total variance attributable to each parameter (e.g., "Force Field: X%, Duration: Y%").
3. **Given** the final analysis, **When** the visualization module runs, **Then** a variance component plot is generated showing the relative contribution of each parameter to the total prediction uncertainty.

---

### Edge Cases

- What happens when a specific PDB complex fails to solvate or equilibrate due to steric clashes in the initial structure?
- How does the system handle a scenario where the MM-PBSA calculation yields a non-physical value (e.g., extremely high positive energy) for a specific trajectory?
- What is the behavior if the PDBbind v2020 dataset download fails or the specific subset (≤2.0 Å) contains fewer than 10 high-quality complexes?

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute MD simulations using OpenMM or GROMACS with explicit solvent (TIPP) and neutralizing ions for a defined set of protein-ligand complexes, supporting force field variants (ff14SB, CHARMM36m) and 3 duration settings (1ns, 2ns, 3ns) on a single temperature (300K). (See US-1)
- **FR-002**: System MUST automatically calculate binding free energy estimates using MM-PBSA or MM-GBSA post-processing on the generated trajectories for every completed simulation. (See US-2)
- **FR-003**: System MUST compute the Root Mean Square Error (RMSE) between the predicted binding affinity and the experimental binding constant for each parameter combination. (See US-2)
- **FR-004**: System MUST perform a three-way ANOVA to assess main effects and interactions of force field, simulation length, and temperature on the prediction error, ensuring the method is observational and findings are framed as associational. (See US-3)
- **FR-005**: System MUST generate variance component plots and a summary report identifying the dominant sources of uncertainty (e.g., force field vs. duration) to support protocol recommendations. (See US-3)
- **FR-006**: System MUST enforce a strict resource constraint where the total wall-clock time for the full factorial analysis (or subsampled equivalent) does not exceed a predefined time limit on a runner with limited CPU and RAM resources, automatically subsampling the dataset to a representative subset of complexes if necessary. (See US-1)

### Key Entities

- **SimulationRun**: Represents a single MD execution defined by a unique combination of complex ID, force field, duration, and temperature.
- **TrajectoryData**: The output file (e.g., `.nc`, `.xtc`) generated from a `SimulationRun`, containing atomic coordinates over time.
- **AffinityEstimate**: A numerical record linking a `SimulationRun` to its calculated binding free energy (kcal/mol) and the method used (MM-PBSA/MM-GBSA).
- **ExperimentalValue**: The ground-truth binding constant (kcal/mol) retrieved from PDBbind for a specific complex, used as the reference for error calculation.
- **AnalysisResult**: A structured record containing the statistical outcomes (ANOVA p-values, variance percentages) for the entire batch of runs.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The system's ability to calculate and report the Coefficient of Variation (CV) of binding affinity estimates across varying parameters is measured against the calculated value from the dataset. (See US-3)
- **SC-002**: The statistical significance (p-value < 0.05) of force field and duration effects on prediction error is measured against the null hypothesis of no effect using three-way ANOVA. (See US-3)
- **SC-003**: The total computational cost (wall-clock time) is measured against the CI runner time limit to ensure feasibility on free-tier hardware. (See US-1)
- **SC-004**: The prediction accuracy (Mean Absolute Error) of the optimal parameter combination is measured against the baseline accuracy of the standard protocol (ff14SB, 2ns, 300K) to demonstrate improvement or robustness. (See US-2)

## Assumptions

- **Assumption about dataset availability**: The PDBbind v2020 "refined" subset contains at least 10 complexes with resolution ≤2.0 Å and experimental binding constants (kcal/mol) that are compatible with the selected force fields and solvation models.
- **Assumption about software compatibility**: The chosen MD engine (OpenMM or GROMACS) and the MM-PBSA/GBSA implementation are available and functional on the GitHub Actions free-tier runner (Ubuntu, CPU-only, limited RAM) without requiring proprietary licenses or GPU acceleration.
- **Assumption about computational feasibility**: The subsampling strategy (prioritizing 10 complexes) is sufficient to provide exploratory insights for the ANOVA; the study acknowledges the limited statistical power (N=10) for a 3-factor design and frames findings as preliminary rather than definitive.
- **Assumption about methodological framing**: The study is purely observational; therefore, any observed correlations between parameter settings and prediction accuracy are interpreted as associational, not causal, unless randomization is explicitly introduced in a future iteration.
- **Assumption about measurement validity**: The experimental binding constants in PDBbind v2020 are treated as the ground truth for error calculation, assuming they are derived from consistent experimental conditions (e.g., standard temperature/pH) appropriate for the simulation parameters (300K).