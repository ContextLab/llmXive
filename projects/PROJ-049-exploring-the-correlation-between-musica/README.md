# Exploring the Correlation Between Musical Preference and Personality Traits

## Overview
This project investigates the relationship between the Big Five personality traits (BFI-2) and musical preferences (Last.fm data). It implements a full data science pipeline: ingestion, preprocessing, statistical analysis, and visualization.

## Project Structure
```
.
├── code/ # Source code
│ ├── analysis.py # Statistical analysis & visualization
│ ├── ingest.py # Data ingestion & preprocessing
│ ├── mapping.py # Genre mapping logic
│ ├── synthetic_data.py # Synthetic data generator
│ ├── utils.py # Utilities (logging, config)
│ ├── pipeline.py # Main orchestration script
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Cleaned/merged data
├── results/ # Outputs (plots, reports)
├── logs/ # Execution logs
├── tests/ # Unit tests
└── README.md
```

## Prerequisites
- Python 3.8+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution
Run the full pipeline:
```bash
python code/pipeline.py
```

This script will:
1. Setup directory structure.
2. Attempt to download real data (BFI-2, Last.fm).
3. If real data download fails (timeout/404), it automatically falls back to **synthetic data** generation with a fixed seed for reproducibility.
4. Clean, merge, and standardize data.
5. Compute correlations and run regressions.
6. Generate visualizations and reports.

## Synthetic Data Explanation
If real external data sources are unavailable, the pipeline uses `code/synthetic_data.py` to generate a deterministic dataset. This ensures the pipeline can be tested and demonstrated without network dependencies. The synthetic data mimics the structure of BFI-2 and Last.fm datasets (user IDs, personality scores, genre tags, listening minutes) using a fixed random seed (`RANDOM_SEED=42` by default).

## Output Files
- `data/processed/merged_data.csv`: Cleaned, merged dataset.
- `data/processed/analysis_results.csv`: Statistical results.
- `results/correlation_heatmap.png`: Visual correlation map.
- `results/results_report.csv`: Detailed report with effect sizes.

## License
MIT
