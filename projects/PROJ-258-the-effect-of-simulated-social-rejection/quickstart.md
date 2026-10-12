# Quickstart: Social Rejection Analysis Pipeline

## Prerequisites

* Python 3.11+
* Git
* Access to GitHub Actions (or local runner with 7 GB RAM).

## Installation

1. **Clone the Repository**:
```bash
git clone <repo_url>
cd projects/PROJ-258-the-effect-of-simulated-social-rejection
```

2. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Ingest Data
Download and validate the datasets from OpenNeuro.
```bash
python code/ingest.py --dataset-ids ds000208 ds003392 --output-dir data/raw
```
* **Expected Output**: Datasets downloaded to `data/raw/ds000208/` and `data/raw/ds003392/`, and a manifest at `data/raw/dataset_manifest.json`.
* **Failure**: Exits with code 1 if API is unreachable, size > 7 GB, or downloads fail.

### Step 2: Preprocess
Clean data and extract features.
```bash
python code/preprocess.py --input data/raw --output data/processed/analysis_ready.csv
```
* **Expected Output**: `data/processed/analysis_ready.csv` (cleaned, outliers flagged).

### Step 3: Analyze
Run statistical tests.
```bash
python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json
```
* **Expected Output**: `results/analysis_output.json` (ANOVA results, FDR, sensitivity).

### Step 4: Generate Report
Create the final report.
```bash
python code/report.py --input results/analysis_output.json --output paper/report.md
```
* **Expected Output**: `paper/report.md` (contains "associational" in Limitations, no "causal" in Results).

## Testing

Run the test suite to verify the pipeline:
```bash
pytest tests/
```

## Troubleshooting

* **Error: Missing Variables**: Ensure the dataset contains `participant_id`, `condition`, `reaction_time`, and `mood_rating`.
* **Error: Memory Overflow**: Check dataset size. If > 7 GB, the pipeline should have halted at ingestion.
* **Error: Missing Conditions**: If the dataset lacks 'Rejection' or 'Control' conditions, the pipeline halts as per FR-001.