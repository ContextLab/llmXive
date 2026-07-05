# Usage Examples

This document provides practical examples for using the pipeline components.

---

## 1. Data Generation

### Generating Synthetic MFQ Data

```bash
python code/data/simulation_mfq.py
```

**Output**: `data/raw/synthetic_mfq.csv`

**Custom Parameters**:

```bash
python code/data/simulation_mfq.py \
 --n-participants 100 \
 --seed 123 \
 --output data/raw/custom_mfq.csv
```

### Generating Moral Stories and VR Logs

```bash
python code/data/simulation_stories.py
```

**Output**:
- `data/raw/synthetic_stories.csv`
- `data/raw/synthetic_vr_logs.csv`

**Custom Parameters**:

```bash
python code/data/simulation_stories.py \
 --n-stories 50 \
 --n-participants 100 \
 --ground-truth-effect 0.15 \
 --seed 456 \
 --output-dir data/raw/custom/
```

---

## 2. Data Ingestion and Merging

### Loading and Merging Datasets

```bash
python code/data/ingest.py
```

**Input**:
- `data/raw/synthetic_mfq.csv`
- `data/raw/synthetic_stories.csv`
- `data/raw/synthetic_vr_logs.csv`

**Output**: `data/processed/merged.csv`

**Custom Paths**:

```bash
python code/data/ingest.py \
 --mfq-path data/custom/mfq.csv \
 --stories-path data/custom/stories.csv \
 --vr-logs-path data/custom/vr_logs.csv \
 --output data/processed/custom_merged.csv
```

### Handling ID Mismatches

The `ingest.py` script automatically handles participant ID mismatches by:
1. Logging unmatched IDs to `data/logs/unmatched_ids.log`
2. Dropping rows with missing joins
3. Generating a summary report in the console

---

## 3. Preprocessing

### Mapping Stories to VR Scenes

```bash
python code/data/preprocess.py
```

**Input**: `data/processed/merged.csv`

**Output**: `data/processed/preprocessed.csv`

**Salience Assignment**:
- Stories are mapped to VR scenes based on `story_id`
- `salience_level` is assigned via blend-shape parameters (LOW/HIGH)

**Custom Configuration**:

```bash
python code/data/preprocess.py \
 --input data/processed/merged.csv \
 --output data/processed/custom_preprocessed.csv \
 --salience-ratio 0.5
```

---

## 4. Bayesian Modeling

### Running the Bayesian Model

```bash
python code/models/bayesian.py
```

**Input**: `data/processed/preprocessed.csv`

**Output**: `state/bayesian_results.json`

**Model Structure**:
- Gaussian likelihood
- Normal priors on coefficients
- Foundation scores as covariates
- Salience as fixed-effect predictor

**Custom Parameters**:

```bash
python code/models/bayesian.py \
 --input data/processed/preprocessed.csv \
 --output state/custom_bayesian.json \
 --n-samples 2000 \
 --n-chains 4 \
 --seed 789
```

### Handling Convergence Failures

If MCMC fails to converge (R-hat > 1.05):
1. The script logs the failure to `data/logs/model_failures.log`
2. Falls back to Maximum Likelihood Estimation (MLE)
3. Flags the result as `inconclusive` in the output

---

## 5. Regression Analysis

### Running Mixed-Effects Regression

```bash
python code/models/regression.py
```

**Input**: `data/processed/preprocessed.csv`

**Output**: `state/regression_results.json`

**Model Formula**:
```
judgment ~ salience * foundation + (1 | participant_id)
```

**Bonferroni Correction**:
- Applied to interaction term p-values
- Corrected for number of foundations tested

**Custom Parameters**:

```bash
python code/models/regression.py \
 --input data/processed/preprocessed.csv \
 --output state/custom_regression.json \
 --alpha 0.05
```

---

## 6. Validation

### Parameter Recovery Check

```bash
python code/analysis/validation.py
```

**Input**: `state/bayesian_results.json`, `state/regression_results.json`

**Output**: `state/validation_results.json`

**Primary Metric**:
- Checks if `ground_truth_effect` is within 95% credible interval
- Reports PASS/FAIL status

**Sensitivity Analysis**:
- Sweeps decision thresholds over {2, 10, 20}
- Reports model selection stability matrix

**Custom Thresholds**:

```bash
python code/analysis/validation.py \
 --input state/ \
 --output state/custom_validation.json \
 --thresholds 2 10 20 50
```

---

## 7. Report Generation

### Generating the Final Report

```bash
python code/reports/generate_report.py
```

**Input**:
- `state/bayesian_results.json`
- `state/regression_results.json`
- `state/validation_results.json`

**Output**: `reports/final_report.md`

**Report Contents**:
- Pipeline validation status (PASSED/FAILED)
- Summary of findings
- Parameter recovery metrics
- Model comparison statistics (AIC, WAIC)
- Sensitivity analysis results

**Custom Output**:

```bash
python code/reports/generate_report.py \
 --input state/ \
 --output reports/custom_report.md
```

---

## 8. Full Pipeline Execution

### Sequential Execution

```bash
# Step 1: Generate data
python code/data/simulation_mfq.py
python code/data/simulation_stories.py

# Step 2: Ingest and preprocess
python code/data/ingest.py
python code/data/preprocess.py

# Step 3: Model and analyze
python code/models/bayesian.py
python code/models/regression.py

# Step 4: Validate and report
python code/analysis/validation.py
python code/reports/generate_report.py
```

### Using a Shell Script (Optional)

If `scripts/run_pipeline.sh` is available:

```bash
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh
```

---

## 9. Testing

### Running the Test Suite

```bash
# All tests
pytest code/tests/ -v

# Specific test file
pytest code/tests/test_schema.py -v

# With coverage
pytest code/tests/ --cov=code --cov-report=html
```

### Running Individual Tests

```bash
# Test MFQ generator interface
pytest code/tests/test_ingest_mfq.py::TestMFQGeneratorInterface -v

# Test parameter recovery
pytest code/tests/test_model_recovery.py::TestParameterRecovery -v
```

---

## 10. Data Integrity Verification

### Checking Artifact Checksums

```bash
python code/utils/hashing.py --verify
```

**Output**:
- List of verified artifacts
- Status (OK/FAILED) for each checksum
- State file updates if needed

### Updating State File

```bash
python code/utils/hashing.py --update
```

---

## 11. Configuration

### Editing `code/config.py`

```python
# code/config.py
RUN_MODE = 'simulation' # or 'real'
RANDOM_SEED = 42
DATA_PATHS = {
 'raw': 'data/raw/',
 'processed': 'data/processed/',
 'logs': 'data/logs/'
}
MODEL_PARAMS = {
 'n_samples': 2000,
 'n_chains': 4,
 'tune': 1000
}
VALIDATION_THRESHOLDS = [2, 10, 20]
```

### Environment Variables

Override configuration via environment variables:

```bash
export RUN_MODE=real
export RANDOM_SEED=12345
python code/data/simulation_mfq.py
```

---

## 12. Debugging

### Enabling Verbose Logging

```bash
python code/data/ingest.py --log-level DEBUG
```

### Checking Log Files

```bash
# Exclusion logs
cat data/logs/exclusions.log

# VR mapping logs
cat data/logs/vr_mappings.log

# Model failures
cat data/logs/model_failures.log
```

---

## 13. Real Data Mode (Future)

### Fetching Real Data from OSF

```python
from code.data.ingest_real import fetch_from_osf

data = fetch_from_osf(
 endpoint='https://osf.io/your-project-id/',
 auth_token='your_api_token'
)
```

### Fetching from HuggingFace

```python
from code.data.ingest_real import fetch_from_huggingface

data = fetch_from_huggingface(
 dataset_id='your-username/your-dataset',
 split='train'
)
```

**Note**: Real data mode requires valid authentication tokens and network access.

---

## 14. Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'pymc'`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: `ValidationError: score must be between 0 and 5`
**Solution**: Check input data for out-of-range values

**Issue**: `ConvergenceWarning: R-hat > 1.05`
**Solution**: Increase `n_samples` or check model specification

**Issue**: `FileNotFoundError: data/raw/synthetic_mfq.csv`
**Solution**: Run `simulation_mfq.py` before `ingest.py`

---

## 15. Performance Tips

### CPU-Only Execution

All models are optimized for CPU execution:

```python
# In code/models/bayesian.py
import pymc as pm
with pm.Model() as model:
 #... model definition...
 trace = pm.sample(cores=4, chains=4) # Use multiple CPU cores
```

### Parallel Processing

For large datasets, enable parallel processing:

```bash
export OMP_NUM_THREADS=4
python code/models/bayesian.py
```

---

## 16. Extending the Pipeline

### Adding New Schemas

1. Define new Pydantic model in `code/utils/schema.py`
2. Add validation function
3. Update `data_schema.md` documentation

### Adding New Models

1. Create new module in `code/models/`
2. Implement `main()` function
3. Update `usage_examples.md` with examples

---

For additional support, refer to the main [README.md](../README.md) or open an issue on the repository.
