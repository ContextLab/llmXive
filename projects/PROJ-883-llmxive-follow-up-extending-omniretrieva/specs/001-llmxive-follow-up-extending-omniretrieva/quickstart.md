# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11 or newer
- Linux environment (GitHub Actions runner or local Linux VM)
- Internet access (to download the open datasets)

## Installation
```bash
# Clone the repository (if not already)
git clone https://github.com/your-org/llmxive-follow-up-extending-omniretrieva.git
cd llmxive-follow-up-extending-omniretrieva

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## Verify the Environment
These commands must succeed; the integration test `tests/integration/test_skeleton.py` checks them and stores the outputs under `artifacts/`.

1. **Lint the codebase**
   ```bash
   ruff check code/
   ```
   *Expected:* exit code 0 and a non‑empty `artifacts/ruff_output.txt`.

2. **Show the CLI help**
   ```bash
   python -m code.main --help
   ```
   *Expected:* help text printed and saved to `artifacts/help_output.txt`.

3. **Run the CLI with no arguments (defaults to full benchmark)**
   ```bash
   python -m code.main
   ```
   *Expected:* the full pipeline runs (datasets download, query generation, benchmark, analysis, plot) and finishes within the CI time limit.

If any of the above steps fail, re‑run the command manually to see the error; the `.ruff.toml` file has been corrected to a valid TOML configuration.

## Full Benchmark Execution
```bash
# Run the entire study (includes optimal planner on sampled subset)
python -m code.main --run-optimal-planner --baseline-reps=5
```
- `--run-optimal-planner` enables Phase 0 (exhaustive optimal planning on the sampled subset).  
- `--baseline-reps=5` repeats the trivial‑query baseline measurement five times (default is five).  

All outputs are written under `data/processed/` and `data/results/`. The interaction plot will appear at `data/results/interaction_plot.png`.

## Re‑Running Specific Phases (optional)
- **Only data download & checksum**
  ```bash
  python -m code.main --stage data_download
  ```
- **Only query generation**
  ```bash
  python -m code.main --stage generate_queries
  ```
- **Only statistical analysis (after execution logs exist)**
  ```bash
  python -m code.main --stage analyze
  ```

## Expected Artifacts
| Artifact | Location |
|----------|----------|
| Raw datasets (`ms_marco.parquet`, `dbpedia_triples.parquet`) | `data/raw/` |
| Checksums | `data/raw/checksums.txt` |
| Generated queries | `data/processed/generation_log.json` |
| Optimal ground‑truth (sampled) | `data/processed/optimal_ground_truth.json` |
| Baseline overhead | `data/processed/baseline_overhead.json` |
| Execution logs (CSV) | `data/processed/execution_logs.csv` |
| Aggregated execution metric (JSON) | `data/processed/execution_metric.json` |
| Statistical results (JSON) | `data/results/*.json` |
| Interaction plot | `data/results/interaction_plot.png` |

All files are version‑hashed and reproducible on a fresh runner, satisfying Constitution Principle I.

---
