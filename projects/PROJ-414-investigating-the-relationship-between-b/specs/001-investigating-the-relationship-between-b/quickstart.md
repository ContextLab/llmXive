# Quickstart: Running the Brain Network‑Improvisation Analysis

## Prerequisites
- Python 3.11 (installed by the CI runner).  
- `git` access to the repository (already cloned in CI).  
- Internet connectivity (to download the verified OpenNeuro parquet dataset).

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # contains nilearn>=0.10.0, scikit-learn, networkx, statsmodels, datasets, pandas, numpy, matplotlib, pytest
```

## 2. Verify Data Availability
```bash
python -c "from datasets import load_dataset; ds = load_dataset('clane9/openneuro-fslr64k'); print(ds)"
```
The command should list the parquet split and show column names. If any required column is missing, the pipeline will abort with a clear error (see Constitution Principle III).

## 3. Execute the Full Pipeline
```bash
python -m src.pipeline.run_all \
    --seed 42 \
    --output_dir data/output \
    --min_subjects 20
```
`run_all` orchestrates the phases defined in `plan.md`:
1. download & verification,
2. preprocessing,
3. sliding‑window connectivity & graph metrics,
4. PCA,
5. regression + permutation + FDR,
6. sensitivity sweep,
7. visualizations.

All intermediate files are written under `data/output/` with timestamps.

## 4. Inspect Results
- **Metrics table**: `data/output/metrics_summary.csv`  
- **Regression results**: `data/output/regression_results.csv` (passes `contracts/network_metrics.schema.yaml`).  
- **Sensitivity table**: `data/output/sensitivity_summary.csv`  
- **Figures**: `data/output/fig_network_topology.png`, `data/output/fig_sensitivity.png`

## 5. Run Contract Tests
```bash
pytest -q tests/contract
```
The test suite validates that each output file conforms to the schemas in `contracts/`.

## 6. Reproduce a Specific Sensitivity Setting (optional)
```bash
python -m src.pipeline.run_all \
    --window_size 30 \
    --step_size 5 \
    --seed 123 \
    --output_dir data/output/window30_step5
```
Use the same `--seed` to obtain deterministic results.

## 7. Clean Up
```bash
rm -rf data/output
```
The raw parquet file remains cached under `~/.cache/huggingface/datasets/` for future runs.

**Note**: All steps run on the CPU‑only GitHub Actions runner; no GPU resources are required. Runtime on the free tier is typically < 5 h for 25 subjects.

---
