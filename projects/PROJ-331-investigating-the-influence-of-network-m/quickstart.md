# Quick Start Guide: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

This guide provides step-by-step instructions to run the full pipeline on a fresh environment.
It covers installation, configuration, data download, preprocessing, motif analysis, statistical correlation, and report generation.

## Prerequisites

- **Python**: 3.9 or higher
- **System Dependencies**:
 - `git` (for cloning)
 - `wget` or `curl` (for downloading data)
 - `libxml2-dev`, `libxslt1-dev` (for WeasyPrint PDF generation)
- **Disk Space**: Minimum 20GB (raw HCP data + processed artifacts)
- **Memory**: Minimum 16GB RAM (recommended 32GB for motif analysis)

## 1. Environment Setup

### Clone the Repository
```bash
git clone <repository-url>
cd PROJ-331-investigating-the-influence-of-network-m
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install the core Python requirements:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: If you encounter issues with `weasyprint` or `reportlab`, ensure system libraries are installed:
- **Ubuntu/Debian**: `sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`
- **macOS**: `brew install pango`

## 2. Configuration

The pipeline relies on the `code/config.py` file for global settings.
Ensure the following parameters are set correctly in `code/config.py`:

- `EXPECTED_COHORT_SIZE`: Number of subjects to process.
- `DATA_ROOT`: Path to the project root (usually auto-detected).
- `SEED`: Random seed for reproducibility (default: 42).

No further configuration is required for the default HCP S3 anonymous access.

## 3. Execution

Run the full pipeline using the main entry point. This script orchestrates:
1. Data download (HCP S3)
2. Preprocessing (Parcellation, Binarization)
3. Motif Analysis (Enumeration, Z-scores)
4. Statistical Analysis (Correlation, Permutation)
5. Report Generation (PDF)

```bash
python code/download.py
python code/preprocess.py
python code/motifs.py
python code/stats.py
python code/report.py
```

Alternatively, run the unified pipeline script if available (check `scripts/run_pipeline.sh`):
```bash
bash scripts/run_pipeline.sh
```

## 4. Expected Outputs

Upon successful completion, the following artifacts will be generated:

### Data Artifacts (`data/processed/`)
- `subject_list_manifest.json`: List of processed subjects.
- `weighted_adjacency.npy`: Weighted structural connectomes.
- `canonical_binary_adj.npy`: Binarized structural connectomes.
- `motif_profiles.json`: Z-scores for all 3-node motifs.
- `subject_metrics.csv`: Aggregated metrics for correlation analysis.
- `global_efficiency.json`: Global efficiency values.

### Results (`results/`)
- `correlation_results.json`: Partial correlation results (Pearson/Spearman).
- `permutation_results.json`: Empirical p-values for significant motifs.
- `power_analysis.json`: Minimum detectable effect size.
- `analysis_report.pdf`: Comprehensive PDF report including:
 - Methods section
 - Scatter plots with confidence intervals
 - Sensitivity analysis
 - Limitations
 - Disclaimer: "These findings are associational only and do not imply causation."

### Logs (`data/logs/`)
- `pipeline.log`: Detailed execution log containing:
 - Bonferroni-adjusted alpha
 - Random seed
 - Library versions
 - Permutation count
 - VIF thresholds

## 5. Validation

To verify the pipeline ran correctly, check the success rate and log integrity:

```bash
python code/validate_quickstart.py
```

This script validates:
- Existence of all required output files.
- Integrity of `pipeline.log` (statistical parameters).
- Correctness of `subject_metrics.csv` schema.

## Troubleshooting

- **HCP S3 Access Failed**: Ensure network connectivity. The pipeline retries 3 times with exponential backoff.
- **Out of Memory**: Reduce `N_MOTIF_NODES` in `config.py` or increase system RAM.
- **PDF Generation Error**: Verify `libpango` and `libxslt` are installed on the system.

## Next Steps

After the initial run, you can:
- Modify `code/config.py` to change the cohort size or motif parameters.
- Re-run specific stages (e.g., only `code/stats.py`) if data is already downloaded.
- Inspect `results/analysis_report.pdf` for scientific insights.