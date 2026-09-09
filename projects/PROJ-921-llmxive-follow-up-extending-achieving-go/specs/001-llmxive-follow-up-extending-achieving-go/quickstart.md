# Quickstart: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient RAM (Sufficient memory is recommended for safety.)
-   Internet access (for dataset download)

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to the CPU-only version and `transformers` to a stable release.*

## Running the Pipeline

The pipeline is executed via a single entry point script.

### 1. Data Download & Validation
```bash
python code/data/download.py
```
This script downloads datasets from verified URLs, computes checksums, and formats them into `data/processed/unified_prompts.jsonl` (converting ScienceQA MCQs to open-ended prompts).

### 2. Inference (CPU-Only)
```bash
python code/inference/runner.py --model su01 --dataset opensci --n_samples: a sufficiently large number to ensure statistical power.
python code/inference/runner.py --model baseline --dataset opensci --n_samples 500
```
*Note: The SU-01 model weights must be available locally or via HuggingFace. If the model is not found, the script will exit with an error.*

### 3. Scoring
```bash
python code/scoring/proxy_model.py --input data/processed/su01_responses.jsonl --output data/processed/su01_scores.jsonl
python code/scoring/proxy_model.py --input data/processed/baseline_responses.jsonl --output data/processed/baseline_scores.jsonl
```
*This step uses the INT quantized Llama-3-8B model. It may take significant time on CPU.*

### 4. Analysis
```bash
python code/analysis/stats.py
```
This generates the final statistical report, including the Linear Mixed Effects (LME) model results, dimension independence metrics, and power analysis.

## Verification

To verify the proxy model:
```bash
python code/scoring/validator.py
```
This checks the correlation between proxy scores and the `gold_standard` set.

## Troubleshooting

-   **OOM Error**: Ensure `load_in_4bit=True` is set in `proxy_model.py`. If still failing, reduce `batch_size` to 1 (default).
-   **Timeout**: If the job exceeds a prolonged duration, check the `truncation_log.jsonl` for excessive token usage.
-   **Model Not Found**: Ensure `SU-01` weights are present in the expected HuggingFace cache or local path.


## projects/PROJ-921-llmxive-follow-up-extending-achieving-go/specs/001-llmxive-follow-up-extending-achieving-go/contracts/output_schema.schema.yaml