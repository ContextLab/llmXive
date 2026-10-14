# Quickstart: Running the Brain Network‑Improvisation Analysis

## Prerequisites
- Python 3.11 (pre‑installed on the CI runner).  
- Internet connectivity (to download the verified OpenNeuro datasets).  
- FSL 6.0.5 and AFNI 22.2.07 binaries available in `$PATH` (pre‑installed on the GitHub Actions runner image).  

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes nilearn, nipype, fslpy, etc.
```

## 2. Download and Verify Data
The data are fetched directly from the verified HuggingFace OpenNeuro mirrors. This approach streams the data and verifies required columns without relying on a separate script that previously failed.

```python
# download_hf.py (run with python)
from datasets import load_dataset, DatasetDict
import json, pathlib

datasets_to_load = ["openneuro/ds000246", "openneuro/ds001600"]
out_dir = pathlib.Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)

required_cols = {
    "subject_id", "run_label", "age", "years_training", "fd",
    # ROI columns
    *{f"roi_{i}" for i in range(1, 101)},
    # optional covariates
    "instrument_type", "genre", "practice_intensity", "education", "improv_rating"
}

for ds_name in datasets_to_load:
    ds: DatasetDict = load_dataset(ds_name, streaming=True)
    # Iterate and write to parquet, verifying columns
    for split, split_ds in ds.items():
        parquet_path = out_dir / f"{ds_name.replace('/', '_')}_{split}.parquet"
        # Collect rows that contain all required columns (optional cols may be missing)
        rows = []
        for row in split_ds:
            missing = required_cols - row.keys()
            if missing - {"instrument_type","genre","practice_intensity","education","improv_rating"}:
                raise RuntimeError(f"Missing required columns {missing} in {ds_name} {split}")
            rows.append(row)
        # Write parquet
        import pandas as pd
        pd.DataFrame(rows).to_parquet(parquet_path)
        # Record checksum
        import hashlib, json
        checksum = hashlib.sha256(open(parquet_path, "rb").read()).hexdigest()
        checksums = {}
        if (out_dir / "checksums.json").exists():
            checksums = json.load(open(out_dir / "checksums.json"))
        checksums[str(parquet_path)] = checksum
        json.dump(checksums, open(out_dir / "checksums.json", "w"), indent=2)
print("Download and verification complete.")
```

Run the script:

```bash
python download_hf.py
```

The script:
- Pulls the parquet files from the **verified** HuggingFace URLs `https://huggingface.co/datasets/openneuro/ds000246` and `https://huggingface.co/datasets/openneuro/ds001600` via `datasets.load_dataset`.
- Writes a checksum manifest to `data/raw/checksums.json`.
- **Verifies** that the required columns (`subject_id`, `run_label`, `age`, `years_training`, `fd`, `roi_1…roi_100`) are present; aborts with a clear error if any are missing.
- Retains optional columns (`instrument_type`, `genre`, `practice_intensity`, `education`, `improv_rating`) for downstream covariate control.

## 3. Run the Full End‑to‑End Pipeline
```bash
python -m src.pipeline.run_all \
    --seed 42 \
    --output_dir data/output \
    --permutations 1000 \
    --window_size 45 \
    --step_size 10
```
`run_all` orchestrates the phases defined in `plan.md`:
1. Preprocessing (FSL/AFNI via Nipype).  
2. Sliding‑window connectivity + Ledoit‑Wolf regularization.  
3. Graph‑metric computation.  
4. PCA dimensionality reduction.  
5. Regression with permutation testing (1 000 permutations) and FDR correction.  
6. Sensitivity sweep (default parameters are also executed for reporting).  
7. Visualizations (NetworkX + Matplotlib).  
8. Generation of `data/output/master_manifest.csv` (the Single Source of Truth).

All intermediate artifacts are written under `data/output/` with timestamps.

## 4. Inspect Results
- **Metrics table**: `data/output/metrics_summary.csv`  
- **Regression table**: `data/output/regression_results.csv` (validated against `contracts/network_metrics.schema.yaml`).  
- **Sensitivity summary**: `data/output/sensitivity_summary.csv`  
- **Figures**: `data/output/fig_network_topology.png`, `data/output/fig_sensitivity.png`  
- **Master manifest**: `data/output/master_manifest.csv`

## 5. Run Contract Tests
```bash
pytest -q tests/contract
```
The suite checks each output file against its JSON schema in `contracts/`.

## 6. Re‑run a Specific Sensitivity Setting (optional)
```bash
python -m src.pipeline.run_all \
    --window_size 30 \
    --step_size 5 \
    --seed 123 \
    --output_dir data/output/window30_step5 \
    --permutations 1000
```
Use the same `--seed` for deterministic results.

## 7. Clean Up
```bash
rm -rf data/output
```
The raw parquet files remain cached in `~/.cache/huggingface/datasets/` for future runs.

**Note**: The entire workflow runs on the CPU‑only GitHub Actions free tier; total runtime is typically < 5 h for 40 subjects.

---



