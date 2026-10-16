# Implementation Plan: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Branch**: `001-explore-network-structure-superconducting-qubit-coupling` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/spec.md`

## Summary
This project investigates the **associational** relationship between the physical connectivity graph topology of superconducting quantum processors and their performance metrics (coherence times, gate errors, readout errors). The hypothesis is that certain topological descriptors (e.g., spectral gap, clustering coefficient) are **correlated** with better coherence and lower error rates. All statements are explicitly associational; no causal inference is claimed.

Because the number of publicly accessible IBM back‑ends is modest (≈ 10‑20 devices), the study is **exploratory**. We therefore:

* Compute a **Minimum Detectable Effect Size (MDES)** for Spearman ρ given the actual sample size and number of tests; if MDES > 0.5 we flag the analysis as low‑power and report bootstrap confidence intervals.
* Provide **bootstrap (1 000 resamples) BCa confidence intervals** for every correlation.
* Offer an **optional aggregation across chip families** (e.g., pooling Eagle devices) to increase effective N, documented as a sensitivity analysis.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `qiskit-ibm-runtime`, `networkx`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `requests`, `pingouin`, `pytest`  
- **Storage**: Files under `data/` (raw JSON snapshots, processed CSVs).  
- **Testing**: `pytest` unit & integration tests; schema validation against contracts.  
- **Target Platform**: Linux (`ubuntu-latest`) GitHub Actions runner.  
- **Performance Goals**: Full pipeline < 10 min, < 7 GB RAM, CPU‑only.  
- **Constraints**: No GPU, respect IBM API rate limits, exclude data > 30 days old (FR‑001).  
- **Scale/Scope**: All publicly accessible IBM back‑ends (spanning multiple devices).

## Constitution Check
| Principle | Status | Action / Verification |
|---|---|---|
| I. Reproducibility | PASS | Fixed random seeds, pinned dependencies, deterministic scripts. |
| II. Verified Accuracy | PASS | Citations will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | PASS | Raw JSON saved with SHA‑256 checksums; derived CSVs are new files. |
| IV. Single Source of Truth | PASS | All figures/tables generated from CSVs in `data/processed/`. |
| V. Versioning Discipline | PASS | `code/hygiene.py` updates `state/projects/...yaml` with artifact hashes. |
| VI. Calibration Data Integrity | PASS | Timestamp recorded for each snapshot; freshness filter applied. |
| VII. Topology Representation Fidelity | PASS | Graph built directly from `coupling_map` without abstraction. |

## Project Structure
```text
specs/001-exploring-the-role-of-network-structure-superconducting-qubit-coupling/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── raw_calibration.schema.yaml
│   ├── graph_metrics.schema.yaml
│   ├── performance_metrics.schema.yaml
│   ├── correlation_results.schema.yaml
│   └── mdes_report.schema.yaml
└── tasks.md   # to be created by /speckit-tasks
```

```text
projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│   ├── __init__.py
│   ├── fetcher.py           # FR‑001: API fetching, freshness check, metric extraction (FR‑002)
│   ├── graph_builder.py     # FR‑003: Graph construction, metric computation (including custom degree assortativity)
│   ├── stats_engine.py      # FR‑004: Correlation, partial correlation (covariates: chip_generation, qubit_count, device_age_days, readout_architecture), bootstrap CI, FDR correction, robustness, power/MDES analysis (PowerAnalysisResult)
│   ├── hygiene.py           # Principle V: checksums & state update
│   ├── viz.py               # Visualization of significant pairs and heatmaps
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # JSON snapshots (current and historical)
│   └── processed/           # CSVs for metrics, correlations, power analysis, plots
├── tests/
│   ├── test_fetcher.py
│   ├── test_graph_builder.py   # CLI accepts both --out and legacy --output flags; custom degree assortativity yields a strongly negative result for a 3‑node path as required by tests
│   ├── test_stats_engine.py
│   └── test_integration_fetch.py   # live API (rate‑limited)
└── requirements.txt
```

## Implementation Phases (mapped to FRs & SCs)

| Phase | Description | FR(s) / SC(s) Addressed |
|---|---|---|
| **Data Ingestion** | Fetch current and up‑to‑30‑day historical calibration snapshots; filter by freshness; store raw JSON. | FR‑001, FR‑002 |
| **Metric Extraction** | Parse JSON → `performance_metrics.csv`; compute per‑device aggregates (mean T1, T2, CX error, readout error). | FR‑002 |
| **Graph Construction** | Build undirected `networkx.Graph` from coupling map; compute metrics (avg shortest path, diameter, clustering, edge betweenness, **custom degree assortativity** yielding -1.0 for a 3‑node path, spectral gap). | FR‑003 |
| **Statistical Analysis** | Spearman correlation + **partial correlation** controlling for `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`; bootstrap 1 000 CI; BH‑FDR correction; robustness checks (LODO, chip‑family exclusion, **30‑day performance‑window comparison**, longitudinal drift assessment). | FR‑004, SC‑004 |
| **Power / MDES** | Compute Minimum Detectable Effect Size for Spearman ρ given N and number of tests; write results to `power_analysis.csv` conforming to `contracts/mdes_report.schema.yaml` (`PowerAnalysisResult` entity). Flag exploratory when MDES > 0.5. | FR‑004 |
| **Visualization** | Generate scatter plots for each significant (adj p < 0.05) metric pair; heatmap of full matrix; MDES summary table. | — |
| **Hygiene & Versioning** | Record checksums, update project state YAML. | — |

## Complexity Tracking
All FRs and SCs are now explicitly covered. The plan ties every functional requirement to a concrete module or task, includes the required SC‑004 robustness step, references the `PowerAnalysisResult` entity and its contract, and expands confound control. No undefined FR numbers (FR‑005/FR‑006/FR‑07) remain.

---



