# Quickstart Guide

## Prerequisites

- Python 3.9 or higher
- pip
- Access to the internet (for data fetching)

## Installation

1. Clone the repository:
 ```bash
 git clone <repo-url>
 cd PROJ-328-predicting-the-impact-of-composition-on-
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Execute the full research pipeline:

```bash
python code/run_pipeline.py
```

This command will:
1. **Ingest Data**: Fetch from APIs and scrape literature.
2. **Clean & Validate**: Filter invalid compositions and temperatures.
3. **Engineer Features**: Generate physical descriptors and CLR transforms.
4. **Train Models**: Run XGBoost and Linear Regression with CV.
5. **Evaluate**: Compute metrics, bootstrap CIs, and sensitivity analysis.
6. **Visualize**: Generate plots and final reports.

## Verifying Results

After the pipeline completes, verify the following artifacts exist:

- `data/processed/solder_hardness_cleaned.csv`
- `data/processed/.ingestion_status.json`
- `data/processed/model_metrics.yaml`
- `data/outputs/sensitivity_plot.png`
- `data/processed/final_aggregated_report.yaml`

You can also run the validation report generator:

```bash
python code/ingestion/generate_validation_report.py
```

## Troubleshooting

- **API Fetch Errors**: Check `data/config/sources.yaml` for correct endpoints and keys.
- **Memory Errors**: The pipeline is optimized for <7GB RAM. If issues persist, check for large intermediate files.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.

## Next Steps

- Review `specs/001-predict-solder-hardness/paper_draft.md` for the generated research paper.
- Explore `data/outputs/` for visualizations.
- Run `pytest tests/` to verify system integrity.