# Quickstart: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with sufficient RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-504-evaluating-the-impact-of-variable-select
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `code/config.py` to set:
- `RANDOM_SEED`: Fixed seed for reproducibility (default: 42).
- `SIMULATION_COUNT`: Number of sims per tuple (default: 200).
- `SNR_LEVELS`: List of SNR values (default: [0.5, 1.0, 2.0, 5.0]).
- `SPARSITY_LEVELS`: List of sparsity values (default: [0.1, 0.2, 0.4]).
- `ALPHA_THRESHOLDS`: List of alpha values (default: [0.01, 0.05, 0.10]).
- `MAX_PREDICTORS`: Max predictors for stepwise (default: 200).

## Running the Pipeline

### 1. Download Datasets
```bash
python code/downloader.py
```
This fetches a set of datasets from OpenML (IDs -1599) and stores them in `data/raw/`.

### 2. Run Simulations
```bash
python code/main.py --mode simulate
```
This generates synthetic outcomes, runs selection methods, and calculates power. Output saved to `data/processed/simulation_results.csv`.

### 3. Analyze Results
```bash
python code/main.py --mode analyze
```
This performs Kruskal-Wallis tests, Dunn's post-hoc, and generates plots. Output saved to `data/processed/power_metrics.csv` and `figures/`.

### 4. Generate Paper Draft
```bash
python code/main.py --mode paper
```
This generates a draft paper text based on the results.

## Verification

Run tests:
```bash
pytest tests/ -v
```

Check data integrity:
```bash
python code/verify.py --check-memory --check-runtime
```

## Troubleshooting

- **Memory Error**: Reduce `SIMULATION_COUNT` or process in smaller chunks.
- **OpenML Timeout**: Check network; increase retry limit in `config.py`.
- **Collinearity Warning**: Dataset skipped; check `logs/download.log`.
- **Runtime Exceeded**: Check `logs/runtime.log` for profiling data; reduce `SIMULATION_COUNT`.