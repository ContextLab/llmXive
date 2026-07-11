# Quickstart: llmXive follow-up: extending "Code as Agent Harness"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)
- Sufficient Disk Space (for dataset and intermediate files)
- Sufficient RAM (recommended for smooth operation)

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-953-llmxive-follow-up-extending-code-as-agen/code/
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Authenticate with HuggingFace** (if required for specific datasets).
   ```bash
   huggingface-cli login
   ```

## Running the Pipeline

The pipeline is orchestrated via `main.py`.

### Step 0: Pilot & Base-Rate Estimation
Run a small subset to estimate failure rates before full processing.
```bash
python scripts/ingest.py --sample-size 100 --mode pilot
```
*Output*: `data/processed/pilot_stats.json` (contains base failure rate)

### Step 1: Ingest and Generate Ground Truth
Download datasets and run the dynamic execution baseline (if pilot passes).
```bash
python scripts/ingest.py --sample-size 500 --timeout 600
```
*Output*: `data/processed/ground_truth.csv`

### Step 2: Extract Structural Features
Parse code and calculate metrics.
```bash
python scripts/extract_features.py --input data/processed/ground_truth.csv
```
*Output*: `data/processed/features.csv`, `data/graphs/`

### Step 3: Train and Evaluate Model
Train the model and perform sensitivity analysis.
```bash
python scripts/train_model.py --input data/processed/features.csv --thresholds 0.01,0.05,0.1
```
*Output*: `models/model.pkl`, `data/processed/model_results.csv`

### Step 4: Generate Report
Automatically generate the research summary.
```bash
python scripts/evaluate.py --model models/model.pkl --results data/processed/model_results.csv
```
*Output*: `reports/summary.md`

### Step 5: Update State
Update the project state file (Constitution Principle V).
```bash
python scripts/update_state.py --status research_complete
```

## Validation

Run the test suite to ensure contract compliance:
```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: Reduce `--sample-size` in `ingest.py`.
- **Timeout**: Increase `--timeout` or reduce the complexity of the sample set.
- **Parse Error**: Check `data/processed/ground_truth.csv` for `is_unparseable=True` rows.
- **Pilot Failure**: If `pilot_stats.json` shows a failure rate < 0.5%, the pipeline will skip full modeling and report the statistical limitation.