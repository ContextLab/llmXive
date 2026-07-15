# PROJ-015: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## Overview
This project implements a research pipeline to evaluate the efficacy of Explainable AI (XAI) interfaces versus traditional interfaces for users with disabilities. The system supports a standardized usability testing protocol, data collection, statistical analysis, and reproducible reporting.

## Features
- **Simulator**: Renders Traditional and Explainable interface variants with configurable XAI overlays.
- **Data Collection**: Captures completion time, error counts, SUS scores, and explanation engagement time.
- **Counterbalancing**: Implements Latin Square design for interface sequence assignment.
- **Statistical Analysis**: Performs Shapiro-Wilk, Repeated Measures ANOVA, and Holm-Bonferroni corrections.
- **Visualization**: Generates publication-quality box plots and summary reports.

## Project Structure
```
PROJ-015-improving-accessibility-and-usability-of/
├── code/
│ ├── analysis/ # Statistical analysis, visualization, reporting
│ ├── config/ # Environment and study configuration
│ ├── models/ # Data models (Participant, Session, Metric)
│ ├── setup/ # Project initialization utilities
│ ├── simulator/ # Interface renderers, data collection, session logging
│ ├── utils/ # Checksum, logging, seeding, performance optimization
│ └── validation/ # Quickstart validation scripts
├── data/
│ ├── raw/ # Immutable raw session logs (JSON)
│ └── processed/ # Aggregated metrics, descriptive stats, reports
├── docs/
│ ├── user_guide.md # User guide for the simulator and analysis pipeline
│ └── api_reference.md # API reference for core modules
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Installation
1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. (Optional) Set up linting and formatting:
 ```bash
 python code/setup/configure_linting.py
 ```

## Usage

### Running the Simulator
Launch the Streamlit application to conduct usability tests:
```bash
streamlit run code/simulator/app.py
```
The simulator supports:
- Participant registration with disability type and interface sequence.
- Task execution on Traditional and Explainable interfaces.
- Real-time metric collection (time, errors, SUS, engagement).
- Session logging to `data/raw/session_{id}.json` with checksums.

### Running the Analysis Pipeline
After data collection, run the analysis pipeline:
```bash
python code/analysis/run_analysis.py
```
This script:
1. Cleans raw data (filters incomplete sessions, imputes SUS).
2. Computes descriptive statistics.
3. Performs statistical tests (ANOVA, Shapiro-Wilk).
4. Generates visualizations and summary reports.
5. Outputs results to `data/processed/`.

### Reproducible Reporting
Execute the master Jupyter notebook for end-to-end reproducibility:
```bash
jupyter notebook code/analysis.ipynb
```
The notebook covers data loading, cleaning, analysis, visualization, and reporting.

## Configuration
Study parameters are managed via `code/config/settings.py`. Key settings include:
- `STUDY_SEED`: Random seed for reproducibility.
- `DATA_DIR`: Base directory for data storage.
- `INTERFACE_VARIANTS`: List of interface types to test.
- `SUS_IMPUTATION_THRESHOLD`: Maximum missing items allowed for SUS imputation.

## Data Schema
- **Raw Sessions**: `data/raw/session_{id}.json` containing participant details, interface sequence, and per-task metrics.
- **Processed Metrics**: `data/processed/metrics_summary.csv` with statistical test results.
- **Descriptive Stats**: `data/processed/descriptive_stats.csv` with means and standard deviations.
- **Reports**: `data/processed/report_summary.txt` summarizing N, power flags, and exclusion reasons.

## Testing
Run unit tests for statistical functions:
```bash
python -m pytest tests/unit/test_stat_utils.py -v
```
Validate the quickstart workflow:
```bash
python code/validation/validate_quickstart.py
```

## Contributing
1. Fork the repository.
2. Create a feature branch.
3. Ensure all tests pass and linting/formatting checks are satisfied.
4. Submit a pull request.

## License
[Insert License Here]

## Acknowledgments
This project implements research protocols for accessibility and usability studies, adhering to best practices in statistical analysis and reproducible research.
