# Quickstart: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for model weights, if required)
- GitHub Actions account (for CI execution)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Generate Misleading Contexts

Run the generation script on a sample of the `medqa` dataset.
```bash
python scripts/generate_mislead.py --dataset medqa --sample-size 50 --output data/processed/mislead_questions.jsonl
```
*Note: This step requires the `medqa` dataset to be available. If the dataset ID is not found, ensure you have the `datasets` library and internet access.*

### 2. Run Inference

Execute the inference pipeline.
```bash
python scripts/run_inference.py \
  --input data/processed/mislead_questions.jsonl \
  --models Llama-2-7B,Llama-2-13B \
  --strategies Baseline,CoT,Self-Critique \
  --output data/processed/inference_results.jsonl
```
*Note: On GitHub Actions free-tier, Llama-2-70B will be automatically skipped if GPU is not detected.*

### 3. Analyze Resilience

Calculate metrics and statistical significance.
```bash
python scripts/analyze_resilience.py \
  --input data/processed/inference_results.jsonl \
  --output data/analysis/resilience_metrics.json \
  --report data/analysis/report.md
```

## Testing

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/ -v
```

Run unit tests:
```bash
pytest tests/unit/ -v
```

## Troubleshooting

- **OOM Error**: If you encounter "Out of Memory" on the 70B model, the script should automatically skip it. If not, check the `--models` flag to exclude it manually.
- **Dataset Not Found**: Ensure the `datasets` library is up to date: `pip install --upgrade datasets`.
- **Invalid Output**: If the model outputs invalid answers, check the `extracted_answer` logic in `scripts/run_inference.py`.
