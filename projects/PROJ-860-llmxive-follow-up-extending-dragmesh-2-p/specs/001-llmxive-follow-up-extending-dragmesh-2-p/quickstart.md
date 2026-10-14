# Quickstart: Virtual Tactile Zero-Shot Adaptation

## Prerequisites
- Python 3.11 or newer  
- `git`  
- Internet access (to download the DragMesh‑2 manifest)  
- A machine (or GitHub Actions runner) with at least **multiple CPU cores** and **7 GB RAM**  

## Installation

```bash
# 1. Clone the repository
git clone 
cd llmxive-follow-up-extending-dragmesh-2-p

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies (CPU‑only PyTorch)
pip install -r requirements.txt
```

## Running the Full Experiment

```bash
python code/main.py --mode full \
    --num_objects 10 \
    --seed 42
```

### Arguments
| Argument | Default | Description |
|---|---|---|
| `--mode` | `full` | `full`, `generate`, `train`, `analyze` |
| `--num_objects` | `10` | Number of novel objects to generate (must be ≥ 10). |
| `--seed` | `fixed` | Random seed for reproducibility (pinned for all runs). |

### Expected Outputs
- **Generated objects**: `data/generated/novel_objects/` (JSON files).  
- **Simulation logs**: `data/logs/simulation_run_*.csv`.  
- **Summary report**: `data/logs/experiment_summary.json`.  

## Verifying Core Hypotheses

```bash
# 1. Run the statistical analysis (GLMM + paired t‑test)
python code/analysis/statistical_test.py --input data/logs/
```

The script prints:
- **Improvement %** (should be ≥ 15 % for PASS).  
- **GLMM p‑value** (must be `< 0.05`).  
- **Paired t‑test p‑value** (must be `< 0.05` per Constitution Principle VII).  
- **Pearson r** from the correlation experiment (must be ≥ 0.8).  

If any metric fails, the script exits with a non‑zero status and prints a helpful message.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `MemoryError` or OOM | Too many objects or too long episodes | Reduce `--num_objects` or add `--max_steps` flag (default 500). |
| `CUDA`‑related error | Accidentally installed GPU PyTorch | Re‑install with CPU‑only: `pip uninstall torch && pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| Simulation diverges (exploding forces) | Extreme friction values | Ensure friction coefficients are within `[0.0, 2.0]`; the estimator clamps `k_norm`. |
| GLMM fails to converge | Insufficient data | Increase `--num_objects` (up to 20) – the pipeline will stay within the allocated time budget. |
| Paired t‑test not significant | Low power | See the power‑analysis note in the plan; run with more objects. |

## Re‑running with New Random Seeds

```bash
python code/main.py --mode full --seed $RANDOM
```

Each run is fully reproducible given the seed; the checksum of all generated files will differ, and the new hashes are recorded automatically.
