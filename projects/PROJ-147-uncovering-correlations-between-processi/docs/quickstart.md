# Quickstart Guide: Uncovering Correlations Between Processing Conditions and Texture

This guide provides instructions for running the llmXive research pipeline locally, including both native Python execution and containerized execution via Docker.

## Prerequisites

- **Python**: Version 3.11 or higher
- **System**: Linux, macOS, or Windows (WSL2 recommended)
- **Docker** (Optional): Required only if `ENABLE_DOCKER=true`
- **Memory**: Minimum 6GB RAM recommended for full dataset processing

## 1. Project Setup

Ensure you are in the project root directory. The project structure should look like this:

```
.
├── code/
│ ├── config.py
│ ├── main.py
│ ├── data/
│ ├── models/
│ └── utils/
├── data/
│ ├── raw/
│ └── processed/
├── docs/
├── tests/
├── requirements.txt
└── README.md
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configuration

The pipeline uses a configuration file to manage paths and execution modes.

### `ENABLE_DOCKER` Configuration

The `ENABLE_DOCKER` flag controls whether the pipeline runs natively or inside a Docker container.

- **Default**: `false` (Native execution)
- **To Enable**: Set the environment variable before running the pipeline.

**Native Execution (Default):**
```bash
export ENABLE_DOCKER=false
# or simply do not set it
python code/main.py
```

**Containerized Execution:**
```bash
export ENABLE_DOCKER=true
python code/main.py
```
*Note: If `ENABLE_DOCKER=true`, the script will attempt to build and run the Docker image defined in `Dockerfile`.*

## 3. Running the Pipeline

### Full Pipeline Execution

Run the complete data processing, training, evaluation, and reporting pipeline:

```bash
python code/main.py
```

This will:
1. **Load Data**: Ingest real data from Materials Project/OMDB or generate synthetic data if real data is unavailable (see `code/data/loader.py`).
2. **Preprocess**: Standardize units, impute missing values, and derive physics-based features.
3. **Train**: Train a multi-output RandomForest model with 5-fold cross-validation.
4. **Predict**: Generate predictions for test sets and new samples.
5. **Evaluate**: Compute R², MAE, RMSE, and feature importance.
6. **Report**: Generate `evaluation_report.json`, `sensitivity_report.json`, and `importance_plot.png`.

### Output Artifacts

Upon successful completion, the following files will be generated in the `data/` and `figures/` directories:

- `data/predictions.csv`: Model predictions on the test set.
- `data/new_predictions.csv`: Predictions for new sample inputs.
- `data/evaluation_report.json`: Detailed performance metrics per alloy family.
- `data/sensitivity_report.json`: Results of the threshold sensitivity analysis.
- `figures/importance_plot.png`: Visual ranking of feature importance.
- `pipeline.log`: Execution logs including warnings and hyperparameters.

## 4. Running Tests

### Unit Tests

Run the test suite to verify individual components:

```bash
pytest tests/ -v
```

### Integration Tests

Run the end-to-end integration test (requires `code/main.py` to be functional):

```bash
pytest tests/test_pipeline.py -v
```

## 5. Docker Execution (Optional)

If you prefer to run the pipeline in an isolated environment:

### Prerequisites

- Docker Engine installed and running.
- `ENABLE_DOCKER=true` set in your environment.

### Build and Run

The `main.py` script handles the Docker build and run process automatically if `ENABLE_DOCKER=true`. Alternatively, you can run manually:

```bash
# Build the image
docker build -t llmXive-pipeline:latest.

# Run the container
docker run -v $(pwd)/data:/app/data -v $(pwd)/figures:/app/figures llmXive-pipeline:latest
```

### CI/CD

Continuous Integration is configured via `.github/workflows/ci.yml`. The workflow respects the `ENABLE_DOCKER` flag:
- If `ENABLE_DOCKER=true`: Builds the image, runs the pipeline, and verifies exit code 0.
- If `ENABLE_DOCKER=false`: Skips containerization steps and runs native tests.

## 6. Troubleshooting

### "Module not found" Errors
Ensure you are running from the project root and the virtual environment is activated.
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Data Loading Failures
If real data sources (Materials Project/OMDB) are unreachable, the loader will fall back to synthetic data generation. Check `pipeline.log` for specific error messages regarding network connectivity.

### Memory Errors
If processing large datasets fails due to memory constraints, ensure you have at least 6GB of RAM available. The pipeline attempts to stream data where possible, but full dataset loading may occur for certain operations.

## 7. Next Steps

- Review `docs/research.md` for the scientific methodology.
- Check `docs/data-model.md` for entity definitions.
- Modify `code/config.py` to adjust hyperparameters or file paths.
- Extend the pipeline by implementing additional user stories in `tasks.md`.