# Quickstart: Evaluating the Impact of Code Generation Models on Code Testability

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for dataset and models)
- (Optional) Kaggle account for GPU offloading

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/294-evaluating-code-testability
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Authenticate with HuggingFace** (if required for models):
   ```bash
   huggingface-cli login
   ```

## Run the Pipeline

Execute the main pipeline:

```bash
python code/main.py
```

This will:
1. Download HumanEval.
2. Generate code samples.
3. Calculate metrics.
4. Run statistical tests.
5. Generate a Markdown report.

## Verify Results

Check the generated artifacts:

```bash
# View metrics
cat data/analysis/metrics.json

# View statistical results
cat data/analysis/results.yaml

# View validation report
cat state/validation_report.yaml
```

## Troubleshooting

- **GPU Memory Error**: The pipeline will automatically attempt to offload to Kaggle GPU if local inference fails. Ensure `KAGGLE_USERNAME` and `KAGGLE_KEY` are set.
- **Citation Validation Failure**: Check `state/validation_report.yaml` for missing or mismatched citations.
