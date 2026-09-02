# Quickstart: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

## Prerequisites

- Python 3.11+
- Docker (for local environment validation)
- Git
- Access to a GitHub Actions runner (or local equivalent with 7 GB RAM)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-reproducibility
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: Ensure `ruff` and `black` are installed for linting.*

4. **Verify environment**:
 ```bash
 ruff check.
 black --check.
 ```

## Configuration

1. **Create the manifest**:
 Place your target papers in `data/manifest.csv` with columns: `doi,repo_url,dataset_name,reported_mae,reported_r2,reported_spearman,hyperparameters_json,seed`.

2. **Verify datasets**:
 Ensure the datasets listed in the manifest are accessible via the verified URLs in `research.md`. The system will attempt to download them automatically.

## Running the Pipeline

Execute the main pipeline:

```bash
python code/main.py
```

This command will:
1. Ingest the manifest.
2. Download/stream datasets.
3. Run the model reproduction (with seed sweep).
4. Perform statistical analysis.
5. Generate reports.

## Expected Outputs

After completion, check the `artifacts/` directory:

- `reports/repro_results.json`: Per-paper reproducibility scores and deviations.
- `reports/stat_summary.json`: Meta-analysis results (t-tests, LME).
- `reports/reproducibility_checklist.md`: The generated guideline checklist.
- `plots/`: Bland-Altman plots.
- `logs/environment.log`: Docker hash and library versions.

## Troubleshooting

- **Dataset Download Failed**: Check the `research.md` "Verified datasets" block. If the URL is unreachable, the system will log a `covariate_missing` or `data_unavailable` flag.
- **Memory Error**: The system uses streaming by default. If an error occurs, verify that the dataset is not being loaded entirely into memory (check `code/ingest.py`).
- **Model Substitution**: If a paper requires a GPU or >1M parameters, the system will substitute a baseline model and log the deviation. Check `artifacts/logs/failure_log.txt`.
