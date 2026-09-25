# Quickstart: Investigating the Effectiveness of Loss Functions on Small-World Graphs

## Prerequisites

- Python 3.11+
- `pip` (Python package manager)
- A terminal with access to the project root.

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `networkx`, `torch`, `lifelines`, `statsmodels`, `pandas`, `numpy`.*

## Execution Workflow

### Step 1: Generate Synthetic Graphs
Run the graph generation script to create the dataset.
```bash
python code/generate_graphs.py
```
**Output**: `data/raw/graphs.jsonl` (110 entries).

### Step 2: Train Models
Run the training script. This will iterate over all graphs and both loss functions.
```bash
python code/train.py
```
**Output**: 
- `data/processed/convergence_logs.csv`
- `data/processed/trajectories/` (per-run logs)

### Step 3: Statistical Analysis
Run the analysis script to compute Tobit, Cox (with PH check), and Fixed-Epoch models.
```bash
python code/analysis.py
```
**Output**: `data/analysis_results.json`.

### Step 4: Verify Results
Check the final output:
```bash
cat data/analysis_results.json
```
Expected keys: `tobit_interaction_p_value`, `cox_interaction_p_value`, `is_significant`, `fixed_epoch_results`.

## Testing

Run the test suite to ensure correctness:
```bash
pytest tests/ -v
```

## Troubleshooting

- **ImportError: No module named 'networkx'**: Ensure you activated the virtual environment and ran `pip install -r requirements.txt`.
- **CUDA Error**: This project is CPU-first. If you see CUDA errors, ensure `torch` was installed with CPU-only support or set `os.environ["CUDA_VISIBLE_DEVICES"] = ""` before running.
- **Convergence Issues**: If no graphs converge, check `MAX_EPOCHS` in `code/train.py` or the learning rate. The default is a sufficient number of epochs to ensure convergence. Note that non-convergence is a valid outcome and will be treated as censored data.
- **Cox PH Assumption Violation**: If `cox_ph_valid` is `false` in results, rely on the Tobit model and fixed-epoch metrics for interpretation.