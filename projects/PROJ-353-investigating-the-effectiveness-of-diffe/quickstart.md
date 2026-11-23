# Quickstart Guide: Investigating Loss Functions on Small-World Graphs

This guide provides instructions to set up the environment and run the full research pipeline for **Project PROJ-353**.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- A POSIX-compliant shell (bash, zsh) or PowerShell on Windows

## 1. Environment Setup

Ensure you are in the project root directory. Install the required dependencies:

```bash
pip install -r requirements.txt
```

*Note: The pipeline is designed to run on CPU only. Do not attempt to install CUDA-specific PyTorch builds.*

## 2. Project Structure

The project follows this structure:

- `code/`: Source code modules (data generation, models, training, analysis).
- `data/`:
 - `raw/`: Generated synthetic graphs (`graphs.jsonl`).
 - `logs/`: Per-run training trajectories and convergence logs.
 - `analysis/`: Final statistical results and reports.
- `contracts/`: JSON/YAML schemas for data validation.
- `tests/`: Unit and integration tests.

## 3. Running the Full Pipeline

The pipeline executes in three main phases: **Data Generation**, **Training**, and **Analysis**.

### Step 1: Generate Synthetic Graphs (User Story 1)

This step generates $N=110$ Watts-Strogatz graphs with varying rewiring probabilities ($\beta$).

```bash
python code/data_generation.py
```

**Output**:
- `data/raw/graphs.jsonl`: Contains graph metadata, edge lists, and community labels.

### Step 2: Train Models & Track Convergence (User Story 2)

This step trains a 2-layer GCN on each generated graph using both **Cross-Entropy** and **InfoNCE** losses. It records per-epoch trajectories and convergence steps.

```bash
python code/main.py
```

**Output**:
- `data/logs/training_run_<id>_<loss_type>.json`: Detailed logs for every training run, including:
 - `trajectory`: List of `{loss, accuracy}` per epoch.
 - `convergence_status`: "converged" or "censored".
 - `steps_to_convergence`: Epoch count when accuracy $\ge$ 0.90.

### Step 3: Statistical Analysis & Reporting (User Story 3)

This step aggregates training logs, performs Tobit Regression and Cox Proportional Hazards analysis, and generates the final report.

```bash
python code/analyze.py
```

**Output**:
- `data/analysis_results.json`: Statistical coefficients, p-values, and significance flags.
- `data/report.md`: Human-readable summary of findings regarding loss function effectiveness on small-world topology.

## 4. Validation

To verify the project structure and data model alignment:

```bash
python scripts/validate_plan.py
```

## 5. Troubleshooting

- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed and that you are running from the project root.
- **Memory Errors**: The pipeline is optimized for the specified $N=110$ sample size. If running on restricted environments, verify `code/utils.py` constants are respected.
- **Data Missing**: If `data/raw/graphs.jsonl` is missing, re-run `code/data_generation.py`.

## 6. Next Steps

After a successful run, review `data/report.md` for the interaction analysis between the rewiring parameter $\beta$ and the loss function types.