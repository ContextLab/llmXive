# Quickstart: 001-social-rejection-reward

## Prerequisites

* Python 3.11+
* Git
* Access to GitHub Actions (or local runner with 7 GB RAM).

## Installation

1. **Clone the Repository**:
 ```bash
 git clone
 cd projects/PROJ-258-the-effect-of-simulated-social-rejection
 ```

2. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Step 1: Ingest Data
Download and validate the dataset (ds000208).
```bash
python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw
```
* **Expected Output**: `data/raw/cyberball.parquet` and `state/projects/PROJ-258...yaml` (updated with checksum).
* **Failure**: Exits with code 1 if variables are missing, size > 7 GB, or conditions (Rejection/Control) are missing.

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
* **Error: Missing Conditions**: If the dataset lacks 'Rejection' or 'Control' conditions, the pipeline halts as per FR-001. This is expected behavior.
