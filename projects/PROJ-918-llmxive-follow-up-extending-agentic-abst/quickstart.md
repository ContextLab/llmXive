# Quick Start Guide: llmXive Agentic Abstention Pipeline

This guide walks you through the end-to-end execution of the llmXive research pipeline, from data ingestion to statistical validation.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Hugging Face CLI (for benchmark data access)
- Sufficient disk space (~10GB for data and models)

## Step 1: Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd llmXive

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Hugging Face CLI if not already installed
pip install huggingface_hub
```

## Step 2: Configure the Pipeline

Create a `config.yaml` file in the project root (or use environment variables):

```yaml
# config.yaml
paths:
 data_root: "data"
 raw_data: "data/raw"
 processed_data: "data/processed"
 results: "data/results"
 models: "models"

simulation:
 max_turns: 20
 seed: 42
 token_budget: 10000

model:
 learning_rate: 0.1
 max_depth: 6
 n_estimators: 100

logging:
 level: INFO
 file: "logs/pipeline.log"
```

## Step 3: Data Ingestion and Feature Extraction (User Story 1)

### 3.1 Fetch Benchmark Data

```bash
python code/data/ingest.py
```

This script:
- Fetches the real "Agentic Abstention" benchmark from Hugging Face
- Verifies data integrity using checksums
- Falls back to the synthetic simulator only if the real benchmark is unavailable

**Output**: `data/raw/benchmark_data.parquet`

### 3.2 Extract Features

```bash
python code/data/extract_features.py
```

This script:
- Parses interaction trajectories
- Computes state features: search count, error frequency, token usage, turn number
- Calculates query-context embedding distance
- Joins with oracle-generated abstention labels

**Output**: `data/processed/features.parquet`

### 3.3 Preprocess Data

```bash
python code/data/preprocess.py
```

This script:
- Applies mean imputation for missing numeric variables
- Validates dataset quality (halts if >5% missing critical variables)
- Generates a validation report

**Output**: `data/processed/features_clean.parquet`, `data/validation_report.json`

## Step 4: Meta-Critic Model Training (User Story 2)

### 4.1 Train the Meta-Critic

```bash
python code/models/train_meta_critic.py
```

This script:
- Loads the preprocessed features
- Trains an XGBoost classifier to predict abstention points
- Evaluates model performance
- Logs abstention events for auditability

**Output**: `models/meta_critic_model.json`, `models/model_metrics.json`

### 4.2 Run Baseline Simulation

```bash
python code/simulation/run_baseline.py
```

This script:
- Runs the reference CONVOLVE implementation
- Simulates agent interactions with full-context baseline
- Records token consumption and turn counts

**Output**: `data/results/baseline_simulation.json`

### 4.3 Run Meta-Critic Simulation

```bash
python code/models/evaluate.py
```

This script:
- Runs simulations where the Meta-Critic evaluates state before each action
- Calculates Timely Abstention Recall, token consumption, and latency
- Compares against the full-context baseline
- Verifies if token reduction >= 40% or Cohen's d >= 0.5

**Output**: `data/results/simulation_results.json`

## Step 5: Statistical Validation (User Story 3)

### 5.1 Run Statistical Tests

```bash
python code/analysis/statistical_tests.py
```

This script:
- Performs Mann-Whitney U and Kolmogorov-Smirnov tests on token consumption
- Calculates effect sizes (Cohen's d)
- Computes Variance Inflation Factors (VIF) for collinearity diagnostics
- Generates distribution comparison plots

**Output**: `data/results/statistical_test_results.json`

### 5.2 Run Survival Analysis

```bash
python code/analysis/survival_analysis.py
```

This script:
- Performs Kaplan-Meier analysis on token consumption
- Conducts Log-Rank tests
- Handles censored data appropriately
- Generates survival curves

**Output**: `data/results/survival_analysis.json`, `figures/survival_curves.png`

### 5.3 Run Sensitivity Analysis

```bash
python code/analysis/sensitivity_analysis.py
```

This script:
- Sweeps decision thresholds across a range of values
- Calculates false-positive and false-negative rates at each threshold
- Generates sensitivity curve plots

**Output**: `data/results/sensitivity_analysis.json`, `figures/sensitivity_curve.png`

### 5.4 Generate Final Reports

```bash
python code/analysis/generate_baseline_comparison.py
python code/analysis/generate_statistical_report.py
```

These scripts:
- Compile baseline comparison metrics
- Generate a comprehensive markdown report with p-values, effect sizes, and visualizations

**Output**: `data/results/baseline_comparison.json`, `data/results/statistical_report.md`

## Step 6: Verification

### 6.1 Verify Output Schemas

```bash
python code/data/verify_features.py
```

Ensures that output files comply with the defined schemas and contain no full semantic context strings.

### 6.2 Run Test Suite

```bash
pytest tests/
```

Verifies that all contract and integration tests pass.

## Expected Results

A successful run should produce:
- Token reduction of >= 40% compared to baseline
- Statistical significance (p < 0.05) for token consumption differences
- Cohen's d effect size >= 0.5
- No full semantic context strings in processed features
- All validation checks passing

## Troubleshooting

### Data Ingestion Fails
- Ensure Hugging Face CLI is configured: `huggingface-cli login`
- Check network connectivity
- Verify the benchmark dataset exists on Hugging Face Hub

### Missing Dependencies
- Re-run `pip install -r requirements.txt`
- Ensure Python 3.11+ is being used

### Memory Issues
- Reduce the dataset size in `config.yaml`
- Enable streaming for large datasets (modify `code/data/ingest.py`)

### Validation Failures
- Check `data/validation_report.json` for specific issues
- Verify that input data matches expected schema

## Next Steps

- Review the generated `data/results/statistical_report.md` for detailed findings
- Analyze the sensitivity curves to determine optimal decision thresholds
- Consider extending the pipeline with additional agent behaviors or datasets
- Contribute improvements back to the project

## Support

For issues or questions, please open an issue on the project repository.
