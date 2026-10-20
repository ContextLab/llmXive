# Quickstart: Minimal Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`  
**Goal**: Run a lightweight end‑to‑end pipeline on a small subset of clips and produce `data/descriptors_subset.csv`.

## Prerequisites
All heavy dependencies are listed in `requirements.txt`. Create a virtual environment and install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scripts
- `scripts/quickstart.sh` – activates the virtual environment (if present) and adds `src/` to `PYTHONPATH`.  
- `scripts/run_minimal.sh` – orchestrates the minimal pipeline:
  1. Generates **50** deterministic clips (`src/pipeline/generate_clips.py` with `--num 50`).  
  2. Extracts the three descriptors for each clip (`src/pipeline/extract_descriptors.py`).  
  3. Writes `data/descriptors_subset.csv`.  

Both scripts are executable (`chmod +x scripts/*.sh`) and are used by the CI runner.

## Run the Minimal Pipeline (single command)

```bash
bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh"
```

### Expected Output
```text
Generating 50 clips ... done.
Extracting descriptors ... done.
Wrote a subset of rows (including the header) to data/descriptors_subset.csv
```

You can verify the file exists and contains the expected columns:

```bash
head data/descriptors_subset.csv
wc -l data/descriptors_subset.csv   # should contain the expected number of rows (header plus the intended data entries)
```

The produced CSV conforms to `contracts/descriptor.schema.yaml`; the CI test `tests/contract/test_descriptor_schema.py` validates it automatically.

---  

## Note on End‑to‑End Execution
The full pipeline is driven by `src/pipeline/run_all.py`. The quickstart script only exercises the generation and descriptor steps for rapid verification.
