# Quickstart: Investigating the Impact of Code Complexity on LLM Code Understanding

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with 7GB+ RAM).

## 1. Clone and Setup

```bash
git clone <repo-url>
cd projects/PROJ-481-investigating-the-impact-of-code-complex
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## 2. Download Data

Run the data download script (fetches from verified URLs):

```bash
python code/00_download_data.py
```
*Note: This script verifies checksums and stores data in `data/raw/`.*

## 3. Compute Complexity Metrics

Process the code to generate static metrics:

```bash
python code/01_compute_metrics.py
```
*Output: `data/derived/metrics.csv`*

## 4. Run LLM Inference

Execute the inference pipeline (CPU-optimized). This may take several hours.

```bash
# Optional: Set a smaller sample size for testing
export SAMPLE_SIZE=100
python code/02_run_inference.py
```
*Output: `data/derived/inference_results.csv`*

## 5. Analyze and Visualize

Run the statistical analysis (includes data merge), generate plots, and detect thresholds:

```bash
python code/03_analyze_results.py
```
*Output: `results/plots/`, `results/report.md`*

## 6. Verify Results

Run the test suite to ensure data integrity:

```bash
pytest code/tests/
```

## Troubleshooting

- **Memory Error**: Reduce `SAMPLE_SIZE` in the environment variable or use a smaller model (e.g., `starcoder-1b`).
- **Timeout**: Increase the timeout threshold in `code/utils/inference.py` or reduce batch size.
- **Parse Errors**: Check `data/derived/errors.csv` for code snippets that failed static analysis.