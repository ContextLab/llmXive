# Single-Cell Trajectories of T-Cell Exhaustion

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

Run the pipeline:
```bash
python code/download_data.py
python code/preprocess.py
python code/velocity.py
```

## Configuration

Linting and formatting are configured via:
- `pyproject.toml`: Black and Ruff settings
- `.pre-commit-config.yaml`: Pre-commit hooks

Run manually:
```bash
ruff check code/
black code/
```
