# Quickstart Guide: Motif-RSFC Pipeline

This guide provides step-by-step instructions to run the full **Investigating the Influence of Network Motifs on Resting-State Functional Connectivity** pipeline on a fresh environment.

## Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: Version 3.9 or higher
- **Disk Space**: At least 50 GB free (for raw data and processed artifacts)
- **Internet Access**: Required to download HCP data and Python dependencies
- **HCP Access**: Ensure you have anonymous access to the HCP S3 bucket as per the project's `research.md` configuration.

## Step 1: Environment Setup

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-root>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

4. **Verify HCP connectivity** (Optional but recommended):
 ```bash
 bash scripts/verify_hcp_access.sh
 ```
 Ensure this script completes successfully and creates `data/raw/.access_verified`.

## Step 2: Project Initialization

1. **Initialize project directories**:
 ```bash
 python code/setup_project.py
 ```
 This creates `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, and `state/`.

2. **Configure the pipeline**:
 Edit `code/config.py` if necessary to set `EXPECTED_COHORT_SIZE` or other constants.

## Step 3: Run the Full Pipeline

The pipeline is executed in stages. Run the following commands in order:

### 3.1 Download and Process Subject Data (US1)
This stage downloads raw DWI and rsfMRI data, performs Schaefer parcellation, and generates connectomes.

```bash
python code/download.py --mode full
```
*Output*: `data/processed/subject_list_manifest.json`, `data/processed/weighted_adjacency.npy`, `data/processed/canonical_binary_adj.npy`, `data/processed/rsfc.npy`.

### 3.2 Motif Quantification (US2)
This stage enumerates 3-node motifs, computes z-scores against null models, and aggregates profiles.

```bash
python code/motifs.py --mode full
```
*Output*: `data/processed/motif_profiles.json`, `data/processed/sensitivity_z*.json`.

### 3.3 Statistical Analysis and Reporting (US3)
This stage correlates motif scores with functional connectivity, applies Bonferroni correction, runs permutation tests, and generates the final PDF report.

```bash
python code/stats.py --mode full
python code/report.py --mode full
```
*Output*: `results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`, `results/results.pdf`.

## Step 4: Validation

Verify that the pipeline executed correctly and all artifacts are present:

1. **Check Success Rate**:
 Inspect `data/processed/success_rate.json`. The `success_rate` should match the ratio of completed subjects to `subjects_attempted`.

2. **Validate Statistical Logging**:
 Ensure `data/logs/pipeline.log` contains the required parameters (Bonferroni alpha, seed, library versions, permutation count, VIF threshold) by running:
 ```bash
 python code/utils.py --validate-log
 ```

3. **Verify PDF Report**:
 Open `results/results.pdf` and confirm the presence of:
 - Correlation plots with confidence intervals
 - Sensitivity analysis across z-thresholds
 - Power analysis section
 - Limitations section
 - Mandatory disclaimer: "These findings are associational only and do not imply causation."

4. **Run Automated Validation Script**:
 ```bash
 bash scripts/validate_quickstart.sh
 ```
 This script re-runs key steps in a clean environment and verifies all outputs against expected schemas.

## Troubleshooting

- **HCP Download Failures**: If `stream_hcp_dwi` fails, verify your internet connection and the `HCP_S3_BUCKET` configuration in `code/config.py`. Ensure no firewall is blocking S3 access.
- **Timeout Errors**: If motif enumeration exceeds 300s per subject, the pipeline will log a warning and skip that subject. Check `data/logs/pipeline.log` for details.
- **Missing Dependencies**: If `pip install` fails, ensure you are using Python 3.9+ and that `requirements.txt` is up to date.

## Next Steps

After a successful run, you can:
- Analyze the `results/results.pdf` for scientific insights.
- Customize the analysis by modifying parameters in `code/config.py`.
- Extend the pipeline by implementing additional user stories or feature flags.

For more details, refer to the main `README.md` and the `specs/feature/motif-rsfc/` documentation.