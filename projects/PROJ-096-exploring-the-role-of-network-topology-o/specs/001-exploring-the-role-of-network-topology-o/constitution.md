# Constitution: Exploring the Role of Network Topology on Synchronization in Coupled Oscillators

## Preamble

This constitution defines the fundamental principles and constraints governing the research project "Exploring the Role of Network Topology on Synchronization in Coupled Oscillators". All implementation, analysis, and reporting must adhere to these principles to ensure scientific validity, reproducibility, and methodological coherence.

## Core Principles

### Principle I: Single Source of Truth
There must be exactly one authoritative specification for every requirement, parameter, and data source. Conflicting definitions across documents (spec.md, plan.md, constitution.md) are strictly forbidden.

### Principle II: Methodological Validity
All data sources and generation methods must be theoretically justified. Using an irregular empirical network (e.g., ca-AstroPh) as the basis for a synthetic regular ring lattice is methodologically incoherent and prohibited.

### Principle III: Reproducibility
Every step of the research pipeline must be deterministic and reproducible. All random processes must use documented seeds, and all external data sources must be either:
1. Downloaded from a verified, stable URL with checksums, OR
2. Generated synthetically using a documented algorithm and seed.

### Principle IV: Failure Transparency
The pipeline must fail loudly and explicitly when requirements cannot be met. Silent fallbacks to synthetic data, placeholder values, or reduced scope without logging are prohibited.

### Principle V: Observer Invariance
Physical quantities (e.g., critical coupling strength $K_c$) must be invariant under coordinate frame transformations. Verification of rotational invariance is mandatory.

### Principle VI: Fixed Parameters
Once feasibility parameters (time steps, number of topologies, run counts) are determined, they must remain fixed for the entire experiment to ensure reproducibility.

## Reproducibility Requirements

1. **Base Graph Generation**: The base graph MUST be generated as a synthetic regular ring lattice of N=500 nodes using the Watts-Strogatz algorithm with p=0.0 and a documented random seed. The original requirement to download the 'ca-AstroPh' citation network from the Stanford Network Analysis Project is hereby REMOVED as it is methodologically invalid for this study.

2. **Seed Documentation**: All random seeds used in graph generation, simulation initialization, and analysis must be logged in `data/processed/graph_metadata.json` and `data/processed/simulation_results.csv`.

3. **Checksum Verification**: All data artifacts (generated graphs, simulation results) must have SHA256 checksums recorded in `data/checksums.txt`.

4. **Configuration Locking**: The feasibility study parameters (`data/processed/config.json`) must be read as immutable inputs by all downstream tasks.

5. **Invariance Verification**: The critical coupling strength $K_c$ must be verified to be identical under two reference frames: "single oscillator" and "center-of-mass".

## Scope Constraints

- Maximum runtime: 6 hours on a 2-core CPU runner
- Minimum valid topology count: 10 (if fewer are feasible, the pipeline must halt with a clear error)
- Minimum time steps: 1000 (if fewer are feasible, the pipeline must halt with a clear error)

## Amendment History

- **T000a**: Removed 'ca-AstroPh' download requirement from Reproducibility Requirements. Replaced with synthetic regular ring lattice generation (N=500, p=0.0, documented seed). Rationale: The original requirement was methodologically incoherent (reconstructing an irregular citation network into a regular ring lattice). This amendment aligns the Constitution with the Plan and resolves the contradiction with FR-001 in the spec.