# Quickstart: Counterfactual Consistency Research Pipeline

> **One‑command end‑to‑end** – reproduces the full experiment (data generation, training, evaluation, and report) on the free‑tier GitHub Actions runner.

## Prerequisites
- GitHub Actions runner (CPU‑only) **or** a local Linux environment with ≥ 4 GB RAM.  
- Python 3.11 installed.  
- No internet download required beyond the three verified URLs (which are not used for primary video data).

## Step‑by‑Step

```bash
# 1️⃣ Clone the repository (already present in CI)
git clone <repo-url>
cd llmxive-project

# 2️⃣ Create a fresh virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins torch, torchvision, opencv, etc.

# 3️⃣ Set a deterministic seed list (15 seeds as used in the plan)
export SEED_LIST="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15"

# 4️⃣ Run the full pipeline (single entrypoint)
python -m src.pipeline.run_all \
    --num_videos <sufficient number of videos> \
    --lambda_values 0.1 0.5 1.0 \
    --seeds $SEED_LIST \
    --flow_divergence_thresh 0.15 \
    --feature_sim_thresh 0.9 \
    --output_dir ./output

# 5️⃣ Inspect the main artifacts
#   - Counterfactual metadata (validated against schema)
head output/data/counterfactuals/metadata.csv

#   - Pre‑computed optical flow files (orig & cf)
ls output/data/flow/orig/ output/data/flow/cf/

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
| **Pre‑compute flow for originals** | `src/data/optical_flow.py` | `output/data/flow/orig/*.npy` |
| **Counterfactual generation & validation** | `src/data/counterfactual.py` (uses ResNet‑18 similarity & flow divergence) | `output/data/videos/cf/*.mp4`, `metadata.csv` |
| **Pre‑compute flow for counterfactuals** | `src/data/optical_flow.py` (on‑the‑fly) | `output/data/flow/cf/*.npy` |
| **Feature extraction (FlowNet‑C)** | `src/data/feature_extractor.py` | `output/data/flow_features/*.npy` |
| **Model training** | `src/train/trainer.py` (loops over λ & 15 seeds) | `output/checkpoints/*.pt` |
| **Evaluation** | `src/eval/evaluator.py` | `per_seed.csv`, `summary.csv` |
| **Report & figures** | `src/eval/report.py` | `figures/*.png` (ΔAcc vs λ, bootstrap CI, example frames, construct‑validity plots) |

All files are automatically checksummed; hashes are written to `state/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i.yaml`.

## Extending / Re‑running
- **Change the number of synthetic videos**: edit `--num_videos`.  
- **Add λ values**: extend `--lambda_values`.  
- **Use a different seed list**: modify `SEED_LIST`.  

All changes preserve reproducibility because seeds and hyper‑parameters are recorded in `output/config.yaml`.

## Notes on Required Resources
- The `data/patches/` directory containing simple colored‑shape patches is shipped with the repository. If it is missing (e.g., a fresh clone), the pipeline will automatically generate a minimal set of placeholder patches (solid‑color squares) before counterfactual generation, ensuring no script failure.
- Optical flow for counterfactual videos is **computed after generation** (still CPU‑only) and cached for downstream steps, satisfying FR‑006 while validating motion preservation.
