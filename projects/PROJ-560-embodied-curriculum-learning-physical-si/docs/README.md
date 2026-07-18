# Embodied Curriculum Learning: Physical Simulation for Abstract Concept Teaching

## Overview

This project implements a statistical analysis pipeline to evaluate the efficacy of embodied curriculum learning methods compared to static instruction for teaching abstract concepts. The system processes educational data, calculates learning gains, performs statistical inference, and conducts sensitivity analysis.

**Important**: All statistical findings in this project are framed as **associational** in nature. No causal claims are made regarding the "teaching" effect. The analysis identifies correlations between instruction types and learning outcomes.

## Project Structure

```
code/
├── requirements.txt # Python dependencies
├── src/
│ ├── __init__.py
│ ├── cli.py # Command-line interface
│ ├── data_loader.py # Data loading and validation
│ ├── logging_config.py # Logging setup
│ ├── models.py # Data structures (DatasetRecord, AnalysisResult, SensitivitySweep)
│ ├── results_aggregator.py # Result aggregation and JSON output
│ ├── sensitivity.py # Sensitivity analysis and robustness checks
│ ├── stats_engine.py # Statistical tests (t-test, effect size, power)
│ ├── synthetic_gen.py # Synthetic data generation for validation
│ └── utils.py # Utilities (seed management)
└── tests/
 ├── test_data_loader.py
 ├── test_models.py
 ├── test_sensitivity.py
 ├── test_stats_engine.py
 ├── test_synthetic_gen.py
 └──...

data/
├── raw/ # Raw input data (CSV/JSON)
├── processed/ # Processed data and analysis results
├── synthetic/ # Synthetic datasets and mapping logs
└── derivation_logs/ # Logs of skipped records and processing details

state/
└── projects/PROJ-560-embodied-curriculum-learning-physical-si/
```

## Installation

1. Ensure Python 3.11+ is installed.
2. Navigate to the `code/` directory.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies**:
- `pandas`: Data manipulation
- `scipy`: Statistical functions (t-tests, etc.)
- `statsmodels`: Additional statistical tools
- `numpy`: Numerical operations
- `pyyaml`: Configuration handling
- `ruff`: Linting
- `black`: Code formatting
- `pytest`: Testing

## Usage

### Running the Analysis

The CLI supports two primary modes: `secondary_analysis` (real data) and `synthetic` (generated data).

**Secondary Analysis Mode**:
```bash
python code/src/cli.py --mode=secondary_analysis --input=data/raw/my_dataset.csv
```

**Synthetic Generation Mode**:
```bash
python code/src/cli.py --mode=synthetic --sample-size=1000 --seed=42
```

**Sensitivity Sweep**:
```bash
python code/src/cli.py --mode=secondary_analysis --input=data/raw/my_dataset.csv --sweep_thresholds=0.05,0.01,0.001
```

### Command-Line Arguments

- `--mode`: Analysis mode (`secondary_analysis` or `synthetic`)
- `--input`: Path to input CSV/JSON file (required for `secondary_analysis`)
- `--sweep_thresholds`: Comma-separated list of significance thresholds for sensitivity analysis
- `--seed`: Random seed for reproducibility (default: 42)
- `--sample-size`: Number of samples to generate (for `synthetic` mode)

## Data Processing

### Input Data Requirements

The system expects input data (CSV or JSON) with the following columns:
- `pre_test_score`: Pre-intervention score
- `post_test_score`: Post-intervention score
- `instruction_type`: Type of instruction (e.g., "embodied", "static")
- `covariates`: Optional dictionary or JSON string of covariates

**Automatic Fallback**:
If `instruction_type` is missing in the public dataset, the system automatically invokes the `SyntheticDataGenerator` to create a labeled dataset, ensuring deterministic processing without manual intervention (FR-008).

### Gain Score Calculation

Learning gain is calculated as:
```
gain = post_test_score - pre_test_score
```

Rows with missing values in `pre_test_score` or `post_test_score` are excluded and logged to `data/derivation_logs/skipped_records.log`.

## Statistical Methods

### T-Tests

The system performs independent samples t-tests to compare mean gain scores between instruction groups.
- **Levene's Test**: Used to determine if variances are equal.
- **Student's t-test**: Used if variances are equal.
- **Welch's t-test**: Used if variances are unequal.

### Effect Size

Cohen's d is calculated to measure the magnitude of the difference:
```
d = (mean_group1 - mean_group2) / pooled_std
```

### Bonferroni Correction

When testing multiple concepts, the significance threshold is adjusted to control the family-wise error rate:
```
alpha_corrected = alpha / number_of_tests
```

### Power Analysis

Achieved power is calculated to assess the probability of detecting an effect if it exists. Results with power < 0.80 are flagged as "underpowered".

### Collinearity Check

The system checks for multicollinearity among predictors (|r| > 0.8) and reports diagnostics.

## Sensitivity Analysis

A sensitivity sweep iterates over multiple significance thresholds (e.g., 0.05, 0.01, 0.001) to demonstrate the robustness of the headline effect size.
- If the number of samples (N) is less than 30, the sweep is skipped, and a warning is issued.
- If the effect size drops below a substantively meaningful threshold at any point, a `robustness_warning` is set to `true`.

## Associational Framing

**Critical Note**: All statistical findings are explicitly labeled as **associational**. The analysis identifies correlations between instruction types and learning outcomes but does not claim causation. The system output includes methodological caveats to prevent misinterpretation of results as causal effects (FR-003).

## Logging

The system uses Python's `logging` module to record:
- Data loading events
- Skipped records (missing values)
- Synthetic generation parameters
- Statistical test results

Logs are written to `data/derivation_logs/`.

## Testing

Run the test suite with:
```bash
cd code
pytest
```

Tests cover:
- Data validation
- Statistical engine logic (t-tests, effect size, power)
- Sensitivity sweep logic
- Synthetic data generation schema

## License

This project is part of the llmXive automated science pipeline.
