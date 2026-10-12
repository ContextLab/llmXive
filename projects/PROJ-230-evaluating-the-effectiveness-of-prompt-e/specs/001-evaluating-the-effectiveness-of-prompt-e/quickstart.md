# Quickstart: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

## Prerequisites

- Python 3.11+
- Node.js 18+
- HuggingFace API token (set as `HF_API_TOKEN` environment variable)
- Git

## Installation

1. Clone the repository and navigate to the project directory.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Node.js dependencies (for ESLint):
   ```bash
   npm install -g eslint eslint-plugin-complexity
   ```

## Data Preparation

1. Download and preprocess the dataset:
   ```bash
   python src/ingestion/download_datasets.py
   python src/ingestion/preprocess_corpus.py
   ```
   This creates `data/processed/corpus.csv` with ≥100 valid Python/JS pairs conforming to `dataset.schema.yaml`.

## Running the Experiments

1. Execute the inference pipeline:
   ```bash
   python src/execution/run_inference.py
   ```
   This generates `data/evaluation/raw_outputs/` with results for all four conditions. Metadata is logged in `data/evaluation/raw_outputs/metadata.csv`.

2. Run the evaluation pipeline:
   ```bash
   python src/evaluation/extract_io_pairs.py
   python src/evaluation/run_js_validation.py
   python src/evaluation/compute_quality.py
   python src/evaluation/statistical_analysis.py
   ```
   This produces:
   - `data/evaluation/io_pairs.csv`: Ground-truth I/O pairs extracted from Python code (with extraction_status column).
   - `data/evaluation/validation_results.csv`: Pass/fail status for each snippet-condition pair, conforming to `translation_result.schema.yaml`.
   - `data/evaluation/quality_metrics.csv`: Cyclomatic complexity and lines of code for each translation.
   - `data/evaluation/statistical_summary.csv`: Statistical results (p-values, confidence intervals, observed power, effect sizes) conforming to `statistical_summary.schema.yaml`.

## Viewing Results

- **Raw Outputs**: `data/evaluation/raw_outputs/`
- **I/O Pairs**: `data/evaluation/io_pairs.csv` (ground-truth from Python execution with fixed synthetic inputs)
- **Validation Results**: `data/evaluation/validation_results.csv` (JS validation against I/O pairs)
- **Quality Metrics**: `data/evaluation/quality_metrics.csv`
- **Statistical Summary**: `data/evaluation/statistical_summary.csv` (includes observed power and confounder analysis)

## Troubleshooting

- **API Rate Limit**: The script automatically retries with exponential backoff. If wall-clock time exceeds 5.5 hours at the [deferred] checkpoint, the script falls back to N=50 sample or local Ollama model.
- **Memory Error**: The ingestion script processes data in chunks. If memory is still exceeded, reduce the sample size in `preprocess_corpus.py`.
- **Test Timeout**: Node.js tests are subject to a fixed timeout limit (10 seconds). Infinite loops will be caught and logged as failures.
- **Python Execution Failure**: If a snippet's Python code fails to execute, it is excluded from the correctness analysis. Exclusion independence is verified via chi-square contingency test.
- **Fallback Model Non-equivalence**: If Ollama 7B fallback is used and equivalence check (N=10 subset) shows metrics differ by >10%, Ollama outputs are excluded from the main analysis.