# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites
- Python 3.11 or newer  
- Git  
- (Optional) NASA EarthData or Google Earth Engine credentials for Landsat download  

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-125-statistical-analysis-of-openstreetmap-da
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```

## Configuration

Edit `code/config.py` (or set environment variables) to match your environment:

```python
MAX_MEMORY_GB = 6          # memory cap
MAX_SAMPLES   = 500_000    # max cells after sampling
RANDOM_SEED   = 42
CITY_LIST = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
             "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
```

If you plan to use EarthEngine for LST:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/ee-credentials.json"
```

## Running the Pipeline

### 1. Download data (if not already cached)
```bash
python code/main.py --task download --city "New York"
```
*The command will fetch OSM vectors from the verified HuggingFace parquet URLs and attempt a Landsat LST download via NASA EarthData. Check `data/raw/` for checksums.*

### 2. Execute the full analysis
```bash
python code/main.py --task run --city "New York"
```
*Progress, memory usage, and any fallback mode (`OLS_DEGRADED`) are logged to stdout and `data/results/metrics.csv`.*

### 3. Inspect results
- **Metrics**: `data/results/metrics.csv`  
- **Plots**: `data/results/plots/` (including the bandwidth‑sweep or OLS‑stability plot)  
- **Report**: `data/results/reports/report_New_York.md`

## Troubleshooting

- **Memory error**: If the log shows `model_type: OLS_DEGRADED`, the pipeline ran in degraded mode due to RAM > 5 GB. Results are still valid but limited to OLS.  
- **Landsat download failure**: Verify network access and that the EarthData API credentials (if used) are correct. The pipeline will abort with a clear error message; no synthetic data are generated.  
- **Lint failures**: Run `ruff check code/ && black --check code/`. Fix any reported issues before re‑running.  

---
