# Quickstart: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Prerequisites
- Python 3.11+  
- Internet connectivity (to query the IBM Quantum API).  
- (Optional) IBM Quantum API token for higher rate limits (`QISKIT_IBM_TOKEN` environment variable).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-163-exploring-the-role-of-network-structure-/
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify the environment:

```bash
python -c "import networkx, pandas, qiskit_ibm_runtime, pingouin, matplotlib; print('Ready')"
```

## Running the Full Pipeline

```bash
python code/main.py
```

The orchestrator executes the steps **in order**:

1. **Fetch** current and 30‑day historical calibration snapshots (`fetcher.py`).  
2. **Build** undirected coupling graphs and compute topological metrics (`graph_builder.py`).  
3. **Analyze** correlations, partial correlations, permutation‑based confidence intervals, FDR correction, and robustness checks (LODO, chip‑family exclusion, time‑window comparison) (`stats_engine.py`).  
4. **Generate** a power‑analysis / MDES report (`stats_engine.py`).  
5. **Visualize** scatter plots, heatmaps, and MDES summary (`viz.py`).  
6. **Record** SHA‑256 checksums and update `state/projects/...yaml` (`hygiene.py`).

### Expected Output Files

| Path | Description |
|------|-------------|
| `data/raw/*.json` | Raw JSON calibration snapshots (current + historical). |
| `data/processed/performance_metrics.csv` | Median performance metrics per device (`source_window="current"`). |
| `data/processed/performance_window_metrics.csv` | Time‑averaged performance metrics (`source_window="window"`). |
| `data/processed/graph_metrics.csv` | Topological descriptors per device. |
| `data/processed/correlation_results.csv` | Spearman/partial correlation results (schema: `contracts/correlation_results.schema.yaml`). |
| `data/processed/window_comparison.csv` | Cross‑sectional vs. window ρ and `window_delta` (SC‑004). |
| `data/processed/power_analysis.csv` | MDES and power‑analysis report (schema: `contracts/mdes_report.schema.yaml`). |
| `data/processed/plots/*.png` | Scatter plots, correlation heatmap, MDES figure. |
| `state/projects/PROJ-163-...yaml` | Artifact hashes and timestamps for reproducibility. |

## Testing

```bash
pytest tests/test_fetcher.py -v
pytest tests/test_graph_builder.py -v
pytest tests/test_stats_engine.py -v
pytest tests/test_integration_fetch.py -v   # hits live API (rate‑limited)
```

All tests must pass; schema validation is performed automatically against the files in `contracts/`.

## CLI Usage (graph_builder)

The graph‑building CLI accepts both the new `--out` flag and the legacy `--output` flag for backward compatibility:

```bash
python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv
# or
python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv
```

The CLI implements a **custom degree assortativity** calculation that yields –1.0 for a 3‑node path, satisfying the unit‑test expectation.

## Inspection Commands

```bash
head data/processed/performance_metrics.csv
head data/processed/graph_metrics.csv
grep True data/processed/correlation_results.csv   # show significant pairs
cat data/processed/power_analysis.csv
```

## Troubleshooting
- **Rate‑limit errors** – the fetcher retries with exponential backoff; set `QISKIT_IBM_TOKEN` to increase limits.  
- **Disconnected graphs** – `spectral_gap` will be assigned its minimal baseline value; path‑length metrics are computed on the largest component only.  
- **Missing metrics** – devices lacking a metric are omitted from that specific correlation pair.  
- **Low statistical power** – if `N < 30`, the MDES report will flag the study as exploratory; only effect‑size estimates with permutation‑CI are reported.  

---
