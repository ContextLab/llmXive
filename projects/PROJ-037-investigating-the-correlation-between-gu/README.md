# PROJ-037: Gut Microbiome and Circadian Rhythm Investigation

> **Disclaimer**: This project investigates **associational** links between gut microbiome composition and circadian rhythm disruption. No causal claims are made.

## Quick Start

1. **Setup Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Run Pipeline**:
 ```bash
 # Step 1: Ingest and clean data
 python code/ingestion.py

 # Step 2: Analyze diversity and correlations
 python code/analysis.py

 # Step 3: Validate results
 python code/validation.py

 # Step 4: Generate report
 python code/report.py
 ```

3. **View Outputs**:
 - `data/outputs/correlation_results.csv`
 - `data/outputs/heatmap.png`
 - `data/outputs/pcoa_sleep_quality.png`
 - `data/outputs/validation_status.json`
 - `data/outputs/sensitivity_report.csv`

## Documentation

- [Analysis Methodology](docs/analysis_methodology.md)
- [Limitations and Mitigations](docs/limitations_and_mitigations.md)
- [Full Project README](docs/README.md)

## Key Features

- **Real Data**: Uses American Gut Project and Open Humans data (no synthetic fallbacks).
- **Associational Framing**: Explicitly avoids causal language (FR-008 compliant).
- **Robust Validation**: Bootstrap resampling and sensitivity analysis.
- **Performance Optimized**: Parallel processing for large datasets.

## License

[Insert License]
