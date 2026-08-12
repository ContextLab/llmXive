# Quickstart: Phenomenological AI: First-Person Experience Modeling in Language Models

## Prerequisites

- Python 3.11 or higher.
- Git.
- HuggingFace account (for model access).
- (Optional) Philosophy graduate students for qualitative validation.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd phenomenological-ai
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Authenticate with HuggingFace** (if needed):
 ```bash
 huggingface-cli login
 ```

## Running the Pipeline

### Step 1: Generate Reports

Run the generation script to create the phenomenological corpus.

```bash
python -m src.generation.runner --strategy all --samples 80 --model mistralai/Mistral-7B-Instruct-v0.2
```

- `--strategy`: Prompting strategy (`Direct`, `Hypothetical`, `Comparative`, `Role-play`, or `all`).
- `--samples`: Number of samples per strategy.
- `--model`: Model checkpoint ID.

**Output**: Reports saved in `data/raw/reports/`.

### Step 2: Compute Validity Metrics

Run the metrics computation script.

```bash
python -m src.analysis.metrics --input data/raw/reports/ --output data/derived/validity_scores.csv
```

**Output**: Validity scores saved in `data/derived/validity_scores.csv`.

### Step 3: Perform Statistical Analysis

Run the statistical analysis script.

```bash
python -m src.analysis.statistics --input data/derived/validity_scores.csv --output data/derived/statistical_results.json
```

**Output**: Statistical results saved in `data/derived/statistical_results.json`.

### Step 4: Human Qualitative Validation (Optional)

Distribute reports to human raters. They should fill out the rating sheet and save it as `data/qualitative/ratings.csv`.

Run the qualitative analysis script.

```bash
python -m src.analysis.qualitative --input data/qualitative/ratings.csv --output data/derived/qualitative_results.json
```

**Output**: Inter-rater reliability (Cohen's κ) and other metrics saved in `data/derived/qualitative_results.json`.

## Testing

Run the test suite to ensure everything is working.

```bash
pytest tests/
```

## Reproducibility

To reproduce the results:

1. Ensure the same random seeds are used (pinned in `code/`).
2. Use the same model checkpoints and prompt templates.
3. Re-run the pipeline from `Step 1`.

All data and code are versioned. Check the `state/` directory for artifact hashes.

## Troubleshooting

- **Memory Error**: If you run out of memory, reduce the number of samples or use a smaller model (e.g., `Q4_K` quantization).
- **Rate Limits**: If HuggingFace rate limits you, wait and retry or use a local model cache.
- **NLI Model Failure**: If the NLI model fails on a long sentence, it will be skipped and logged. Check `logs/` for details.

## Support

For issues, open a GitHub issue or contact the project maintainers.
