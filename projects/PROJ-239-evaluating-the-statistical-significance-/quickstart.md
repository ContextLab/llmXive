# Quickstart Guide: Evaluating Statistical Significance with Non-Independent Observations

This guide validates the setup and core functionality of the A/B test significance project.

## Prerequisites

- Python 3.11+
- pip (package manager)

## 1. Environment Setup

Clone the repository and create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Project Structure Verification

Ensure the following directory structure exists:

```bash
ls code tests data/raw data/derived
```

## 3. Linting Validation

Run the linters to ensure code style compliance:

```bash
black --check.
flake8.
```

## 4. Unit Test Execution

Run the full test suite to verify core logic:

```bash
pytest tests/ -v
```

**Expected Result**: All tests should pass (exit code 0).

## 5. Simulation Validation (Quick Run)

Run a reduced simulation to verify the pipeline end-to-end:

```bash
python code/run_simulation_robust.py --icc 0.1 --iterations 10 --seed 42
```

This should generate `data/derived/robustResults.csv`.

## 6. Report Generation

Once full simulations are complete, generate the research report:

```bash
python scripts/generate_report.py
```

This produces `specs/001-evaluating-the-statistical-significance/research.md`.