# Quickstart: Leveraging LLMs for Automated Code Refactoring

## Prerequisites

- Python 3.11+
- HuggingFace Account with API Token (for `bigcode/the-stack` and `WizardCoder` API).
- Git repository with the project structure.

## Setup

1.  **Clone and Install Dependencies**:
    ```bash
    cd projects/PROJ-043-leveraging-large-language-models-for-aut/code/
    pip install -r requirements.txt
    ```

2.  **Configure Environment**:
    Create a `.env` file in `code/` with your API token:
    ```bash
    export HF_API_TOKEN="your_huggingface_token_here"
    ```
    *(Note: The actual token should be passed via GitHub Secrets in CI, not committed.)*

3.  **Set Random Seeds**:
    The `config.py` file sets global random seeds for reproducibility. No manual intervention is required unless custom seeds are needed.

## Running the Pipeline

Execute the main pipeline script:

```bash
python main.py
```

### What Happens?

1.  **Data Acquisition**: Attempts to download up to 400 Python functions from the BigCode dataset. **Note**: If the dataset is inaccessible, the pipeline halts with an error (no silent fallback).
2.  **Static Analysis**: Computes LOC, nesting depth, parameters, PEP-8 score, and docstring presence.
3.  **Refactoring**: Sends valid functions to the WizardCoder API (with caching, retry logic, and **batching of ≤10 functions**).
4.  **Null Baseline**: Generates identity copies.
5.  **Metric Calculation**: Computes cyclomatic complexity, pylint scores, and warning counts for original, refactored, and baseline. Calculates `relative_improvement` metrics.
6.  **Schema Validation**: **Validates `data/processed/metrics.csv` against `contracts/output.schema.yaml`**. If validation fails, the pipeline halts.
7.  **Modeling**: Fits Ridge Regression models (for scores) and GLM (for counts) with robust standard errors and runs **one-sample t-tests** against zero.
8.  **Output**: Saves results to `data/processed/`.

## Verifying Results

Check the summary output:

```bash
cat data/processed/experiment_summary.json
```

Expected output fields: `valid_functions`, `refactor_success_rate`, `t_p_value`, `significance`.

## Testing

Run unit tests for metric calculation:

```bash
pytest tests/unit/
```

Run integration tests for the full pipeline (uses a small subset):

```bash
pytest tests/integration/
```

## Contract Validation

The pipeline automatically validates the final CSV output against `contracts/output.schema.yaml`. If validation fails, the pipeline halts and reports the error.