# Implementation Plan: Quantifying the Impact of Network Proximity on Epidemic Spreading in Scale‑Free Networks

**Branch**: `001-network-proximity-epidemic` | **Date**: 2026-10-21 | **Spec**: [/specs/001-network-proximity-epidemic/spec.md](../specs/001-network-proximity-epidemic/spec.md)  
**Input**: Feature specification from `/specs/001-network-proximity-epidemic/spec.md`

## Summary
The project must (1) obtain a scale‑free network, (2) run a discrete‑time SIR simulation with (a) uniform transmission (λ = 0) and (b) distance‑scaled transmission (λ > 0), (3) generate a spatial‑null by randomising node coordinates, (4) sweep base transmission β ∈ [0.01, 0.5] (Δβ = 0.01) and λ ∈ {0.05, 0.1, 0.2}, (5) perform 50 Monte‑Carlo runs per configuration, (6) conduct permutation tests, and (7) respect the 6‑hour / 7 GB CPU‑only compute budget. Because no verified open dataset supplies a real‑world scale‑free graph **with geographic coordinates**, the plan falls back to (i) a synthetic Barabási‑Albert (BA) graph (open‑source generator) for the topology‑only baseline, and (ii) synthetic coordinates generated via Multidimensional Scaling (MDS) as a *synthetic‑control* condition. The empirical spatial effect (FR‑011) therefore cannot be evaluated on real geographic data; this limitation is explicitly flagged in the research design (see Research.md). All other functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑005) are addressed by concrete pipeline phases.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx>=3.2`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.12`, `scikit‑learn>=1.4`, `matplotlib>=3.8`, `tqdm>=4.66`, `datasets>=2.16` (for verified MDS and SIR parquet files), `pyyaml>=6.0` (for contracts).  
- **Storage**: Files under `data/` (raw network, generated coordinates, simulation results).  
- **Testing**: `pytest` with deterministic seeds; contract validation via `jsonschema`/`pyyaml`.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Project Type**: Research‑pipeline library + CLI driver.  
- **Performance Goals**: Entire pipeline ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 2 CPU cores.  
- **Constraints**: CPU‑only; no GPU off‑load required.  
- **Scale/Scope**: Baseline BA graph with ≈ 10 k nodes (fits memory).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned; external datasets (MDS JSON, SIR parquet) are fetched from the verified URLs listed in the spec. |
| II. Verified Accuracy | No new literature citations are introduced beyond the SIR model definition (standard epidemiology textbooks) – these will be validated by the Reference‑Validator. |
| III. Data Hygiene | Raw files are checksummed (`sha256`) and stored under `data/raw/`. Transformations write to `data/derived/` with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/derived/` and a specific line in `code/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/PROJ-263-...yaml` will be updated automatically by the platform. |
| VI. Spatial‑Topology Decoupling | Baseline (λ = 0) vs. spatial (λ > 0) vs. synthetic‑control (MDS coordinates) are explicitly compared; the null model randomises coordinates while preserving topology. |
| VII. Computational Boundedness | Pipeline includes dynamic down‑sampling and early‑termination heuristics (FR‑007) to guarantee ≤ 6 h runtime and ≤ 7 GB RAM. |

All principles are satisfied; no violations require justification.

## Project Structure
```text
specs/001-network-proximity-epidemic/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── simulation_output.schema.yaml
└── tasks.md            # (generated later by /speckit-tasks)

src/
├── pipeline/
│   ├── __init__.py
│   ├── config.py               # constant definitions, seeds, paths
│   ├── data_loader.py          # fetches verified MDS/SIR files, generates BA graph
│   ├── coordinate_generator.py # MDS fallback, randomisation for null
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
| **Phase 0 – Data Acquisition** | Load verified MDS JSON (coordinates) and SIR parquet (optional). Generate synthetic BA graph (10 k nodes) if no real network with coordinates exists. | FR‑001 (fallback), FR‑011 (MDS generation) | — |
| **Phase 1 – Pre‑processing** | Extract largest connected component (FR‑008). Generate synthetic coordinates via MDS when missing (FR‑011). Randomise coordinates 100× for null (FR‑004). | FR‑008, FR‑011, FR‑004 | — |
| **Phase 2 – Simulation Engine** | Implement discrete‑time SIR with βᵢⱼ = β₀·exp(‑λ·dᵢⱼ) (FR‑002). Sweep β ∈ [0.01, 0.5] (Δ=0.01) and λ ∈ {0.05, 0.1, 0.2} (FR‑006, FR‑013). Perform 50 Monte‑Carlo runs per config (FR‑003). | FR‑002, FR‑003, FR‑006, FR‑013 | SC‑002, SC‑004 |
| **Phase 3 – Threshold Estimation** | Binary‑search over β to locate epidemic threshold as defined in FR‑015 (≥5 % infected in >50 % runs). Handle “undefined” case (FR‑009). | FR‑015, FR‑009 | SC‑001 |
| **Phase 4 – Null Model & Statistics** | Run spatial‑null simulations (randomised coordinates) 100× (FR‑004). Perform two‑sample permutation test, report statistic, p‑value, Cohen’s d (FR‑014, FR‑005, FR‑010). Apply Bonferroni correction for the three λ values (multiple‑comparison). | FR‑004, FR‑005, FR‑014, FR‑010 | SC‑001, SC‑003 |
| **Phase 5 – Sensitivity & Runtime Guardrails** | Monitor wall‑clock; if >5 h, reduce remaining MC iterations (FR‑007). Log any down‑sampling of the graph (FR‑008). | FR‑007, FR‑008 | SC‑005 |
| **Phase 6 – Visualisation & Reporting** | Generate Fig 1 (threshold curve), Fig 2 (infection trajectory), Fig 3 (spatial heatmap) (FR‑012). Export CSV per simulation respecting schema (contract). | FR‑012 | SC‑001‑SC‑004 |
| **Phase 7 – Contract Validation** | Validate all CSV outputs against `contracts/simulation_output.schema.yaml`. | — | — |

## Tasks (to be materialised by `/speckit-tasks`)
1. `data_loader.load_or_generate_network()` – FR‑001, FR‑008.  
2. `coordinate_generator.ensure_coordinates()` – FR‑011.  
3. `coordinate_generator.randomise_coordinates(num=100)` – FR‑004.  
4. `sir_simulator.run(beta, lambda_, seed)` – FR‑002, FR‑003.  
5. `analysis.estimate_threshold()` – FR‑015, FR‑009.  
6. `analysis.perform_permutation_test()` – FR‑014, FR‑010.  
7. `visualisation.plot_threshold_curve()` – FR‑012.  
8. `visualisation.plot_infection_trajectory()` – FR‑012.  
9. `visualisation.plot_spatial_heatmap()` – FR‑012.  
10. `runtime.monitor_and_adjust()` – FR‑007.  
11. `contract.validate_output()` – contract compliance.

Each task will be implemented as a pure‑Python function, unit‑tested, and invoked from a top‑level CLI entry point `python -m src.pipeline.run --config config.yaml`.

---
