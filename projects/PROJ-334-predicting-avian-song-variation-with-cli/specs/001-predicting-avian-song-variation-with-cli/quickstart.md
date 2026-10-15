# Quickstart: Predicting Avian Song Variation with Climatic and Geographic Factors

## Prerequisites
- Python 3.11 or newer  
- Git  
- Internet access (to download the verified `AnalysisDataset` parquet files)  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-334-predicting-avian-song-variation-with-cli

# 2️⃣ Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup

The pipeline works **directly** from the verified, open dataset; no manual download is required.

```bash
# This will download the parquet file(s) and record checksums automatically
python code/ingestion.py --download-only
```

The script:
1. Fetches `analysis_dataset.parquet` from the HuggingFace URL(s) listed in `contracts/analysis_dataset.schema.yaml`.  
2. Verifies SHA‑256 checksums (recorded in `data/checksums.txt`).  
3. Saves a copy to `data/processed/analysis_dataset.parquet`.

## Running the Full Pipeline

```bash
python code/main.py
```

The pipeline executes the following stages in order:
1. **Ingestion & validation** (Phase 0)  
2. **Exploratory Data Analysis** (Phase 1) – creates `outputs/eda_report.json` and figures.  
3. **Model fitting & FDR correction** (Phase 2) – creates `outputs/model_summary.csv`.  
4. **Sensitivity analysis** (Phase 3) – creates `outputs/sensitivity_report.json`.  

All output artifacts are stored under `outputs/`.

## Testing

```bash
pytest tests/ -v
```

Key test suites:
- `test_ingestion.py` – checksum handling, schema validation, optional CRS reprojection.  
- `test_eda.py` – correlation matrix properties, VIF‑pair flagging.  
- `test_modeling.py` – OLS fit, aggregated p‑value generation, Benjamini‑Hochberg implementation, threshold sweep.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Checksum mismatch** | Data file changed on remote source | Re‑run `ingestion.py --download-only` to refresh checksum file. |
| **MemoryError** | Dataset larger than available RAM | Edit `code/utils.py` → `MAX_ROWS` to a smaller value (e.g., 30 000) and re‑run. |
| **CRS warning** | User‑provided raster not in WGS84 | Ensure raster is reprojected; the script will do it automatically if `rasterio` can read the CRS. |
| **Model did not improve over null** | Insufficient power (reported in `model_summary.csv`) | Consider collecting more recordings; results are flagged as preliminary. |

---
