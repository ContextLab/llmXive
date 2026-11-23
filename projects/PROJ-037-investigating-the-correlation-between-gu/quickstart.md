# Quickstart Guide: Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption

## Prerequisites

- Python 3.8+
- Virtual environment tool (`venv`)

## Setup

1. **Create Virtual Environment**:
 ```bash
 cd projects/PROJ-037-investigating-the-correlation-between-gu
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Download

The pipeline requires data from the American Gut Project (AGP) and Open Humans.
Follow the instructions in `docs/data_download.md` to download and place raw data in `data/raw/`.
Ensure the following files exist:
- `data/raw/agp_16s.biom`
- `data/raw/agp_metadata.tsv`
- `data/raw/open_humans_sleep.tsv`

If you do not have access to these files, the pipeline will fail with a clear error message.

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py
```

This command runs the following stages in order:
1. **Ingestion**: Downloads, merges, and cleans data (T011-T017).
2. **Diversity**: Calculates alpha and beta diversity (T020).
3. **Analysis**: Performs correlations, dbRDA, GLM, PERMANOVA (T021-T025).
4. **Visualization**: Generates heatmap and PCoA plots (T026-T027).
5. **Validation**: Runs bootstrap and sensitivity analysis (T032-T035).
6. **Report**: Generates final associational report (T029).

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/processed/cohort_merged.csv`: Cleaned, merged cohort.
- `data/outputs/correlation_results.csv`: Correlation coefficients and p-values.
- `data/outputs/heatmap.png`: Heatmap of taxa-sleep associations.
- `data/outputs/pcoa_sleep_quality.png`: PCoA ordination colored by sleep quality.
- `data/outputs/validation_status.json`: Bootstrap and sensitivity results.
- `data/outputs/final_report.md`: Comprehensive associational report.

## Troubleshooting

- **Missing Data**: If the pipeline fails with "No matching participants found", ensure your AGP and Open Humans data files are correctly formatted and contain overlapping participant IDs.
- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
- **Memory Issues**: If running out of memory, consider reducing the dataset size or increasing system resources.

## Notes

- All findings are framed as **associational**; no causal claims are made.
- The pipeline uses real data sources only; synthetic data is not used.
- If sample size N < 200, a power limitation warning will be issued.
- If sample size N < 40, bootstrap resampling will be skipped with a clear explanation.