# Quick‑start Guide

## Python version

The project requires Python **3.9** (or newer, up to 3.11). It has been tested with 3.9.13.

## Installing dependencies

```bash
# From the project root
python -m venv venv
source venv/bin/activate  # on Windows use `venv\\Scripts\\activate`
pip install -r requirements.txt
```

## Running the pipeline

The entry point is the quick‑start validator script:

```bash
python -m code.reproducibility.quickstart_validator
```

If a convenience shell script is provided, you can also run:

```bash
./scripts/quickstart.sh
```

This will download the Knot Atlas (if not already present), run the data validation, and generate the reproducibility logs under `docs/reproducibility/logs/`.

For more detailed usage see `docs/reproducibility/quickstart_validation.md`.

