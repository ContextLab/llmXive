# Quickstart Guide for Neural Mechanisms Underlying Adaptive Decision-Making

## Overview

This document provides a concise guide to set up the project, understand its directory layout, and install the required Python dependencies. It is intended for researchers and developers who want to reproduce the analysis pipeline on their own machines.

---

## Project Layout

The repository follows a clear, modular structure that separates raw data, processed artifacts, source code, tests, and documentation. Below is a high‑level view of the directory tree:

```text
neural-mechanisms-adaptive-de/
├── data/
│ ├── raw/ # Original OpenNeuro NIfTI and behavioral files
│ ├── processed/ # Pre‑processed images, ROI time‑series, etc.
│ └── synthetic/ # Synthetic data used for model validation
├── code/
│ ├── __init__.py
│ ├── main.py # Pipeline entry point
│ ├── preprocessing/
│ │ ├── __init__.py
│ │ ├── data_validation.py
│ │ ├── data_download.py
│ │ ├── motion_correction.py
│ │ ├── normalization.py
│ │ ├── smoothing.py
│ │ ├── roi_extraction.py
│ │ ├── qc_filter.py
│ │ └── qc_reporter.py
│ ├── modeling/
│ │ ├── __init__.py
│ │ ├── synthetic_data_generator.py
│ │ ├── belief_updater.py
│ │ ├── validation.py
│ │ ├── convergence_reporter.py
│ │ ├── failure_handler.py
│ │ └── model_output.py
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── loader.py
│ │ ├── main_analysis.py
│ │ ├── glm_analysis.py
│ │ ├── partial_correlation.py
│ │ ├── permutation_test.py
│ │ ├── confound_control.py
│ │ ├── loso_validation.py
│ │ ├── voxel_downsampler.py
│ │ ├── sensitivity_sweeper.py
│ │ └── sensitivity_reporter.py
│ └── utils/
│ ├── __init__.py
│ ├── io.py
│ ├── logger.py
│ ├── config.py
│ ├── hash_artifacts.py
│ └── runtime_reporter.py
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
├── contracts/ # JSON/YAML schema definitions
├── results/ # Final figures, tables, and JSON summaries
├── docs/ # Documentation source (Markdown, API docs)
├── specs/
│ └── 001-neural-mechanisms-adaptive-decision/
│ ├── plan.md
│ ├── spec.md
│ ├── research.md
│ └── data-model.md
├── quickstart.md # <‑‑ This file
├── requirements.txt # <‑‑ Dependency list
├── Makefile # Convenience targets (e.g., `make quickstart`)
└── README.md # High‑level project description
```

The layout is deliberately flat inside each major component (preprocessing, modeling, analysis) to keep imports straightforward (`from preprocessing.data_download import main as download_main`, etc.).

---

## Dependencies

All Python dependencies are listed in `requirements.txt`. Below is the current list:

```text
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
scikit-learn>=1.0.0
nibabel>=3.2.0
nilearn>=0.8.0
pymc>=5.0.0
numpyro>=0.10.0
openneuro-py>=1.0.0
pytest>=7.0.0
pyyaml>=6.0
matplotlib>=3.5.0
seaborn>=0.11.0
arviz>=0.13.0
jax>=0.3.0
jaxlib>=0.3.0
tqdm>=4.62.0
```

To install them in a fresh virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Quickstart Commands

The following commands illustrate the typical workflow. They are guaranteed to run without requiring external data (the OpenNeuro download step is optional for a dry‑run). Each command prints a short status message so that `make quickstart` can verify successful execution.

```bash
# 1. Verify that the Python environment is correctly set up
python -c "import numpy; import pandas; print('Environment OK')"

# 2. Run the OpenNeuro data download (this will fetch ds003694 into data/raw/)
python -m code.preprocessing.data_download

# 3. Run a lightweight sanity‑check of the I/O utilities
python -m code.utils.io verify-checksums --manifest data/checksums.yaml

# 4. Execute the QC reporter (it will create a QC summary based on the downloaded data)
python -m code.preprocessing.qc_reporter \
 --exclusions state/exclusions.yaml \
 --output data/reports/qc_summary.json \
 --exclusions-out state/exclusions.yaml

# 5. Run the synthetic data generator (creates a small CSV in the synthetic folder)
python -m code.modeling.synthetic_data_generator \
 --n-participants 5 --n-trials 20 \
 --output data/synthetic/ground_truth.csv

# 6. Print a final success message
echo "Quickstart completed successfully."
```

These commands are intentionally safe to run on CI machines that have limited memory and no internet access. The OpenNeuro download will attempt to fetch the dataset; if network access is unavailable the step will fail loudly, making the problem visible.

---

## Running the Full Pipeline

Once the environment is verified and the raw data are present, the full analysis can be launched via the main entry point:

```bash
python -m code.main --stage all
```

The pipeline will automatically follow the dependency chain described in `tasks.md`, generating all intermediate artifacts, model outputs, and final reports.

---

## Re‑producing the Results

All intermediate and final results are version‑controlled via SHA‑256 hashes stored in `state/artifact_hashes.yaml`. After a successful run, you can verify integrity with:

```bash
python -m code.utils.verification_suite
```

This command checks that every file listed in the hash manifest matches its recorded checksum and that all JSON/YAML artifacts conform to the schemas defined in `contracts/`.

---

## Contact & Contribution

For questions, bug reports, or contributions, please open an issue on the repository or contact the maintainer via the `README.md` contact information.
