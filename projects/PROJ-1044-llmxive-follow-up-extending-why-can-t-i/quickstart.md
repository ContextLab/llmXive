# Quickstart: Counterfactual Consistency Research Pipeline

> **One‑command end‑to‑end** – reproduces the full experiment (data generation, training, evaluation, and report) on the free‑tier GitHub Actions runner.

## Prerequisites
- GitHub Actions runner (CPU‑only) or a local Linux environment with ≥ 4 GB RAM.
- Python 3.11 installed.
- No internet download required beyond the open‑source Something‑Something V2 dataset (automatically streamed).

## Step‑by‑Step

```bash
# 1️⃣ Clone the repository (already present in CI)
git clone <repo_url>
cd llmxive-project

# 2️⃣ Create a fresh virtual environment and install pinned deps
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins torch, torchvision, opencv, etc.

# 3️⃣ Set deterministic seeds (handled automatically)
export SEED=42 # optional; defaults are defined in src/utils/seed.py

# 4️⃣ Run the full pipeline (single entrypoint)
python -m src.pipeline.run_all --config configs/run.yaml

# 5️⃣ Inspect results
# - Metadata of generated pairs:
head output/data/counterfactuals/metadata.csv

# - Per‑seed evaluation:
cat output/results/per_seed.csv

# - Summary (includes paired t‑test and bootstrap CI):
cat output/results/summary.csv

# - Figures (PNG) for the paper:
ls output/figures/
```

### What `run_all` does internally
| Stage | Script | Key Output |
|-------|--------|------------|
| **Dataset streaming & sampling** | `src/data/something_something_loader.py` | `output/data/videos/orig/*.mp4` (sampled subset) |
| **Counterfactual generation & validation** | `src/data/counterfactual.py` | `output/data/videos/cf/*.mp4`, `metadata.csv` |
| **Optical‑flow extraction** | `src/data/optical_flow.py` | `output/data/flow/*.npy` |
| **Model training** | `src/train/trainer.py` (loop over λ & seeds) | `output/checkpoints/*.pt` |
| **Evaluation** | `src/eval/evaluator.py` | `per_seed.csv`, `summary.csv` |
| **Report & figures** | `src/eval/report.py` | `figures/*.png` (ΔAcc vs λ, bootstrap CI, example frames) |

All files are automatically checksummed; hashes are written to `state/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i.yaml`.

## Re‑running or Extending
- To change the number of sampled videos, modify `subset_size` in the config file.
- To add a new λ value, extend `lambda_values` in the config file.
- To use a different random seed list, edit `seeds` in the config file.

All changes preserve reproducibility because seeds and hyper‑parameters are recorded in `output/config.yaml`.
