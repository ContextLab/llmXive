# Quickstart: Brain Network Dynamics & Improvisation Skill Analysis

## Prerequisites

- Python 3.11, internet access (one verified parquet shard is downloaded).
- No FSL/AFNI/GPU required — CPU-only by design.

## 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

All pinned parameters (seeds, window/step, QC thresholds, permutation
count, power target) live in `code/config.py`.

## 2. Download and verify data (verified real source)

```bash
python code/download_openneuro.py
```

This script:
- Downloads the **verified** parquet shard
  (`clane9/openneuro-fslr64k`, test split, `test-00000-of-00016.parquet`)
  to `data/raw/` via `huggingface_hub.hf_hub_download`; it fails loudly on
  any fetch error and never falls back to synthetic data.
- Records its SHA-256 in `data/checksums.json`.
- Streams the parquet with `pyarrow`, inventories the real columns, and
  writes `data/raw/column_inventory.json` listing which
  behavioral/covariate fields actually exist plus
  `available_subject_count`.
- Exits 0 on success.

## 3. Run the full pipeline (exact end-to-end command)

```bash
python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000
```

This orchestrates, in order: vertex-block extraction + bandpass + QC →
sliding-window Ledoit‑Wolf connectivity → vertex‑block connectivity
descriptors → PCA → power analysis (reporting‑only) → conditional
association regression (Freedman–Lane permutation + FDR) → sensitivity
sweep ({30,45,60}s × {5,10}s) → NetworkX/Matplotlib figures →
`results/manifest.csv`.

Run a subset of stages (e.g. the Phase‑1 checkpoint):

```bash
python code/run_all.py --stage download --stage extract --stage metrics
```

**Expected path:** if no real skill‑proxy column exists in the data, the
association stage prints a clear data‑mismatch message and the remaining
stages still complete.

## 4. Inspect results

- `results/manifest.csv` — master manifest
- `results/regression_results.csv` — association results (if proxy exists)
- `results/sensitivity_summary.csv` — window/step robustness table
- `results/power_analysis.json` — required vs. available N
- `results/fig_network_topology.png` — descriptive vertex‑block topology

## 5. Run tests

```bash
pytest -q tests
```

## 6. Re‑run one sensitivity setting

```bash
python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000 \
    --output_dir results/window30_step5
```
