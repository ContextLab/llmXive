# Quickstart: Predicting Yield Strength of BCC Alloys

## Prerequisites
- Python 3.11 or newer
- Git
- Access to a Linux environment (local machine or GitHub Actions runner)

## Setup

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-525-predicting-the-yield-strength-of-bcc-all

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Directory Structure

The pipeline expects the following layout (created on demand by the toolkit's `paths` helper, or manually):

```text
data/raw/          # immutable raw MPEA download
data/processed/    # filtered, aggregated, and engineered CSVs
data/logs/         # rejected_entries.log, aggregation.log, descriptor_errors.log
code/              # pipeline modules
tests/             # pytest unit tests
reports/           # results.json
state/             # checksums and artifact hashes
```

## Run the Full Pipeline

```bash
# Execute the end‑to‑end script
python code/main.py
```

`main.py` orchestrates the following steps (each corresponds to a functional requirement):

1. **Download & Verify MPEA** – FR‑001, FR‑002  
2. **Filter for BCC & Normalize** – FR‑001, FR‑002, FR‑004  
3. **Aggregate duplicate compositions** – FR‑007  
4. **Compute descriptors & ILR** – FR‑003, FR‑003.1, FR‑008  
5. **Repeated 5‑Fold CV (10 repeats)** – FR‑005  
6. **Bootstrap CI for R²** – FR‑006  
7. **Permutation importance** – FR‑006  
8. **Write results** – `reports/results.json` (validated against `contracts/results.schema.yaml`)

## Expected Outputs

| File/Folder | Content |
|-------------|---------|
| `data/raw/mpea.csv` | Raw downloaded MPEA dataset (immutable) |
| `data/processed/bcc_filtered.csv` | BCC‑only, yield‑strength‑present rows |
| `data/processed/bcc_aggregated.csv` | One row per unique composition, with averaged yield and std‑dev |
| `data/processed/features_engineered.csv` | Scalar + ILR descriptors |
| `reports/results.json` | Model performance, CI, feature importance, stability, practical‑utility flag |
| `data/logs/rejected_entries.log` | List of rows removed during filtering |
| `data/logs/aggregation.log` | Aggregation method (`"average"`) per duplicate group |
| `data/logs/descriptor_errors.log` | Alloy IDs for which a descriptor fell back to 0.0 |

## Checksum Recording

After download, the SHA‑256 checksum of `data/raw/mpea.csv` is computed and recorded in the project's `state/` artifact-hash map (Constitution Principle III). Raw files are never modified in place; every transformation writes a new file under `data/processed/`.

## Troubleshooting

- **`DATA_SCARCITY`** – If you see `DATA_SCARCITY: Insufficient BCC alloys (N < 80)` in `stderr`, the filtered dataset contains fewer than 80 entries. The pipeline halts as required.
- **`YIELD_DEFINITION_INVALID`** – Indicates the source file lacks a clear yield‑strength definition; the run stops.
- **`DATA_UNAVAILABLE`** – DOI resolution failed (paywall or missing file). No fallback dataset is permitted.
- **`COMPLEMENTARITY_FAILURE`** – Feature selection removed all ILR or all scalar descriptors; check the `descriptor_errors.log` for possible domain errors.
- **`CONFOUNDING_METADATA_MISSING`** – Testing-condition metadata (temperature, strain rate) is absent for some rows; the run continues and the limitation is recorded in `reports/results.json`.
- **MemoryError** – Ensure you are using the provided `requirements.txt`; the dataset size is well within limits for the free runner.