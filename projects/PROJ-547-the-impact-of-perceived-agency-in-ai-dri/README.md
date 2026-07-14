# The Impact of Perceived Agency in AI-Driven Cognitive Behavioral Therapy on Treatment Adherence

**Project ID**: PROJ-547

This research project investigates whether perceived agency in an AI therapist influences treatment adherence in Cognitive Behavioral Therapy (CBT). The pipeline ingests conversation transcripts, computes agency scores based on linguistic markers, extracts adherence metrics from usage logs, and performs statistical regression analysis to test the hypothesis.

## Quickstart

To run the full pipeline:

1. **Setup Environment**:
 ```bash
 bash setup_env.sh
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Download Data**:
 ```bash
 python code/data_acquisition/download_datasets.py
 python code/data_acquisition/validate_metadata.py
 ```

3. **Run Agency Scoring (US1)**:
 ```bash
 python code/agency_scoring/ingest_transcripts.py --input data/raw/transcripts.json --output data/processed/agency_scores.csv
 python code/agency_scoring/compute_scores.py --input data/processed/agency_scores.csv --output data/processed/agency_scores_final.csv
 ```

4. **Run Adherence Extraction (US2)**:
 ```bash
 python code/adherence_extraction/extract_metrics.py --input data/raw/usage_logs.json --output data/processed/adherence_metrics.csv
 ```

5. **Validation (US4)**:
 ```bash
 python code/validation/select_subset.py --agency data/processed/agency_scores_final.csv --external data/external/agency_scale.csv --output data/processed/validation_subset.csv
 python code/validation/compute_reliability.py --input data/processed/validation_subset.csv
 python code/validation/compute_convergent.py --input data/processed/validation_subset.csv
 python code/validation/generate_report.py
 ```

6. **Run Regression Analysis (US3)**:
 ```bash
 python code/analysis/merge_datasets.py --agency data/processed/agency_scores_final.csv --adherence data/processed/adherence_metrics.csv --demo data/processed/demographics.csv --output data/processed/merged_data.csv
 python code/analysis/run_regression.py --input data/processed/merged_data.csv --output output/
 ```

## Output Directory

All final results, including regression coefficients, plots, and validation reports, are stored in the `output/` directory:

- `output/regression_summary.csv`: Main statistical results with FDR-corrected p-values.
- `output/plots/`: Visualizations of agency scores vs. adherence.
- `output/provenance.yaml`: Metadata linking statistics to source data and scripts.
- `validation/report.pdf`: Comprehensive validation report for the agency metric.

## Project Structure

```
.
├── code/ # Source code modules
│ ├── agency_scoring/ # US1: Compute agency scores
│ ├── adherence_extraction/ # US2: Extract adherence metrics
│ ├── analysis/ # US3: Regression and merging
│ ├── validation/ # US4: Metric validation
│ ├── logging/ # Centralized logging
│ └── utils/ # Shared utilities
├── data/
│ ├── raw/ # Downloaded raw data
│ ├── processed/ # Intermediate processed files
│ └── external/ # External datasets (agency scale)
├── output/ # Final analysis results and plots
├── tests/ # Unit and integration tests
├── configs/ # Configuration files
├── docs/ # Documentation
├── README.md
└── requirements.txt
```

## Verification

To verify the pipeline execution:
- Check `logs/run_<timestamp>.log` for complete audit trails.
- Run `python code/logging/verify_logging.py` to ensure logging completeness.
- Run `pytest tests/` to verify unit and integration tests.

## License

This project is for research purposes only.
