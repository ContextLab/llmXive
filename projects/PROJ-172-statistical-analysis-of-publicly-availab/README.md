# Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

## Project Structure

This project follows a standard data science pipeline structure:

- `code/`: Source code for data loading, feature engineering, modeling, and evaluation.
- `data/`:
 - `raw/`: Raw, unprocessed data files.
 - `processed/`: Cleaned and engineered data ready for modeling.
- `tests/`: Unit and integration tests.
- `artifacts/`:
 - `reports/`: Generated reports (JSON, HTML, etc.).
 - `figures/`: Visualizations (PNG, SVG, etc.).
- `state/`: Checksums and state management files for reproducibility.

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure environment variables:
 ```bash
 cp.env.example.env
 # Edit.env with your specific settings
 ```

4. Run the project setup script to ensure directories exist:
 ```bash
 python code/setup_project_structure.py
 ```

## Running Tests

```bash
pytest
```

## Linting and Formatting

```bash
# Check code style
ruff check.
black --check.

# Fix code style
ruff check. --fix
black.
```

## Workflow

1. **Data Ingestion**: Run `code/data_loader.py` to fetch and validate data.
2. **Feature Engineering**: Run `code/feature_engineering.py` to create features.
3. **Modeling**: Run `code/models.py` to train and evaluate models.
4. **Evaluation**: Run `code/evaluation.py` for statistical significance testing.
5. **Reporting**: Artifacts are automatically saved to `artifacts/` and `state/`.