# Quickstart: llmXive follow-up: extending "AI for Auto-Research: Roadmap & User Guide"

## 1. Prerequisites

- Python 3.11+
- `git`
- Access to the "AI for Auto-Research" benchmark dataset (see `research.md` for dataset strategy) OR permission to use synthetic data.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-836-llmxive-follow-up-extending-ai-for-auto

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Data Setup

1. **Download the dataset**:
   - Place the raw dataset file in `data/raw/`.
   - Ensure the file is named `benchmark_raw.csv` (or as specified in the dataset documentation).
   - Run the checksum script:
     ```bash
     python code/data_ingestion.py --download
     ```
   - Verify the checksum in `data/checksums.json`.
   - **Note**: If the dataset is not found, the script will automatically generate synthetic data.

2. **(Optional) Use a sample**:
   - If the full dataset is too large, run with a sample:
     ```bash
     python code/data_ingestion.py --sample-size 1000
     ```

## 4. Running the Pipeline

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1. Download/verify data (or generate synthetic data).
2. Construct graphs and extract metrics.
3. Train the model and run cross-validation.
4. Perform the permutation test (min 1,000 iterations).
5. Generate reports in `output/`.

## 5. Testing

Run unit tests:

```bash
pytest tests/unit/
```

Run integration tests:

```bash
pytest tests/integration/
```

## 6. Output

- **Reports**: `output/report.pdf` (or `.md`) containing AUC, p-values, and feature importance.
- **Artifacts**: `data/processed/` contains the feature matrix and model artifacts.
- **Logs**: `logs/pipeline.log` contains warnings (e.g., empty graphs, missing labels, synthetic data generation).

## 7. Troubleshooting

- **Memory Error**: Reduce `--sample-size` or enable streaming in `data_ingestion.py`.
- **Dataset Not Found**: The pipeline will automatically switch to synthetic data generation.
- **Graph Construction Failures**: Check `logs/pipeline.log` for parsing errors.
- **PII Scan Failed**: Ensure no PII is present in the input data.