# Quickstart: Low-Rank RL for Foresight in LLM Training

## Prerequisites
- Python 3.10 or newer
- Git
- At least **7 GB** of RAM (CPU‑only)
- Internet access for dataset download

## Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-828-llmxive-follow-up-extending-learning-to
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # Ensure CPU‑only PyTorch:
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   ```

## Running the Full Experiment

The **single entry point** is `src/cli/run_experiment.py`. All phases are orchestrated automatically.

```bash
# 1️⃣ Prepare data (downloads GSM8K subset and verifies checksum)
python src/cli/run_experiment.py --prepare-data

# 2️⃣ Execute the complete pipeline with 10 seeds per variant
python src/cli/run_experiment.py --full-pipeline --seeds 10
```

The command performs, in order:

1. OPD training → subspace extraction.  
2. Six RL variants (Standard, Low‑Rank, Random Projection, Random Walk Prior, OPD‑Initialized, plus OPD baseline).  
3. Logging of convergence, alignment, memory usage.  
4. Statistical analysis, power check, and figure generation.  
5. Artifact hashing for reproducibility (Principle V).

### Running a Single Variant (optional)

```bash
python src/cli/run_experiment.py --variant low_rank_rl --seeds 10
```

*Make sure the OPD subspace has been generated first (`--prepare-data` also runs OPD).*

## Analyzing Results

```bash
python src/cli/run_experiment.py --analyze
```

- **Plots** are saved under `results/plots/`.  
- **Metrics** are stored in `results/analysis/alignment_metrics.json`.  
- A **summary JSON** conforming to `contracts/analysis_results.schema.yaml` is written to `results/analysis/summary.json`.

## Verifying the Geometric Constraint (Constitution Principle VI)

```bash
python src/cli/run_experiment.py --verify-alignment --variant low_rank_rl
```

Expected output (example):

```
[INFO] Alignment check passed: mean cosine similarity = 0.992 ≥ 0.99
```

If the check fails, the run aborts and logs a warning; you can increase `rank_k` via `--rank-k` flag.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **OOM error** | Batch size too large or SVD on full model | Reduce `--batch-size` or add `--svd-method randomized`. |
| **SVD failed / variance < 80 %** | Flat spectrum or too few steps captured | Increase `--opd-steps` or accept default `k=10` (the script logs a warning). |
| **Run exceeds 6 h** | Seed count too high for current runner | Reduce `--seeds` to 6 (will lower power; update `SC‑003` note). |
| **Alignment check fails** | Projection matrix corrupted or rank too low | Re‑run OPD (`--recompute-subspace`) or increase `--rank-k`. |
| **Hash mismatch** | Data file changed after download | Re‑run `--prepare-data` to recompute checksums. |

## Reproducibility Guarantees
- All random seeds are fixed in `src/utils/seeds.py`.  
- Dataset checksum is stored in `state/data_checksums.yaml`.  
- After any run, `state/run_hashes.yaml` contains SHA‑256 hashes of all derived artifacts; CI will reject mismatched hashes.

---
