# Quickstart Guide: Evaluating LLMs for Code Smell Detection

This guide provides step-by-step instructions to set up the environment, run the full pipeline, and verify the results for **PROJ-271**.

## Prerequisites

- Python 3.11+
- pip
- At least 16GB RAM (recommended for LLM inference)
- Internet connection (for downloading datasets and models)

## 1. Environment Setup

### Clone and Install Dependencies

```bash
# Navigate to the project root
cd PROJ-271-evaluating-the-effectiveness-of-llms-for

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

Ensure `radon`, `pandas`, `datasets`, `sentence-transformers`, and `llama-cpp-python` are installed:

```bash
python -c "import radon, pandas, datasets, sentence_transformers, llama_cpp; print('Dependencies OK')"
```

## 2. Project Initialization

Run the setup script to create the required directory structure and configuration files:

```bash
python code/setup_directories.py
```

This creates:
- `data/raw/`, `data/processed/`
- `results/`
- `tests/`

## 3. Run the Data Pipeline (User Story 1)

This step ingests a sample of code from HuggingFace, computes structural metrics, and generates static smell labels.

```bash
python code/data_pipeline.py
```

**Output**:
- `data/static_baseline.csv` (contains code, LOC, complexity, and static labels)
- Logs in `results/`

**Note**: This step may take a few hours depending on the sample size. The script automatically adjusts the sample size to fit within a 5.5-hour window.

## 4. Run Semantic Analysis (User Story 2)

This step computes embeddings and runs the LLM (CodeLlama-7B-GGUF) to generate semantic smell labels.

```bash
python code/semantic_analysis.py
```

**Output**:
- `data/processed/semantic_results.json` (contains embeddings and LLM labels)
- Resource metrics in `results/resource_metrics.json`

**Note**: Ensure you have sufficient RAM (≥16GB) for the 4-bit quantized model.

## 5. Run Statistical Analysis (User Story 3)

This step correlates static and semantic results, performs McNemar's test, logistic regression, and sensitivity analysis.

```bash
python code/statistical_analysis.py
```

**Output**:
- `results/statistical_significance.json`
- `results/logistic_regression.json`
- `results/sensitivity_report.md`

## 6. Validate End-to-End Reproducibility

Run the validation script to ensure all artifacts are present and correctly formatted:

```bash
python code/run_quickstart_validation.py
```

**Expected Output**:
- A summary of checks passed/failed.
- Exit code `0` if all checks pass.

## 7. (Optional) Run Unit Tests

```bash
pytest tests/unit/ -v
```

## Troubleshooting

- **OOM Errors**: If you run out of memory during LLM inference, reduce the batch size in `code/config.py` or use a smaller sample size.
- **Dataset Download Fails**: Ensure your internet connection is stable. The script uses streaming for large datasets.
- **Pylint Errors**: If `radon` or `pylint` fail on specific files, they are logged and skipped. Check `results/error_log.txt` for details.

## Next Steps

- Review `results/sensitivity_report.md` for insights on false positives/negatives.
- Analyze `results/logistic_regression.json` for feature importance.
- Contribute improvements or report issues on the project repository.
