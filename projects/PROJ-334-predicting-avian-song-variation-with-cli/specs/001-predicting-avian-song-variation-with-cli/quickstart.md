# Quickstart: Predicting Avian Song Variation with Climatic and Geographic Factors

## Prerequisites
- Python 3.11+  
- Git  
- Internet access (to download the verified `AnalysisDataset` parquet file)  

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
# Download the merged dataset and record its checksum
python code/ingestion.py --download-only
```

The script:
1. Fetches `analysis_dataset.parquet` from the HuggingFace URL(s) listed in `contracts/analysis_dataset.schema.yaml`.  
2. Verifies the SHA‑256 checksum (recorded in `data/checksums.txt`).  
3. Saves a copy to `data/processed/analysis_dataset.parquet`.

## Running the Full Pipeline

```bash
python code/main.py
```

The pipeline executes the following stages in order:
1. **Ingestion & validation** (Phase 0) – includes merge validation (T018).  
2. **Exploratory Data Analysis** (Phase 1) – creates `outputs/eda_report.json` and figures.  
3. **Power analysis** (Phase 2) – runs a priori power calculation and flags under‑powered scenarios.  
4. **Model fitting & global FDR correction** (Phase 3) – creates `outputs/model_summary.csv`.  
5. **Sensitivity analysis** (Phase 4) – creates `outputs/sensitivity_report.json` (threshold sweep, omitted‑variable bias checks).  

All output artifacts are stored under `outputs/`.

## Testing

```bash
pytest tests/ -v
```

Key test suites:
- `test_ingestion.py` – checksum handling, schema validation, optional CRS reprojection, merge validation.  
- `test_eda.py` – correlation matrix properties, VIF‑pair flagging, Moran's I diagnostics.  
- `test_power.py` – a priori power calculation logic and reporting.  
- `test_modeling.py` – OLS fit, aggregated p‑value generation, global Benjamini‑Hochberg implementation, sensitivity analysis, omitted‑variable bias checks.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Checksum mismatch** | Remote file changed | Re‑run `ingestion.py --download-only` to refresh `checksums.txt`. |
| **MemoryError** | Dataset larger than RAM | Edit `code/utils.py` → `MAX_ROWS` to a smaller value (e.g., 30 000) and re‑run. |
| **CRS warning** | User‑provided raster not in WGS84 | Ensure raster is reprojected; the script will do it automatically if `rasterio` can read the CRS. |
| **Model did not improve over null** | Insufficient statistical power (reported in `model_summary.csv`) | Consider collecting more recordings; results are flagged as preliminary. |
| **Spatial autocorrelation detected** | Significant Moran's I | Rerun modeling with `cluster_robust=True` (handled internally). |

---

