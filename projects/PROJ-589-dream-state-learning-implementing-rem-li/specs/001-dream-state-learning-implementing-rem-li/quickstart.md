# Quickstart: Dream-State Learning: Implementing REM-like Consolidation in Language Models

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local machine with GB+ RAM, 2+ CPU cores).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-589-dream-state-learning-implementing-rem-li
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `torch` is installed as the CPU-only wheel.*

## Running the Experiment

### 1. Run a Single Wake/Dream Cycle
Execute the main training script for a single seed (default steps for testing):
```bash
python code/main.py --seed 42 --steps 100 --mode wake_dream
```

### 2. Run the Baseline Comparison
Execute the continuous training baseline for the same seed:
```bash
python code/main.py --seed 42 --steps 100 --mode baseline
```

### 3. Run Full Statistical Evaluation (5 Seeds)
Run the full experiment with multiple seeds and automatically compute the t-test:
```bash
python code/main.py --seeds 42 123 456 789 101 --steps 500 --mode full_eval
```
*This command will:*
-   Train Wake/Dream models.
-   Train multiple Baseline models.
-   Evaluate all on GLUE AX.
-   Generate `data/results/experiment_results.json`.
-   Print the final t-test p-value and effect size.

## Verifying Constraints

### Memory Check
The script includes a built-in memory monitor. If peak memory exceeds a predefined high threshold, the job will abort and save the checkpoint.
-   **Log Output**: Look for `MEMORY_MONITOR: Peak RSS = X MB`.
-   **Failure**: If `Peak RSS > 6500`, check `data/logs/abort_log.txt` for the checkpoint path.

### Time Check
The script will print a timer at the start.
-   **Limit**: 5 hours for the full 5-seed evaluation.
-   **Monitoring**: Check `data/logs/timing.log` for step durations.

## Troubleshooting

-   **OOM Error**: If you encounter "CUDA out of memory" (even on CPU), ensure you are not using a CUDA-enabled PyTorch build. Reinstall with `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
-   **Low Entropy**: If the dream phase collapses (entropy < 0.5), the script will retry 3 times. If it fails, it logs a warning. This is expected behavior for early training; the warm-up period (a sufficient number of steps) should mitigate this.
-   **Dataset Missing**: Ensure you have internet access to download the GLUE parquet files from HuggingFace on the first run.

## Next Steps

-   **Analyze Results**: Inspect `data/results/experiment_results.json` to see the accuracy differences.
-   **Visualize**: (Future) Plot the loss curves for Wake vs. Dream phases.
-   **Extend**: Modify `code/config.py` to test different `dream_temperature` values (FR-006).
