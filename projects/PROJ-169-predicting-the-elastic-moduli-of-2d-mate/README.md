# Structure-Only Surrogate Model for 2D Material Elastic Moduli

This project implements a machine learning surrogate model to interpolate pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.

## Reproducibility

To ensure reproducibility (Constitution Principle I), all random seeds are pinned in `code/utils/config.py`.
When running the pipeline, ensure the environment variables are set correctly and the dependencies are installed.

## Usage

1. Install dependencies: `pip install -r code/requirements.txt`
2. Run the pipeline: `python code/ingest/pipeline.py` (after setting up data sources)
3. Train the model: `python code/model/train.py`
4. Generate reports: `python code/analysis/report_generator.py`

## Disclaimer

These results are derived from a machine learning surrogate model interpolating pre-computed DFT data.
They do not represent first-principles calculations or solutions to the Schrödinger equation.
