# Quickstart: llmXive follow-up: extending "SynthDocBench" with Decoupled Retrieval

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (free-tier) or local machine with ≥7 GB RAM.
- `tesseract-ocr` installed on the system (for OCR).
- `poppler-utils` installed (for PDF handling if needed).
- `reportlab` (for synthetic document generation).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-1071-llmxive-follow-up-extending-synthdocbenc
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

3. **Install system dependencies** (if not already present).
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr poppler-utils
   ```

## Running the Pipeline

### Step 1: Generate Synthetic Documents

Run the document generator to create a set of synthetic long documents locally.
```bash
python code/doc_generator.py --count 200 --output data/raw/generated_docs.parquet
```
*This creates the dataset with precise "middle-third" metadata. No external download is performed.*

### Step 2: Execute Baseline Evaluation

Run the baseline evaluation (static image) for the selected models.
```bash
python code/baseline_eval.py --models "model1,model2,model3" --limit 50
```
*`--limit` restricts the number of documents to process (for testing). Remove for full run.*

### Step 3: Execute Retrieval-Augmented Evaluation

Run the retrieval-augmented pipeline.
```bash
python code/retrieval_eval.py --models "model1,model2,model3" --limit 50
```

### Step 4: Statistical Analysis & Latency Reporting

Compute the accuracy deltas, Spearman correlation, and **p95 retrieval latency**.
```bash
python code/stats_analysis.py
```
*Output will be saved to `data/derived/statistical_results.json` and includes `p95_retrieval_latency_ms`.*

## Verification

- Check `data/derived/statistical_results.json` for the correlation coefficient, p-value, and **p95 retrieval latency**.
- Verify that `accuracy_delta` is positive for "middle-third" questions if the hypothesis holds.
- Ensure `sample_size_used` and `runtime_hours` are reported to confirm feasibility within the established temporal constraints.
- Verify that the `state/` YAML file has been updated with content hashes.

## Troubleshooting

- **Memory Error**: Reduce the `--limit` parameter or use a smaller model.
- **OCR Failure**: Ensure `tesseract-ocr` is installed and accessible in the PATH.
- **Token Overflow**: The pipeline automatically truncates retrieved text. Check logs for truncation warnings.
- **Runtime Exceeded**: If the runtime exceeds a reasonable threshold, the pipeline will stop and report the feasible sample size achieved.