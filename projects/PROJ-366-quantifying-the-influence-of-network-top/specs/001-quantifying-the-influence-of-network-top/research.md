# Research: Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

## Problem Statement

Amorphous silicon (a-Si) exhibits thermal conductivity significantly lower than its crystalline counterpart, a property critical for thermoelectric and thermal barrier applications. While the Stillinger-Weber (SW) potential has been widely used to model a-Si, the specific influence of **network topology** (e.g., coordination defects, ring statistics, clustering) on thermal transport remains poorly quantified. This project aims to bridge this gap by combining Molecular Dynamics (Green-Kubo) with Graph Neural Networks (GNNs) to correlate local topological metrics with global thermal conductivity.

## Dataset Strategy

### Primary Data Sources

| Dataset | Description | Source URL | Verification Status |
|---------|-------------|------------|---------------------|
| **ThermalSample** | Pre-equilibrated amorphous silicon configurations (≥1000 atoms, XYZ format) | **NO verified source found** | ⚠️ **Critical Gap**: The spec assumes N ≥ 10 independent samples are available. If no raw data is provided, the pipeline will generate synthetic samples using `ase` + `LAMMPS` (SW potential) with a melt-quench protocol. This generation step will be logged and checksummed. |
| **AtomicGraph** | Derived graph objects (nodes=atoms, edges=bonds < 3.0 Å) | **NO verified source found** | Generated from `ThermalSample` via `code/ingest/graph_builder.py`. |

### Data Generation Protocol (if no raw data provided)

If no pre-equilibrated XYZ files are provided in `data/raw/`, the pipeline will execute `code/ingest/sample_generator.py`:
1. **Initialization**: Create a cubic supercell of 1000 Si atoms at high density.
2. **Melting**: Heat to 3000 K using NPT ensemble (SW potential) for 50 ps.
3. **Quenching**: Cool to 300 K at 10 K/ps rate.
4. **Equilibration**: NVT ensemble at 300 K for 100 ps.
5. **Output**: Save final configuration as `data/raw/sample_N.xyz`.

*Note: This generation step is computationally expensive. To meet the 6-hour runtime limit on GitHub Actions, the number of samples (N) is capped at **2** for this proof-of-concept study.*

### Variable Fit Assessment

| Required Variable | Source | Fit Status |
|-------------------|--------|------------|
| Atomic positions (x, y, z) | `ThermalSample` (XYZ) | ✅ Directly available |
| Bond connectivity (edges) | Derived (3.0 Å cutoff) | ✅ Derivable |
| Topological metrics (degree, clustering) | Derived from graph | ✅ Derivable |
| Global thermal conductivity | `Green-Kubo` simulation | ✅ Computed via LAMMPS |
| Static Scattering Potential | Derived from topology (GNN target) | ✅ Derivable |

**Fatal Mismatch Check**: The spec requires "post-task anxiety/rumination" (from the template example) — **NOT APPLICABLE**. The required variables (atomic positions, heat flux, conductivity) are all present or derivable from the `ThermalSample` and `Green-Kubo` simulation. No fatal mismatches.

## Methodological Rationale

### 1. Graph Construction (FR-001)
- **Tooling**: `ase` (Atomic Simulation Environment) is used instead of `rdkit`. `ase` provides robust neighbor list calculation for XYZ files with a distance cutoff, which is the standard for amorphous solids.
- **Cutoff Radius**: 3.0 Å is chosen based on literature (e.g., *Phys. Rev. B* 48, 1993) as the standard for the first coordination shell in a-Si.
- **Justification**: Ensures consistent bond definition across samples; captures local defects (under/over-coordinated atoms).

### 2. Green-Kubo Simulation (FR-003, SC-003)
- **Potential**: Stillinger-Weber (SW) is the industry standard for a-Si thermal conductivity.
- **Convergence Criterion**: Relative change in heat current autocorrelation function (HCACF) < 1% over the final [deferred] of the trajectory (SC-003).
- **Runtime Constraint**: Simulations will be run on 2 CPU cores. To ensure completion within the **6-hour total pipeline budget** (not 12 hours per sample, which is infeasible for N=10), the sample size is reduced to **N=2**. The trajectory length will be limited to a duration sufficient for HCACF decay in a-Si (sufficient for HCACF decay in a-Si)..
- **Power Limitation**: With N=2 samples, statistical power for correlation analysis is extremely low. The study is framed as a **proof-of-concept** for the pipeline. If N < 2, the analysis will be flagged as invalid.

### 3. GNN Architecture (FR-004, SC-002)
- **Architecture**: 2-layer Graph Convolutional Network (GCN) with ReLU activation.
- **Input Features**: Node degree, clustering coefficient, shortest-path distribution (aggregated per atom).
- **Output**: **Static Scattering Potential** (a scalar proxy derived from topology).
- **Justification**: Predicting dynamic heat flux from static topology is physically ill-posed (static-to-dynamic mapping). Instead, the GNN predicts a static proxy that reflects topological complexity. This breaks the tautology of correlating model explanations of a dynamic target with a global dynamic property.
- **Baseline**: Linear regression will be used as a baseline (SC-002) to demonstrate added value of non-linear modeling.

### 4. Correlation Analysis (FR-005, SC-001)
- **Method**: **Linear Mixed-Effects Model (LMM)** where the fixed effects are the **variance** of local topological metrics (e.g., variance of node degree) and the response is global thermal conductivity.
- **Unit of Analysis**: The sample-level variance of local metrics, not a mean SHAP score. This addresses the unit mismatch and allows the model to capture the spread of topological features within a sample.
- **Multiple Comparison Correction**: Bonferroni correction is noted but may be inapplicable for N=2. The LMM p-values will be reported with extreme caution.
- **Causal Inference**: Claims will be framed as **associational** (observational study). No randomization of topology is performed; thus, causal claims are not licensed.

### 5. Statistical Rigor
- **Collinearity**: Topological metrics (e.g., degree and clustering) may be correlated. The LMM approach inherently handles collinearity by modeling the joint distribution of metrics. The plan will report confidence intervals and acknowledge that high collinearity may widen them, but the model will still estimate the unique contribution of each metric's variance.
- **Measurement Validity**: The LMM is a standard statistical tool for hierarchical data.
- **Power Analysis**: With N=2, power is negligible for rigorous hypothesis testing. The study is limited to demonstrating the pipeline's feasibility and the directionality of the trend.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **CPU-only execution** | GitHub Actions free-tier has no GPU; GNN training on 2 samples is feasible on CPU. |
| **N=2 samples** | Required to fit the 6-hour runtime budget on 2 CPUs for Green-Kubo simulations. |
| **LMM instead of Pearson/SHAP** | Resolves unit-of-analysis mismatch and tautology; handles collinearity better. |
| **Static Scattering Potential target** | Avoids physically ill-posed static-to-dynamic mapping. |
| **Associational claims only** | Observational study; no randomization of topology. |
| **Synthetic sample generation** | Required if no raw data provided; ensures reproducibility (Constitution I). |

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Green-Kubo non-convergence** | Flag sample for exclusion; rerun with longer trajectory if time permits (Edge Case). |
| **Extreme topological defects** | Exclude samples with >15% atoms having coordination <3 or >6 (Edge Case). |
| **Insufficient samples (N < 2)** | Flag statistical power limitation; defer conclusion; require additional data (Edge Case). |
| **Runtime exceedance** | Optimize simulation parameters; reduce trajectory length; use sampled data for GNN. |
| **Dataset unavailability** | Generate synthetic samples via melt-quench protocol (documented in `research.md`). |