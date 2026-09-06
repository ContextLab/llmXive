# Quickstart: Function-Aware FIM for Non-Code Domains

## Prerequisites

-   Python 3.11+
-   Access to a GitHub Actions runner (or local machine with ≥7GB RAM).
-   HuggingFace CLI access (for dataset downloads).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `torch` is installed with CPU support (no CUDA).*

## Running the Pipeline

The pipeline consists of three main stages: Data Construction, Training, and Evaluation.

### 1. Construct Synthetic Dataset

Run the conversion script to transform GSM8K into pseudo-code functions.

```bash
python code/data/convert_to_pseudo_code.py \
    --dataset openai/gsm8k \
    --output data/processed/synthetic_logical_dataset.jsonl \
    --validate-deps
```

*This step validates the dependency graph and excludes cyclic examples.*

### 2. Mid-Training (CPU Only)

Run the FIM training script. This will train the TinyLlama model for one epoch.

```bash
python code/training/train_fim.py \
    --model tinyllama-110m \
    --data data/processed/synthetic_logical_dataset.jsonl \
    --output-dir data/artifacts/fim_model \
    --batch-size 16 \
    --device cpu \
    --epochs 1
```

*To run the Natural Language Control, use `code/training/train_nl_control.py` with the same arguments but the plain-text dataset.*

### 3. Evaluate on LogiQA

Evaluate the trained models against the LogiQA benchmark.

```bash
python code/evaluation/eval_logiqa.py \
    --model data/artifacts/fim_model \
    --dataset logiqa \
    --output data/artifacts/results/fim_results.json
```

### 4. Statistical Analysis

Run the statistical comparison.

```bash
python code/evaluation/statistical_analysis.py \
    --results data/artifacts/results/ \
    --output data/artifacts/results/statistical_report.json
```

## Verification

-   **Check Masking**: Inspect `data/artifacts/masking_map.json` to ensure function bodies are targeted.
-   **Check Memory**: Monitor RAM usage; it should stay under 7GB.
-   **Check Significance**: Verify `statistical_report.json` contains `is_significant: true/false` and the p-value.

## Troubleshooting

-   **OOM Error**: Reduce `--batch-size` in the training command.
-   **Cycle Detected**: The conversion script will skip problematic examples. Check logs for `VAR-001` warnings.
-   **CUDA Error**: Ensure `device="cpu"` is explicitly set; the script should fail if it tries to access CUDA.
