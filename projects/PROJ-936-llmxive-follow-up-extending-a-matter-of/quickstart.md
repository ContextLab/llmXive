# Quickstart: Running the Efficiency‑Reasoning Trade‑off Pipeline

This guide walks you through a single‑command end‑to‑end execution on the CI runner.

## Prerequisites
- Python 3.11 (provided by the CI environment).
- `ollama` server running locally with the **Llama‑2‑7B 8‑bit** model pulled (`ollama pull llama2:7b-q8_0`).
- Internet access to download open datasets (the script will attempt to fetch τⁿ‑Bench; if unavailable it aborts with a clear error).

## Step‑by‑Step

1. **Setup virtual environment & install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run the full pipeline**
 ```bash
 python -m src.pipelines.run_all \
 --max_tasks 150 \
 --penalty_threshold 2.0 \
 --seed 42
 ```
 - `--max_tasks` caps the number of tasks to stay within the 6 h budget ([deferred] per task ⇒ ≤ 150 min total).
 The script will:
 1. Attempt to download the τⁿ‑Bench task set (abort if not found).
 2. Execute the baseline Llama‑2‑7B 8‑bit agent and produce `baseline_execution.csv`.
 3. Compute penalties using the **tool‑diversity** count k as the optimal denominator.
 4. Filter high‑penalty tasks, train the difficulty regression tree on the **full** dataset, and evolve new tasks.
 5. Re‑run the agent on evolved tasks.
 6. Perform statistical evaluation (McNemar's test as primary, logistic regression, point‑biserial correlation).
 7. Perform sensitivity analysis using the pure tool‑diversity heuristic.
 8. Write results, figures, and a concise markdown report.

3. **Inspect results**
 ```bash
 # Summary table (includes both primary and sensitivity results)
 cat data/outputs/summary.csv

 # Visualisation
 display data/outputs/figures/regression_coefficients.png
 display data/outputs/figures/cost_performance_frontier.png
 ```

4. **Run contract tests (optional)**
 ```bash
 pytest -q tests/contract
 ```

## Reproducibility Tips
- All random seeds are fixed (`--seed` propagates to `numpy`, `sklearn`, and any internal RNG).
- SHA‑2 family checksums of every generated file are recorded in `state/projects/PROJ-936-...yaml`..
- To reproduce exactly, use the same `--seed` and `--max_tasks` values.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `OllamaConnectionError` | Ollama server not running or model not pulled | Start Ollama (`ollama serve`) and run `ollama pull llama2:7b-q8_0`. |
| `TimeoutError` during baseline run | Individual task exceeds 6 h limit | The script marks the task as `timeout`; check `baseline_execution.csv` for `status="timeout"`. |
| Dataset download fails | τⁿ‑Bench repo unreachable (no verified URL) | The pipeline aborts with a clear error; provide an alternative open dataset or host a mirror with a verified URL. |
| Missing `tool_diversity_k` warning | Dataset does not provide the heuristic (unlikely) | The pipeline logs `OPTIMAL_PATH_MISSING` and skips the affected task. |
| Sensitivity analysis not running | Dataset lacks `minimum_step_count` field | The pipeline notes this limitation and reports results for the primary metric only. |