# Quickstart: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Prerequisites

- Python 3.11 or newer
- Git
- Internet access to the verified OpenStreetMap extract source (e.g., Geofabrik)  
- An LST GeoTIFF inventory satisfying the FR‑002 contract **once the spec amendment is in place**.

> **LST note (temporary deviation)**: FR‑002’s USGS EarthExplorer route cannot be run unattended on the CI runner, and no verified open LST URL currently exists in the project's verified‑datasets block. **Until a spec amendment authorises a programmatically downloadable LST product or a local checksummed asset, users must manually place the required GeoTIFFs under `data/raw/lst/` and register them in `data/raw/manifest.json` with SHA‑256 checksums.** This manual step is a **temporary deviation** from Constitution Principle I; the steady‑state workflow will automatically fetch LST from the approved source once the amendment is approved.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-125-statistical-analysis-of-openstreetmap-da
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Configuration

`code/config.py`:

```python
RANDOM_SEED   = 42
MAX_MEMORY_GB = 6          # hard abort (exit code 99)
DEGRADE_GB    = 5          # OLS_DEGRADED fallback
MAX_SAMPLES   = 500_000    # max cells after spatial block sampling
MAX_BLOCKS    = 250        # tuned so peak RSS stays below 6 GB
CITY_LIST = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
]
```

## Running the Pipeline

```bash
# 1. Download OSM data (checksums recorded)
python code/main.py --task download --city "New York"

# 2. Run the full analysis
python code/main.py --task run --city "New York"

# 3. Quality assurance (lint + tests)
python code/main.py --task lint
python code/main.py --task test
```

## Inspecting Results

- **Metrics**: `data/results/metrics.csv` (includes `correction_method = "permutation-FDR"`, `memory_status`, `memory_peak_gb`)  
- **Model outputs**: `data/results/models/*.json` (validated against `contracts/model_output.schema.yaml`)  
- **Plots**: `data/results/plots/` (bandwidth sweep / OLS stability)  
- **QA artifacts**: `data/results/qa/lint_report.txt`, `data/results/qa/test_report.txt`  
- **Report**: `data/results/reports/report_<city>.md`

## Quickstart Validation

The quickstart is validated by running the `download`, `run`, `lint`, and `test` commands end‑to‑end on a fresh environment. The resulting logs are saved under `data/results/qa/quickstart_validation.txt`.

## Troubleshooting

- **`DATA_GAP` error**: no LST rasters registered — see the LST note above.  
- **`model_type: OLS_DEGRADED`**: Peak RAM usage exceeded a substantial threshold; OLS‑only results with clustered SE, Moran’s I, and a bias warning were produced.  
- **Exit code 99**: peak RAM exceeded 6 GB (SC‑005) — reduce `MAX_BLOCKS` or city extent.  

