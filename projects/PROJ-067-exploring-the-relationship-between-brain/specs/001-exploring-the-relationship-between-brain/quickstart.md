# Quickstart: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

## Prerequisites

- Python 3.11+
- Git
- 14 GB free disk space
- Internet access (for downloading OpenNeuro data)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-067-exploring-the-relationship-between-brain
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Dataset Validation & Download
```bash
python code/main.py --stage validate_download --n-subjects 50
```
- **Action**: Downloads `ds000228` (or substitutes) and **validates** for "dream recall frequency".
- **Critical**: If the field is missing, the script halts with "Fatal Dataset Mismatch".
- **Memory Check**: The script monitors RAM usage and fails if >7GB.

### Step 2: Preprocess & Quality Control
```bash
python code/main.py --stage preprocess
```
- Runs ICA-AROMA, normalization, and **FD calculation**.
- Excludes subjects with FD > 0.5mm.
- Outputs: `data/processed/`.

### Step 3: Extract Metrics
```bash
python code/main.py --stage extract_metrics
```
- Computes sliding window correlations (30s window, 10s step) and Louvain clustering.
- Uses **Schaefer-100** atlas.
- Calculates Flexibility and **Mean Dwell Time** (Stability).
- Outputs: `data/metrics/subject_metrics.csv`.

### Step 4: Statistical Analysis
```bash
python code/main.py --stage statistical_analysis
```
- Runs Spearman correlation, FDR correction, and 1000-permutation test.
- Performs post-hoc power analysis (calculates MDE).
- Outputs: `results/stats.json` and `results/plots/`.

### Step 5: View Results
```bash
cat results/stats.json
```

## Testing

Run the test suite to verify contract compliance:
```bash
pytest tests/
```
- Contract tests validate output files against schemas in `contracts/`.

## Troubleshooting

- **Fatal Dataset Mismatch**: If "dream recall frequency" is missing, the dataset `ds000228` is invalid for this specific question. A pivot to a sleep-dream dataset is required.
- **Memory Error**: If the process fails with OOM, reduce `--n-subjects` to 20.
- **Runtime Error**: Ensure `nilearn` and `networkx` are installed correctly.