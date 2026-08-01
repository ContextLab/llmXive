# The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Project Overview

This research project investigates the effect of nostalgia induction on cognitive flexibility in adults aged 65 and older. Using data from established executive function tasks (WCST variants), we analyze whether nostalgia-inducing stimuli lead to improved performance compared to control conditions.

## Key Findings

- **Primary Analysis**: Welch's independent samples t-test comparing nostalgia vs. control groups on perseverative errors and categories completed.
- **Effect Sizes**: Cohen's d calculated with 95% confidence intervals.
- **Robustness**: Sensitivity analysis across multiple significance thresholds and MMSE-based exclusion criteria.
- **Statistical Power**: Minimum Detectable Effect Size (MDES) calculated for observed effects.

## Repository Structure

```
.
├── code/ # Python implementation
│ ├── __init__.py
│ ├── analysis.py # Statistical analysis functions
│ ├── config.py # Configuration management
│ ├── ingestion.py # Data loading and validation
│ ├── reference_validator.py # Citation validation
│ ├── schema_generator.py # Schema generation
│ ├── setup_dirs.py # Directory initialization
│ ├── utils.py # Utility functions
│ ├── task_t014a_create_cleaned_dataset.py
│ ├── task_t014b_validity_metrics.py
│ ├── task_t015_stimulus_integrity.py
│ ├── task_t020_effect_sizes.py
│ ├── task_t021_power_analysis.py
│ ├── task_t022_generate_report.py
│ ├── task_t027_robustness_check.py
│ ├── task_t029_threshold_sensitivity.py
│ └── task_t030_final_report.py
├── data/
│ ├── raw/ # Raw dataset files
│ ├── processed/ # Cleaned and validated data
│ ├── results/ # Analysis outputs
│ └── stimuli/ # Stimulus materials
├── docs/ # Documentation
├── specs/ # Feature specifications
├── contracts/ # Data schemas
├── tests/ # Test suite
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration (ruff, black)
└── README.md # This file
```

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running the Pipeline

1. **Setup Directories**:
 ```bash
 python code/setup_dirs.py
 ```

2. **Data Ingestion** (US1):
 ```bash
 python code/ingestion.py
 ```

3. **Statistical Analysis** (US2):
 ```bash
 python code/analysis.py
 ```

4. **Sensitivity Analysis** (US3):
 ```bash
 python code/analysis.py --sensitivity
 ```

5. **Generate Final Report**:
 ```bash
 python code/task_t030_final_report.py
 ```

## Configuration

Environment variables (via `.env` or system):

- `DATA_SOURCE_URL`: URL to fetch raw data
- `MMSE_THRESHOLD`: Minimum MMSE score for inclusion (default: 24)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## Statistical Methods

- **Primary Test**: Welch's independent samples t-test (between-subjects design)
- **Effect Size**: Cohen's d with 95% CI
- **Correction**: Bonferroni for multiple comparisons
- **Power Analysis**: Post-hoc power and MDES calculation
- **Sensitivity**: Threshold sweep (α ∈ {0.01, 0.05, 0.1})

## Data Sources

Data is sourced from publicly available repositories (OpenML/HuggingFace) containing WCST performance metrics. All data is validated against schema contracts before processing.

## Validation & Quality Assurance

- **Schema Validation**: All datasets validated against `dataset.schema.yaml`
- **Citation Verification**: References validated via DOI/URL fetch
- **Stimulus Integrity**: SHA-256 checksum verification for stimulus files
- **Exclusion Logging**: Detailed logging of all excluded records

## Output Artifacts

- `data/processed/cleaned_dataset.csv`: Validated participant data
- `data/processed/exclusion_log.json`: Record exclusion details
- `data/processed/validity_metrics.json`: Data quality metrics
- `data/results/statistical_report.json`: Full statistical analysis
- `data/results/sensitivity_report.json`: Robustness check results
- `paper/001_results.md`: Final research paper draft

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Contributing

This is a research pipeline. All changes should maintain reproducibility and data integrity.

## License

Research use only. See LICENSE for details.