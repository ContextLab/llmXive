# Investigating the Neural Correlates of Predictive Coding Errors (MMN)

This project implements an automated pipeline for analyzing EEG data from the OpenNeuro dataset `ds003645` (Auditory Oddball).
It focuses on extracting the Mismatch Negativity (MMN) component and performing statistical analysis.

## Project Structure

```
.
├── code/ # Source code for the pipeline
│ ├── preprocess.py # Data preprocessing (filtering, ICA, epoching)
│ ├── extract.py # Metric extraction (peak amplitude, latency)
│ ├── stats.py # Statistical analysis (t-tests, permutation tests)
│ ├── viz.py # Visualization (ERP plots, topomaps)
│ ├── config_loader.py # Configuration management
│ ├── download.py # Data acquisition from OpenNeuro
│ └──...
├── data/
│ ├── raw/ # Raw EEG data (downloaded)
│ └── processed/ # Cleaned epochs and intermediate artifacts
├── results/ # Final outputs (metrics, stats, plots)
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.11+
- OpenNeuro API Key (register at https://openneuro.org)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Set environment variables:
 ```bash
 export OPENNEURO_API_KEY="your_api_key_here"
 ```

## Usage

### 1. Download Data
```bash
python code/download.py
```
This fetches the dataset from OpenNeuro and verifies checksums.

### 2. Preprocess Data
```bash
python code/preprocess.py
```
Runs filtering, re-referencing, epoching, and ICA artifact removal.

### 3. Extract Metrics
```bash
python code/extract.py
```
Computes MMN amplitude and latency for each participant.

### 4. Statistical Analysis
```bash
python code/stats.py
```
Performs t-tests, FDR correction, and cluster-based permutation tests.

### 5. Visualization
```bash
python code/viz.py
```
Generates ERP plots and topographic maps.

## Performance Verification (Task T042)

To verify that the pipeline runs within the 2 CPU / 7 GB RAM / 6-hour constraint:
```bash
python code/performance_benchmark.py
```
This script measures memory and time for ICA and permutation steps and saves a report to `results/performance_benchmark.json`.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

## License

MIT License
