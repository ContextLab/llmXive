# Quickstart: Counterfactual Consistency Research Pipeline

> **One‑command end‑to‑end** – reproduces the full experiment (data generation, training, evaluation, and report) on the free‑tier GitHub Actions runner.

## Prerequisites
- GitHub Actions runner (CPU‑only) or a local Linux environment with ≥ 4 GB RAM.
- Python 3.11 installed.
- No internet download required beyond the open‑source Something‑Something V2 dataset (automatically streamed). [UNRESOLVED-CLAIM: c_b772fcfc — status=not_enough_info]

## Step‑by‑Step

```bash
# 1️⃣ Clone the repository (already present in CI)
git clone <repo_url>
cd llmxive-project

# 2️⃣ Create a fresh virtual environment and install pinned deps
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins torch, torchvision, opencv, etc.

# 3️⃣ Run the full pipeline (single entrypoint)
# You can either use the config file (recommended) …
python -m src.pipeline.run_all --config configs/run.yaml

# … or invoke the historic CLI directly:
# python -m src.pipeline.run_all \
# --num_videos 200 \
# --lambda_values 0.1 0.5 1.0 \
# --seeds 1 2 3 4 5 \
# --flow_divergence_thresh 0.15 \
# --feature_sim_thresh 0.9 \
# --output_dir./output
```

### What `run_all` does internally
| Stage | Script | Key Output |
|-------|--------|------------|
| **Dataset streaming & sampling** | `src/data/something_loader.py` | `output/data/videos/orig/*.mp4` (sampled subset) |
| **Counterfactual generation & validation** | `src/data/counterfactual.py` | `output/data/videos/cf/*.mp4`, `metadata.csv` |
| **Optical‑flow extraction** | `src/data/optical_flow.py` | `output/data/flow/*.npy` |
| **Model training** | `src/train/trainer.py` (loop over λ & seeds) | `output/checkpoints/*.pt` |
| **Evaluation** | `src/eval/evaluator.py` | `per_seed.csv`, `summary.csv` |
| **Report & figures** | `src/eval/report.py` | `figures/*.png` (ΔAcc vs λ, bootstrap CI, example frames) |

All files are automatically checksummed; hashes are written to `data/checksums/manifest.csv`.

## Re‑running or Extending
- To change the number of sampled videos, modify `subset_size` in the config file.
- To add a new λ value, extend `lambda_values` in the config file.
- To use a different random seed list, edit `seeds` in the config file.

All changes preserve reproducibility because seeds and hyper‑parameters are recorded in `output/config.yaml`.
