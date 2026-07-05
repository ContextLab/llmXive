# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

## Prerequisites

- Python 3.11+
- Docker (for fMRIPrep)
- Git
- Sufficient Disk Space (for dataset and temporary files)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-359-investigating-the-relationship-between-b
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via the main CLI entry point.

### Step 1: Download Data
```bash
python src/cli.py download --dataset ds000277 --output data/raw --sample-size 15
```
*Note: This downloads the dataset from OpenNeuro. The `--sample-size` flag is used for CI feasibility (N=15). Remove for full analysis.*

### Step 2: Preprocess (fMRIPrep)
```bash
python src/cli.py preprocess --input data/raw --output data/preprocessed --fmriprep-version 23.1.3 --nprocs 1 --mem 6000
```
*This step runs fMRIPrep. It may take several hours. Memory limits are enforced.*

### Step 3: Extract Metrics
```bash
python src/cli.py metrics --preprocessed data/preprocessed --atlas Schaefer400 --output data/metrics
```

### Step 4: Run Analysis
```bash
python src/cli.py analyze --metrics data/metrics --behavioral data/raw/phenotypic.tsv --output data/results
```
*This performs the regression, permutation testing, and power analysis. The `baseline_wm_score` column is verified before execution. Power analysis output is written to `data/results/power_analysis.txt`.*

### Step 5: Visualize
```bash
python src/cli.py viz --results data/results --output data/results/effect_sizes.pdf --seed 42
```
*Seed pinning is enforced for reproducibility (SC-004). The `--seed` flag ensures identical hashes on re-run.*

## Verification

Check the `data/results/pipeline_log.json` for the following:
- `id_validation_status`: "PASS"
- `exclusion_motion`: Count of excluded participants (threshold > 3.0mm)
- `exclusion_missing_wm`: Count of excluded participants (missing WM score)
- `runtime`: Total execution time
- `power_analysis.txt`: Check for achieved power report.

## Troubleshooting

- **fMRIPrep OOM**: Reduce `--mem` flag in the preprocessing step or reduce `--sample-size`.
- **Missing Behavioral Data**: Ensure the `ds000277` download includes the phenotypic TSV file. If `baseline_wm_score` is missing, the pipeline will halt.
- **Motion Exclusion**: Check `data/motion/exclusions.csv` to see how many participants were dropped due to FD > 3.0mm.
- **Reproducibility**: Ensure `--seed` is set in the visualization step.