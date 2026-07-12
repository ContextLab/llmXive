# LLMXive Follow-up: Quick Start Guide

This guide provides instructions to run the full LLMXive pipeline on a free-tier runner (e.g., GitHub Actions, Google Colab, or a local CPU-only machine).

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- At least 8GB RAM (recommended)
- CPU-only environment (no GPU required)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PROJ-835-llmxive-follow-up-extending-a-survey-of
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: The `requirements.txt` includes CPU-only versions of PyTorch and other necessary packages.

## Running the Pipeline

The pipeline is orchestrated via a CLI command. It performs the following steps in order:

1. **Download**: Fetches or generates the dataset.
2. **Preprocess**: Validates and prepares audio files.
3. **Embed**: Extracts latent embeddings using a frozen encoder.
4. **Train**: Trains a lightweight binary classifier.
5. **Evaluate**: Computes metrics and validates results.
6. **Update State**: Records artifact hashes.

### Execute the Full Pipeline

```bash
python code/src/cli/run_pipeline.py
```

### Optional: Custom Configuration

You can customize the dataset sampling size and batch size:

```bash
python code/src/cli/run_pipeline.py --sample-size 500 --batch-size 16
```

## Output Artifacts

Upon successful completion, the following artifacts will be generated:

- `data/embeddings.parquet`: Latent embeddings for all samples.
- `data/anomaly_scores.parquet`: Mahalanobis distance scores.
- `results/predictions.csv`: Model predictions and probabilities.
- `results/correlation.json`: Correlation analysis results.
- `results/report.md`: Comprehensive evaluation report.
- `results/resource_log.json`: Resource usage metrics.
- `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml`: Updated artifact hashes.

## Troubleshooting

### CPU-Only Enforcement

The pipeline enforces CPU-only execution by default. If you encounter CUDA-related errors, ensure that `CUDA_VISIBLE_DEVICES` is unset or set to an empty string:

```bash
export CUDA_VISIBLE_DEVICES=""
```

### Memory Issues

If you run into memory errors, try reducing the batch size:

```bash
python code/src/cli/run_pipeline.py --batch-size 8
```

### Dependency Installation Errors

If `pip install` fails due to missing system libraries (e.g., `libsndfile` for audio processing), install them via your package manager:

- **Ubuntu/Debian**: `sudo apt-get install libsndfile1`
- **macOS**: `brew install libsndfile`
- **Windows**: Install via `conda` or download pre-built wheels.

## Verification

To verify that the pipeline ran correctly, check the `results/report.md` file for the final metrics and ensure that the `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` file has been updated with new artifact hashes.

## Next Steps

- Review the `results/report.md` for performance metrics.
- Analyze the `results/correlation.json` for correlation insights.
- Explore the generated `data/` and `results/` artifacts for further analysis.

For more details, refer to the project documentation in the `specs/` directory.