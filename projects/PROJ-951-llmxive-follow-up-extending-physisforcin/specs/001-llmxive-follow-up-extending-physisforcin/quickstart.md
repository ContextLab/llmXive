# Quickstart: llmXive follow‑up – Post‑generation Physics Filtering

Reproduce the entire experiment on a fresh GitHub Actions runner (or locally on Linux).

## Prerequisites
* Python 3.11
* Git clone of the repository
* Internet access (to download open datasets)

## Step‑by‑Step

1. **Create a virtual environment & install dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r code/requirements.txt
   python src/utils/verify_env.py   # asserts CPU‑only, checks data checksums
   ```

2. **Download raw assets**  
   ```bash
   python src/generation/download_wan_weights.py
   python src/generation/download_pybullet_examples.py
   ```

3. **Generate synthetic videos** (default batch size = 200)  
   ```bash
   python src/generation/generate_videos.py \
       --num_videos 200 \
       --output_dir data/generated/videos/
   ```

4. **Run the physics filter** (keep top 60 th percentile)  
   ```bash
   python src/filtering/pybullet_filter.py \
       --input_dir data/generated/videos/ \
       --output_csv data/curated/curated_dataset.csv \
       --percentile 60
   ```

5. **(Optional) Augment to reach n ≥ 30**  
   ```bash
   python src/augmentation/geometric_augmenter.py \
       --manifest data/curated/curated_dataset.csv \
       --target_n 30
   ```

6. **Train the ≈ 50 M‑parameter diffusion model**  
   ```bash
   python src/training/train_diffusion.py \
       --manifest data/curated/curated_dataset.csv \
       --epochs 10 \
       --batch_size 4 \
       --frame_resolution 64 \
       --precision float16 \
       --output_dir data/models/
   ```

7. **Validate the filter with MuJoCo**  
   ```bash
   python src/filtering/mujoco_validator.py \
       --manifest data/curated/curated_dataset.csv
   ```

8. **Evaluate on benchmarks**  
   ```bash
   python src/evaluation/evaluate_benchmarks.py \
       --model_path data/models/diffusion_checkpoint.pt \
       --output_dir data/reports/
   ```

9. **Run the TOST equivalence test**  
   ```bash
   python src/evaluation/tost_equivalence.py \
       --baseline data/reports/baseline_RBench.json \
       --candidate data/reports/curated_RBench.json \
       --margin 0.15 \
       --output data/reports/tost_results.json
   ```

10. **Inspect the final report**  
    The file `data/reports/final_summary.md` is generated automatically and contains:
    * Retention rate after filtering (SC‑001).  
    * **Physical‑consistency scores** (SC‑002).  
    * **Performance gap** vs. PhysisForcing baseline (SC‑003).  
    * **p‑value** from TOST (SC‑004).  
    * Training **duration** (SC‑005).  
    * Pearson **correlation** between PyBullet and MuJoCo scores (SC‑006).  

All steps are fully scripted; running the CI workflow executes tasks T0‑T19 sequentially, guaranteeing end‑to‑end reproducibility.

---
