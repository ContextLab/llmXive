# Quickstart: Investigating the Impact of Code Ownership on LLM Code Understanding

## Prerequisites

- Python 3.11+
- Git installed and in PATH
- Sufficient available RAM (local or CI)
- Internet access (for model and dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-441-investigating-the-impact-of-code-ownersh
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only version and `bitsandbytes` for 4-bit quantization on CPU.*

## Running the Pipeline

### 0. Pre-flight Validation
```bash
python code/main.py --task validate-citations --checksum-data
```
*Output: Validation report, checksums recorded in `state/...yaml`.*

### 1. Extract Ownership Metrics (with Temporal Alignment)
```bash
python code/main.py --task extract-ownership --repos data/repos.txt --dataset code_x_glue_ct_code_to_text
```
*Output: `data/processed/ownership_metrics.json` (includes `target_commit_sha`).*

### 2. Calculate Complexity
```bash
python code/main.py --task calculate-complexity --input data/processed/ownership_metrics.json
```
*Output: `data/processed/code_snippets.json`.*

### 3. Run LLM Inference (StarCoder2-3B 4-bit CPU)
```bash
python code/main.py --task run-inference --input data/processed/code_snippets.json --model bigcode/starcoder2-3b --quantization 4bit
```
*Output: `data/results/performance_scores.json`.*
*Note: Includes automatic model unloading and fallback to fewer snippets if time/memory constrained.*

### 4. Statistical Analysis
```bash
python code/main.py --task regression --input data/results/performance_scores.json
```
*Output: `data/results/regression_summary.csv`, `data/results/sensitivity_report.csv`.*

## Verification

- Check `data/results/regression_summary.csv` for p-values and VIF scores.
- Verify `data/results/sensitivity_report.csv` for stability across window sizes {100, 500}.
- Ensure no `OOM` errors in logs.
- Confirm `state/...yaml` contains checksums for raw data.