# The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

Automated research pipeline for analyzing the relationship between nostalgia stimuli and cognitive flexibility metrics (WCST) in adults aged 65+.

## Project Structure

```
.
├── code/ # Python implementation modules
│ ├── analysis.py # Statistical analysis (Welch's t-test, effect sizes)
│ ├── config.py # Configuration management
│ ├── ingestion.py # Data fetching and preprocessing
│ ├── utils.py # Utility functions (logging, checksums)
│ └──... # Task-specific scripts
├── data/
│ ├── raw/ # Raw fetched datasets
│ ├── processed/ # Cleaned and filtered datasets
│ ├── results/ # Statistical reports and outputs
│ └── stimuli/ # Audio stimuli files
├── contracts/ # Data schemas
├── tests/ # Unit and integration tests
├── paper/ # Generated research paper
└── specs/ # Project specifications
```

## Prerequisites

- Python 3.9+
- pip

## Installation

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` includes:
 - `pandas`, `numpy`, `scipy`, `statsmodels` (data analysis)
 - `datasets`, `openml` (data fetching)
 - `pyyaml`, `requests` (configuration and networking)
 - `pytest`, `black`, `ruff` (testing and linting)

3. **Verify setup**
 ```bash
 python -m pytest tests/unit/ -v
 ```

## Usage

### Quick Start

Run the full pipeline to ingest data, clean it, and perform statistical analysis:

```bash
python code/main.py
```

This script will:
1. Fetch data from the canonical source (or fallback to simulation if unreachable).
2. Validate and filter the dataset (age ≥ 65, score validity, optional MMSE).
3. Run Welch's t-tests and calculate effect sizes.
4. Generate `data/results/statistical_report.json`.

### Running Specific Tasks

- **Data Ingestion**:
 ```bash
 python code/ingestion.py
 ```
 Produces `data/raw/raw_dataset.csv` and `data/processed/cleaned_dataset.csv`.

- **Statistical Analysis**:
 ```bash
 python code/analysis.py
 ```
 Requires `data/processed/cleaned_dataset.csv` to exist. Outputs `data/results/statistical_report.json`.

- **Sensitivity Analysis**:
 ```bash
 python code/task_t028_sensitivity_report.py
 ```

### Output Artifacts

After successful execution, check these files:

- `data/processed/cleaned_dataset.csv`: Final analysis-ready dataset.
- `data/results/statistical_report.json`: P-values, effect sizes, power analysis.
- `data/results/sensitivity_report.json`: Robustness check results.
- `paper/001_results.md`: Generated research summary.

## Configuration

Environment variables (optional):
- `DATA_SOURCE_URL`: Override canonical data source.
- `MMSE_THRESHOLD`: Default 24 for cognitive impairment cutoff.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Run specific test categories:
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- Contract tests: `pytest tests/contract/`

## Contributing

1. Ensure code passes `black` and `ruff` checks.
2. Add tests for new features.
3. Update `README.md` if adding new CLI commands.

## License

MIT License. See LICENSE file for details.