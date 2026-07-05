# Quickstart: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for dataset download)

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to the CPU-only version via `--index-url https://download.pytorch.org/whl/cpu`.*

## Data Download

The pipeline automatically downloads verified datasets from HuggingFace and OSF on first run. To manually download or verify:

```bash
python code/main.py --action download
```

This will populate `data/raw/` with the verified parquet/csv files and **image files** (if available).

## Running the Pipeline

Execute the full pipeline (Ingestion -> Derivation -> Aggregation -> Modeling -> Reporting):

```bash
python code/main.py --action run
```

### Arguments

- `--sample`: Run on a sample subset (N=100 trials) for quick testing.
- `--force-derive`: Force re-derivation of valence scores (ambiguity requires human-rated source).
- `--output-dir`: Specify output directory for the PDF report.

## Expected Outputs

1. **Data**: `data/processed/linked_trials.csv`, `data/processed/stimulus_metadata.csv`
2. **Models**: `data/models/lmm_results.json`
3. **Report**: `reports/visual_priming_analysis.pdf` containing:
   - Interaction plots (Prime Valence x Ambiguity) - *if ambiguity source available*
   - Coefficient table with FDR-corrected p-values
   - Sensitivity analysis summary
   - Collinearity diagnostics (VIF)
   - **Confounding Check Report** (Prime vs. Trial Order)

## Troubleshooting

- **Convergence Failure**: If the model fails to converge, check `logs/modeling.log` for optimizer attempts. The pipeline will suggest simplifying random effects.
- **Missing Images**: If >10% of images are missing, the process halts with `Data Gap: Image files missing for >10% of trials`.
- **Missing Ambiguity Source**: If no human-rated ambiguity is found, the pipeline reports "Ambiguity Analysis Skipped" and proceeds with valence-only analysis.
- **Memory Error**: If RAM exceeds a sufficient threshold, enable `--sample` or reduce the batch size in `config.py`.
