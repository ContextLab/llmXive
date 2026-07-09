# Implementation Plan: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Branch**: `001-gene-regulation` | **Date**: 2026-07-03 | **Spec**: `specs/001-exploring-the-influence-of-network-topol/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-influence-of-network-topol/spec.md`

## Summary

This feature implements a computational study to determine how the topological structure of atomic connectivity networks (Small-World, Scale-Free, Random) influences thermal conductivity in disordered materials. The approach involves generating physically realizable disordered atomic structures, deriving connectivity graphs from the relaxed coordinates, computing anharmonic lattice dynamics for thermal transport (CPU-only) using EAM-derived force constants, and performing rigorous statistical regression with bootstrap resampling and multiple-comparison corrections. Crucially, the topology is derived *from* the physical structure, not imposed *on* it, ensuring force constants are independent of the abstract graph (satisfying FR-009).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `numpy`, `scipy`, `scikit-learn`, `lammps` (CPU mode), `pymatgen`, `pandas`, `matplotlib`, `phono3py` (optional, with fallback)  
**Storage**: Local file system (`data/`), JSON/YAML configuration files  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Computational Research / Simulation  
**Performance Goals**: Ensemble generation < 15 mins; Transport calculation < 45 mins per realization; Total runtime < 6 hours  
**Constraints**: No GPU/CUDA; Memory footprint < 6 GB; No external API calls during runtime (datasets must be cached or locally reproducible)  
**Scale/Scope**: N realizations determined by Phase 0 Power Analysis (see below); System size limited to a representative scale. to ensure convergence within 45 mins while satisfying Constitution Principle VI.

> Domain-specific empirical specifics are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/` configs. `data/` checksums recorded. No transient external dependencies in runtime. |
| **II. Verified Accuracy** | **Pass** | All citations in `research.md` verified against primary sources. No unreachable URLs. |
| **III. Data Hygiene** | **Pass** | Raw data immutable. Derivations written to new files with checksums. No PII (atomic structures). |
| **IV. Single Source of Truth** | **Pass** | All stats in `paper/` derived via scripts from `data/` rows. No manual entry. Duplicate schema files removed. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked in `state/`. Artifact changes update timestamps. |
| **VI. Numerical Stability** | **Pass** | `simulation_config.yaml` defines convergence criteria. System size limited to 2000 atoms to ensure convergence within 45 mins. Runs failing convergence are flagged and retried/rejected. |
| **VII. Network Construction Transparency** | **Pass** | Cutoffs, algorithms, and seeds stored in `data/processed/network_realizations/` YAML files alongside graph data (specifically in `construction_params`), ensuring exact reconstruction. |

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-influence-of-network-topol/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── network_realization.schema.yaml
    └── transport_result.schema.yaml
    └── analysis_schema.schema.yaml
```
*Note: Duplicate schema file `network.schema.yaml` has been removed to ensure a Single Source of Truth (Principle IV). The canonical schema for network realizations is `network_realization.schema.yaml`.*

### Source Code (repository root)

```text
projects/PROJ-236-exploring-the-influence-of-network-topol/
├── code/
│   ├── requirements.txt
│   ├── power_analysis.py
│   ├── generate_networks.py
│   ├── compute_transport.py
│   ├── analyze_correlations.py
│   ├── simulation_config.yaml
│   └── utils/
│       ├── graph_metrics.py
│       └── physics_solvers.py
├── data/
│   ├── raw/
│   │   └── atomic_structures/
│   ├── processed/
│   │   ├── network_realizations/
│   │   └── transport_results/
│   └── checksums.json
├── tests/
│   ├── unit/
│   │   ├── test_network_generation.py
│   │   └── test_transport_solver.py
│   └── integration/
│       └── test_full_pipeline.py
└── state/
    └── projects/PROJ-236-exploring-the-influence-of-network-topol.yaml
```

**Structure Decision**: Single project structure selected. The workflow is linear (Generate -> Simulate -> Analyze), making a monolithic codebase with modular scripts more efficient than a complex microservice architecture. This aligns with the "Computational Research" project type.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Physics-First Generation** | Required to ensure force constants are independent of topology (FR-009). | Graph-first generation creates circular validation where topology dictates force constants. |
| **EAM Force Constants** | Required to derive force constants from atomic species and positions (physics) rather than abstract topology (tautology). | Bond-stiffness models based on coordination number create circular validation with the topology metric. |
| **Stratified Analysis** | Required to handle ballistic transport without selection bias. | Excluding ballistic cases biases the Scale-Free ensemble and fails to test the full hypothesis. |
| **Bootstrap Resampling** | FR-004 requires + iterations for robust CI estimation. | Standard parametric CIs assume normality, which may not hold for the skewed distributions of thermal conductivity in disordered networks. |
| **Sensitivity Sweep** | FR-008 requires sweeping distance cutoffs. | A single cutoff assumption is insufficient given the sensitivity of network topology to geometric parameters in disordered systems. |
| **Targeted Power Analysis** | Required to distinguish topological signal from mass disorder noise. | A generic power analysis may underestimate N if it only accounts for total variance, failing to detect the subtle topological effect after controlling for mass disorder. |

## Implementation Phases

### Phase 0: Power Analysis & Sample Size Determination
*   **Task**: Execute formal power analysis (FR-010) to determine minimum N required for r≥0.3, power≥0.80.
*   **Critical Distinction**: The analysis will explicitly estimate the **residual variance** of thermal conductivity after regressing out mass disorder effects (e.g., atomic mass variance, composition). The sample size N will be calculated based on the ability to detect the *remaining* topological signal (r ≥ 0.3) against this residual noise, ensuring the study is not underpowered for the specific hypothesis of topological influence.
*   **Input**: Pilot variance estimate from a preliminary run of 20 realizations (10 with controlled mass disorder, 10 with varied topology).
*   **Output**: `data/processed/power_analysis.yaml` (sets N for subsequent phases).
*   **Dependency**: None.

### Phase 1: Network Generation & Sensitivity Sweep
*   **Task 1.1**: Generate N realizations per topology type using **Physics-First Generation**:
    1.  Generate a random disordered atomic structure (e.g., random alloy).
    2.  Relax the structure using EAM potentials (via `lammps` CPU mode).
    3.  Derive the connectivity graph from the relaxed coordinates using a distance cutoff.
    4.  Classify the resulting graph into topological bins (Small-World, Scale-Free, Random) based on its metrics.
*   **Task 1.2**: Perform distance cutoff sweep (starting from the baseline to an expanded range) to verify robustness (FR-008).
*   **Task 1.3**: Validate connectedness and degree distribution. Exclude invalid realizations only if physically impossible (e.g., disconnected due to cutoff too low).
*   **Output**: `data/processed/network_realizations/` (YAML files containing `construction_params` per Principle VII).

### Phase 2: Transport Calculation
*   **Task**: Derive force constants via EAM potential (CPU-only) for each valid realization.
*   **Task**: Validate transport regime. If ballistic transport is detected, **flag** the realization with `regime_flag: Ballistic` but **do not exclude**.
*   **Task**: Compute thermal conductivity via Green-Kubo (or fallback scipy solver if phono3py fails).
*   **Fallback**: If `phonopy` fails or exceeds a reasonable time limit, switch to a simplified `scipy`-based harmonic/anharmonic solver..
*   **Output**: `data/processed/transport_results/`.

### Phase 3: Correlation Analysis & Validation
*   **Task**: Perform linear regression and bootstrap resampling (sufficient iterations).
*   **Task**: Calculate CI width. If width > 0.2, flag result or retry with increased N/iterations (SC-004).
*   **Task**: Apply Bonferroni/FDR correction (FR-005).
*   **Task**: Calculate power-law fit R² for disorder parameters (SC-005).
*   **Task**: Perform stratified analysis by `regime_flag` to test topology-transport relationships across diffusive and ballistic regimes.
*   **Output**: `data/processed/analysis/`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Physics Invalidity** | High | Use EAM potentials and physics-first generation to ensure physical realizability. |
| **Solver Convergence Failure** | Medium | Implement retry logic and fallback to simplified scipy solver. Exclude outliers with logging only if convergence fails completely. |
| **Runtime Exceeds 6h** | High | Limit ensemble size based on Phase 0 power analysis. |
| **Ballistic Transport Bias** | Medium | Stratify analysis by regime rather than excluding ballistic cases. |
| **Underpowered Topological Signal** | High | Phase 0 explicitly targets residual variance after controlling for mass disorder to ensure N is sufficient for the specific topological effect. |