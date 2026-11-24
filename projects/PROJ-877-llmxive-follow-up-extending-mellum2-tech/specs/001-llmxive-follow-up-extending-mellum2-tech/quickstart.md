# Quickstart: llmXive follow‑up – extending "Mellum2 Technical Report"

## Prerequisites
- Python 3.11 or newer  
- At least **8 GB RAM** (≥ 4 GB required for TinyLlama fallback)  
- Internet access (to download the verified code dataset and model)

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
# Execute the orchestrated pipeline (all phases)
python -m code.main --phase all
```

- The orchestrator runs phases 0 → 13 in order, respecting the CPU‑only constraint.  
- If the primary Mistral‑7B model exceeds memory, the pipeline automatically falls back to **TinyLlama‑1.1B** (`https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v0.1`, cited from arXiv 2401.02385) and logs a warning.  
- All results are written under `data/results/` and figures under `data/figures/`.

### Quick sanity‑check run (small sample)

```bash
python -m code.main --phase all --sample small
```

The `--sample small` flag forces `N = 50` repositories per language, enabling a fast end‑to‑end test (< 15 min). The log `logs/power_analysis.log` will show the sampled `N`.

## Expected Outputs
- `data/results/correlation_results.parquet`
- `data/results/threshold_results.parquet`
- `data/results/final_report.json`
- `data/figures/correlation_scatter.png`
- `data/figures/piecewise_fit.png`
- `data/checksums.txt` (SHA‑256 hashes of all artifacts)

## Verification Steps (addressing previous failures)

1. **Language‑count verification** – after Phase 1 the file `logs/phase1_counts.log` contains a table like:
   ```
   language  count
   python    a significant quantity
   java      a substantial quantity
   ```
   The pipeline aborts if any language does not have exactly `N` rows.

2 **Static‑analysis success check** – after Phase 2 the script validates `code_chunks.parquet` against `contracts/code_chunk.schema.yaml`. Any schema violations (e.g., missing `language` column) cause a fatal error with a clear message.

3. **Checksum logging** – every generated Parquet/JSON file is hashed and appended to `data/checksums.txt`; the final report lists these hashes for reproducibility.

4. **Human‑benchmark requirement** – the pipeline will abort if the CodeXGLUE dataset cannot be loaded, ensuring the primary construct‑validity claim is always tested.

## Troubleshooting
- **Missing language counts**: Inspect `logs/phase1_counts.log`. If counts are off, adjust the `--sample-size` flag or increase the streaming window.  
- **Out‑of‑memory**: The pipeline will automatically switch to TinyLlama; check `logs/model_load.log` for the switch message.  
- **Static analysis failures**: Review `logs/static_analysis_errors.log`. Chunks with parse errors are skipped but counted in the final summary.  
- **Benchmark unavailable**: The run aborts with a clear error; provide the CodeXGLUE dataset or resolve access issues.  

---



