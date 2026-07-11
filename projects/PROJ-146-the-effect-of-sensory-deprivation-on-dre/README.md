# PROJ-146: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

## Project Setup

This project uses `ruff` for linting and formatting, and `pre-commit` to enforce code quality before every commit.

### Prerequisites

- Python 3.11+
- `pip`

### Installation

1. **Create and activate a virtual environment:**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install dependencies:**
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `requirements.txt` is managed in `code/`. The `pyproject.toml` in `code/` also lists dependencies for packaging.*

3. **Install development tools:**
 ```bash
 pip install pre-commit ruff black
 ```

4. **Initialize pre-commit hooks:**
 ```bash
 pre-commit install
 ```

### Usage

- **Run Linter:** `ruff check.`
- **Run Formatter:** `ruff format.` (or `black.`)
- **Run Tests:** `pytest`
- **Run Data Generation:** `python code/generate_data.py`
- **Run Analysis:** `python code/models.py`

### Configuration

- **Linting/Formatting:** Configured in `code/pyproject.toml` (Ruff/Black settings).
- **Pre-commit:** Configured in `.pre-commit-config.yaml`.
- **Pytest:** Configured in `code/pyproject.toml`.

## Project Structure

- `code/`: Source code
- `data/`: Raw, synthetic, and processed data
- `results/`: Model outputs and reports
- `tests/`: Unit, contract, and integration tests
- `specs/`: Feature specifications
- `contracts/`: Data schemas