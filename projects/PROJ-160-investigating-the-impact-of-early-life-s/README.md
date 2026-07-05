# Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

This project implements an automated scientific pipeline to investigate the association between early-life stress (measured by Adverse Childhood Experiences - ACE scores) and hippocampal subfield volumes (CA3, DG, Subiculum) using data from the ABCD Study Release 4.0.

The pipeline includes data acquisition, preprocessing, statistical modeling (Linear Mixed-Effects Models), and robustness validation (permutation tests, sensitivity analysis).

## Prerequisites

- Python 3.9+
- pip
- Virtual environment tool (venv)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project root:
 ```bash
 cd projects/PROJ-160-investigating-the-impact-of-early-life-s
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical modeling and robustness checks
│ ├── data/ # Data acquisition and preprocessing
│ ├── config.py # Configuration constants and paths
│ ├── main.py # Pipeline entry point
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data (ABCD)
│ └── processed/ # Cleaned and normalized datasets
├── tests/ # Test suites
├── contracts/ # Data schemas and validation rules
├── specs/ # Design documents and specifications
├── requirements.txt # Python dependencies
└── README.md
```

## Usage

The pipeline is designed to run sequentially through three main phases: Data Acquisition, Modeling, and Robustness Validation.

### 1. Data Acquisition and Preprocessing

This phase downloads the necessary ABCD data files, filters for quality, normalizes volumes, and generates a cleaned dataset.

```bash
python code/main.py --phase acquisition
```

This will:
- Download phenotypic and subcortical segmentation data from the ABCD portal.
- Filter participants with missing ACE scores or poor MRI quality.
- Normalize hippocampal subfield volumes by Intracranial Volume (ICV).
- Output: `data/processed/cleaned_dataset.csv`

### 2. Statistical Modeling

This phase fits Linear Mixed-Effects Models (LMM) to test the association between ACE scores and hippocampal subfield volumes, controlling for age, sex, scanner site, and family structure.

```bash
python code/main.py --phase modeling
```

This will:
- Fit LMMs for CA3, DG, and Subiculum volumes.
- Calculate CA3:DG volume ratio and fit an exploratory model.
- Apply Bonferroni correction for multiple comparisons.
- Output: `data/processed/model_results.json` and `data/processed/model_results_summary.csv`

### 3. Robustness Validation

This phase performs non-parametric permutation tests and sensitivity analyses to validate the robustness of the findings.

```bash
python code/main.py --phase robustness
```

This will:
- Run 5,000 cluster-level permutations (permuting family_id).
- Perform sensitivity analysis across different alpha thresholds.
- Conduct ICV-restricted analysis to check effect stability.
- Output: `data/processed/robustness_report.json` and `data/processed/sensitivity_report.csv`

### Run the Full Pipeline

To execute the entire pipeline from acquisition to robustness:

```bash
python code/main.py
```

## Configuration

Configuration options (random seeds, paths, thresholds) are managed in `code/config.py` and `code/config_env.py`.

- **Random Seeds**: Set in `code/config.py` for reproducibility.
- **Alpha Thresholds**: Configurable in `code/config_env.py` (default: 0.01, 0.05, 0.1).
- **Permutation Count**: Set via `get_permutation_count()` in `code/config_env.py`.

## Testing

Run the test suite to verify contract, integration, and unit tests:

```bash
pytest tests/ -v
```

## Data Requirements

This project requires access to the ABCD Study Release 4.0. Ensure you have the necessary credentials and permissions to download the data. The acquisition script (`code/data/acquisition.py`) handles the download from the official portal.

## License

This project is part of the llmXive automated science pipeline. See the LICENSE file for details.

## Contributing

Please refer to the project's contribution guidelines in the `specs/` directory.