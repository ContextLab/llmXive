# Quickstart Guide: Investigating Loss Functions on Small-World Graphs

This guide provides step-by-step instructions to run the full research pipeline for **Project PROJ-353**.
The pipeline generates synthetic Watts-Strogatz graphs, trains GCN models with Cross-Entropy and InfoNCE losses,
and performs statistical analysis (Tobit Regression and Cox Proportional Hazards) on convergence data.

## Prerequisites

- Python 3.11+
- A modern Unix-like environment (Linux/macOS)
- 16GB+ RAM recommended (for full batch processing)

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
# Navigate to project root
cd PROJ-353-investigating-the-effectiveness-of-diffe

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Validation (Optional but Recommended)

Before running the full pipeline, verify that the project configuration matches the specification:

```bash
python code/validate_plan.py
```

This script checks that `spec.md` and `plan.md` contain required constants (e.g., N=110, Convergence Threshold 0.90).
If this fails, the build is rejected.

## 3. Step 1: Generate Synthetic Graphs (User Story 1)

Generate the dataset of 110 Watts-Strogatz graphs with varying rewiring probabilities ($\beta$).

```bash
python code/data_generation.py
```

**Outputs:**
- `data/raw/graphs.jsonl`: Contains graph metadata, edge lists, and community labels.
- `state/projects/PROJ-353-investigating-the-effectiveness-of-diffe.yaml`: Updated with SHA-256 checksums.

**Verification:**
Ensure the file exists and contains 110 entries:
```bash
wc -l data/raw/graphs.jsonl
# Expected: 110
```

## 4. Step 2: Train Models (User Story 2)

Train GCN models on the generated graphs using both Cross-Entropy and InfoNCE losses.
This step processes every graph in `data/raw/graphs.jsonl`.

```bash
python code/main.py
```

**Outputs:**
- `data/processed/trajectories/`: Directory containing JSON files for each run.
 - Pattern: `training_run_{id}_ce.json` (Cross-Entropy)
 - Pattern: `training_run_{id}_infonce.json` (InfoNCE)
- Each file includes per-epoch loss/accuracy trajectories and convergence status.

**Note:** This process may take several hours depending on hardware. It runs sequentially over all 110 graphs.

## 5. Step 3: Statistical Analysis (User Story 3)

Aggregate training results and perform statistical testing to determine if loss function effectiveness depends on graph topology ($\beta$).

```bash
python code/analyze.py
```

**Outputs:**
- `data/processed/convergence_logs.csv`: Aggregated scalar metrics (steps to convergence, beta, loss type).
- `data/analysis_results.json`: Contains Tobit and Cox model coefficients, p-values, and significance flags.
- `data/report.md`: Final human-readable summary of the findings.

## 6. Expected Results

Upon successful completion, you should see:
- `data/report.md` stating whether the interaction between $\beta$ and loss type is statistically significant.
- `data/analysis_results.json` with `is_significant` set to `true` or `false` based on Bonferroni-corrected p-values.

## Troubleshooting

- **Missing `data/raw/graphs.jsonl`**: Run Step 1 first. The training script expects this file to exist.
- **Import Errors**: Ensure you are using the virtual environment created in Step 1.
- **CUDA Errors**: This project is CPU-only. Ensure no CUDA device is forced in the environment.
- **Validation Failures**: If `validate_plan.py` fails, check that `spec.md` and `plan.md` have not been modified incorrectly.

## Further Reading

- Research Questions: See `specs/353-loss-functions-small-world/research.md`
- Data Model: See `data-model.md`
- API Documentation: See `code/models.py`, `code/losses.py`, and `code/utils.py`