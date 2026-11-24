# Quickstart: Running the Efficiency‑Reasoning Trade‑off Pipeline

This guide walks you through a single‑command end‑to‑end execution on the CI runner.

## Prerequisites
- Python 3.11 (provided by the CI environment).  
- **Ollama** server running locally with the quantized model `llama2:7b-q8_0` pulled (`ollama pull llama2:7b-q8_0`).  
- Internet access to download the open‑source τⁿ‑Bench dataset (the pipeline will abort cleanly if the repository is unavailable).  

## Step‑by‑Step

1. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the full pipeline**
   ```bash
   python -m src.__main__ \
       --max_tasks 200 \
       --penalty_threshold 2.0 \
       --seed 42
   ```
   - `--max_tasks` caps the number of tasks to keep total runtime ≤ 6 h on the free‑tier CPU runner.  
   - The script performs the following in order:
     1. Attempts to download τⁿ‑Bench; aborts with a clear error if unavailable.  
     2. Executes the baseline Llama‑2‑7B 8‑bit agent and writes `baseline_execution.csv`.  
     3. Computes the **primary** efficiency penalty (`total_calls / optimal_path_length`) and flags high‑penalty tasks; also computes the **fallback** penalty for sensitivity.  
     4. Trains a difficulty‑score model on the **full** task set using only raw task features (excluding any penalty‑derived columns).  
     5. Evolves ≥ 5 harder variants per high‑penalty task based solely on predicted difficulty.  
     6. Re‑runs the baseline on evolved tasks; logs with the same schema as Phase 1.  
     7. Performs a **paired McNemar test** (or Fisher’s exact test if counts are low) for success‑rate differences, a **paired t‑test** for the cost‑performance frontier, logistic regression with VIF check, and a formal **power analysis** for the paired proportion test.  
     8. Conducts the **sensitivity analysis** using the fallback penalty.  
     9. Validates all generated CSV/JSON/PNG files against their JSON‑Schema contracts (including `artifact.schema.yaml`).  
     10. Generates `summary.csv`, frontier and coefficient figures, and `report/analysis.md`.  

3. **Inspect the results**
   ```bash
   # Summary table (includes primary and sensitivity analyses)
   cat data/outputs/summary.csv

   # View figures (requires an image viewer, e.g., `display` on Linux)
   display data/outputs/figures/regression_coefficients.png
   display data/outputs/figures/cost_performance_frontier.png
   ```

4. **Run contract tests (optional)**
   ```bash
   pytest -q tests/contract
   ```

## Reproducibility Tips
- All random seeds are fixed (`--seed` propagates to NumPy, Scikit‑learn, and any internal RNG).  
- SHA checksums of every generated artifact are recorded in `state/projects/PROJ-936-...yaml`.  
- To reproduce exactly, use the same `--seed` and `--max_tasks` values.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `OllamaConnectionError` | Ollama server not running or model not pulled | Start Ollama (`ollama serve`) and run `ollama pull llama2:7b-q8_0`. |
| `TimeoutError` during baseline run | Individual task exceeds 6 h limit | The pipeline marks the task as `timeout`; check `baseline_execution.csv` for `status="timeout"`. |
| Dataset download fails | τⁿ‑Bench repo unreachable (no verified URL) | The pipeline aborts with a clear error; no synthetic data are used. |
| Missing `tool_diversity_k` warning | Dataset does not provide the heuristic (unlikely) | The pipeline logs `OPTIMAL_PATH_MISSING` and skips the affected task for primary penalty. |
| Sensitivity analysis not run | Dataset lacks `minimum_step_count` field | The pipeline notes the limitation and reports results only for the primary metric. |
| Power analysis warning | Sample size below the computed requirement for the expected effect size | Review the warning; consider increasing `--max_tasks` if compute budget permits. |

---


