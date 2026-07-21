# Structure-Only Surrogate Model for 2D Material Elastic Moduli

> **Scientific Integrity Statement**: This project implements a machine learning surrogate model to interpolate pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations.

## Overview

This project implements a **Structure-Only Surrogate Model** for predicting the elastic moduli of 2D materials. The model is trained on pre-computed Density Functional Theory (DFT) data and functions as an interpolator of existing quantum mechanical calculations, not as a solver of the underlying physics.

**Key Distinction**: Unlike first-principles methods that solve the Schrödinger equation to derive material properties from fundamental physical laws, this surrogate model learns statistical correlations between structural descriptors and pre-computed elastic moduli. It is a high-fidelity curve-fitting exercise designed for rapid inference within the chemical space covered by its training data.

## Scientific Integrity

> "The first principle is that you must not fool yourself — and you are the easiest person to fool." — Richard Feynman

### What This Model Is
- A Graph Neural Network (GNN) surrogate trained on DFT-computed elastic tensors.
- A tool for rapid interpolation of elastic properties within known chemical families.
- A statistical model that identifies structural descriptors correlated with stiffness.

### What This Model Is NOT
- **NOT** a solution to the Schrödinger equation.
- **NOT** a first-principles calculation.
- **NOT** capable of discovering new physical laws or extrapolating to unseen chemical spaces.
- **NOT** a replacement for DFT when high-accuracy, physics-grounded results are required for novel materials.

## Reproducibility

Random seeds are pinned in `code/utils/config.py` to ensure deterministic execution across runs. The project strictly adheres to Constitution Principle I (Reproducibility) by enforcing fixed seeds for `torch`, `numpy`, and `random`.

## Project Structure

- `code/`: Source code for data ingestion, model training, and analysis.
- `data/`:
 - `raw/`: Downloaded raw data (CIFs, tensors).
 - `processed/`: Processed graphs, splits, and model checkpoints.
 - `results/`: Final metrics, reports, and visualizations.
- `docs/`: Methodology, contributing guidelines, and terminology compliance.
- `tests/`: Unit and integration tests.

## Quickstart

1. **Setup Environment**:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Run Data Pipeline**:
 ```bash
 python code/ingest/pipeline.py
 ```

3. **Train Model**:
 ```bash
 python code/model/train.py --config code/model/train_config.yaml
 ```

4. **Evaluate & Analyze**:
 ```bash
 python code/model/eval_runner.py
 python code/analysis/importance.py
 ```

5. **Generate Report**:
 ```bash
 python code/analysis/report_generator.py
 ```

## Dependencies

See `code/requirements.txt` for the full list of pinned dependencies, including `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, and `scikit-learn`.

## License

MIT License. See `LICENSE` for details.

## Disclaimer

All results derived from this project are based on machine learning interpolation of pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation. Users must not interpret these results as fundamental physical predictions.