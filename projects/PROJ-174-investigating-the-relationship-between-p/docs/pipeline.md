# Pipeline Documentation

## Overview

This pipeline investigates the relationship between pupil dilation and cognitive load during visual search tasks. It processes eye-tracking data, extracts features, computes correlations, fits linear mixed-effects models, and prototypes a real-time classification system.

## Architecture

The pipeline is organized into the following modules:

- **`code/preprocessing/`**: Data loading, filtering, and feature extraction
 - `load_data.py`: Ingests raw eye-tracking files into a uniform CSV format
 - `filter.py`: Applies blink interpolation and low-pass filtering
 - `features.py`: Computes load proxies (search time, fixation count, target salience)

- **`code/analysis/`**: Statistical analysis
 - `correlations.py`: Calculates Pearson correlations with FDR correction
 - `lme_model.py`: Fits Linear Mixed-Effects models with collinearity mitigation

- **`code/classification/`**: Real-time classification prototype
 - `classifier.py`: Sliding-window logistic regression
 - `evaluate.py`: Metrics computation (accuracy, ROC-AUC)
 - `ground_truth.py`: Labeling logic and limitations documentation
 - `correlation_validation.py`: Continuous correlation validation

- **`code/`**: Core infrastructure
 - `main.py`: Pipeline orchestrator
 - `config.py`: Configuration loader
 - `data_model.py`: Data structures
 - `verify_data_availability.py`: Data verification hard gate

## CLI Usage

### Prerequisites

1. Ensure Python 3.11+ is installed
2. Navigate to the `code/` directory
3. Activate the virtual environment:
 ```bash
 source venv/bin/activate # Linux/Mac
 # or
 venv\Scripts\activate # Windows
 ```
4. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Running the Pipeline

#### Full Pipeline Execution

Run the entire pipeline from data verification to classification:

```bash
python main.py --config config.yaml
```

#### Individual Modules

**Data Verification** (Must run first):
```bash
python verify_data_availability.py
```

**Preprocessing**:
```bash
python -m preprocessing.load_data --input data/raw/ --output data/processed/
python -m preprocessing.filter --input data/processed/ --output data/processed/filtered/
python -m preprocessing.features --input data/processed/filtered/ --output data/processed/features/
```

**Correlation Analysis**:
```bash
python -m analysis.correlations --input data/processed/features/ --output results/correlations.csv
```

**LME Model Fitting**:
```bash
python -m analysis.lme_model --input data/processed/features/ --output results/model_summary.csv
```

**Classification**:
```bash
python -m classification.ground_truth --input data/processed/features/ --output data/processed/labeled/
python -m classification.classifier --input data/processed/labeled/ --output results/classification_metrics.csv
python -m classification.evaluate --input data/processed/labeled/ --output results/evaluation_metrics.csv
```

### Configuration

The pipeline uses `config.yaml` for configuration:

```yaml
seeds:
 random: 42

thresholds:
 blink_threshold: 0.5
 lowpass_cutoff: 4.0
 vif_threshold: 5.0

paths:
 raw_data: data/raw/
 processed_data: data/processed/
 results: results/
```

Environment variables can be set in `.env`:

```
DATA_PATH=data/raw/
OPENNEURO_API_KEY=your_api_key
LOG_LEVEL=INFO
```

## Output Artifacts

The pipeline produces the following outputs:

- `data/processed/`: Preprocessed and feature-extracted data
- `results/correlations.csv`: Pearson correlations with FDR-corrected p-values
- `results/model_summary.csv`: LME model coefficients, SEs, p-values
- `results/classification_metrics.csv`: Classification performance metrics
- `results/sensitivity_analysis.csv`: Threshold sensitivity analysis
- `results/quality_report.csv`: Data quality and exclusion statistics
- `results/limitations.md`: Documentation of methodological limitations
- `state/structure_check.yaml`: Directory structure verification status

## Limitations

### Data Limitations

- **Ground Truth**: When independent cognitive load measures are absent, labels are derived from search-time median splits. This limits predictive validity claims.
- **Dataset Availability**: The pipeline requires verified eye-tracking datasets. It will halt if only fMRI or invalid data sources are detected.

### Methodological Limitations

- **Salience Computation**: Target salience is computed on-the-fly using Gabor filters. If stimulus images are unavailable, this proxy is marked as `UNFULFILLABLE`.
- **Collinearity**: Predictors with VIF > 5 are dropped to mitigate multicollinearity, potentially reducing model complexity.
- **Trial Count**: Subjects with fewer than 20 trials trigger a `RuntimeError` unless aggregation is enabled in config.

### Real-Time Classification Caveats

- The sliding-window classifier uses a fixed-duration lookback window but updates every 200ms.
- Ground truth labels are derived from search-time median splits; predictive validity claims have been removed per SC-004.
- Classification output status is marked as `UNVALIDATED` to prevent downstream misinterpretation.

## Testing

Run tests from the `code/` directory:

```bash
pytest tests/
```

Specific test modules:
- `tests/test_config.py`: Configuration validation
- `tests/test_data_loader.py`: Data loading validation
- `tests/test_preprocess.py`: Blink interpolation tests
- `tests/test_analysis.py`: VIF and LME model tests
- `tests/test_classifier.py`: Sliding window and sensitivity tests

## Troubleshooting

### Common Issues

**1. Data Verification Failure**
- Error: "No verified eye-tracking dataset found"
- Solution: Check `plan.md` for valid dataset sources or update the verified datasets block.

**2. Missing Dependencies**
- Error: `ModuleNotFoundError`
- Solution: Run `pip install -r requirements.txt` in the `code/` directory.

**3. Configuration Errors**
- Error: `KeyError` or type mismatches in config
- Solution: Verify `config.yaml` structure matches the schema in `code/config.py`.

**4. Insufficient Trials**
- Error: "Subject {id} has < 20 trials"
- Solution: Enable aggregation in `config.yaml` or ensure datasets have sufficient trials.

## Contributing

1. Create a feature branch
2. Implement changes with tests
3. Run `black --check code/` and `pytest tests/`
4. Submit a pull request

## License

See LICENSE file in the repository root.
