# Quickstart: Evaluating the Impact of Code Complexity on LLM Code Understanding

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available (for local testing; CI will handle constraints).
- `bitsandbytes` installed (required for 4-bit quantization on CPU).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-154-evaluating-the-impact-of-code-complexity/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Environment**:
    Ensure `torch` and `bitsandbytes` are installed:
    ```bash
    python -c "import torch; import bitsandbytes; print('CPU' if not torch.cuda.is_available() else 'GPU')"
    ```

## Running the Pipeline

Execute the full pipeline via the orchestrator:

```bash
python main.py
```

### Step-by-Step Execution

1.  **Data Acquisition**:
    ```bash
    python data_acquisition.py --source "kejian/codesearchnet-python-raw-457k" --sample-size 10000
    ```
    *Downloads and samples CodeSearchNet (larger initial sample for stratification).*

2.  **Complexity Annotation**:
    ```bash
    python 02_complexity_annotation.py --input data/processed/sample.parquet --output data/processed/annotated_snippets.csv
    ```
    *Computes Radon metrics and records version in metadata.json.*

3.  **Inference (CPU Mode, 4-bit)**:
    ```bash
    python inference_script.py --model microsoft/Phi-3-mini-4k-instruct --quantization 4bit --batch-size 1 --max-runs 5000
    ```
    *Runs LLM Summarization tasks with memory guard.*

4.  **Analysis**:
    ```bash
    python 04_analysis.py --input results/inference_logs.jsonl --output results/analysis_metrics.csv
    ```
    *Generates correlations, GLM results, and VIF checks.*

## Validation

Check the generated files:
- `data/processed/annotated_snippets.csv`: Ensure no `NaN` in complexity columns.
- `data/processed/metadata.json`: Verify `radon` version is recorded.
- `results/analysis_metrics.csv`: Ensure p-values are present and VIF status is recorded.

## Troubleshooting

- **OOM Error**: Reduce `--sample-size` in step 1 or `--max-runs` in step 3.
- **Model Load Fail**: If `Phi-3-mini` fails, ensure `bitsandbytes` is installed and `load_in_4bit=True` is used.