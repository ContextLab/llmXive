# Quickstart Guide: Code Duplication Impact Analysis Pipeline

This guide provides step-by-step instructions to run the complete analysis pipeline.

## Prerequisites

- Python 3.11+
- Required packages installed (see `requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
```

## Pipeline Execution Steps

Follow these steps in order to run the complete analysis:

### Stage 1: Download Data

Download the code corpus sample:

```bash
python code/data_loader.py --output data/raw/github-code-sample.csv --max-samples 100
```

This creates `data/raw/github-code-sample.csv` with code samples from the repository.

### Stage 2: Run Main Pipeline

Execute the full pipeline to compute clone density and perplexity:

```bash
python code/main.py --raw-data data/raw/github-code-sample.csv
```

This produces:
- `data/processed/clone_metrics.csv` - Clone density metrics
- `data/processed/perplexity_scores.csv` - Perplexity scores
- `data/processed/merged_metrics.csv` - Combined metrics

### Stage 3: Validation

Validate the pipeline outputs:

```bash
python code/quickstart_validation.py
```

## Output Files

After successful execution, you should have:

| File | Description |
|------|-------------|
| `data/raw/github-code-sample.csv` | Raw code samples |
| `data/processed/clone_metrics.csv` | Clone density per sample |
| `data/processed/perplexity_scores.csv` | Perplexity scores per sample |
| `data/processed/merged_metrics.csv` | Combined metrics |
| `data/parse_failures.csv` | Parse failure log |
| `data/pipeline.log` | Pipeline execution log |

## Troubleshooting

### Missing raw data file

If you see "Raw data file not found" error, run the data loader first:

```bash
python code/data_loader.py --output data/raw/github-code-sample.csv
```

### Model loading errors

If model loading fails, ensure you have sufficient GPU memory or use CPU fallback.

### Checksum validation failed

Run the checksum computation tasks to update the manifest:

```bash
python code/checksum_manifest.py
```

## Next Steps

After completing the pipeline, proceed to User Story 2 (Bug Detection and Correlation Analysis) tasks.