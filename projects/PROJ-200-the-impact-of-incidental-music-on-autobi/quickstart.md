# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites
- Python 3.11+
- `pip`

## Installation
1. **Clone the repository** and enter the project root.
2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
3. **Initialize Project Layout**:
 ```bash
 python code/setup_project.py
 ```

## Running the Pipeline
The pipeline is orchestrated via `code/main.py`.

### 1. Download Data
Fetch the MSD track metadata and generate simulated AMT data.
```bash
python code/main.py --step download
```

### 2. Ingest & Aggregate
Parse data, match cues, calculate exposure ratios, and filter.
```bash
python code/main.py --step ingest
```

### 3. Run Analysis
Fit the LMM, run sensitivity analysis, and perform permutation tests.
```bash
python code/main.py --step analyze
```

### 4. Update State
Verify checksums and update `state.yaml`.
```bash
python code/main.py --step verify
```

## Full Run (Single Command)
To run the entire pipeline from scratch:
```bash
python code/main.py --full-run
```

## Expected Outputs

- `data/processed/user_track_pairs.parquet`: Core analysis dataset.
- `data/final/regression_summary.csv`: Model coefficients and statistics.
- `data/final/plots/`: Diagnostic plots.
- `state.yaml`: Updated with artifact hashes.
