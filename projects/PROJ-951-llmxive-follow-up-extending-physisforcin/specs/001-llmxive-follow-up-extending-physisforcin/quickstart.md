# Quickstart: llmXive follow‑up – Post‑generation Physics Filtering

This guide walks you through reproducing the entire experiment on a fresh GitHub Actions runner (or locally on Linux).

## Prerequisites
* Python 3.11
* Git clone of the repository
* Internet access (to download open datasets)

## Step‑by‑Step

1. **Setup the environment**  
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

3. **Generate synthetic videos**  
   ```bash
   python src/generation/generate_videos.py \
       --num_videos 200 \
       --output_dir data/generated/videos/
   ```

4. **Run the physics filter**  
   ```bash
   python src/filtering/pybullet_filter.py \
       --input_dir data/generated/videos/ \
       --output_csv data/curated/curated_dataset.csv \
       --percentile <desired_percentile>   # keep top <desired_percentile>th percentile
   ```

5. **(Optional) Augment to reach n ≥ 30**  
   ```bash
   python src/augmentation/geometric_augmenter.py \
       --manifest data/curated/curated_dataset.csv \
       --target_n 30
   ```

6. **Train the distilled diffusion model**  
   ```bash
   python src/training/train_diffusion.py \
       --manifest data/curated/curated_dataset.csv \
       --epochs 8 \
       --batch_size <small> \
       --frame_resolution <desired_resolution> \
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
       --margin <default small margin> \
       --output data/reports/tost_results.json
   ```

10. **Inspect the final report**  
    The file `data/reports/final_summary.md` is auto‑generated and contains:
    * Retention rate after filtering (SC‑001)
    * **Physical consistency score (SC‑002)** – extracted from benchmark results.
    * **Performance gap (SC‑03) within 15 % equivalence margin (SC‑003)**.
    * **p‑value < 0.05 (SC‑004)** indicating statistical significance.
    * Correlation **> 0.95?** (SC‑006) **?** — should be < 0.95 to satisfy SC‑006.
    * Training **time ≤ 4 h (SC‑005)** – by `````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````


