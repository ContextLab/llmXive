# Quickstart: Dream-State Learning

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a Linux environment (GitHub Actions runner or local Linux VM)
-   At least 8GB RAM (to allow for 7GB limit headroom)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-589-dream-state-learning-implementing-rem-li
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Experiment

### 1. Data Download
The script will automatically download the GLUE dataset to `data/raw/` on first run.
```bash
python code/data_loader.py --download
```
*Note: Ensure you have sufficient disk space for the subset.*

### 2. Run a Single Seed (Debug Mode)
Run a single seed with reduced steps to verify the pipeline.
```bash
python code/train.py --seed 42 --steps 10 --mode debug
```
*Expected Output*: Logs showing "Wake Phase", "Dream Phase", entropy checks, and a final checkpoint.

### 3. Run Full Experiment
Run the full experiment (5 seeds + baseline) with an imbalanced ratio.
```bash
python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20
```
*Note*: This will run for a moderate duration on a standard CI runner.

### 4. Evaluate & Statistical Analysis
After training completes, run the evaluation script to compute accuracy and t-tests.
```bash
python code/eval.py --results-dir data/results/
```
*Output*: A JSON report in `data/results/statistical_report.json` containing the p-value and effect size.

## Troubleshooting

-   **OOM Error**: If you see "Memory Error", reduce the batch size in `code/config.py` or switch to DistilBERT.
-   **Dream Phase Skipped**: Check logs for "Low Entropy" or "High Perplexity". This is expected behavior to prevent training on garbage.
-   **Timeout**: If the job exceeds 6 hours, check the `wall_clock_hours` in the log. Reduce the number of seeds or steps.

## Verification

To verify the installation:
1.  Run the debug mode.
2.  Check `logs/debug.log` for the sequence: `Wake -> Dream -> Wake -> Dream`.
3.  Verify `data/checkpoints/debug.pt` exists and is loadable.
