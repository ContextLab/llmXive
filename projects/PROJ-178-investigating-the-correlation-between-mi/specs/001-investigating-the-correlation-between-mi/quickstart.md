# Quickstart: Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

## Prerequisites

- Python 3.11+
- Git
- 10 GB free disk space (for VCF downloads and processing)
- Internet connection (to download data from 1000 Genomes FTP)

## Installation

1. **Clone the repository**:
 ```bash
 git clone https://github.com/your-org/your-repo.git
 cd your-repo
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Install `haplogrep2`** (optional, for haplogroup assignment):
 - Download and install `haplogrep2` from.
 - Ensure `haplogrep` is in your PATH.

## Data Download & Validation

The pipeline will automatically attempt to download the required data from the 1000 Genomes Project FTP site. **CRITICAL**: The pipeline will first check for the presence of the `age` column in the metadata.

1. **Run the main script**:
 ```bash
 python code/run_analysis.py
 ```

 This script will:
 - **Check Data Availability**: Verify the `age` column exists. If missing, it will halt and report "Data Unavailable".
 - Download and parse VCFs (streaming to save RAM).
 - Calculate heteroplasmy burden (depth-stratified).
 - Assign haplogroups.
 - Run Rank-OLS regression and sensitivity analyses.
 - Generate plots and save results.

2. **Monitor progress**:
 - Logs will be printed to the console.
 - Intermediate files will be saved to `data/processed/`.
 - Runtime will be logged to `logs/runtime.log`.

3. **View results**:
 - Statistical results: `data/processed/analysis_results.csv`
 - Plots: `paper/figures/`
 - Draft manuscript: `paper/draft.md`

## Troubleshooting

- **Error: "Data Unavailable: Chronological age not found"**: The 1000 Genomes Project metadata does not contain individual ages. The project cannot proceed with the original hypothesis. Re-scope to descriptive analysis or use a different dataset.
- **Error: "Data source unreachable"**: The 1000 Genomes FTP site may be down. Retry later.
- **Error: "Not enough memory"**: Ensure you have at least 7 GB of free RAM. The pipeline uses streaming to minimize memory usage.
- **Error: "haplogrep2 not found"**: Ensure `haplogrep2` is installed and in your PATH.

## Next Steps

- **Review results**: Check `data/processed/analysis_results.csv` for correlation coefficients and p-values.
- **Refine analysis**: Adjust parameters (e.g., VAF threshold) in `code/analysis/sensitivity.py` and re-run.
- **Write paper**: Use the generated figures and statistics to draft the manuscript in `paper/draft.md`.