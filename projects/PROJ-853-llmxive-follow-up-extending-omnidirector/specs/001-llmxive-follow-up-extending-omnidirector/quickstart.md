# Quickstart: llmXive follow-up: extending "OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired D"

## Prerequisites

- Python 3.11+
- Git
- ~14 GB free disk space (for dataset and intermediate files)
- ~8 GB RAM (recommended for smooth processing)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
cd projects/PROJ-853-llmxive-follow-up-extending-omnidirector
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## 2. Data Preparation

Place the OmniDirector dataset (or the provided subset) in `data/raw/`.
If no dataset is available, the system will attempt to load a synthetic control set for testing.

```bash
# Verify data presence
ls data/raw/
```

## 3. Run the Pipeline

Execute the full pipeline (Ingestion $\to$ Solve $\to$ Analyze):

```bash
python code/main.py --run-all
```

### Step-by-Step Execution

1. **Ingest & Filter**:
   ```bash
   python code/main.py --step ingest
   ```
   *Output*: `data/processed/filtered_sequences.csv`

2. **Geometric Solver**:
   ```bash
   python code/main.py --step solve
   ```
   *Output*: `data/processed/poses_estimated.json`

3. **Statistical Analysis**:
   ```bash
   python code/main.py --step analyze
   ```
   *Output*: `data/processed/reconstruction_results.csv`, `data/processed/validation_report.json`

## 4. Verify Results

Check the validation report for key metrics:

```bash
cat data/processed/validation_report.json
```

Expected output includes:
- `pearson_correlation`: Value between -1 and 1.
- `mean_reconstruction_error`: Absolute difference in meters.
- `aspect_ratio_validated`: Boolean (True if within $\pm 5\%$).

## 5. Unit Testing

Run the test suite to ensure solver correctness:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: Reduce the batch size in `config.py` or process fewer sequences.
- **No Grid Lines Detected**: Ensure images are not corrupted; check `config.py` for Canny threshold parameters.
- **Solver Fails**: Verify camera intrinsics in the metadata; incorrect focal length causes `solvePnP` divergence.
