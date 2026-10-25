# Implementation Plan: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

**Branch**: `001-network-proximity-epidemic` | **Date**: 2026-10-25 | **Spec**: [/specs/001-network-proximity-epidemic/spec.md](../specs/001-network-proximity-epidemic/spec.md)  
**Input**: Feature specification from `/specs/001-network-proximity-epidemic/spec.md`

## Summary
Implement a reproducible pipeline that (1) obtains a **real‑world** scale‑free network with genuine geographic coordinates (Brightkite social network). If the Brightkite dataset cannot be fetched, the pipeline aborts with a clear error (no synthetic topology is used for primary analysis, preserving FR‑001). (2) runs a discrete‑time SIR simulation with uniform transmission (λ = 0) and distance‑scaled transmission (βᵢⱼ = β₀·e^{‑λ·dᵢⱼ}) using the **real coordinates** for the primary spatial condition. (3) generates a **synthetic‑control** condition by assigning **random uniform coordinates** (independent of topology) when real coordinates are missing, and (4) generates a spatial‑null distribution by randomising the **empirical** coordinates (no MDS). (5) sweeps β₀ over [0.01, 0.46] in **0.05** increments and λ ∈ {0.05, 0.1, 0.2}. (6) executes **15** Monte‑Carlo runs per configuration (reduced from 50 for compute feasibility). (7) estimates epidemic thresholds, (8) performs two‑sample permutation tests with Bonferroni correction, (9) conducts a sensitivity analysis on λ, and (10) respects the 6‑hour / 7 GB CPU‑only compute budget. All outputs are validated against a JSON‑Schema contract.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx>=3.2`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `tqdm>=4.66`, `datasets>=2.16`, `pyyaml>=6.0`  
- **Storage**: Files under `data/` (raw, derived, outputs).  
- **Testing**: `pytest` with deterministic seeds; contract validation via `pyyaml`.  
- **Target Platform**: Linux (GitHub Actions free‑tier runner).  
- **Project Type**: Research‑pipeline library + CLI driver.  
- **Performance Goals**: ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 2 CPU cores.  
- **Constraints**: CPU‑only; no GPU off‑load required.  
- **Scale/Scope**: Real Brightkite network (on the order of tens of thousands of nodes, approximately one million edges). The pipeline **automatically extracts the largest connected component** and **down‑samples to 10 k nodes** if memory would exceed ~7 GB; this action is logged (FR‑008).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned; external datasets (Brightkite SNAP dump) are fetched from the verified URL listed in `research.md`. |
| II. Verified Accuracy | No new literature citations beyond standard SIR and exponential decay references; these will be validated by the Reference‑Validator. |
| III. Data Hygiene | Raw files are checksummed (`sha256`) and stored under `data/raw/`. Transformations write to `data/derived/` with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/derived/` and a specific line in `code/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/PROJ-263-...yaml` will be updated automatically. |
| VI. Spatial‑Topology Decoupling | Primary analysis uses **real geographic coordinates** from Brightkite, ensuring spatial effects are independent of topology. Synthetic‑control coordinates are random and independent of the graph structure. |
| VII. Computational Boundedness | Dynamic down‑sampling, reduced Monte‑Carlo count, and early‑termination guardrails guarantee ≤ 6 h runtime and ≤ 7 GB RAM. |

All principles are satisfied; no violations requiring justification.

## Project Structure
```text
specs/001-network-proximity-epidemic/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── simulation_output.schema.yaml
└── tasks.md            # generated later by /speckit-tasks

src/
├── pipeline/
│   ├── __init__.py
│   ├── config.py               # seeds, paths, constants
│   ├── data_loader.py          # loads Brightkite or aborts
│   ├── coordinate_generator.py # random‑control, null randomisation
│   ├── sir_simulator.py        # discrete‑time SIR with distance‑scaled β
│   ├── analysis.py             # threshold estimation, permutation test
│   └── visualisation.py        # Fig 1‑3 generation
tests/
├── unit/
│   └── test_sir_simulator.py
└── contract/
    └── test_simulation_output.py
```

## Mapping of Functional Requirements & Success Criteria to Plan Phases
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **Phase 0 – Data Acquisition** | Download Brightkite edge list and node latitude/longitude (verified URL). Abort with error if download fails (FR‑001). | FR‑001 | — |
| **Phase 1 – Pre‑processing** | Extract the largest connected component (FR‑008). Log size of any discarded components. Generate **synthetic‑control** coordinates uniformly at random (FR‑011). Randomise empirical coordinates 20 × for null (reduced from 100, FR‑004). | FR‑008, FR‑011, FR‑004 | — |
| **Phase 2 – Simulation Engine** | Implement discrete‑time SIR with βᵢⱼ = β₀·exp(‑λ·dᵢⱼ) (FR‑002). Sweep β₀ ∈ {0.01,0.06,0.11,0.16,0.21,0.26,0.31,0.36,0.41,0.46} and λ ∈ {0.05,0.1,0.2} (FR‑006, FR‑013). Perform **15** Monte‑Carlo runs per config (FR‑003, reduced for compute). | FR‑002, FR‑003, FR‑006, FR‑013 | SC‑002, SC‑004 |
| **Phase 3 – Threshold Estimation** | Binary‑search over β₀ to locate the smallest β₀ where ≥5 % of nodes become infected in >50 % of MC runs (FR‑015). Handle “undefined” case per FR‑009. | FR‑015, FR‑009 | SC‑001 |
| **Phase 4 – Null Model & Statistics** | Run spatial‑null simulations (randomised empirical coordinates) 20 × (FR‑004). Perform two‑sample permutation test, report statistic, p‑value, Cohen’s d (FR‑014, FR‑005, FR‑010). Apply Bonferroni correction for the three λ values (multiple‑comparison). | FR‑004, FR‑005, FR‑014, FR‑010 | SC‑001, SC‑003 |
| **Phase 5 – Sensitivity & Runtime Guardrails** | After each batch of 10 MC runs, log cumulative wall‑clock time. If cumulative time > 5 h, truncate remaining iterations to stay ≤ 6 h (FR‑007). If graph size > 10 k nodes, uniformly down‑sample to 10 k and log the action (FR‑008). | FR‑007, FR‑008 | SC‑005 |
| **Phase 6 – Visualisation & Reporting** | Generate Fig 1 (threshold curve), Fig 2 (infection trajectory), Fig 3 (spatial heatmap) (FR‑012). Export CSVs and validate them against `contracts/simulation_output.schema.yaml`. (Contract validation merged here, removing the previously separate Phase 7.) | FR‑012 | SC‑001‑SC‑004 |

## Tasks (to be materialised by `/speckit-tasks`)
1. `data_loader.load_network_or_abort()` – FR‑001, FR‑008.  
2. `coordinate_generator.generate_random_control()` – FR‑011.  
3. `coordinate_generator.randomise_empirical(num=20)` – FR‑004.  
4. `sir_simulator.run(beta_0, lambda_, seed)` – FR‑002, FR‑003. *(parameter name aligned with schema)*  
5. `analysis.estimate_threshold()` – FR‑015, FR‑009.  
6. `analysis.perform_permutation_test()` – FR‑014, FR‑010.  
7. `visualisation.plot_threshold_curve()` – FR‑012.  
8. `visualisation.plot_infection_trajectory()` – FR‑012.  
9. `visualisation.plot_spatial_heatmap()` – FR‑012.  
10. `runtime.monitor_and_adjust()` – FR‑007.  
11. `contract.validate_output()` – integrated into Phase 6 (no separate FR required).  

Each task will be a pure‑Python function, unit‑tested, and invoked from a top‑level CLI entry point `python -m src.pipeline.run --config config.yaml`.
