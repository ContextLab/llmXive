# Quickstart: llmXive follow-up: extending "COLLEAGUE.SKILL"

## Prerequisites

- Python 3.11+
- Substantial RAM (for CPU inference)
- Sufficient free disk space to accommodate the dataset and intermediate processing artifacts.
- Git

## Installation

1. **Clone and Setup**:
   ```bash
   git checkout 001-llmxive-skill-separation
   cd code
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**:
   ```bash
   python -c "import torch; import transformers; import sympy; import z3; print('Dependencies OK')"
   ```

## Running the Pipeline

### Step 1: Generate Data
```bash
python -m data_generation.profiles --count 10 --output ../data/raw/profiles.jsonl
python -m data_generation.tasks --count 50 --output ../data/raw/tasks.jsonl
```
*This creates `data/raw/profiles.jsonl` and `data/raw/tasks.jsonl`.*

### Step 2: Run Inference
```bash
python -m inference.engine \
  --profiles ../data/raw/profiles.jsonl \
  --tasks ../data/raw/tasks.jsonl \
  --conditions monolithic,separated,generic \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --quantize 4-bit \
  --output-dir ../data/interim/outputs \
  --timeout 300
```
*This runs the inference tasks. Outputs are saved to `data/interim/outputs/`.*

### Step 3: Evaluate
```bash
python -m evaluation.metrics \
  --inputs ../data/interim/outputs/ \
  --profiles ../data/raw/profiles.jsonl \
  --tasks ../data/raw/tasks.jsonl \
  --external-truth ../data/raw/external_truth.jsonl \
  --output ../data/processed/metrics.csv
```
*This calculates Heuristic Adherence (AST/SymPy), Hallucination Rate (NLI/External), and Style Consistency (NLI/Classifier).*

### Step 4: Analyze
```bash
python -m analysis.stats \
  --data ../data/processed/metrics.csv \
  --output ../data/processed/results.json \
  --plot-dir ../data/processed/plots
```
*This fits the GLMM, applies Bonferroni correction, and generates plots.*

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration test (small subset):
```bash
pytest tests/integration/test_inference_pipeline.py -v
```

## Troubleshooting

- **OOM Error**: Reduce `--batch-size` in `inference.engine` or switch to `Phi-3-mini`.
- **Timeout**: Increase `--timeout` (not recommended for CI) or optimize task complexity.
- **Model Load Fail**: Ensure `llama-cpp-python` is installed and the model is downloaded.