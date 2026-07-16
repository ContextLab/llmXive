# Usage Examples

This document provides practical examples for using the pipeline components.

## Quick Start

### Running the Full Pipeline

The simplest way to run the entire pipeline is using the validation script:

```python
# code/quickstart_validation.py
python code/quickstart_validation.py
```

This will:
1. Generate synthetic data
2. Ingest and preprocess datasets
3. Run Bayesian models
4. Perform statistical validation
5. Generate the final report

## Data Generation Examples

### Generating Synthetic MFQ Data

```python
from code.data.simulation_mfq import generate_synthetic_mfq
from code.config import init_random_seeds

# Initialize random seeds for reproducibility
init_random_seeds(42)

# Generate 1000 synthetic MFQ responses
mfq_data = generate_synthetic_mfq(
 n_participants=100,
 n_responses_per_participant=30,
 output_path="data/processed/synthetic_mfq.csv"
)
```

### Generating Moral Stories and VR Logs

```python
from code.data.simulation_stories import generate_moral_stories_dataset, generate_vr_logs_dataset

# Generate moral stories with known ground truth effect
stories_df, ground_truth = generate_moral_stories_dataset(
 n_stories=50,
 ground_truth_effect=0.5,
 output_path="data/processed/stories.csv"
)

# Generate corresponding VR interaction logs
vr_logs_df = generate_vr_logs_dataset(
 stories_df=stories_df,
 n_participants=100,
 output_path="data/processed/vr_logs.csv"
)
```

## Data Ingestion Examples

### Loading and Merging Datasets

```python
from code.data.ingest import load_mfq_data, load_stories_data, merge_datasets

# Load synthetic datasets
mfq_data = load_mfq_data("data/processed/synthetic_mfq.csv")
stories_data = load_stories_data("data/processed/stories.csv")
vr_logs_data = load_vr_logs_data("data/processed/vr_logs.csv")

# Merge datasets
merged_df = merge_datasets(mfq_data, stories_data, vr_logs_data)
merged_df.to_csv("data/processed/merged_dataset.csv", index=False)
```

### Preprocessing with Salience Mapping

```python
from code.data.preprocess import process_salience_mapping, save_preprocessed_data

# Assign salience levels based on story characteristics
processed_data = process_salience_mapping(merged_df)

# Save preprocessed data
save_preprocessed_data(
 processed_data,
 "data/processed/preprocessed_data.csv",
 "data/logs/preprocessing_log.json"
)
```

## Model Execution Examples

### Running Bayesian Model

```python
from code.models.bayesian import run_bayesian_model

# Run the salience-augmented Bayesian model
results = run_bayesian_model(
 data_path="data/processed/preprocessed_data.csv",
 model_type="salience_augmented",
 n_samples=2000,
 n_chains=4,
 output_path="data/processed/bayesian_results.json"
)
```

### Model Comparison

```python
from code.analysis.model_comparison import calculate_aic_waic, run_model_comparison

# Compare salience-augmented model vs baseline
comparison_results = run_model_comparison(
 data_path="data/processed/preprocessed_data.csv",
 models=["baseline", "salience_augmented"],
 output_path="data/processed/model_comparison.json"
)

# Calculate information criteria
aic_waic = calculate_aic_waic(comparison_results)
print(f"ΔAIC: {aic_waic['delta_aic']:.2f}")
print(f"ΔWAIC: {aic_waic['delta_waic']:.2f}")
```

## Validation Examples

### Parameter Recovery Check

```python
from code.analysis.validation import check_parameter_recovery

# Verify that the model recovered the ground truth effect
recovery_status = check_parameter_recovery(
 results_path="data/processed/bayesian_results.json",
 ground_truth_effect=0.5,
 credible_interval=0.95
)

if recovery_status["passed"]:
 print("Parameter recovery: PASS")
else:
 print(f"Parameter recovery: FAIL (CI: {recovery_status['ci']})")
```

### Sensitivity Analysis

```python
from code.analysis.validation import conduct_sensitivity_analysis

# Conduct sensitivity analysis over decision thresholds
sensitivity_results = conduct_sensitivity_analysis(
 data_path="data/processed/preprocessed_data.csv",
 thresholds=[2, 10, 20],
 output_path="data/processed/sensitivity_analysis.json"
)
```

### Regression Analysis

```python
from code.models.regression import run_regression_pipeline

# Run hierarchical mixed-effects regression
regression_results = run_regression_pipeline(
 data_path="data/processed/preprocessed_data.csv",
 output_path="data/processed/regression_results.json"
)
```

## Report Generation

### Generating Final Report

```python
from code.reports.generate_report import generate_report_content

# Generate comprehensive report
report = generate_report_content(
 bayesian_results="data/processed/bayesian_results.json",
 comparison_results="data/processed/model_comparison.json",
 regression_results="data/processed/regression_results.json",
 sensitivity_results="data/processed/sensitivity_analysis.json",
 output_path="reports/final_report.md"
)
```

## Error Handling Examples

### Handling Convergence Failures

```python
from code.models.bayesian import run_bayesian_model
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Run model with convergence failure handling
try:
 results = run_bayesian_model(
 data_path="data/processed/preprocessed_data.csv",
 model_type="salience_augmented",
 handle_convergence_failures=True
)
except Exception as e:
 logging.error(f"Model execution failed: {str(e)}")
 # Fallback to MLE if configured
```

### Validating Data Quality

```python
from code.utils.schema import validate_merged_data
from code.utils.logging_utils import log_exclusion

# Validate dataset
validation_result = validate_merged_data("data/processed/merged_dataset.csv")

if not validation_result["valid"]:
 for error in validation_result["errors"]:
 log_exclusion(
 reason=error["reason"],
 record_id=error["record_id"],
 log_type="validation"
)
```

## Advanced Configuration

### Custom Configuration

```python
from code.config import ensure_directories
import yaml

# Load custom configuration
with open("config/custom_config.yaml", "r") as f:
 config = yaml.safe_load(f)

# Initialize directories with custom paths
ensure_directories(
 base_path=config["base_path"],
 data_dirs=config["data_directories"],
 output_dirs=config["output_directories"]
)
```

### Parallel Execution

```python
from code.data.simulation_mfq import generate_synthetic_mfq
from code.data.simulation_stories import generate_moral_stories_dataset
from concurrent.futures import ThreadPoolExecutor

def run_simulations():
 with ThreadPoolExecutor(max_workers=2) as executor:
 mfq_future = executor.submit(generate_synthetic_mfq, 100, 30)
 stories_future = executor.submit(generate_moral_stories_dataset, 50, 0.5)

 mfq_data = mfq_future.result()
 stories_data = stories_future.result()

 return mfq_data, stories_data

mfq, stories = run_simulations()
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
 ```bash
 pip install -r requirements.txt --upgrade
 ```

2. **Directory Not Found**:
 ```bash
 python code/setup_directories.py
 python code/setup_subdirectories.py
 ```

3. **Model Convergence Issues**:
 - Increase number of samples
 - Adjust priors
 - Check data quality

4. **Data Validation Errors**:
 - Check input data format
 - Verify schema compliance
 - Review exclusion logs in `data/logs/`
