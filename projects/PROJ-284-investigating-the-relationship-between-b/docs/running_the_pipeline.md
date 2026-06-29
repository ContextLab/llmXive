# Running the Pipeline: Step-by-Step Guide

This document details how to execute the full research pipeline, from data acquisition to report generation.

## Prerequisites

- **Python 3.11** or higher.
- **HCP Credentials:** Valid username and password for the Human Connectome Project.
- **External Tools (Optional):** FSL and AFNI are required for full local preprocessing validation. If not installed, the pipeline will use synthetic data for validation or skip local preprocessing steps depending on configuration.

## Step 1: Environment Setup

1. **Activate Virtual Environment:**
 ```bash
 source venv/bin/activate
 ```

2. **Set Environment Variables:**
 Export your HCP credentials:
 ```bash
 export HCP_USERNAME="your_username"
 export HCP_PASSWORD="your_password"
 ```
 Alternatively, create a `.env` file in the project root:
 ```
 HCP_USERNAME=your_username
 HCP_PASSWORD=your_password
 ```

3. **Verify Dependencies:**
 ```bash
 pip install -r requirements.txt
 ```

## Step 2: Configuration

Review `code/config.py` to ensure settings match your environment:
- `MEMORY_LIMIT`: Default is 7GB. Adjust if you have more/less RAM.
- `BATCH_SIZE`: Dynamic batch sizing is enabled by default.
- `HCP_API_VERSION`: Ensure this matches the current HCP API version.

## Step 3: Execute the Pipeline

The pipeline can be run as a single monolithic command or module by module.

### Option A: Full Automated Run

Run the main entry point:
```bash
python code/main.py
```
This script orchestrates:
1. Data download (T012)
2. Preprocessing (T013a-c)
3. Metric extraction (T017, T020-T022)
4. Correlation analysis (T023a-e)
5. Visualization (T031, T032)
6. Report generation (T033)

### Option B: Modular Execution

Run individual stages for debugging or partial updates:

1. **Download Data:**
 ```bash
 python code/data/download.py
 ```
 *Outputs:* `data/raw/`

2. **Preprocess Data:**
 ```bash
 python code/data/preprocess.py
 ```
 *Outputs:* `data/processed/` (NIfTI files)

3. **Extract Metrics:**
 ```bash
 python code/data/metrics.py
 ```
 *Outputs:* `data/analysis/` (Time-series, connectivity matrices, graph metrics)

4. **Run Analysis:**
 ```bash
 python code/analysis/correlations.py
 ```
 *Outputs:* `data/analysis/correlation_results.csv`, `data/analysis/pca_loadings.csv`

5. **Generate Visualizations:**
 ```bash
 python code/viz/scatter.py
 python code/viz/network.py
 ```
 *Outputs:* `figures/` (PNG/PDF)

6. **Generate Report:**
 ```bash
 python code/report/generate.py
 ```
 *Outputs:* `docs/report.md`

## Step 4: Validate Outputs

Check the `logs/pipeline.log` for any errors or warnings.
Verify the presence of output files:
- `data/analysis/full_metrics.csv`
- `figures/scatter_plot_*.png`
- `docs/report.md`

## Troubleshooting

- **Missing Dependencies:** Ensure FSL/AFNI are in your PATH if running local preprocessing.
- **Memory Errors:** Reduce `BATCH_SIZE` in `code/config.py` or increase `MEMORY_LIMIT` if hardware allows.
- **API Errors:** Check your HCP credentials and network connection.
