# Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

## Project Overview
This project implements an automated pipeline to analyze Discrete Element Method (DEM) simulation data, extract contact network topology, calculate energy dissipation metrics, and perform statistical correlation analysis.

## Quick Start

### Prerequisites
- Python 3.11+
- Dependencies listed in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Running the Pipeline
The main entry point is `code/main.py`.

```bash
python code/main.py --input <path_to_dem_output> --output <output_directory>
```

**Arguments:**
- `--input`: Path to the raw DEM output file (e.g., `.log` or `.csv` from YADE).
- `--output`: Directory where processed metrics and results will be written.
- `--help`: Display available arguments and usage information.

## Automated Validation Gate: Reference-Validator Agent

This project utilizes an automated `Reference-Validator Agent` to ensure data integrity and code correctness before finalizing any analysis.

### Invocation Parameters

To trigger the validation gate, run the following command after the main pipeline execution:

```bash
python code/main.py --input <path_to_dem_output> --output <output_directory> --validate
```

**Key Flags:**
- `--validate`: Activates the Reference-Validator Agent. This flag performs:
 1. Schema verification of `data/processed/metrics.csv` against `contracts/dataset.schema.yaml`.
 2. Statistical sanity checks (e.g., ensuring no NaN values in critical metric columns).
 3. Verification that `results/regression_summary.json` contains valid confidence intervals.
 4. Execution of the `Reference-Validator Agent` logic to confirm "Constitution Principle II" compliance.

### Exit Codes

The `Reference-Validator Agent` and the main pipeline script return the following exit codes:

| Code | Meaning | Description |
|:--- |:--- |:--- |
| `0` | **Success** | All validation checks passed. Output artifacts are verified and ready for downstream use. |
| `1` | **General Error** | A runtime error occurred (e.g., file not found, invalid arguments). Check stderr for details. |
| `2` | **Validation Failed** | The `Reference-Validator Agent` detected schema mismatches, missing data, or statistical anomalies. The pipeline did not complete successfully. |
| `3` | **Memory Threshold Exceeded** | Subsampling was triggered (via `check_subsample_trigger`), but the process failed to handle the large dataset within the 6GB RAM limit. |
| `4` | **Data Quality Critical** | More than 50% of contacts were missing in a timestep, leading to exclusion of critical data segments. |

### Example Usage

```bash
# Run full pipeline and validation
python code/main.py --input data/raw/simulation_01.log --output results/experiment_1 --validate

# Check exit code
echo $?
# Expected output: 0 (if validation passes)
```

## Project Structure

```text
.
├── code/
│ ├── __init__.py
│ ├── main.py # CLI Entry point
│ ├── utils.py # Memory estimation and subsampling logic
│ ├── extract.py # YADE parser and metric calculation
│ └── analyze.py # Statistical correlation and regression
├── data/
│ ├── raw/ # Input DEM files
│ └── processed/ # Generated metrics.csv
├── results/
│ ├── regression_summary.json
│ └── figures/ # Generated plots
├── tests/
│ ├── unit/
│ └── integration/
├── contracts/
│ ├── dataset.schema.yaml
│ └── results.schema.yaml
├── requirements.txt
└── README.md
```

## License
[Insert License Here]