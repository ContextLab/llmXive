# Quickstart: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

## Prerequisites

- Python 3.11+
- pip
- Git
- A GitHub Actions runner (or local machine with sufficient RAM and CPU cores).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    cd code
    pip install -r requirements.txt
    cd ..
    ```
    *Note: Ensure `pybullet` is installed. If running on a headless server, install `xvfb`.*

## Running the Pipeline

### 1. Generate Novel Objects
Generate a set of novel articulated objects with randomized friction and mass.
```bash
python code/generator.py --num-objects 30 --trials-per-object 50 --output data/generated/
```

### 2. Run the Experiment
Execute the full evaluation loop (Static Baseline vs. Adaptive Policy).
```bash
python code/evaluate.py --objects data/generated/ --policy adaptive --output data/results/
```
*This command runs the simulation for a set of objects across multiple trials, applying the Virtual Tactile Estimator.*

### 3. Analyze Results
Perform the statistical comparison (Paired T-Test) and Estimator Accuracy check.
```bash
python code/analysis.py --results data/results/ --output data/results/summary_report.md
```

## Verification

To verify the system is working correctly:
1.  Check `data/results/summary_report.md` for the **p-value**. It should be `< 0.05` if the hypothesis is supported.
2.  Inspect `data/logs/{object_id}_adaptive.jsonl` to confirm that `k_est` values are within `[0.01, 100.0]` and that `r_detach` increases smoothly when `k_est > 1.0`.
3.  Verify the "Estimator Accuracy" section in the report, which should show a high Pearson correlation ($r > 0.8$) between $k_{est}$ and the injected friction.

## Troubleshooting

- **OOM Errors**: If you encounter "Out of Memory" errors, reduce the number of objects in `generator.py` or ensure `gc.collect()` is called after each object evaluation.
- **Simulation Jitter**: If the estimator produces NaN values, check the `epsilon` value in `code/estimator.py` (default: $10^{-4}$).
- **CUDA Errors**: If you see CUDA errors, ensure `torch` is installed with CPU-only support or set `CUDA_VISIBLE_DEVICES=""` in your environment.