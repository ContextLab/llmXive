# The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

Computational research pipeline (PROJ-490) investigating whether exposure to
idealized avatars in VR affects self-esteem, moderated by individual social
comparison tendency (INCOM).

## Study Design

- **Outcome**: `post_self_esteem` (Rosenberg Self-Esteem Scale, post-intervention)
- **Covariate**: `pre_self_esteem` (RSES, pre-intervention)
- **Predictors**: `avatar_condition` (0 = Neutral, 1 = Idealized),
 `comparison_tendency` (INCOM), and their interaction
- **Model**: ANCOVA-style OLS regression (avoids mathematical coupling of
 change-score regression)
- **Robustness**: bootstrap resampling (>= 1000 iterations), threshold
 sensitivity sweeps, family-wise error correction

## Project Structure

```text
projects/PROJ-490-the-effect-of-simulated-social-compariso/
├── code/
│ ├── main.py # Pipeline entry point
│ ├── data/ # download, preprocess, validation, config
│ ├── analysis/ # regression, bootstrap, sensitivity, reporting
│ └── utils/ # logger, validators
├── data/
│ ├── raw/ # Downloaded or synthetic raw data
│ └── processed/ # Imputed data, coefficients, diagnostics, reports
├── tests/
│ ├── contract/ # Schema validation tests
│ └── unit/ # Logic tests
├── contracts/ # dataset / output / results JSON schemas
├── docs/ # analysis_plan.md (pre-registration artifact)
├── state/ # Data path decisions, checksums, reproducibility
├── requirements.txt
├──.flake8 # flake8 configuration
└── pyproject.toml # black + pylint configuration
```

## Setup

```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python code/main.py --action download # Data discovery / synthetic fallback
python code/main.py --action preprocess # MICE imputation -> data/processed/imputed_data.csv
python code/main.py --action analyze # ANCOVA, bootstrap, sensitivity
python code/main.py --action report # data/processed/final_report.json
python code/main.py --action validate # Schema validation checks
# or all at once:
python code/main.py --action all
```

See `specs/001-simulated-social-comparison-self-esteem/quickstart.md` for the
full run-book.

## Code Quality

This project enforces linting and formatting (T001b):

```bash
# Lint (flake8, zero errors expected)
flake8 code/ tests/

# Lint (pylint, configured for research code)
pylint code/

# Format check / apply (black)
black --check code/ tests/
black code/ tests/
```

Configurations live in `.flake8` (flake8) and `pyproject.toml` (black, pylint).

## Data Integrity & Ethics

- Real data is used only if IRB/consent documentation is verified
 (Constitution Principle VI); otherwise the pipeline falls back to a
 synthetic generator with known ground-truth parameters labeled
 "Pipeline Validation Only".
- All raw artifacts are SHA-256 checksummed in `state/`.
- All data path decisions are logged to `logs/data_path_decision.log`.
- Final reports distinguish "Empirical Association" (real data) from
 "Simulated Causal Effect" (synthetic data).

## Reproducibility

All random operations use fixed seeds defined in `code/data/config.py`.
Dependencies are pinned in `requirements.txt`.
