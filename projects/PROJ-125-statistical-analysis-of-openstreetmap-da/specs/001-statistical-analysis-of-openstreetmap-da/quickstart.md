# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites
- Python 3.11 or newer  
- Git  
- (Optional) NASA EarthData or Google Earth Engine credentials for Landsat download (not required for the open HuggingFace LST dataset)

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
CITY_LIST = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
]
```

If you wish to use the original Landsat download route (requires credentials), set the appropriate environment variables; otherwise the pipeline will default to the **open LST dataset** hosted on HuggingFace.

## Running the Pipeline

### 1. Download data (if not already cached)
```bash
python code/main.py --task download --city "New York"
```
*The command fetches OSM vectors from the verified HuggingFace parquet URLs and downloads the **open** Landsat LST composite from `https://huggingface.co/datasets/earthlab/landsat8_lst`. Checksums are recorded under `data/`.*

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
- **LST download failure**: With the open HuggingFace source this should not occur. If it does, verify internet connectivity and that the URL is reachable.  
- **Lint failures**: Linting is outside the scope of the current functional requirements; ensure code follows standard style but no automated lint check is required.  

--- 

## Scope Note
The quickstart documentation is provided for user guidance; automated validation of the quickstart script is not a required functional requirement in the specification.
