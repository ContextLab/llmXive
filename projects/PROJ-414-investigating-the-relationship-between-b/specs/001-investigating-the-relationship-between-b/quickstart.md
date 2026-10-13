# Quickstart: Running the Brain Network‑Improvisation Analysis

## Prerequisites
- Python 3.11 (installed by the CI runner).  
- `git` access to the repository (already cloned in CI).  
- Internet connectivity (to download the verified OpenNeuro dataset).

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # includes nilearn, nipype, fslpy, scikit-learn, networkx, statsmodels, datasets, pandas, numpy, matplotlib, pytest
```

> **Note:** The pipeline relies on **FSL (v6.0.5)** and **AFNI (v22.2.07)** binaries, which are pre‑installed on the GitHub Actions runner image. If running locally, ensure these tools are available in your `$PATH`.

## 2. Download and Verify Data
```bash
python code/download_openneuro.py
```
The script downloads the OpenNeuro dataset `ds000246`, creates
`data/raw/openneuro/ds000246/manifest.json` and records SHA‑256 checksums in
`data/raw/checksums.json`. It aborts with a clear error if the dataset does
not contain at least 20 subjects or if any subject is missing the required
``Improv`` and ``Scripted`` runs.

## 3. Execute the Full Pipeline
```bash
python -m src.pipeline.run_all \
    --seed 42 \
    --output_dir data/output \
    --min_subjects 20 \
    --permutations 5000
```
`run_all` orchestrates the phases defined in `plan.md`:
1. download & verification,  
2. **FSL/AFNI** preprocessing via Nipype,  
3. sliding‑window connectivity & graph metrics,  
4. PCA,  
5. regression + 5 000 permutation + FDR,  
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
    --output_dir data/output/window30_step5 \
    --permutations 5000
```
Use the same `--seed` to obtain deterministic results.

## 7. Clean Up
```bash
rm -rf data/output
```
The raw parquet file remains cached under `~/.cache/huggingface/datasets/` for future runs.

**Note**: All steps run on the CPU‑only GitHub Actions runner; no GPU resources are required. Runtime on the free tier is typically < 5 h for 25 subjects.