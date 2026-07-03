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
   This creates `data/processed/corpus.csv` with ≥200 valid Python/JS pairs.

## Running the Experiments

1. Execute the inference pipeline:
   ```bash
   python src/execution/run_inference.py
   ```
   This generates `data/evaluation/raw_outputs/` with results for all four conditions.

2. Run the evaluation pipeline:
   ```bash
   python src/evaluation/translate_tests.py
   python src/evaluation/run_node_tests.py
   python src/evaluation/compute_quality.py
   python src/evaluation/statistical_analysis.py
   ```
   This produces `data/evaluation/results.csv` with pass/fail status, complexity, and statistical summaries.

## Viewing Results

- **Raw Outputs**: `data/evaluation/raw_outputs/`
- **Processed Results**: `data/evaluation/results.csv`
- **Statistical Summary**: `data/evaluation/statistical_summary.csv`

## Troubleshooting

- **API Rate Limit**: The script automatically retries with exponential backoff. If it fails after a limited number of retries, the snippet is marked as failed.
- **Memory Error**: The ingestion script processes data in chunks. If memory is still exceeded, reduce the sample size in `preprocess_corpus.py`.
- **Test Timeout**: Node.js tests are limited to a fixed timeout duration. Infinite loops will be caught and logged as failures.
