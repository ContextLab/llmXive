# Quickstart: Brain Network Dynamics & Improvisation Skill Analysis

## Prerequisites

- Python 3.11, internet access (one verified parquet URL is downloaded).
- No FSL/AFNI/GPU required — CPU-only by design.

## 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Download and verify data (redo of previously failed T001)

```bash
python code/download_openneuro.py
```

This script:
- Downloads the **verified** parquet shard directly from
  `
  to `data/raw/` (resumable; exits non-zero on HTTP failure).
- Records its SHA-256 in `data/checksums.json`.
- Streams the parquet with `pyarrow`, inventories the real columns, and writes `data/raw/column_inventory.json` listing which behavioral/covariate fields actually exist.
- Exits 0 on success. (The previous version failed because it referenced a non-existent HuggingFace dataset from the OpenNeuro collection.)

## 3. Run the full pipeline

```bash
python code/run_all.py --seed 42 --window 45 --step 10 --permutations 1000
```

Orchestrates: vertex-block extraction + bandpass + QC → sliding-window Ledoit-Wolf connectivity → vertex-block connectivity descriptors → PCA → power analysis (reporting-only) → conditional association regression (Freedman–Lane permutation + FDR) → sensitivity sweep ({30,45,60}s × {5,10}s) → NetworkX/Matplotlib figures → `results/manifest.csv`.

**Expected path:** if no real skill-proxy column exists in the data (the anticipated outcome), the association stage prints a clear data-mismatch message, records the scope gap in the report, and the remaining stages (descriptor sensitivity, descriptive topology figure, manifest) still complete — the descriptive characterization is the primary deliverable. The power analysis never aborts the pipeline; under-power gates the association stage only.

## 4. Inspect results

- `results/manifest.csv` — master manifest (Single Source of Truth)
- `results/regression_results.csv` — coefficients, Freedman–Lane permutation p, FDR p, significance (only if the association stage ran)
- `results/sensitivity_summary.csv` — window/step robustness table (correlation SD marked `not_computable_no_skill_proxy` on the expected path)
- `results/power_analysis.json` — required vs. available N (correlation/F-test framework)
- `results/fig_network_topology.png` — descriptive vertex-block topology figure (group comparison only if real task labels exist)

## 5. Run tests

```bash
pytest -q tests/unit tests/contract
```

Contract tests validate every output file against `contracts/*.schema.yaml`.

## 6. Re-run one sensitivity setting

```bash
python code/run_all.py --seed 123 --window 30 --step 5 --permutations 1000 \
    --output_dir results/window30_step5
```

Same seed ⇒ deterministic results (Constitution Principle I).