# The Impact of Text Message Tone on Perceived Emotional Support

This project implements an automated research pipeline to analyze how text message tone (emojis, punctuation, length) affects perceived emotional support in different relationship contexts (friend vs. acquaintance).

## Project Structure

- `code/`: Python scripts for the data pipeline (stimulus generation, data collection, cleaning, analysis).
- `data/`: Data storage.
 - `raw/`: Raw data exports (e.g., from Prolific).
 - `processed/`: Intermediate and cleaned datasets.
 - `consent/`: Consent forms and provenance records.
 - `results/`: Statistical analysis outputs.
- `figures/`: Generated plots and visualizations.
- `tests/`: Unit and integration tests.
- `specs/`: Research design documents and specifications.
- `contracts/`: JSON/YAML schema definitions for data validation.

## Quickstart

1. **Setup Environment**:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Verify Project Structure**:
 Ensure all directories exist. You can run:
 ```bash
 python code/setup_project_structure.py
 ```

3. **Run the Pipeline**:
 The primary analysis requires real data. Mock mode is restricted for final reports.
 ```bash
 python code/run_pipeline.py --mode real
 ```

## Data Requirements

This pipeline requires real participant data collected via Prolific. The file `data/raw/real_ratings.csv` must be present for the analysis to proceed. Synthetic data is not permitted for the primary analysis path.

## Reproducibility

All random seeds are fixed in `code/config.py`. Checksums for all data artifacts are recorded in `data/checksums.json` to ensure data integrity.

## License

[Insert License Here]
