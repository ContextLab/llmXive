# Implementation Plan: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Branch**: `001-explore-network-structure-superconducting-qubit-coupling` | **Date**: 2026-10-16 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/spec.md`

## Summary
We will retrieve live calibration data from all publicly accessible IBM Quantum back‑ends, construct undirected coupling‑graph representations, compute a suite of topological descriptors (including spectral gap), and correlate them with contemporaneous performance metrics (T₁, T₂, CX gate error, readout error, entanglement fidelity). The primary analysis is cross‑sectional; robustness is assessed via Leave‑One‑Device‑Out (LODO) and a 30‑day historical performance window. Power analysis targets ≥ 80 % power to detect a Spearman ρ = 0.4. All steps are reproducible on a GitHub Actions CPU‑only runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `qiskit-ibm-runtime`, `networkx`, `pandas`, `numpy`, `scipy`, `pingouin`, `matplotlib`, `seaborn`, `statsmodels`, `pytest`  
- **Storage**: Files under `data/` (raw JSON snapshots, processed CSVs, PNG figures)  
- **Testing**: `pytest` unit & integration tests; schema validation against contracts in `contracts/`  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner (CPU‑only)  
- **Constraints**: Respect IBM API rate limits (C‑001), exclude stale data (FR‑001), no synthetic data (NFR‑002)  

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic scripts, pinned `requirements.txt`. |
| II. Verified Accuracy | PASS | All citations will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | PASS | Raw JSON saved with SHA‑256 checksums; derived files are new and version‑hashed. |
| IV. Single Source of Truth | PASS | Every figure/table is generated directly from CSV artifacts. |
| V. Versioning Discipline | PASS | `hygiene.py` updates `state/projects/...yaml` with artifact hashes. |
| VI. Calibration Data Integrity | PASS | Each metric row records the exact calibration timestamp; freshness filter applied. |
| VII. Topology Representation Fidelity | PASS | Graphs are built directly from the `coupling_map` without abstraction. |

## Project Structure
```text
specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── correlation_results.schema.yaml
└── tasks.md   # generated later

projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│   ├── __init__.py
│   ├── fetcher.py           # FR‑001, FR‑002, FR‑012
│   ├── graph_builder.py     # FR‑003, FR‑007, FR‑013
│   ├── stats_engine.py      # FR‑004, FR‑008, FR‑010, FR‑011
│   ├── viz.py               # FR‑009
│   ├── hygiene.py           # data‑hygiene & checksum handling
│   └── main.py              # orchestration
├── data/
│   ├── raw/                 # JSON snapshots (current + historical)
│   └── processed/
│       ├── performance_metrics.csv
│       ├── graph_metrics.csv
│       ├── correlation_results.csv
│       ├── power_analysis.csv
│       └── plots/
├── tests/
│   ├── test_fetcher.py
│   ├── test_graph_builder.py
│   ├── test_stats_engine.py
│   └── test_integration_fetch.py
└── requirements.txt
```

## Implementation Phases (Coverage of All FRs & SCs)

| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|------------------|-----------------|
| **0 – Data Ingestion** | • Authenticate (optional token).<br>• Query `IBMQBackendService().backend_properties()` for all public back‑ends (current snapshot).<br>• Loop over past 30 days via IBM archive API to fetch daily snapshots.<br>• Apply exponential backoff (C‑001).<br>• Filter out any snapshot older than 30 days (FR‑001).<br>• Save raw JSON to `data/raw/` with SHA‑256 checksum. | FR‑001, FR‑002, FR‑012 | — |
| **1 – Metric Extraction** | • Parse each JSON to extract T₁, T₂, CX gate error, readout error, **entanglement fidelity**, and `coupling_map` (FR‑002, FR‑006).<br>• Compute per‑device median of per‑qubit values (FR‑003).<br>• Write `performance_metrics.csv` with `source_window="current"` (SC‑001). | FR‑002, FR‑003, FR‑006 | SC‑001 |
| **2 – Graph Construction** | • Build undirected `networkx.Graph` from `coupling_map` (FR‑003, FR‑007).<br>• For tunable couplers, annotate edges with `edge_type` (`active`/`inactive`).<br>• Compute metrics: average shortest‑path length, diameter, global clustering coefficient, mean edge betweenness, **degree assortativity**, **spectral gap** (FR‑013).<br>• For disconnected graphs, compute path‑length metrics on the largest component; set spectral gap = 0 (C‑002).<br>• Record `is_finite` and `component_size`.<br>• Export `graph_metrics.csv`. | FR‑003, FR‑007, FR‑013 | SC‑002 |
| **3 – Primary Statistical Analysis** | • Join `graph_metrics.csv` and `performance_metrics.csv` on `device_id`.<br>• Verify timestamps differ ≤ 1 hour; raise `RuntimeError` if not (FR‑005).<br>• **Spearman** correlation for each topology‑performance pair (FR‑004).<br>• **Permutation‑test** p‑values & 95 % CI when N < 30; otherwise exact p‑value.<br>• **Partial correlation** controlling for chip generation, qubit count, device age, readout architecture, timestamp (FR‑011).<br>• **Benjamini‑Hochberg FDR** correction across all tests (SC‑003).<br>• Write `correlation_results.csv`. | FR‑004, FR‑008, FR‑011 | SC‑003 |
| **4 – Robustness Checks** | • **LODO**: repeat Phase 3 omitting each device; store per‑fold ρ values.<br>• **Chip‑family exclusion**: repeat after removing each generation.<br>• **30‑day window**: run Phase 3 using rows with `source_window="window"` (derived from historical snapshots).<br>• Verify LODO sign retention ≥ 90 % (SC‑004) and window ρ within ±0.05 of cross‑sectional ρ (SC‑004). | FR‑004, FR‑010, FR‑012 | SC‑004 |
| **5 – Power / MDES Analysis** | • Compute Minimum Detectable Effect Size for Spearman ρ at 80 % power, α = 0.05 (FR‑010).<br>• If MDES > 0.5, flag study as exploratory and suppress significance claims (SC‑007).<br>• Write `power_analysis.csv`. | FR‑010 | SC‑007 |
| **6 – Visualization & Reporting** | • Scatter plots for each topology‑performance pair (significant after FDR).<br>• Heatmap of the full correlation matrix.<br>• MDES summary figure.<br>• Assemble a markdown report that embeds all PNGs (FR‑009, SC‑005).<br>• Save figures under `data/processed/plots/`. | FR‑009 | SC‑005, SC‑006 |
| **7 – Contract Validation** | • Validate all CSV outputs against their JSON‑Schema contracts (`contracts/*.schema.yaml`).<br>• Record validation results in CI logs. | — | — |
| **8 – Reproducibility & Hygiene** | • Run `hygiene.py` to compute checksums, update `state/projects/...yaml`.<br>• Pin random seeds in all scripts.<br>• Ensure CI workflow executes the full pipeline end‑to‑end. | — | I, III, V |

All functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑007) are explicitly addressed by the phases above. No extra constraints have been introduced.

---
