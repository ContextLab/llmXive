# Quickstart: llmXive Procedural Memory Augmentation Experiment

This guide walks you through reproducing the full experiment on a fresh GitHub Actions (or local) environment.

## Prerequisites
| Item | Version |
|------|---------|
| Python | 3.11 |
| Git | any |
| `git-lfs` (for large model files) | optional |
| Kaggle API token (for optional GPU off‑load) | optional but not required (CPU‑only run) |

## 1. Clone the repository
```bash
git clone 
cd llmxive-procedural-memory
```

## 2. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Verify data integrity (optional)
```bash
python -c "import json, hashlib, pathlib, sys; \
manifest = json.load(open('data/manifest.json')); \
for f, chksum in manifest.items(): \
    data = pathlib.Path('data', f).read_bytes(); \
    if hashlib.sha256(data).hexdigest() != chksum: \
        sys.exit(f'Checksum mismatch: {f}'); \
print('All checksums OK')"
```

## 4. Download the official TUA‑Bench task set and select a representative set of tasks
```bash
python code/generate_synthetic_tasks.py \
    --num_complex 12 --num_routine 12 \
    --output data/synthetic_tasks.json
# This script loads the official TUA‑Bench dataset, verifies required fields,
# and writes a reproducible subset of 24 tasks plus a relevance map.
```

## 5. Run the baseline condition (multiple seeds)
```bash
for SEED in 0 1 2 3 4; do
    python code/run_baseline.py --seed $SEED --output data/baseline_results/seed_${SEED}.json
done
python code/aggregate_results.py --mode baseline
# Generates data/baseline_results/aggregated.json (includes batch runtime check)
```

## 6. Run the augmented condition (k = 1, 3, 5)
```bash
for K in 1 3 5; do
    for SEED in 0 1 2 3 4; do
        python code/run_augmented.py --seed $SEED --top_k $K \
            --output data/augmented_results/k_${K}/seed_${SEED}.json
    done
    python code/aggregate_results.py --mode augmented --top_k $K
done
# Each batch logs its total runtime and verifies it stays ≤ 6 h.
```

## 7. Statistical analysis
```bash
python code/stats.py \
    --baseline data/baseline_results/aggregated.json \
    --augmented data/augmented_results/k_3/aggregated.json \
    --output-dir stats/
```
This script produces:
- `stats/mcnemar_k3.json`
- `stats/wilcoxon_k3.json` (exploratory)
- `stats/holm_corrected.json`
- `stats/subgroup_complex.json`
- `stats/subgroup_routine.json`
- `stats/false_positive.json`
- `stats/gain_complex.json`
- `stats/gain_routine.json`

## 8. Generate figures
```bash
python code/plot_results.py --stats-dir stats/ --fig-dir figures/
```
Figures are saved as PNG files ready for inclusion in the paper.

## 9. Validate contracts
```bash
pytest -q tests/contract/test_execution_result.py
```
All JSON result files must pass the `execution_result.schema.yaml` contract.

## 10. View the summary report
```bash
less results/summary.md
```

## 11. (Optional) Run entirely on the GitHub Actions free tier
Create a workflow file `.github/workflows/run_experiment.yml` (provided in the repo) and push. The workflow will automatically:
1. Install dependencies,
2. Execute the full pipeline on the CPU‑only runner (model quantized to 4‑bit),
3. Upload `results/`, `figures/`, and `stats/` as artifacts.

## 12. Clean‑up
```bash
rm -rf .venv data/baseline_results data/augmented_results stats figures results
```

**Note**: All random seeds are fixed in `code/constants.py`; re‑running the pipeline yields identical JSON outputs, satisfying the reproducibility principle. Randomized execution order per seed is handled internally by the run scripts.  
