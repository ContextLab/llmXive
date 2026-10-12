# Quickstart: Running the Efficiency‑Reasoning Trade‑off Pipeline

This guide walks you through a single‑command end‑to‑end execution on the CI runner.

## Prerequisites
- Python 3.11 installed (provided by the CI environment).  
- `ollama` server running locally with the **Llama‑2‑7B 8‑bit** model pulled (`ollama pull llama2:7b-q8_0`).  
- Internet access to download open datasets (the script will attempt to fetch `τ^c‑Bench`; if unavailable it aborts with a clear error).

## Step‑by‑Step

1. **Setup virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the full pipeline**
   ```bash
   python -m src.pipelines.run_all \
       --max_tasks 200 \
       --penalty_threshold 2.0 \
       --seed 42
   ```
   - `--max_tasks` caps the number of tasks to stay within the 6 h budget.  
   - The script will:
     1. Attempt to download the τ^c‑Bench task set (abort if not found).  
     2. Execute the baseline Llama‑2‑7B 8‑bit agent and produce `baseline_execution.csv`.  
     3. Compute penalties (primary metric: tool diversity heuristic), filter, and train the difficulty regression tree.  
     4. Evolve new tasks and re‑run the agent.  
     5. Perform statistical evaluation (Logistic Regression with difficulty covariate) using the primary metric.  
     6. Perform sensitivity analysis using the alternative metric (minimum step count, if available).  
     7. Compare trade-off coefficients across both metrics and validate robustness.  
     8. Write results/figures.

3. **Inspect results**
   ```bash
   # Summary table (includes both primary and sensitivity results)
   cat data/outputs/summary.csv

   # Visualisations
   display data/outputs/figures/regression_coefficients.png
   ```

4. **Run contract tests (optional)**
   ```bash
   pytest -q tests/contract
   ```

## Reproducibility Tips
- All random seeds are fixed (`seed` argument propagates to numpy, sklearn, and any internal RNG).  
- The SHA‑256 checksums of every generated file are recorded in `state/projects/PROJ-936-...yaml`.  
- To reproduce exactly, use the same `--seed` and `--max_tasks` values.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `OllamaConnectionError` | Ollama server not running or model not pulled | Start Ollama (`ollama serve`) and run `ollama pull llama2:7b-q8_0`. |
| `TimeoutError` during baseline run | Individual task exceeds 6 h limit | The script automatically marks the task as `timeout`; check `baseline_execution.csv` for `status="timeout"`. |
| Missing `optimal_path_length` warnings | τ^c‑Bench dataset does not provide the field | The pipeline falls back to the tool‑diversity heuristic and logs `OPTIMAL_PATH_MISSING`. Sensitivity analysis will use minimum step count if available. |
| Sensitivity analysis not running | Dataset lacks `minimum_step_count` field | The pipeline will note this limitation and report results for the primary metric only. |
