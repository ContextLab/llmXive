# Quickstart: Predicting Molecular Reactivity

## Prerequisites
- Python 3.10+  
- Git  
- (Optional) Docker for local CI simulation  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-243-predicting-molecular-reactivity-using-gr

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify linting and formatting (required by T002)
ruff check . --output-format=json > artifacts/ruff_report.json
black --check . > artifacts/black_report.txt
# Both commands must exit with status 0; otherwise fix the reported issues.
```

## Data Setup

```bash
# Create required directories (tasks T001a‑T001b)
mkdir -p data/raw data/processed data/assets artifacts/logs
touch data/raw/.gitkeep data/processed/.gitkeep data/assets/.gitkeep artifacts/logs/.gitkeep

# 1. Static assets (provided in the repo)
#    - reference_substructures_raw.csv (50 rows)
#    - kinetic_dataset_raw.csv (≥20 rows)

# 2. Initialize an empty checksums file (Task T003)
echo "{}" > data/raw/checksums.json

# 3. Download QM9 subset (streamed)
python code/data/download.py --dataset qm9 --output data/raw
# The script streams to data/raw/qm9_subset.parquet.

# 4. Populate checksums for all raw files (Task T006)
python code/utils/checksums.py --dir data/raw --output data/raw/checksums.json
# This updates the previously empty JSON with SHA‑256 hashes for:
#   - qm9_subset.parquet
#   - reference_substructures_raw.csv
#   - kinetic_dataset_raw.csv
```

## Running the Full Pipeline

### 1. Preprocess
```bash
python code/data/preprocess.py \
  --input data/raw/qm9_subset.parquet \
  --output data/processed
# Generates graphs.pt, exclusion_report.json, and memory_adjustment.log.
```

### 2. Train Models
```bash
python code/train/trainer.py \
  --epochs 50 \
  --device cpu \
  --early-stop-patience 5
# Produces model checkpoints under artifacts/models/.
```

### 3. Evaluate & Test
```bash
python code/train/eval.py \
  --model-dir artifacts/models/ \
  --output artifacts/
# Writes predictions.parquet, metrics.json (incl. paired t‑test).
```

### 4. Attribution
```bash
python code/interpret/explainer.py \
  --model-dir artifacts/models/ \
  --output artifacts/
# Generates attribution_maps.json validated against contracts/attribution.schema.yaml.
```

### 5. Proxy Validation
```bash
python code/interpret/validate_proxy.py \
  --predictions artifacts/predictions.parquet \
  --kinetic data/raw/kinetic_dataset_raw.csv \
  --output artifacts/
# Produces kinetic_correlation.png and kinetic_report.txt.
```

### 6. Single‑Source‑of‑Truth Check
```bash
python code/utils/ssot.py \
  --metrics artifacts/metrics.json \
  --predictions artifacts/predictions.parquet
# Logs verification result to artifacts/ssot.log.
```

## Expected Artifacts
After a successful run, `artifacts/` should contain:

- `metrics.json` (performance & statistical tests)  
- `predictions.parquet` (test‑set predictions)  
- `attribution_maps.json` (explanation data)  
- `exclusion_report.json` (invalid SMILES log)  
- `memory_adjustment.log` (any batch‑size reductions)  
- `ruff_report.json` & `black_report.txt` (lint/format verification)  
- `checksums_artifacts.json` (SHA‑256 of all output files)  
- `ssot.log` (single‑source‑of‑truth validation)  

## Troubleshooting
- **Lint/format failures**: Fix reported style issues, then re‑run the `ruff`/`black` commands.  
- **Memory OOM**: Reduce batch size via `--batch-size` flag in `trainer.py`; the script also auto‑adjusts.  
- **Download errors**: The downloader retries up to 3 times with exponential backoff; persistent failure aborts with a clear error message.  

---
