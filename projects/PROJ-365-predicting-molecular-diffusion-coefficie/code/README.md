# Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

This repository implements a full end‑to‑end pipeline for predicting diffusion
coefficients of solutes in liquids using graph neural networks (GNNs) and a
linear‑regression baseline. The code is organized into three major phases:

1. **Data acquisition & validation** – download a real diffusion dataset from
 NIST TRC (or Zenodo) or generate a synthetic fallback.
2. **Featurization** – convert SMILES strings to RDKit graphs, compute solvent
 descriptors, and store the processed data as a JSON‑Lines file.
3. **Model training & evaluation** – train a single‑layer Message Passing Neural
 Network (MPNN) and a linear‑regression baseline, perform cross‑validation,
 statistical testing, sensitivity analysis, and robustness checks.

---

## Repository layout

```
.
├─ code/ # Python source code
│ ├─ ingestion/ # Data download, validation, featurisation
│ ├─ models/ # MPNN and baseline implementations
│ ├─ training/ # CV strategy, training loop, evaluation, analysis
│ ├─ utils/ # Config, logging, monitoring, safety helpers
│ └─ README.md # ← this file
├─ data/
│ ├─ raw/ # `dataset.csv` (real or synthetic)
│ ├─ processed/ # `featurized.jsonl`
│ ├─ artifacts/ # Model checkpoints, reports, summary JSONs
│ ├─ logs/ # Ingestion logs, runtime logs
│ └─ data_source_flag.json # Indicates whether data is real or synthetic
├─ specs/ # Design documents and JSON‑Schema contracts
├─ tests/ # Unit / contract / integration tests
├─ code/requirements.txt # Pin‑exact dependencies
└─ pyproject.toml # Ruff & Black configuration
```

---

## Prerequisites

* **Python 3.11** (the project was initialized for this version)
* A working internet connection for the first run – the script
 `code/ingestion/fetch_real.py` will download a verified diffusion dataset
 from the URL recorded in `plan.md`. If the download fails, a synthetic
 dataset is generated automatically.
* All required third‑party packages are listed in `code/requirements.txt`.
 Install them in a clean virtual environment:

```bash
python -m venv.venv
source.venv/bin/activate # on Windows:.venv\Scripts\activate
pip install -r code/requirements.txt
```

---

## Data source requirements

1. **Real data** – The pipeline expects a CSV file named `dataset.csv` inside
 `data/raw/`. The file must contain at least the following columns:
 - `solute_smiles` – SMILES string of the solute molecule
 - `solvent_name` – Name of the solvent
 - `temperature_K` – Temperature in Kelvin
 - `diffusion_coeff_cm2_s` – Measured diffusion coefficient (target)

2. **Source flag** – After a successful download (or synthetic fallback) the
 script `code/ingestion/flag_source.py` creates `data/data_source_flag.json`
 with the content `{"source": "real"}` or `{"source": "synthetic"}`. Down‑stream
 stages (e.g., evaluation) read this flag to decide whether to compute
 performance metrics.

3. **Plan record** – `plan.md` must contain a line `Dataset URL: <actual URL>`
 that points to the location from which `dataset.csv` was obtained. The
 helper `code/ingestion/fetch_real.py` automatically updates this line when
 the download succeeds.

---

## Execution workflow

The following commands run the complete pipeline on the *currently available*
dataset (real or synthetic). Each step writes its output to the `data/`
directory hierarchy as described above.

1. **Download / generate the raw dataset**

 ```bash
 python -m code.ingestion.fetch_real
 # This will:
 # • download the CSV to data/raw/dataset.csv
 # • update plan.md with the dataset URL
 # • fall back to synthetic generation if download fails
 # • create data/data_source_flag.json
 ```

2. **Validate and featurize**

 ```bash
 python -m code.ingestion.run_validation # validates SMILES & missing fields
 python -m code.ingestion.featurize # creates data/processed/featurized.jsonl
 ```

3. **Train models (MPNN + Linear Regression)**

 ```bash
 python -m code.training.train
 # Checkpoints are stored under data/artifacts/
 ```

4. **Evaluate (real‑data only)**

 ```bash
 python -m code.training.evaluate
 # Generates artifacts/reports/evaluation.json when source == "real"
 ```

5. **Sensitivity analysis**

 ```bash
 python -m code.training.sensitivity
 # Produces artifacts/reports/sensitivity_report.json
 ```

6. **Ablation / robustness studies**

 ```bash
 python -m code.training.ablation_study # creates ablation_report.json
 python -m code.training.robustness # creates outlier_analysis.json
 ```

7. **Summary report**

 ```bash
 python -m code.training.generate_sensitivity_summary
 # Generates artifacts/reports/sensitivity_summary.md
 ```

8. **Resource summary (optional)**

 ```bash
 python -m code.utils.monitor # writes runtime_memory.json &
 # aggregates to resource_summary.json
 ```

---

## Running the quick‑start script

A deterministic convenience script is provided to execute the whole pipeline on
synthetic data and assert successful completion:

```bash
python code/run_quickstart.py
```

This script is useful for CI checks and for developers who want to verify that
the environment is correctly set up without fetching the real dataset.

---

## Testing

The repository contains a comprehensive test suite. To run all tests:

```bash
pytest -vv
```

Contract tests validate that generated artifacts conform to the JSON‑Schema
definitions in `specs/001-predicting-molecular-diffusion-coefficie/contracts/`.

---

## License

This project is released under the MIT License. See the `LICENSE` file for
details.