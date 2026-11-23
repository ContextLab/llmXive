# The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Project Overview

This project implements an automated scientific pipeline to analyze the effect of simulated social rejection (Cyberball task) on neural and behavioral responses to positive feedback. The pipeline supports two experimental designs:
1. **Within-Subjects**: Single-cohort datasets where participants complete both rejection and reward tasks.
2. **Between-Subjects**: Separate datasets for rejection and reward tasks, analyzed independently.

**CRITICAL**: Merging distinct studies is strictly forbidden. The pipeline automatically detects the design type and adjusts statistical methods accordingly.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- 7 GB+ available RAM (recommended)

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-258-the-effect-of-simulated-social-rejection
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

### Dependencies

The project requires the following Python packages (see `code/requirements.txt`):
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `scipy`: Statistical functions
- `statsmodels`: Statistical modeling and tests
- `pyyaml`: Configuration file handling
- `requests`: HTTP library for data downloads
- `psutil`: System and process monitoring
- `scikit-learn`: Machine learning utilities (if needed)

## Data Sources

This project uses real, publicly available neuroimaging and behavioral datasets from OpenNeuro:

1. **Cyberball Task (Social Rejection)**
 - Dataset: ds000208
 - URL: https://openneuro.org/datasets/ds000208
 - Description: fMRI data from participants playing Cyberball, a virtual ball-tossing game used to simulate social exclusion.

2. **Reward Task (Positive Feedback)**
 - Dataset: ds003392
 - URL: https://openneuro.org/datasets/ds003392
 - Description: fMRI data from participants performing a reward-based task with positive feedback conditions.

**Citation**:
- OpenNeuro datasets are cited according to their DOIs and associated publications. Please refer to the dataset pages for specific citation requirements.
- Cyberball paradigm: Williams, K. D., et al. (2000). "Ostracism: A temporal need-threat model." *Advances in Experimental Social Psychology*.

## Usage Instructions

### Running the Pipeline

The pipeline is executed sequentially through its main stages:

1. **Data Ingestion** (User Story 1)
 ```bash
 python code/ingest.py
 ```
 This script:
 - Checks available memory before downloading
 - Attempts to find a single-cohort dataset (Within-Subjects design)
 - Falls back to separate datasets (Between-Subjects design) if single-cohort is unavailable
 - Validates data schemas and generates manifest files
 - Outputs: `data/raw/dataset_manifest.json`, `data/interim/validation_report.json`, `data/processed/id_match_status.json`, `data/processed/metadata.json`

2. **Preprocessing** (User Story 2)
 ```bash
 python code/preprocess.py
 ```
 This script:
 - Cleans behavioral data
 - Normalizes reaction times
 - Detects and handles outliers using IQR method
 - Extracts summary features (mean RT, avg mood)
 - Outputs: `data/interim/preprocessed_data.csv`

3. **Statistical Analysis** (User Story 3)
 ```bash
 python code/analysis.py
 ```
 This script:
 - Selects appropriate ANOVA type based on design (Mixed vs. One-Way)
 - Applies Benjamini-Hochberg FDR correction
 - Performs sensitivity analysis across α levels {0.01, 0.05, 0.1}
 - Handles convergence warnings for small sample sizes
 - Outputs: `data/processed/final_results.json`, `data/processed/sensitivity_results.json`

4. **Report Generation** (User Story 3)
 ```bash
 python code/report.py
 ```
 This script:
 - Generates the final research report in Markdown format
 - Includes sensitivity tables and effect size confidence intervals
 - Explicitly labels Between-Subjects results as "associational"
 - Outputs: `reports/final_report.md`

### Running Tests

Execute the test suite to verify implementation:
```bash
python -m pytest tests/ -v
```

### Performance Monitoring

The pipeline includes built-in memory monitoring. To benchmark performance:
```bash
python code/performance_monitor.py
```
Output: `data/processed/performance_log.json`

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── config.py # Configuration management
│ ├── data_model.py # Data entities and schemas
│ ├── ingest.py # Data ingestion and validation
│ ├── preprocess.py # Data cleaning and feature extraction
│ ├── analysis.py # Statistical analysis
│ ├── report.py # Report generation
│ ├── performance_monitor.py
│ └── requirements.txt
├── data/
│ ├── raw/ # Downloaded datasets and manifests
│ ├── interim/ # Intermediate processed data
│ └── processed/ # Final analysis results
├── tests/
│ ├── test_ingest.py
│ ├── test_preprocess.py
│ └── test_analysis.py
├── reports/
│ └── final_report.md
├── docs/
│ └── api.md
└── README.md
```

## Design Type Determination

The pipeline automatically determines the experimental design:

- **Within-Subjects**: Detected when a single dataset contains both Cyberball and Reward tasks for the same participants.
 - Statistical method: Mixed ANOVA
 - Claim: Can test for "modulation" of reward responses by prior rejection

- **Between-Subjects**: Used when rejection and reward data come from separate datasets.
 - Statistical method: One-Way ANOVA
 - Claim: Limited to "associational group differences" (no causal modulation claims)

The design type is logged in `data/processed/metadata.json` and explicitly stated in the final report.

## Memory Constraints

The pipeline enforces a 7 GB RAM limit:
- Pre-download memory estimation (T015a)
- Runtime memory monitoring (T015b)
- Automatic halting with exit code 1 if limits are exceeded

## Error Handling

- **Data Unavailable**: If no valid datasets are found, the pipeline halts with a clear error message.
- **Convergence Warnings**: For small sample sizes (N < 30), the pipeline outputs effect size confidence intervals.
- **Schema Validation**: Missing required columns trigger immediate failure with detailed reports.

## Contributing

1. Ensure all tests pass before committing
2. Follow the existing code structure and naming conventions
3. Update documentation when adding new features
4. Never fabricate data or results

## License

This project is open source and available under the MIT License.

## Acknowledgments

- OpenNeuro for providing free, open access to neuroimaging datasets
- The Cyberball research community for developing the social rejection paradigm
- Contributors to the scientific Python ecosystem (pandas, scipy, statsmodels)