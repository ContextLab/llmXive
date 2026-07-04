# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites

- **Python**: 3.11+
- **System Dependencies**: `git`, `make` (optional)
- **Hardware**: CPU-only environment (minimum 7GB RAM recommended for CodeLlama-7B quantization).
- **Accounts**: HuggingFace account (for model access if required, though public models are used).

## Installation

1.  **Clone the Repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-294-evaluating-the-impact-of-code-generation
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure reproducibility.*

## Running the Pipeline

The pipeline is executed as a single script that orchestrates all phases: download, generation, analysis, testing, and reporting.

### Full Execution
```bash
python code/run_pipeline.py
```
**What this does**:
1.  Downloads HumanEval (validates SHA256).
2.  Generates code using `Salesforce/codegen-350M-mono` (retries 3x).
3.  (Optional) Generates code using `CodeLlama-7B` via API or fallback.
4.  Runs `radon` and `pytest --cov` on all samples.
5.  Performs statistical tests (Wilcoxon, McNemar).
6.  Generates `results/results_report.md`.

### Step-by-Step Execution (Debugging)
If you need to debug a specific stage:

1.  **Download Data**:
    ```bash
    python code/download_data.py
    ```
2.  **Generate Code**:
    ```bash
    python code/generate_code.py --model codegen-350M
    ```
3.  **Analyze Metrics**:
    ```bash
    python code/analyze_metrics.py
    ```
4.  **Run Tests**:
    ```bash
    python code/statistical_tests.py
    ```
5.  **Generate Report**:
    ```bash
    python code/report_generator.py
    ```

## Verification

To verify the pipeline ran correctly:

1.  **Check `data/analysis/metrics.json`**: Ensure it contains at least 40 valid paired entries.
2.  **Check `results/results_report.md`**: Open the file to view visualizations and statistical conclusions.
3.  **Check `state/artifact_hashes.yaml`**: Verify that SHA256 hashes are populated.

## Troubleshooting

- **Memory Error**: If you encounter OOM errors during CodeLlama-7B generation, the pipeline should automatically fall back to CodeLlama-3B. Check `errors.log` for details.
- **Missing HumanEval**: Ensure you have internet access and the HuggingFace URL is accessible.
- **Coverage Failures**: If `coverage.py` fails, check `errors.log` for specific Python syntax errors in generated code.
