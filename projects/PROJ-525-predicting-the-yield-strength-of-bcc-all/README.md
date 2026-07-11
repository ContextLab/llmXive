# PROJ-525: Predicting Yield Strength of BCC Alloys

This project implements an automated research pipeline to predict the yield strength of Body-Centered Cubic (BCC) High-Entropy Alloys (HEAs) and Medium-Entropy Alloys (MEAs).

## Project Structure

- `code/`: Source code for data ingestion, feature engineering, and modeling.
- `data/`:
 - `raw/`: Downloaded raw datasets (e.g., MPEA database).
 - `processed/`: Cleaned and filtered datasets.
 - `logs/`: Execution logs and rejected entries.
 - `figures/`: Generated plots.
- `reports/`: Model comparison reports and metrics.
- `specs/`: Feature specifications and design documents.
- `tests/`: Unit and integration tests.

## Dependencies

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Run data ingestion:
 ```bash
 python code/data_ingestion.py
 ```
2. Run feature engineering:
 ```bash
 python code/feature_engineering.py
 ```
3. Run modeling:
 ```bash
 python code/modeling.py
 ```

## License

MIT
