# Quick Start Guide

This guide provides instructions for running the statistical analysis pipeline from start to finish.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for cloning the repository)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <repository-name>
 ```

2. Create a virtual environment:
 ```bash
 python -m venv code/.venv
 source code/.venv/bin/activate # On Windows: code\\.venv\\Scripts\\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

The pipeline can be run in two ways:

### Option 1: Run Individual Components

You can run each component of the pipeline separately:

1. **Data Ingestion**:
 ```bash
 python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv
 ```

2. **Create Cleaned Dataset**:
 ```bash
 python code/t016_create_cleaned_dataset.py
 ```

3. **Feature Extraction**:
 ```bash
 python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv
 ```

4. **Compute Embeddings Checksum**:
 ```bash
 python code/t024c_checksum.py
 ```

5. **Save Final Features**:
 ```bash
 python code/t025_save_features.py
 ```

6. **Statistical Analysis**:
 ```bash
 python code/stats.py --input data/processed/features.csv --output data/results/statistical_metrics.json
 ```

7. **Model Training**:
 ```bash
 python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json
 ```

8. **Record Checksums**:
 ```bash
 python code/t012f_checksum_record.py
 ```

9. **Success Criterion**:
 ```bash
 python code/t012h_success_criterion.py
 ```

### Option 2: Run Full Pipeline

Run the entire pipeline with runtime and memory measurement:

```bash
python code/main.py
```

This will execute all components in sequence and generate:
- `data/results/runtime_log.json`: Total runtime
- `data/results/memory_profile.json`: Peak memory usage

## Expected Outputs

After successful execution, the following files should be present:

- `data/raw/checksums.json`: Checksums for raw dataset
- `data/interim/cleaned_adress.csv`: Cleaned dataset
- `data/interim/exclusions.log`: Log of excluded records
- `data/processed/embeddings.npy`: Sentence embeddings
- `data/processed/features.csv`: Final feature matrix
- `data/processed/checksums.json`: Checksums for processed data
- `data/results/statistical_metrics.json`: Statistical test results
- `data/results/metadata.json`: Dataset metadata
- `data/results/raw_record_count.json`: Raw record count
- `data/results/cv_metrics.json`: Cross-validation metrics
- `data/results/model_performance.json`: Model performance summary
- `data/results/runtime_log.json`: Runtime metrics
- `data/results/memory_profile.json`: Memory usage metrics

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure you've activated the virtual environment and installed all dependencies.

2. **File Not Found**: Verify that previous steps in the pipeline have completed successfully and created the required input files.

3. **Memory Issues**: The pipeline is designed to run within 7 GB of RAM. If you encounter memory issues, reduce the batch size in feature extraction or use a smaller dataset.

4. **Download Failures**: If the ADReSS dataset download fails, check your internet connection and ensure the canonical URL is accessible.

## Running Tests

To run the test suite:

```bash
pytest tests/
```

For specific test categories:

```bash
# Unit tests
pytest tests/unit/

# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/
```

## Configuration

The pipeline behavior can be configured through `code/config.py`. Key settings include:

- `DATASET_SOURCE`: Specifies the dataset source (default: "ADReSS")
- Random seed for reproducibility
- CPU-only constraints
- File paths for inputs and outputs

## Next Steps

After running the pipeline:

1. Review the statistical metrics in `data/results/statistical_metrics.json`
2. Examine the model performance in `data/results/model_performance.json`
3. Check the runtime and memory metrics to ensure they meet the constraints
4. Analyze the derivation logs for data transformation details
5. Review the exclusions log for information about filtered records