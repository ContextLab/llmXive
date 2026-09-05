# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites
- Python 3.11+
- Git
- A GitHub Actions runner (or local machine with 7GB+ RAM).

## 1. Setup

Clone the repository and install dependencies:
```bash
git clone
cd PROJ-125-statistical-analysis-of-openstreetmap-da
pip install -r code/requirements.txt
```

## 2. Data Acquisition

**CRITICAL**: The `# Verified datasets` block for this project **does not contain** OSM or LST sources. You must manually provide a verified URL for the following:
- **OSM Data**: Download a `.osm.pbf` file for your target city (e.g., from Geofabrik). Place it in `data/raw/osm/`.
- **LST Data**: Download MODIS or Landsat LST rasters for the target period. Place them in `data/raw/lst/`.

*Note: Without these files, the pipeline will **halt** with a clear error and output **NO** metrics. It will not generate 'N/A' or '0.0' values.*

## 3. Configuration

Edit `code/config.py` to set:
- `CITY_NAME`: e.g., "Boston"
- `OSM_PATH`: Path to your OSM file.
- `LST_PATH`: Path to your LST file.
- `SEED`: Random seed for reproducibility (e.g., 42).
- `MAX_MEMORY_GB`: Set to 5.5 (to stay under 6GB limit).

## 4. Run the Pipeline

Execute the main script:
```bash
python code/main.py
```

This will:
1. Ingest and reproject data.
2. Rasterize OSM features to 30m.
3. Perform EDA (Moran's I, correlation).
4. Fit OLS (and SAR/GWR if memory permits, else fallback to OLS).
5. Run spatial CV and FDR correction.
6. Generate `data/results/metrics.csv` and plots.

*Note: If data is missing, the pipeline will **halt** with a clear error and output **NO** metrics. It will not generate 'N/A' or '0.0' values.*

## 5. Verify Results

Check `data/results/metrics.csv` for:
- `model_type`: Should be `OLS` or `OLS_DEGRADED` if memory constraints were hit.
- `rmse`, `r2`: Real values (no "N/A" or "0.0" unless data is missing, in which case the file is not generated).
- `correction_method`: "Permutation_FDR".

Check `data/results/sensitivity_plot.png` for the GWR bandwidth sweep (if GWR was run).

*Note: If data is missing, the pipeline will **halt** and output **NO** results.*

## 6. Troubleshooting

- **Memory Error**: If the pipeline crashes, check `config.py` and reduce `MAX_MEMORY_GB` or enable spatial sampling.
- **Data Not Found**: Ensure OSM and LST files are in `data/raw/` and paths are correct in `config.py`. The pipeline will **halt** with a clear error if data is missing.
- **No Verified Source**: If you see "NO VERIFIED SOURCE" in logs, update the `# Verified datasets` block in the spec with a real URL for OSM/LST.