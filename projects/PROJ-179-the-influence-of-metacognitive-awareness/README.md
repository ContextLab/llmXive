# The Influence of Metacognitive Awareness on Reality Testing (PROJ-179)

## Project Overview

This research project investigates the relationship between **metacognitive awareness** (the ability to monitor one's own cognitive processes) and **reality testing accuracy** (the ability to distinguish between internal and external sources of information).

### Research Goals
1. **Primary Analysis**: Compute the correlation between metacognitive awareness (Type-2 AUC) and reality testing accuracy (d') using a Hold-Out design to ensure statistical independence.
2. **Hierarchical Regression**: Test whether metacognitive awareness contributes unique variance to reality testing accuracy after controlling for age, gender, and working memory capacity.
3. **Modality-Specific Robustness**: Replicate the primary analysis separately for ambiguous visual versus auditory stimuli.

### Key Methodology
- **Hold-Out Accuracy Design**: 70/30 train/test split to prevent data leakage between metacognitive score calculation and accuracy measurement.
- **Signal Detection Theory (SDT)**: Used to compute d' (sensitivity) and criterion.
- **Bootstrap Resampling**: 1,000 resamples (with runtime fallback) for 95% confidence intervals.
- **Hierarchical Regression**: Incremental R² change analysis with assumption checks.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (package manager)

### Installation
1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-179-the-influence-of-metacognitive-awareness
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### Configuration
- Create a `.env` file in the project root for environment variables (seeds, paths).
- Ensure the data directory structure is set up as per `data/` folder requirements.

## Data Availability Warning ⚠️

**CRITICAL**: This project requires a **valid behavioral dataset** containing the fields `confidence_rating` and `source_label`.

- **OpenNeuro ds003386** (structural MRI) is **NOT** a valid source for this analysis as it lacks the required behavioral fields.
- If the only available dataset is OpenNeuro ds003386, the pipeline will **abort** with an error message.
- Alternative datasets (e.g., from UCI or OpenNeuro behavioral datasets) must be identified and validated before proceeding.

To check data availability:
```bash
python code/data/validate_data_availability.py
```

If validation fails, the project is blocked until a valid dataset is provided.

## Project Structure

```
projects/PROJ-179-the-influence-of-metacognitive-awareness/
├── code/
│ ├── __init__.py
│ ├── config/
│ │ └── env_config.py # Environment configuration
│ ├── data/
│ │ ├── __init__.py
│ │ ├── preprocess.py # Data preprocessing
│ │ ├── validate_data.py # Data validation
│ │ ├── validate_data_availability.py # Data source check
│ │ └── validate_disjoint_trials.py # Disjoint trial validation
│ ├── models/
│ │ └── data_models.py # Data model definitions
│ ├── src/
│ │ ├── analysis/
│ │ │ ├── bootstrap.py # Bootstrap resampling
│ │ │ ├── filter.py # Modality filtering
│ │ │ ├── regression.py # Hierarchical regression
│ │ │ ├── robustness.py # Robustness analysis
│ │ │ └── correlation.py # Primary correlation analysis
│ │ ├── report/
│ │ │ └── generate.py # Report generation
│ │ └── utils/
│ │ └── stats.py # Statistical utilities
│ └── tests/
│ ├── __init__.py
│ ├── contract/ # Contract tests
│ ├── integration/ # Integration tests
│ └── unit/ # Unit tests
├── data/
│ ├── derived/ # Processed data outputs
│ └── results/ # Analysis results
├── specs/ # Project specifications
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Running the Pipeline

### 1. Validate Data Availability
```bash
python code/data/validate_data_availability.py
```

### 2. Download Dataset (if valid)
```bash
python code/data/download.py
```

### 3. Validate Downloaded Data
```bash
python code/data/validate_data.py
```

### 4. Preprocess Data
```bash
python code/data/preprocess.py
```

### 5. Run Primary Analysis (User Story 1)
```bash
python code/src/analysis/correlation.py
python code/src/analysis/bootstrap.py
```

### 6. Run Hierarchical Regression (User Story 2)
```bash
python code/src/analysis/regression.py
python code/src/analysis/diagnostics.py
```

### 7. Run Modality-Specific Analysis (User Story 3)
```bash
python code/src/analysis/filter.py
python code/src/analysis/robustness.py
```

### 8. Generate Reports
```bash
python code/src/report/generate.py
```

## Output Artifacts

- `data/derived/trial_data.csv`: Preprocessed trial-level data.
- `data/results/primary_analysis.json`: Correlation results (r, p-value, CI).
- `data/results/regression_analysis.json`: Regression coefficients and diagnostics.
- `data/results/robustness_analysis.json`: Modality-specific results.
- `data/validation_report.json`: Data validation status.

## Testing

Run unit tests:
```bash
python -m pytest code/tests/unit/
```

Run integration tests:
```bash
python -m pytest code/tests/integration/
```

Run contract tests:
```bash
python -m pytest code/tests/contract/
```

## Dependencies

See `requirements.txt` for the full list of pinned dependencies:
- pandas
- numpy
- scikit-learn
- scipy
- statsmodels
- matplotlib
- seaborn
- requests
- pyyaml
- pybids

## License

This project is for research purposes only.