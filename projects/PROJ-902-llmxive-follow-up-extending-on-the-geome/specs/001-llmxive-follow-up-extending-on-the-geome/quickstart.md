# Quickstart: llmXive Geometry Extension

This guide reproduces the full experimental pipeline on a fresh GitHub Actions runner or a local Linux environment.

## 1. Clone the Repository
```bash
git clone
cd llmxive-geometry-extension
```

## 2. Set Up the Python Environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```
*The `requirements.txt` pins exact versions (see `requirements.txt`).*

## 3. Verify Data Integrity
```bash
python -m src.data.download_gsm8k
# Output shows SHA‑256 verification success and caches the dataset under data/gsm8k/
```

## 4. Run a Single Condition Locally (optional)
Example: run the full‑parameter OPD baseline for seed 0.
```bash
python -m src.training.opd \
 --seed 0 \
 --epochs 2 \
 --batch-size 8 \
 --output results/opd_full_0.json
```
The script prints peak RAM, wall‑clock time, per‑epoch loss, ΔL, and plateau detection. The JSON file conforms to `contracts/experiment_results.schema.yaml`.

## 5. Execute the Full CI Matrix Locally (for debugging)
```bash
# The helper script runs the same matrix as the CI workflow:
python scripts/run_matrix.py
```
`run_matrix.py` iterates over all conditions and seeds, respecting the **≤ 15 seeds per job** limit (the full experiment uses 30 seeds per condition split across two parallel jobs).

## 6. Run the GitHub Actions Workflow
Push a branch to trigger CI, or run manually:
```bash
git checkout -b test-run
git add.
git commit -m "trigger CI"
git push origin test-run
# In the GitHub UI, go to Actions → ci.yml → "Run workflow"
```
The workflow will:
1. Install dependencies.
2. Download and checksum GSM8K.
3. Execute each condition in parallel jobs (≤ 15 seeds per job).
4. Validate each result JSON against **both** `contracts/experiment.schema.yaml` **and** `contracts/experiment_results.schema.yaml`.
5. Aggregate all metrics into `state.yaml` and upload it as an artifact.

## 7. Inspect Results
After CI finishes, download the `state.yaml` artifact and view:
```bash
cat state.yaml
```
Key sections:
* `experiment_results` – per‑seed metrics (accuracy, RAM, time, loss, ΔL, plateau epoch).
* `analysis` – power, TOST, t‑test outcomes, normality diagnostics, and “inconclusive” flags.
* `resource_usage` – confirms compliance with the stipulated GB / 6 h limits.

## 8. Re‑run a Specific Seed (e.g., to debug a failure)
```bash
python -m src.training.frozen_sft \
 --seed 12 \
 --mask-file results/mask.json \
 --epochs 2 \
 --output results/frozen_sft_12.json
```

## 9. Reproduce Figures (optional)
```bash
python -m src.analysis.plot_results --state state.yaml --output-dir results/figures
```

All commands are deterministic; the same `state.yaml` will be generated on any runner that follows the steps above.