# Quickstart: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Prerequisites
- Python 3.11+  
- Internet access (to call the IBM Quantum API)  
- (Optional) IBM Quantum API token for higher rate limits (`QISKIT_IBM_TOKEN` environment variable).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-163-exploring-the-role-of-network-structure-/
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify dependencies:

```bash
python -c "import networkx, pandas, qiskit_ibm_runtime, sklearn, scipy, matplotlib; print('All good')"
```

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the following steps in order:

1. **Fetch** calibration data (`fetcher.py`) – current snapshot + up to 30‑day historical window.  
2. **Build** graphs & compute metrics (`graph_builder.py`).  
3. **Analyze** correlations, partial correlations (covariates: `chip_generation`, `qubit_count`, `device_age_days`, `readout_architecture`, `timestamp`, `temperature`), permutation‑test confidence intervals (used when N < 30), FDR correction, and robustness checks (LODO, chip‑family exclusion, time‑window performance comparison, longitudinal stability).  
4. **Generate** power‑analysis/MDES report (`stats_engine.py`).  
5. **Visualize** results (`viz.py`) – scatter plots, heatmaps, and MDES summary figures are saved automatically as part of the reporting step (FR‑004).  
6. **Record** checksums & update project state (`hygiene.py`).

### Expected Outputs
- `data/raw/*.json` – raw API snapshots (current and historical).  
- `data/processed/performance_metrics.csv`  
- `data/processed/performance_window_metrics.csv` (30‑day averages)  
- `data/processed/graph_metrics.csv`  
- `data/processed/correlation_results.csv`  
- `data/processed/power_analysis.csv` (MDES report)  
- `data/processed/plots/*.png` – scatter plots & heatmaps.  
- Updated `state/projects/PROJ-163-...yaml` with artifact hashes.

## Testing

```bash
pytest tests/test_fetcher.py -v
pytest tests/test_graph_builder.py -v
pytest tests/test_stats_engine.py -v
pytest tests/test_integration_fetch.py -v   # live API (rate‑limited)
```

All tests must pass; schema validation is performed automatically against the files in `contracts/`.

## CLI Usage (graph_builder)

The graph‑building CLI accepts both the new `--out` flag and the legacy `--output` flag for backward compatibility:

```bash
python -m code.graph_builder --backend ibmq_manila --out graph_metrics.csv
# or
python -m code.graph_builder --backend ibmq_manila --output graph_metrics.csv
```

The CLI implements a **custom degree assortativity** calculation that yields –1.0 for a 3‑node path, matching the unit‑test expectation.

## Inspection Commands

```bash
head data/processed/performance_metrics.csv
head data/processed/graph_metrics.csv
grep True data/processed/correlation_results.csv   # show significant pairs
cat data/processed/power_analysis.csv
```

## Troubleshooting
- **Rate‑limit errors** – the fetcher retries with exponential backoff; add a token to `QISKIT_IBM_TOKEN` if needed.  
- **Disconnected graphs** – `spectral_gap` will be set to its baseline (no gap); path‑length metrics are computed on the largest component only.  
- **Missing metrics** – devices lacking a metric are simply omitted from that specific correlation test.  
- **Low statistical power** – if `N < 30`, the MDES report will flag the study as exploratory; permutation‑CI are used and bootstrap CIs are omitted.  

---

