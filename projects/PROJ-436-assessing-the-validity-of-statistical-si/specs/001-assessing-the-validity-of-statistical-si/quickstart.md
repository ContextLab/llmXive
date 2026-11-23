# Quickstart: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Prerequisites
- Python 3.11 or newer
- Internet access (to download the verified datasets)

## Setup

```bash
# 1. Navigate to the project root
cd projects/PROJ-436-assessing-the-validity-of-statistical-si

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution

### 1. Download & Verify Raw Datasets
```bash
python code/main.py --action download
```
- Downloads the three verified files listed in `research.md`.
- Computes SHA‑256 checksums and writes `data/checksums/manifest.json`.
- Fails fast if any checksum mismatch occurs.

### 2. Run the Full Simulation
```bash
python code/main.py \
    --action run \
    --datasets rct_1 mcar_0 mar_0 \
    --iterations 15000 \
    --rates 0.05 0.10 0.15 0.20 0.25 \
    --mechanisms MCAR MAR MNAR \
    --methods CC MI IPW
```
- Executes the pipeline described in `plan.md`.
- All random seeds are fixed; rerunning produces identical results.
- **Dataset size guard**: any dataset with fewer than 100 rows is automatically skipped and reported in `tipping_points.csv` with status `FLAGGED`.
- Outputs are written to `data/processed/` (see **Data Model**).

### 3. Inspect Results
```bash
# Summary JSON
jq '.' data/processed/simulation_outputs.json | less

# Tipping‑point table (CSV)
column -t -s, data/processed/tipping_points.csv | less
```

### 4. Generate Visualizations
```bash
python code/main.py --action visualize --output figures/
```
Creates:
- `figures/type1_error_by_mechanism.png`
- `figures/tipping_point_curve.png`
- `figures/method_comparison.png`
- `figures/ks_test_pvalues.png`

### 5. Run Tests
```bash
pytest tests/ -v
```
All unit and integration tests must pass; they validate:
- Correct checksum handling (`data_loader`).
- Proper generation of synthetic treatment/outcome.
- Conformance of output files to the JSON‑Schema contracts.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `FileNotFoundError` on a raw dataset | Network interruption during download | Re‑run `--action download`; the script retries up to 3 times. |
| MemoryError on a parquet file | Dataset larger than available RAM | Add `--stream` flag (implemented in `data_loader.py`) to process the file in chunks. |
| Missing columns after preparation | Source file lacks numeric covariates | The pipeline will automatically generate **independent** synthetic covariates; check logs for “Synthetic covariate generated”. |
| `miceforest` raises `RuntimeError` | Insufficient RAM for MI on very large data | Reduce `--iterations` (e.g., to 10000) or use a smaller random sample via `--sample 0.5`. |
| Binary outcome analysis uses logistic regression (as required) | No action needed – the pipeline already applies the correct test. |
| No verified RCT dataset with treatment/outcome | The study uses synthetic RCT construction; this limitation is documented in `research.md`. | Consider extending the scope when an open RCT becomes available. |

---


