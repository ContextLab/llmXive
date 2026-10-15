# Quickstart: llmXive follow‑up – extending "Mellum2 Technical Report"

## Prerequisites
- Python 3.11+
- 8 GB RAM (≥ 4 GB for TinyLlama fallback)
- Internet access (to download HuggingFace dataset & model)

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the full pipeline

```bash
# Execute the orchestrated pipeline
python -m code.main --phase all
```

- The orchestrator runs phases 0 → 11 in order, respecting the CPU‑only constraint.
- If the primary Mistral‑7B model exceeds memory, the pipeline automatically switches to TinyLlama‑1.1B and logs a warning.
- All results are written under `data/results/` and figures under `data/figures/`.

### Quick sanity‑check run (small sample)

```bash
python -m code.main --phase all --sample small
```

The `--sample small` flag tells `code/config.py` to set `N = 50` per language, enabling a fast end‑to‑end test (< 15 min).

## Expected Outputs
- `data/results/correlation_results.parquet`
- `data/results/threshold_results.parquet`
- `data/results/final_report.json`
- `data/figures/correlation_scatter.png`
- `data/figures/piecewise_fit.png`

## Troubleshooting
- **Missing language counts**: Verify `logs/phase1_counts.log` contains a `groupby('language')` summary.  
- **Out‑of‑memory**: The pipeline will fallback to TinyLlama automatically; check `logs/model_load.log`.  
- **No benchmark found**: A limitation report will appear in `final_report.json` under `validation.benchmark_used = false`.  

---
