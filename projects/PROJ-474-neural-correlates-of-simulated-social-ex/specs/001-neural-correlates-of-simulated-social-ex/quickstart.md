# Quickstart: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Prerequisites
- Python 3.11 or newer
- Git
- Docker (required for the optional fMRIPrep container; not needed for the core pipeline)
- Internet access from the CI runner (to fetch verified datasets)

## Installation

```bash
# Clone the repository
git clone 
cd neural-correlates-social-exclusion

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

## Data Setup

```bash
# Attempt to download the verified Cyberball dataset
python code/data_loader.py --dataset ds000030 --output data/raw
```

- If the dataset is not present in the verified list, the command will terminate with `ERR_DATA_UNVERIFIED` and the pipeline will stop.  
- No synthetic data are generated; you must add a verified source for `ds000030` to the project's verified‑datasets block before proceeding.

## Running the Full Analysis

```bash
python code/main.py --seed 42
```

The pipeline performs:

1. Data download & integrity check.  
2. Motion QC (mean FD ≤ 0.2 mm).  
3. ROI time‑series extraction.  
4. Static & sliding‑window connectivity computation.  
5. Paired permutation test (10 000 permutations).  
6. Generation of all required figures and a summary report (`results/report.md`).

## Validation & Testing

```bash
# Unit tests
pytest tests/

# Schema validation (example)
python - <<'PY'
import json, jsonschema, pathlib
schema = yaml.safe_load(open('contracts/connectivity.schema.yaml'))
data   = json.load(open('data/processed/connectivity_sample.json'))
jsonschema.validate(instance=data, schema=schema)
print("Connectivity file validates.")
PY
```

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `ERR_DATA_UNVERIFIED` | No verified Cyberball dataset in the block. | Add a verified URL for `ds000030` or request a substitute verified dataset. |
| `ERR_N_INSUFFICIENT` (101897696) | Fewer than 10 subjects passed QC. | Verify motion thresholds or obtain additional subjects. |
| MemoryError | Attempting to load whole NIfTI into RAM. | Ensure streaming mode (`--stream`) is enabled (default). |
| Missing figures | Pipeline halted early due to QC failure. | Check logs in `data/processed/qc_log.csv` for exclusion reasons. |

---
