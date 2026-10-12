# Quickstart: Counterfactual Consistency Research Pipeline

> **One‑command end‑to‑end** – reproduces the full experiment (data generation, training, evaluation, and report) on the free‑tier GitHub Actions runner.

## Prerequisites
- GitHub Actions runner (CPU‑only) **or** a local Linux environment with ≥ 4 GB RAM.  
- Python 3.11 installed.  
- No internet download required beyond the three verified URLs (which are not used for primary video data).

## Step‑by‑Step

```bash
# 1️⃣ Clone the repository (already present in CI)
git clone https://github.com/your-org/llmxive-project.git
cd llmxive-project

# 2️⃣ Create a fresh virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins torch, torchvision, opencv, etc.

# 3️⃣ (Optional) Set a deterministic seed list; defaults are defined in src/utils/seed.py
export SEED_LIST="1 2 3 4 5 6 7 8 9 10"

# 4️⃣ Run the full pipeline (single entrypoint)
python -m src.pipeline.run_all \
    --num_videos 200 \
    --lambda_values 0.1 0.5 1.0 \
    --seeds $SEED_LIST \
    --optical_flow_divergence_threshold 0.15 \
    --feature_similarity_threshold 0.9 \
    --output_dir ./output

# 5️⃣ Inspect the main artifacts
#   - Counterfactual metadata (validated against schema)
head output/data/counterfactuals/metadata.csv

#   - Per‑seed evaluation results
cat output/results/per_seed.csv

#   - Summary (includes paired t‑test, bootstrap CI, effect size)
cat output/results/summary.csv

#   - Figures for the paper
ls output/figures/
```

### What `run_all` does internally
| Stage | Script | Key Output |
|-------|--------|------------|
| **Synthetic video creation** | `src/data/synthetic_generator.py` | `output/data/videos/orig/*.mp4` |
| **Counterfactual generation & validation** | `src/data/counterfactual.py` | `output/data/videos/cf/*.mp4`, `metadata.csv` |
| **Optical‑flow extraction** | `src/data/optical_flow.py` | `output/data/flow/*.npy` |
| **Model training** | `src/train/trainer.py` (loops over λ & seeds) | `output/checkpoints/*.pt` |
| **Evaluation** | `src/eval/evaluator.py` | `per_seed.csv`, `summary.csv` |
| **Report & figures** | `src/eval/report.py` | `figures/*.png` (ΔAcc vs λ, bootstrap CI, example frames) |

All files are automatically checksummed; hashes are written to `state/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i.yaml`.

## Extending / Re‑running
- **Change the number of synthetic videos**: edit `--num_videos`.  
- **Add λ values**: extend `--lambda_values`.  
- **Use a different seed list**: modify `SEED_LIST`.  

All changes preserve reproducibility because seeds and hyper‑parameters are recorded in `output/config.yaml`.

---
