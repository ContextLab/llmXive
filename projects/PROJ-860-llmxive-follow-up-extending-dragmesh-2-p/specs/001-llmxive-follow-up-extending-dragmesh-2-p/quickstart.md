# Quickstart: Virtual Tactile Zero-Shot Adaptation

## Prerequisites

- Python 3.11+
- pip
- A standard GitHub Actions runner (or local machine with sufficient RAM).

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    cd projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `pybullet`, `torch` (CPU version), `numpy`, `pandas`, `scipy`, and `pytest`.*

## Running the Experiment

Execute the full pipeline (generation, training, inference, analysis):

```bash
python code/main.py --mode full
```

### Arguments

- `--mode`: `full` (default), `generate`, `train`, `analyze`.
- `--num_objects`: Number of novel objects to generate (default: 50).
- `--seed`: Random seed for reproducibility (default: 42).

### Expected Output

1.  **Generated Objects**: `data/generated/novel_objects/`
2.  **Simulation Logs**: `data/logs/simulation_run_*.csv`
3.  **Summary Report**: `data/logs/experiment_summary.json`

## Verifying Results

To verify the core hypothesis of significant improvement:

```bash
python code/analysis/statistical_test.py --input data/logs/
```

**Success Criteria**:
- The output should show `improvement_pct >= 15.0`.
- The `p_value` should be `< 0.05`.

## Troubleshooting

- **OOM Error**: If you encounter `MemoryError`, reduce `--num_objects` to a lower value.
- **CUDA Error**: If you see `CUDA out of memory` or similar, ensure you are using the CPU-only version of PyTorch (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Simulation Instability**: If the simulation crashes, check the friction coefficients in `data/generated/novel_objects/` for extreme values.

## Re-running with New Data

To re-run the experiment with a fresh set of objects:

```bash
python code/main.py --mode full --seed $(date +%s)
```
