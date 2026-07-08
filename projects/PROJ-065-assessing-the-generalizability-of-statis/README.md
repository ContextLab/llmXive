# PROJ-065: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

## Overview
This project implements an automated pipeline to assess the stability and generalizability of statistical findings from pre-registered studies. It ingests data from the Open Science Framework (OSF), performs bootstrap resampling and sensitivity analysis, and aggregates results using meta-analytic techniques.

## Project Structure
```
.
├── code/ # Python source modules
│ ├── config.py # Configuration constants and paths
│ ├── ingestion.py # OSF data download and parsing
│ ├── bootstrap_engine.py # Resampling and stability analysis
│ ├── meta_analysis.py # Aggregation and visualization
│ └── main.py # Orchestration script
├── data/
│ ├── raw/ # Downloaded raw study data
│ └── processed/ # Cleaned and analyzed data
├── outputs/
│ ├── figures/ # Generated plots (forest plots, histograms)
│ └── reports/ # Final summary reports (PDF)
├── tests/ # Unit and integration tests
└── specs/ # Project specifications and design docs
```

## Setup
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Ensure you have an OSF API token configured (via environment variable `OSF_API_TOKEN` or in `code/config.py`).

## Usage
Run the full pipeline:
```bash
python code/main.py
```

## Requirements
- Python 3.9+
- OSF API Access
- 6GB+ RAM (recommended for bootstrap iterations)
- < 6 hours runtime (adaptive iteration reduction enabled)
