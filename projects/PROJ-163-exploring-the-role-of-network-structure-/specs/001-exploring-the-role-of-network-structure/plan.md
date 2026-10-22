# Implementation Plan: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Branch**: `001-explore-network-structure-superconducting-qubit-coupling` | **Date**: 2026-10-22 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/spec.md`

## Summary
We will programmatically fetch live and recent historical calibration snapshots from all publicly accessible IBM Quantum back‑ends, construct undirected coupling‑graph representations (annotating tunable‑coupler edges), compute a suite of topological descriptors (including spectral gap, assortativity, clustering, etc.), and correlate them with contemporaneous performance metrics (T₁, T₂, gate errors, readout errors, entanglement fidelity). The primary analysis is cross‑sectional; robustness is assessed via Leave‑One‑Device‑Out (LODO) and a a short‑term historical window. Because the publicly available IBM back‑ends number fewer than the ~44 devices required for [deferred] power at ρ = 0.4, the pipeline will **perform a priori power analysis, report the achievable power, and flag the study as exploratory when power is insufficient** rather than asserting ≥ 80 % power.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `qiskit-ibm-runtime`, `networkx`, `pandas`, `numpy`, `scipy`, `pingouin`, `statsmodels`, `matplotlib`, `seaborn`, `pytest`  
- **Storage**: Files under `data/` (raw JSON snapshots, processed CSVs, PNG figures)  
- **Testing**: `pytest` unit & integration tests; schema validation against contracts in `contracts/`  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner (CPU‑only)  
- **Constraints**: Respect IBM API rate limits (C‑001), exclude stale data (FR‑001), no synthetic data (NFR‑002)  

## Constitution Check
| Principle | Status | Verification |
|-----------|--------|--------------|
| I. Reproducibility | PASS | Fixed seeds, deterministic scripts, pinned `requirements.txt`. |
| II. Verified Accuracy | PASS | All citations will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | PASS | Raw JSON saved with SHA‑256 checksums; derived files are new and version‑hashed. |
| IV. Single Source of Truth | PASS | **Every figure/table is generated from a single CSV row; the markdown report explicitly references those rows**, satisfying the traceability requirement. |
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
│   ├── correlation_results.schema.yaml
│   ├── graph_metrics.schema.yaml
│   ├── mdes_report.schema.yaml
│   ├── performance_metrics.schema.yaml
│   └── raw_calibration.schema.yaml
└── tasks.md   # generated later

projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│   ├── __init__.py
│   ├── fetcher.py           # FR‑001, FR‑002, FR‑012
│   ├── graph_builder.py     # FR‑003, FR‑007, FR‑013
│   ├── stats_engine.py      # FR‑004, FR‑008, FR‑010, FR‑011, FR‑005
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
| **0 – Data Ingestion** | • Authenticate (optional token).<br>• Query `IBMQBackendService().backend_properties()` for all public back‑ends (current snapshot).<br>• Loop over a recent multi‑day period via IBM archive API to fetch daily snapshots.<br>• Apply exponential backoff (max 3 retries) per C‑001.<br>• Filter out any snapshot older than 30 days (FR‑001).<br>• Save raw JSON to `data/raw/` with SHA‑256 checksums. | FR‑001, FR‑002, FR‑012 | — |
| **1 – Metric Extraction** | • Parse each JSON to extract T₁, T₂, CX gate error, readout error, **entanglement fidelity**, and `coupling_map` (FR‑002, FR‑006).<br>• Compute per‑device **median** of per‑qubit values (FR‑003).<br>• Write `performance_metrics.csv` (wide format) with `source_window="current"` (SC‑001). | FR‑002, FR‑003, FR‑006 | SC‑001 |
| **2 – Graph Construction** | • Build undirected `networkx.Graph` from `coupling_map` (FR‑003, FR‑007).<br>• Annotate edges with `edge_type` (`active`/`inactive`) for tunable‑coupler devices (FR‑007).<br>• Compute: average shortest‑path length, diameter, global clustering coefficient, mean edge betweenness, **degree assortativity**, **spectral gap** (FR‑013).<br>• For disconnected graphs, path‑length metrics are computed on the largest component; spectral gap = 0 (C‑002).<br>• Record `is_finite` and `component_size`.<br>• Export `graph_metrics.csv`. | FR‑003, FR‑007, FR‑013 | SC‑002 |
| **3 – Timestamp Guard** | • Verify that topology and performance timestamps differ by **≤ 1 hour** for each device.<br>• If any pair exceeds this bound, raise a `RuntimeError` and abort the pipeline (FR‑005). This guarantees true simultaneity of the cross‑sectional data. | FR‑005 | — |
| **4 – Primary Statistical Analysis** | • Join `graph_metrics.csv` and `performance_metrics.csv` on `device_id`.<br>• **Spearman Correlation** for each topology‑performance pair.<br>• **Permutation Test** if N < 30 (10 000 permutations) else exact p‑value.<br>• **Partial Correlation** controlling for chip generation, qubit count, device age, readout architecture, timestamp (FR‑011).<br>• **Benjamini‑Hochberg FDR** correction across all tests (SC‑003).<br>• Write `correlation_results.csv` (includes optional `window_delta`). | FR‑004, FR‑008, FR‑011, FR‑005 | SC‑003 |
| **5 – Robustness Checks** | • **LODO**: repeat Phase 4 omitting each device; store per‑fold ρ values.<br>• **Chip‑family exclusion**: repeat after removing each generation.<br>• **30‑Day Window**: re‑run Phase 4 using `"window"` rows; compute `window_delta = ρ_window − ρ_cross` and verify it lies within ±0.05 (SC‑004).<br>• **Longitudinal Stability**: compute variance of each performance metric across the 30‑day window; flag devices with high drift. | FR‑004, FR‑010, FR‑012 | SC‑004 |
| **6 – Power / MDES Analysis** | • Compute Minimum Detectable Effect Size for Spearman ρ at 80 % power, α = 0.05 (FR‑010).<br>• **Exploratory Flag**: because the available device count (< 30) yields **< 80 % power** for detecting ρ = 0.4, the MDES will exceed 0.5. The pipeline automatically labels the study *exploratory* and refrains from declaring statistical significance; only effect‑size estimates with permutation‑based confidence intervals are reported (SC‑007).<br>• Write `power_analysis.csv`. | FR‑010 | SC‑007 |
| **7 – Visualization & Reporting** | • Scatter plots for each topology‑performance pair (significant after FDR).<br>• Heatmap of the full correlation matrix, including covariates.<br>• MDES summary figure.<br>• **Traceability**: each PNG is generated from the exact CSV row(s) that supplied the data; the markdown report explicitly references those rows, satisfying Constitution Principle IV.<br>• Save PNGs under `data/processed/plots/` and assemble a markdown report that embeds all figures and tables (FR‑009, SC‑005, SC‑006). | FR‑009 | SC‑005, SC‑06 |
| **(No additional phases)** | The plan deliberately omits a separate “Contract Validation” or “Reproducibility & Hygiene” phase; validation is performed automatically by schema‑based tests, and reproducibility is enforced by the Constitution and CI workflow. | — | — |

## Compute Feasibility
- **Hardware**: GitHub Actions free tier (2 CPU cores, ~7 GB RAM, ~14 GB disk).  
- **Data Size**: < 2 MB total JSON (current + 30‑day window).  
- **Runtime**: Expected < 10 minutes for the full pipeline; all libraries run on CPU.  
- No GPU resources are required.

---



