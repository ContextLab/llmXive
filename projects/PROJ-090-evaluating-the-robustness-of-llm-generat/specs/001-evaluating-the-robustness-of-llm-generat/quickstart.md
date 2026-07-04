# Quickstart: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

## Prerequisites

*   Python 3.11+
*   7 GB+ RAM available
*   Git
*   Access to HuggingFace Hub (no token required for public datasets)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `bitsandbytes` to a CPU-compatible version and `transformers`.*

## Running the Pipeline

The pipeline is executed via `code/main.py`.

### 1. Download Data
```bash
python code/data/download_humaneval.py
```
This downloads the HumanEval dataset to `data/raw/humaneval.parquet`.

### 2. Generate Perturbations
```bash
python code/data/generate_perturbations.py
```
Generates perturbed prompts, calculates similarity scores, and saves:
*   `data/processed/prompt_variants.jsonl` (all candidates)
*   `data/processed/primary_variants.jsonl` (filtered > 0.95, with fallback logic)

### 3. Run Inference & Execution
```bash
python code/model/inference.py
```
*   Loads StarCoder2-3B (4-bit quantized).
*   Runs generation with 30s timeout, fixed seed (42), and temperature=0.
*   Executes code in sandbox with 10s timeout.
*   Outputs: `data/results/execution_log.jsonl`.

### 4. Statistical Analysis
```bash
python code/analysis/statistics.py
```
*   Computes pass@1 rates.
*   Runs McNemar's test with Bonferroni correction (with power contingency).
*   Runs Mixed-Effects Logistic Regression.
*   Performs sensitivity analysis.
*   Outputs: `data/results/analysis_report.csv` and `data/results/figures/`.

### 5. Error Classification
```bash
python code/analysis/error_classifier.py
```
*   Samples failures.
*   Classifies into syntax/logic/hallucination.
*   Outputs: `data/results/error_classification.csv`.

## Verification

To verify the setup without running the full heavy inference:
```bash
pytest tests/unit/
```
This tests the perturbation logic, sandbox timeout handling, and **contract schema validation**.

## Troubleshooting

*   **OOM Errors**: If you encounter OOM, ensure no other heavy processes are running. The model is 4-bit quantized; if issues persist, reduce the batch size in `code/model/inference.py`.
*   **Timeouts**: If the 30s generation limit is too strict for your hardware, increase `GEN_TIMEOUT` in `config.py`, but be aware of the 6-hour CI limit.
*   **Network**: Ensure HuggingFace Hub is accessible.