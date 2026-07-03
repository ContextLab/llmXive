# Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Project Overview

This research project investigates how pupil dilation correlates with cognitive load during visual search tasks. The pipeline processes eye-tracking data, extracts load proxies, computes statistical correlations, fits linear mixed-effects models, and prototypes a real-time cognitive load classifier.

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- git

### Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd llmXive-investigating-the-relationship-between-p
 ```

2. Navigate to the code directory:
 ```bash
 cd code
 ```

3. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or
 venv\Scripts\activate # Windows
 ```

4. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

5. Set up environment variables (optional):
 ```bash
 cp.env.example.env
 # Edit.env with your API keys and paths
 ```

### Running the Pipeline

#### Verify Data Availability

Before running any analysis, verify that valid eye-tracking datasets are available:

```bash
python verify_data_availability.py
```

This step acts as a hard gate and will halt the pipeline if no valid datasets are found.

#### Run the Full Pipeline

Execute the complete pipeline from preprocessing to classification:

```bash
python main.py --config config.yaml
```

#### Run Individual Modules

You can also run specific modules independently:

```bash
# Preprocessing
python -m preprocessing.features --input data/raw/ --output data/processed/features/

# Correlation Analysis
python -m analysis.correlations --input data/processed/features/ --output results/correlations.csv

# LME Model
python -m analysis.lme_model --input data/processed/features/ --output results/model_summary.csv

# Classification
python -m classification.classifier --input data/processed/labeled/ --output results/classification_metrics.csv
```

### Running Tests

```bash
pytest tests/
```

### Documentation

- [Pipeline Documentation](docs/pipeline.md) - Detailed pipeline architecture and usage
- [Quick Start Guide](docs/quickstart.sh) - Automated setup and validation script

## Project Structure

```
.
├── code/
│ ├── preprocessing/
│ │ ├── load_data.py
│ │ ├── filter.py
│ │ └── features.py
│ ├── analysis/
│ │ ├── correlations.py
│ │ └── lme_model.py
│ ├── classification/
│ │ ├── classifier.py
│ │ ├── evaluate.py
│ │ ├── ground_truth.py
│ │ └── correlation_validation.py
│ ├── config.py
│ ├── data_model.py
│ ├── main.py
│ ├── verify_data_availability.py
│ └── requirements.txt
├── data/
│ ├── raw/
│ └── processed/
├── results/
│ ├── correlations.csv
│ ├── model_summary.csv
│ ├── classification_metrics.csv
│ ├── sensitivity_analysis.csv
│ ├── quality_report.csv
│ └── limitations.md
├── docs/
│ ├── pipeline.md
│ └── quickstart.sh
├── tests/
│ ├── test_config.py
│ ├── test_data_loader.py
│ ├── test_preprocess.py
│ ├── test_analysis.py
│ └── test_classifier.py
├── state/
│ └── structure_check.yaml
├──.env.example
├── config.yaml
└── README.md
```

## Key Features

### 1. Data Verification Hard Gate
- Automatically validates dataset availability before processing
- Halts pipeline if only invalid (e.g., fMRI) datasets are detected
- Downloads verified eye-tracking datasets to `data/raw/`

### 2. Preprocessing Pipeline
- Blink interpolation for missing pupil data
- Low-pass filtering (≤4 Hz) to remove noise
- On-the-fly target salience computation using Gabor filters
- Quality reporting with exclusion statistics

### 3. Statistical Analysis
- Pearson correlations with Benjamini-Hochberg FDR correction
- Linear Mixed-Effects models with subject random intercepts
- Collinearity mitigation via Variance Inflation Factor (VIF) analysis
- Likelihood-ratio tests for model comparison

### 4. Real-Time Classification Prototype
- Sliding-window logistic regression with 200ms update intervals
- Ground truth labeling via search-time median split
- Sensitivity analysis across thresholds {0.40, 0.50, 0.60}
- Continuous correlation validation between predictions and search time

## Limitations

### Ground Truth Limitation
When independent cognitive load measures are unavailable, labels are derived from search-time median splits. **Predictive validity claims have been removed** from all outputs per project specifications.

### Data Requirements
- Valid eye-tracking datasets required (fMRI datasets will trigger pipeline halt)
- Minimum 20 trials per subject unless aggregation is enabled
- Target salience computation requires stimulus images; otherwise marked as `UNFULFILLABLE`

### Classification Caveats
- Ground truth is derived from search-time median split
- Output status marked as `UNVALIDATED` to prevent misinterpretation
- See `results/limitations.md` for detailed methodological constraints

## Configuration

Edit `config.yaml` to customize:

```yaml
seeds:
 random: 42 # Random seed for reproducibility

thresholds:
 blink_threshold: 0.5 # Pupil diameter threshold for blink detection
 lowpass_cutoff: 4.0 # Low-pass filter cutoff frequency (Hz)
 vif_threshold: 5.0 # VIF threshold for collinearity mitigation

paths:
 raw_data: data/raw/
 processed_data: data/processed/
 results: results/
```

Set environment variables in `.env`:

```
DATA_PATH=data/raw/
OPENNEURO_API_KEY=your_api_key
LOG_LEVEL=INFO
```

## Output Files

- `results/correlations.csv`: Pearson correlations with FDR-corrected p-values
- `results/model_summary.csv`: LME model fixed effects, SEs, p-values, likelihood-ratio tests
- `results/classification_metrics.csv`: Accuracy, precision, recall, ROC-AUC
- `results/sensitivity_analysis.csv`: Threshold sensitivity metrics
- `results/quality_report.csv`: Data exclusion statistics
- `results/limitations.md`: Methodological limitations documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with corresponding tests
4. Run `black --check code/` and `pytest tests/` to ensure code quality
5. Submit a pull request

## License

See LICENSE file for details.

## Acknowledgments

This project is part of the llmXive automated science pipeline.
