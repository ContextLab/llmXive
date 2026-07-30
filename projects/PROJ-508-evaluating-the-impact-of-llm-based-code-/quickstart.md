# Quickstart Guide: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

This guide walks you through running the full pipeline to generate the master dataset, perform analysis, and produce the final report.

## Prerequisites

- Python 3.11+
- `GITHUB_TOKEN` environment variable set (optional, for rate limit avoidance)

## Installation

```bash
pip install -r requirements.txt
```

## Execution

Run the pipeline in the following order:

1. **Ingestion**: Fetch repository data and generate the master dataset.
 ```bash
 python code/ingest.py
 ```
 *Output*: `data/derived/master_dataset.csv`

2. **Analysis**: Run statistical models and generate results.
 ```bash
 python code/analyze.py
 ```
 *Output*: `data/derived/analysis_results.json`, `data/derived/sensitivity_analysis.json`, `data/derived/stratified_results.json`

3. **Reporting**: Generate visualizations and the final report.
 ```bash
 python code/report.py
 ```
 *Output*: `docs/output/final_report.pdf`, `docs/figures/forest_plot.png`, `docs/figures/sensitivity_plot.png`

## Verification

Ensure all output files are present:
- `data/derived/master_dataset.csv`
- `data/derived/analysis_results.json`
- `data/derived/sensitivity_analysis.json`
- `docs/output/final_report.pdf` (or `.md`)
- `docs/figures/forest_plot.png`
- `docs/figures/sensitivity_plot.png`

## Troubleshooting

- **Rate Limits**: If you encounter rate limit errors, set a valid `GITHUB_TOKEN`.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Config Errors**: Check `config.json` for correct paths.