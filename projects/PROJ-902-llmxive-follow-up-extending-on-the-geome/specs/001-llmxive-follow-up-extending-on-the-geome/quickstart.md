# Quickstart: llmXive follow-up: extending "On the Geometry of On-Policy Distillation"

## Prerequisites
- Python 3.11 installed (GitHub Actions provides this).
- `git` clone of the repository.
- Internet access (to download GSM8K parquet files).

## Setup (one‑time)
```bash
# Clone the repo (if not already)
git clone
cd llmxive-geometry-extension

# Create a virtualenv and install pinned dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # includes llama-cpp-python for CPU‑only 4‑bit GGML
```

## Run the Full Experiment Pipeline
```bash
# Step 0: Verify checksums (optional but required by Constitution)
python -m src.utils.checksum_verify data/checksums.txt

# Step 1: Download GSM8K (cached under data/raw/)
python -m src.data.download_gsm8k

# Step 2: Run the OPD baseline & compute subspace masks (includes sensitivity sweep)
python -m src.train.opd_baseline --seeds data/metadata/seeds.json --epochs 3
python -m src.data.svd_compute --thresholds 0.90 0.95 0.99 # per‑seed masks are saved as subspace_mask_{seed}.json

# Step 3: Run constrained experiments (Frozen‑Subspace OPD, SFT, Random)
python -m src.train.frozen_subspace_opd --seeds data/metadata/seeds.json
python -m src.train.frozen_subspace_sft --seeds data/metadata/seeds.json # uses each seed’s OPD mask
python -m src.train.frozen_subspace_random --seeds data/metadata/seeds.json # uses fixed random mask

# Step 4: Evaluate & compute statistics
python -m src.eval.evaluate --heldout data/raw/gsm8k_test.parquet
python -m src.eval.stats

# Step 5: Merge per‑run CSVs into the unified summary (required for contract validation)
python -m src.utils.merge_summary # creates results/experiment_summary.csv

# Step 6: Generate report artifacts (figures, tables)
python -m src.utils.generate_report
```

All scripts automatically:
- Log peak RAM and wall‑clock time (`resource_usage.csv`).
- Store random seeds and model hashes for reproducibility.
- Abort with a clear error if RAM > 7 GB or wall‑clock > 6 h (CI enforcement).

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the above commands on an `ubuntu-latest` runner with a timeout of 360 minutes. The workflow fails if any contract validation (`pytest -k contract`) or resource limit is violated.

## Re‑Running a Single Condition
To reproduce a specific condition (e.g., Frozen‑Subspace OPD with seed 7):
```bash
python -m src.train.frozen_subspace_opd --seed 7
```
All intermediate files are cached under `data/` so subsequent runs are fast.

---


