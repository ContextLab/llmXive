# Predicting Molecular Reactivity Using Machine Learning

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Setup directory structure:
 ```bash
 bash scripts/setup_dirs.sh
 ```

## Data Sources

- USPTO-MIT Subset: https://zenodo.org/record/3969375 (JSONL format)
- Reaction templates defined in `src/modeling/config.yaml`

## Pipeline Execution

Run the full pipeline:
```bash
python src/main.py
```

Update state after major stages:
```bash
python scripts/update_state.py --artifact data/processed/filtered_reactions.csv
```

## Testing

```bash
pytest tests/
```

## Linting

```bash
flake8 src/
black src/
```