# Quickstart: GateMem Gatekeeper Extension

## 1. Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (free-tier) or a local machine with similar specs (2 CPU, 7 GB RAM).

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc
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
   *Note: Ensure `torch` is installed without CUDA support (e.g., `pip install torch --index-url https://download.pytorch.org/whl/cpu`).*

## 3. Data Setup

1. **Download the dataset**:
   The script `code/data/loader.py` will automatically download the GateMem dataset from the verified URL.
   ```bash
   python code/data/loader.py --download
   ```
   This will place the raw data in `data/raw/` and compute checksums.

2. **Verify data integrity**:
   ```bash
   python code/data/loader.py --verify
   ```

## 4. Running the Pipeline

### 4.1 Full Evaluation
Run the entire pipeline (Gatekeeper execution, metric calculation, statistical analysis):
```bash
python code/main.py --mode full
```
This will:
- Load the dataset.
- Execute the gatekeeper pipeline for all queries.
- Calculate Access Control, Forgetting, and Utility scores.
- Perform statistical tests and generate reports.
- Output results to `data/processed/evaluation_results.csv`.

### 4.2 Sensitivity Analysis
Run the sensitivity analysis for the DistilBERT threshold:
```bash
python code/main.py --mode sensitivity --thresholds 0.85 0.90 0.95
```

### 4.3 Unit Tests
Run the test suite:
```bash
pytest tests/
```

## 5. Expected Outputs

- `data/processed/evaluation_results.csv`: Detailed results for each query.
- `data/processed/metrics_summary.json`: Aggregated metrics (Access Control, Forgetting, Utility).
- `data/processed/statistical_analysis.json`: P-values, effect sizes, and correction results.
- `data/logs/pipeline.log`: Execution logs including timing and memory usage.

## 6. Troubleshooting

- **OOM Error**: If you encounter "Out of Memory" errors, ensure you are using the CPU-only version of `torch` and that no GPU libraries are installed. Reduce the batch size in `code/gatekeeper/pipeline.py`.
- **Timeout**: If the pipeline exceeds 6 hours, check the `data/processed/pipeline.log` for the slowest step. Consider reducing the dataset size for testing (use `--sample-size` flag).
- **Data Mismatch**: If the checksum verification fails, re-run the download script and ensure the URL has not changed.

## 7. Next Steps

- Review the `research.md` for detailed methodology.
- Examine the `contracts/` for data schema validation.
- Contribute to the `paper/` directory with the generated results.
