# Quickstart Guide: Gut Microbiome-Cognitive Correlation Study

This guide provides step-by-step instructions to reproduce the full analysis pipeline for investigating the correlation between gut microbiome composition and cognitive function using UK Biobank data.

## Prerequisites

- Python 3.10 or higher
- Access to UK Biobank data (requires approved application and token)
- 7GB+ available RAM
- 14GB+ available disk space
- Internet connection for downloading dependencies

## Setup

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Configure credentials**
 - Copy `.env.example` to `.env`
 - Add your UK Biobank token: `UKB_TOKEN=your_token_here`

## Execution Steps

The following tasks (T014-T029a) must be executed in order. Each step produces specific output files.

### Step 1: Data Download (Tasks T014, T015)

Download UK Biobank microbiome and cognitive data using streaming batches.

```bash
python code/download.py
```

**Outputs:**
- `data/raw/microbiome_raw.parquet`
- `data/raw/cognitive_raw.parquet`

### Step 2: Preprocessing Pipeline (Tasks T016-T019.5)

Filter cohort, apply zero-replacement, and perform ILR transformation.

```bash
python code/preprocess.py
```

**Outputs:**
- `data/processed/filtered_cohort.parquet`
- `data/processed/zero_replaced_counts.parquet`
- `data/processed/ilr_coordinates.parquet`
- `data/processed/prevalence_filter_report.json`
- `data/processed/cohort_retention_log.json`

### Step 3: Statistical Analysis (Tasks T028, T028b, T028c, T021, T022a, T022b, T023, T024, T024c)

Fit Lasso, OLS, and Ridge models with confounder control, apply Benjamini-Hochberg correction, and analyze age interactions.

```bash
python code/analysis.py
```

**Outputs:**
- `results/associations/main_effects_lasso.parquet`
- `results/associations/main_effects_ols.parquet`
- `results/associations/main_effects_ridge.parquet`
- `results/associations/main_effects.parquet`
- `results/associations/main_effects_reduced.parquet`
- `results/associations/interaction_effects.parquet`
- `results/associations/interaction_effects_bh.parquet`
- `results/sensitivity/over_control_report.json`

### Step 4: Visualization and Sensitivity Analysis (Tasks T028a, T029a, T033)

Generate Manhattan plots, threshold sweep analysis, and interaction comparison reports.

```bash
python code/visualize.py
```

**Outputs:**
- `results/plots/manhattan_plot.png`
- `results/sensitivity/threshold_sweep_report.json`
- `results/sensitivity/interaction_comparison_report.json`

## Validation

Verify all outputs were generated correctly:

```bash
python code/validate_quickstart.py
```

This script checks:
- Directory structure integrity
- File existence and checksums
- Data format validity
- Expected columns in output files

**Output:** `results/validation/quickstart_pass.json` (exit code 0 on success)

## Troubleshooting

### Common Issues

1. **UK Biobank authentication failed**
 - Verify `UKB_TOKEN` is set in `.env`
 - Ensure token has not expired

2. **Out of memory errors**
 - Ensure system has at least 7GB available RAM
 - Streaming batches are automatically sized based on memory pressure

3. **Missing dependencies**
 - Re-run `pip install -r code/requirements.txt`
 - Check for version conflicts

## Next Steps

After successful completion:
- Review `results/associations/main_effects.parquet` for significant associations
- Examine `results/plots/manhattan_plot.png` for visualization of results
- Read `results/sensitivity/` reports for robustness checks

For detailed methodology, refer to `docs/methodology.md` and the original specification documents in `specs/`.
