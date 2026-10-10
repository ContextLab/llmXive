# Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

Pipeline for assessing p-value reliability in public genomic datasets
(GEO, TCGA, ENCODE) via effect-size stability and stratified block
permutation null modeling.

## Structure

- `src/` — pipeline modules (config, data_loader, preprocessing,
 de_analysis, permutation, metrics, report, versioning)
- `scripts/` — R DE script, environment setup, and utility scripts
- `tests/` — pytest test suite
- `main.py` — pipeline entry point

## Linting & Formatting (T003)

Flake8 and black are configured for this project:

- `code/.flake8` — flake8 configuration (max line length 88,
 black-compatible ignores E203/W503, excludes data/artifacts/venv).
- `code/pyproject.toml` — black configuration (line length 88,
 target Python 3.11).

Install and verify the tooling:

```bash
bash code/scripts/setup_lint_tools.sh
```

Run linting and format checks manually:

```bash
cd code
python -m flake8 src scripts tests main.py
python -m black --check src scripts tests main.py
python -m black src scripts tests main.py # apply formatting
```

## Quickstart

See `specs/001-assess-significance-reliability/quickstart.md` for full
setup and run instructions.