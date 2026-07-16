# The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Project Overview

This project investigates how simulated social rejection (via the Cyberball paradigm) modulates neural and behavioral responses to positive feedback (reward processing). The analysis pipeline supports two experimental designs:
1. **Within-Subjects**: Single-cohort datasets containing both Cyberball and Reward tasks.
2. **Between-Subjects**: Composite strategy matching participant IDs across distinct datasets (ds000208 for rejection, ds003392 for reward).

## Key Features

- **Dual-Design Support**: Automatically detects data availability and switches between Mixed ANOVA (Within-Subjects) and One-Way ANOVA (Between-Subjects).
- **Robust Preprocessing**: IQR-based outlier detection, reaction time normalization, and feature extraction.
- **Statistical Rigor**: Benjamini-Hochberg FDR correction, sensitivity analysis across alpha thresholds, and effect size confidence intervals.
- **Memory Safety**: Runtime RAM monitoring with automatic halting if thresholds are exceeded.
- **Traceability**: Checksums for raw data integrity, design-switch logging, and "associational" framing for Between-Subjects results.

## Project Structure

```
.
├── code/ # Core implementation
│ ├── __init__.py
│ ├── config.py # Paths, seeds, alpha thresholds
│ ├── data_model.py # Dataset, PreprocessedRecord, AnalysisResult entities
│ ├── ingest.py # Data download, validation, design determination
│ ├── preprocess.py # Cleaning, normalization, outlier detection
│ ├── analysis.py # ANOVA execution, FDR, sensitivity sweep
│ ├── report.py # Report generation, phrasing enforcement
│ └── logging_utils.py # Memory tracking utilities
├── data/
│ ├── raw/ # Downloaded datasets, checksums.json
│ ├── interim/ # Preprocessed data (preprocessed_data.csv)
│ └── processed/ # Final results (final_results.json)
├── tests/ # Unit and integration tests
│ ├── test_ingest.py
│ ├── test_preprocess.py
│ ├── test_analysis.py
│ └── test_report.py
├── docs/ # Documentation
│ ├── design.md # Design decisions
│ └── api.md # API reference
├── reports/ # Generated reports
│ └── final_report.md
├── requirements.txt # Python dependencies
└── README.md
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-258-the-effect-of-simulated-social-rejection
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

Execute the pipeline from the project root:

```bash
python code/ingest.py && \
python code/preprocess.py && \
python code/analysis.py && \
python code/report.py
```

### Individual Scripts

- **Data Ingestion**:
 ```bash
 python code/ingest.py
 ```
 Downloads datasets, validates schemas, determines design type, and saves checksums.

- **Preprocessing**:
 ```bash
 python code/preprocess.py
 ```
 Cleans data, normalizes reaction times, detects outliers, and extracts features.

- **Analysis**:
 ```bash
 python code/analysis.py
 ```
 Runs ANOVA (Mixed or One-Way), applies FDR correction, and performs sensitivity sweeps.

- **Reporting**:
 ```bash
 python code/report.py
 ```
 Generates `reports/final_report.md` and `data/processed/final_results.json`.

### Running Tests

```bash
pytest tests/ -v
```

## Design Determination Logic

The pipeline follows a strict decision tree:

1. **Attempt Single-Cohort**: Check if a dataset contains both Cyberball and Reward tasks with consistent Participant IDs.
 - If found: `design_type = "Within-Subjects"` → Use Mixed ANOVA.
2. **Fallback to Composite**: If single-cohort fails, attempt to match IDs between ds000208 (rejection) and ds003392 (reward).
 - If matching IDs exist: `design_type = "Between-Subjects"` → Use One-Way ANOVA.
 - If no match: Halt with exit code 1 ("Data Unavailable").

**Note**: For Between-Subjects designs, the report explicitly uses "associational" phrasing and excludes causal claims.

## Configuration

Edit `code/config.py` to modify:
- Random seeds (`RANDOM_SEED`)
- Alpha thresholds (`ALPHA_THRESHOLDS = {0.01, 0.05, 0.1}`)
- Memory limits (`MEMORY_LIMIT_GB`)
- Dataset URLs

## Output Artifacts

| File | Description |
|------|-------------|
| `data/raw/checksums.json` | SHA-256 hashes of raw data files |
| `data/interim/preprocessed_data.csv` | Cleaned, normalized, outlier-flagged data |
| `data/processed/final_results.json` | ANOVA results, p-values, effect sizes, FDR-corrected p-values |
| `reports/final_report.md` | Human-readable report with design-appropriate phrasing |

## Limitations

- **Convergence Warnings**: If N < 30, the pipeline issues a warning and reports wider confidence intervals for effect sizes.
- **Data Availability**: If neither single-cohort nor composite strategies yield valid data, the pipeline halts with a clear error.
- **Memory Constraints**: Execution halts if RAM usage exceeds the configured threshold (default: 7 GB).

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Cyberball paradigm developers
- OpenNeuro dataset contributors (ds000208, ds003392)
- Statsmodels and SciPy communities
