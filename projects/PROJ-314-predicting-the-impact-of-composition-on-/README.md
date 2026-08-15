# Predicting the Impact of Composition on the Weibull Modulus of Ceramics

This project implements an automated science pipeline to predict the Weibull modulus of ceramic materials based on their chemical composition and processing parameters.

## Project Structure

- `code/`: Source code for ingestion, descriptors, modeling, and reporting.
- `data/`:
 - `raw/`: Raw data fetched from external sources.
 - `processed/`: Cleaned and feature-engineered datasets.
 - `artifacts/`: Intermediate artifacts like plots and models.
 - `models/`: Trained machine learning models.
 - `results/`: Model evaluation metrics and reports.
 - `reports/`: Final generated reports.
- `tests/`: Unit and integration tests.
- `specs/`: Feature specifications and documentation.

## Quickstart

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Set up environment variables (copy `.env.example` to `.env`):
 ```bash
 cp.env.example.env
 ```
3. Run the pipeline:
 ```bash
 python code/run_pipeline_timing.py
 ```

## License

MIT License
