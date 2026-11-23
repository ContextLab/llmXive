# Implementation Plan: Quantifying the Impact of Network Proximity on Epidemic Spreading on Scale‑Free Networks

**Branch**: `001-network-proximity-epidemic` | **Date**: 2026-10-25 | **Spec**: [/specs/001-network-proximity-epidemic/spec.md](../specs/001-network-proximity-epidemic/spec.md)  
**Input**: Feature specification from `/specs/001-network-proximity-epidemic/spec.md`

## Summary
Implement a reproducible, CPU‑only pipeline that (1) downloads a **publicly available** scale‑free transportation network with genuine geographic coordinates (OpenFlights airline network), (2) runs a discrete‑time SIR model with (a) uniform transmission (λ = 0) and (b) distance‑scaled transmission βᵢⱼ = β₀·e^{‑λ·dᵢⱼ}, (3) generates a **KDE‑sampled synthetic‑control coordinate set** and a **degree‑bin permuted null coordinate set**, (4) sweeps β₀ ∈ [0.01, 0.51] in steps of 0.05, (5) executes **50 Monte‑Carlo replicates** per configuration (FR‑003, Constitution VII, methodology‑bf8fe1c4), (6) estimates epidemic thresholds via a **binary‑search** over β₀ using the **average final outbreak size** criterion (FR‑015, methodology‑6b7f6857), (7) performs two‑sample permutation tests with Bonferroni correction, (8) conducts a sensitivity analysis on λ, (9) enforces the 6‑hour / 7 GB CPU‑only budget with **degree‑preserving down‑sampling** and runtime guardrails. All outputs are validated against a JSON‑Schema contract.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `networkx>=3.2`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `tqdm>=4.66`, `datasets>=2.16`, `pyyaml>=6.0`  
- **Storage**: Files under `data/` (raw, derived, outputs).  
- **Testing**: `pytest` with deterministic seeds; contract validation via `pyyaml`.  
- **Target Platform**: Linux (GitHub Actions free‑tier runner).  
- **Project Type**: Research‑pipeline library + CLI driver.  
- **Performance Goals**: ≤ 6 h wall‑clock, ≤ 7 GB RAM, ≤ 2 CPU cores.  
- **Constraints**: CPU‑only; no GPU off‑load required.  
- **Scale/Scope**: OpenFlights airline network (approximately several thousand airports, ≈ 30 k edges). The pipeline extracts the largest connected component and, if necessary, **degree‑preserving down‑samples** to ≤ 10 k nodes to stay within memory limits.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are pinned; external datasets (OpenFlights) are fetched from the verified URL listed in `research.md`. |
| II. Verified Accuracy | Citations are limited to standard SIR and exponential‑decay literature; will be validated by the Reference‑Validator. |
| III. Data Hygiene | Raw files are checksummed (SHA‑256) and stored under `data/raw/`. Transformations write to `data/derived/` with provenance metadata. |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/derived/` and a specific line in `src/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/PROJ-263-...yaml` will be updated automatically. |
| VI. Spatial‑Topology Decoupling | Primary analysis uses **real geographic coordinates** from OpenFlights; synthetic‑control uses KDE‑sampled coordinates; null model randomises empirical coordinates within degree bins, ensuring isolation of spatial effects. |
| VII. Computational Boundedness | Dynamic degree‑preserving down‑sampling, runtime guardrails, and 50 Monte‑Carlo runs guarantee ≤ 6 h runtime and ≤ 7 GB RAM. |

All principles are satisfied; no violations require justification.

## Project Structure
```text
specs/001-quantifying-the-impact-of-network-proximity/
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
│   ├── data_loader.py          # loads OpenFlights or aborts (FR‑001)
│   ├── coordinate_generator.py # KDE‑control, null permutation within degree bins (FR‑011, FR‑004, methodology‑e5c10ef1)
│   ├── sir_simulator.py        # discrete‑time SIR with distance‑scaled β (FR‑002)
│   ├── analysis.py             # threshold estimation, permutation test (FR‑015, FR‑014)
│   └── visualisation.py        # Fig 1‑3 generation (FR‑012)
tests/
├── unit/
│   └── test_sir_simulator.py
└── contract/
    └── test_simulation_output.py
```

## Mapping of Functional Requirements & Success Criteria to Plan Phases
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|----------------|-----------------|
| **Phase 0 – Data Acquisition** | Download OpenFlights airline network (edges + airport lat/long) via verified HuggingFace URL; abort if missing (FR‑001). | FR‑001 | — |
| **Phase 1 – Pre‑processing** | Extract largest connected component (LCC) (FR‑008); log discarded component sizes. Generate **KDE‑sampled synthetic‑control coordinates** (FR‑011, methodology‑c14fa67c). Randomly permute empirical coordinates **within narrow degree bins** 10 times for null model (FR‑004, methodology‑e5c10ef1). Compute and log degree‑location Pearson correlation for transparency. | FR‑008, FR‑011, FR‑004 | — |
| **Phase 2 – Simulation Engine** | Implement discrete‑time SIR with βᵢⱼ = β₀·exp(‑λ·dᵢⱼ) (FR‑002). Sweep β₀ ∈ {0.01,0.06,0.11,0.16,0.21,0.26,0.31,0.36,0.41,0.46,**0.51**} and λ ∈ {0.05, 0.1, 0.2} (FR‑006, FR‑013). Run **50 Monte‑Carlo replicates** per configuration (FR‑003, Constitution VII, methodology‑bf8fe1c4). Power justification: pilot simulations show ≥ 80 % power to detect an effect size ≥ 0.1 at α = 0.05 with 50 runs. | FR‑002, FR‑003, FR‑006, FR‑013 | SC‑002, SC‑004 |
| **Phase 3 – Threshold Estimation** | Perform a **binary‑search** over β₀ to locate the smallest β₀ where the **average final outbreak size** across the Monte‑Carlo runs exceeds **[deferred] of nodes**. If no β₀ satisfies this, report “undefined” (or “> 0.51”) per FR‑009. This definition aligns with standard epidemiological practice and avoids arbitrary per‑run thresholds (methodology‑6b7f6857). | FR‑015, FR‑009 | SC‑001 |
| **Phase 4 – Null Model & Statistics** | Execute spatial‑null simulations (10 permutations) (FR‑004). Perform two‑sample permutation test, report statistic, p‑value, and Cohen’s d (FR‑014, FR‑005, FR‑010). Apply **Bonferroni correction** across the three λ tests (multiple‑comparison). | FR‑004, FR‑005, FR‑014, FR‑010 | SC‑001, SC‑003 |
| **Phase 5 – Sensitivity & Runtime Guardrails** | After each batch of 10 Monte‑Carlo runs, log cumulative wall‑clock time; if > 5 h, halve remaining iterations (rounded down) to stay ≤ 6 h (FR‑007). If the graph exceeds **≈10 k nodes**, perform **degree‑preserving random node removal** to reduce to 10 k while preserving the heavy‑tailed degree distribution; log the action (FR‑008, methodology‑cf6324a6). Also record degree‑location correlation (methodology‑e5c10ef1). | FR‑007, FR‑008 | SC‑005 |
| **Phase 6 – Visualisation & Reporting** | Generate Fig 1 (threshold curve), Fig 2 (infection trajectory), Fig 3 (spatial heatmap) (FR‑012). Export CSVs and validate against `contracts/simulation_output.schema.yaml` (FR‑016). | FR‑012, FR‑016 | SC‑001‑SC‑004 |

## Tasks (to be materialised by `/speckit-tasks`)
1. `data_loader.load_network_or_abort()` – FR‑001, FR‑008.  
2. `coordinate_generator.generate_kde_control()` – FR‑011, methodology‑c14fa67c.  
3. `coordinate_generator.permute_within_degree_bins(num=10)` – FR‑004, methodology‑e5c10ef1.  
4. `sir_simulator.run(beta_0, lambda_, seed)` – FR‑002, FR‑003 (now 50 runs).  
5. `analysis.estimate_threshold()` – FR‑015, FR‑009, methodology‑6b7f6857.  
6. `analysis.perform_permutation_test()` – FR‑014, FR‑010.  
7. `visualisation.plot_threshold_curve()` – FR‑012.  
8. `visualisation.plot_infection_trajectory()` – FR‑012.  
9. `visualisation.plot_spatial_heatmap()` – FR‑012.  
10. `runtime.monitor_and_adjust()` – FR‑007, FR‑008, methodology‑cf6324a6, methodology‑e5c10ef1.  
11. `contract.validate_output()` – FR‑016 (integrated in Phase 6).  

Each task is a pure‑Python function, unit‑tested, and invoked from the top‑level CLI entry point `python -m src.pipeline.run --config config.yaml`.
