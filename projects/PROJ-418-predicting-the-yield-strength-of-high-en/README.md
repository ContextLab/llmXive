# Predicting the Yield Strength of High‑Entropy Alloys

**Project ID:** PROJ-418-predicting-the-yield-strength-of-high-en

This repository contains the end‑to‑end pipeline for predicting the yield strength of high‑entropy alloys (HEAs) from compositional descriptors. The workflow covers data acquisition, descriptor engineering, model training, statistical validation, and reproducible reporting.

---

## Table of Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Data Requirements](#data-requirements)
- [Running the Full Pipeline](#running-the-full-pipeline)
- [Outputs](#outputs)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

```bash
# Clone the repository
git clone
cd PROJ-418-predicting-the-yield-strength-of-high-en

# Create a virtual environment (optional but recommended)
python -m venv.venv
source.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

The project requires Python 3.9+ and the packages listed in `requirements.txt`. All random seeds are fixed for reproducibility.

---

## Quickstart

The `quickstart.md` file provides a step‑by‑step walkthrough of the pipeline. In brief:

1. **Provide the raw dataset** (see [Data Requirements](#data-requirements)).
2. Run the data pipeline:
 ```bash
 python code/data/pipeline.py
 ```
3. Train models:
 ```bash
 python code/models/train.py
 ```
4. Evaluate and generate the final report:
 ```bash
 python code/models/evaluate.py
 python code/models/report_generator.py
 ```

After successful execution you will find:

- Processed descriptor table: `data/processed/hea_descriptors.csv`
- Model metrics: `output/metrics.json`
- VIF diagnostics: `output/vif_results.json`
- Permutation‑importance results: `output/permutation_results.json`
- Final report: `output/report.md`

---

## Data Requirements

### User‑Provided Dataset

The pipeline **does not download** any raw HEA data automatically.
You must supply a CSV file containing the original high‑entropy alloy compositions and their experimentally measured yield strengths.

- **Expected location:** `data/raw/heas_raw.csv`
- **Required columns:**
 - `composition` (string, e.g., `"FeCoNiCrMn"`)
 - `yield_strength` (numeric)
 - `unit` (optional, either `"MPa"` or `"GPa"`; if omitted, MPa is assumed)
- **File format:** Standard comma‑separated values with a header row.

#### Exact error message if the file is missing

The data downloader (`code/data/download.py`) validates the presence of this file **before** any processing begins.
If the file cannot be found, the script raises a `FileNotFoundError` with the following exact message:

```
FileNotFoundError: data/raw/heas_raw.csv not found. Please provide the dataset file at the specified location before running the pipeline.
```

**Do not** rename, move, or delete `data/raw/heas_raw.csv` after placing it, otherwise the pipeline will abort with the error above.

---

## Running the Full Pipeline

Once the dataset is in place, execute the orchestrated pipeline:

```bash
python code/data/pipeline.py # Data download → preprocessing → descriptor calculation
python code/models/train.py # Model training (Linear Regression, Random Forest, Gradient Boosting)
python code/models/evaluate.py # Evaluation, VIF, permutation importance, bootstrap, etc.
python code/models/report_generator.py # Generates `output/report.md`
```

Each script writes its own status and runtime logs under the `output/` directory. The pipeline is designed to complete within a two‑hour wall‑clock limit; exceeding this limit will raise an `AssertionError`.

---

## Outputs

| Artifact | Description |
|----------|-------------|
| `data/processed/hea_descriptors.csv` | Descriptor table for each composition |
| `output/data_status.json` | Summary of processed rows, warnings, and timestamps |
| `output/vif_results.json` | Variance Inflation Factor diagnostics |
| `output/permutation_results.json` | Permutation‑importance scores with Holm‑Bonferroni‑corrected p‑values |
| `output/bootstrap_results.json` | 95 % confidence intervals for key performance metrics |
| `output/metrics.json` | Model performance (R², MAE, RMSE, Pearson r, etc.) |
| `output/report.md` | Full reproducibility report (includes mandatory disclaimer) |
| `outputs/manifest.json` | Provenance manifest with seeds, hyper‑parameters, versions, and checksums |

All output files are version‑controlled by the project state file `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml`.

---

## Contributing

Contributions are welcome! Please follow the contribution guidelines in `CONTRIBUTING.md`. Ensure that any new code passes the existing unit and integration tests (`tests/` directory) and that the documentation (including this README) remains up‑to‑date.

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.