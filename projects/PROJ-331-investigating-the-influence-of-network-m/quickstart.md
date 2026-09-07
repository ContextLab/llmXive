# Quickstart Guide: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

This guide provides step-by-step instructions to set up and run the full pipeline on a fresh environment.
The pipeline retrieves HCP diffusion and rs-fMRI data, constructs structural and functional connectomes,
quantifies 3-node network motifs, and correlates motif prevalence with functional connectivity strength.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Git
- Sufficient disk space (~20GB for raw data, ~5GB for processed data)
- Network access to the HCP S3 bucket (anonymous read access required)

## Installation

1. **Clone the repository**
 ```bash
 git clone <repository_url>
 cd <project_directory>
 ```

2. **Create a virtual environment** (recommended)
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

4. **Verify HCP access** (Optional but recommended)
 Run the access validation script to ensure connectivity to the HCP S3 bucket:
 ```bash
 bash scripts/verify_hcp_access.sh
 ```
 This generates `data/raw/.access_verified` if successful.

## Running the Pipeline

The pipeline is orchestrated by running the main scripts in sequence. Ensure you are in the project root directory.

### Step 1: Project Setup (Run once)
Initializes directory structure and configuration.
```bash
python code/setup_project.py
```

### Step 2: Download Subject List
Loads the list of subject IDs and validates the manifest.
```bash
python code/download.py --step load_subject_list
```
*Output*: `data/processed/subject_list_manifest.json`

### Step 3: Download & Process Data (Full Pipeline)
Downloads raw data, constructs connectomes, computes metrics, and runs motif analysis.
```bash
python code/download.py --step process_subjects
```
*Note*: This step may take several hours depending on network speed and subject count.
*Outputs*:
- `data/processed/weighted_adjacency.npy` (per subject)
- `data/processed/canonical_binary_adj.npy`
- `data/processed/rsfc.npy`
- `data/processed/global_efficiency.json`
- `data/processed/motif_profiles.json`

### Step 4: Statistical Analysis
Computes correlations, applies Bonferroni correction, and runs permutation tests.
```bash
python code/stats.py
```
*Outputs*:
- `results/correlation_results.json`
- `results/permutation_results.json`
- `data/processed/subject_metrics.csv`

### Step 5: Generate Report
Creates the final PDF report with plots and methods section.
```bash
python code/report.py
```
*Output*: `results/report.pdf`

## Validation

To verify the pipeline ran correctly and all outputs are present:
```bash
bash scripts/validate_quickstart.sh
```
This script checks for the existence of all required artifacts and validates their schemas.

## Troubleshooting

- **HCP Access Errors**: Ensure your network allows access to `s3://hcp-openaccess` and that the `verify_hcp_access.sh` script passed.
- **Memory Errors**: If running out of memory during motif enumeration, the pipeline automatically switches to the `igraph` fallback (T050) or times out per SC-002.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` to ensure all packages are installed.
- **Log Files**: Check `data/logs/pipeline.log` for detailed error messages and processing status.

## Output Artifacts

Upon successful completion, the following key artifacts will be available:

| Artifact | Location | Description |
|:--- |:--- |:--- |
| Subject Manifest | `data/processed/subject_list_manifest.json` | List of processed subjects |
| Binary Connectome | `data/processed/canonical_binary_adj.npy` | Thresholded structural matrix |
| Functional Matrix | `data/processed/rsfc.npy` | Resting-state FC matrix |
| Motif Profiles | `data/processed/motif_profiles.json` | Z-scores for 13 directed motifs [UNRESOLVED-CLAIM: c_019999a7 — status=not_enough_info] |
| Correlation Results | `results/correlation_results.json` | Partial correlations & p-values |
| Final Report | `results/report.pdf` | Full analysis report with plots |

## Next Steps

- Review `results/report.pdf` for scientific findings.
- Inspect `data/logs/pipeline.log` for statistical parameters (Bonferroni alpha, seed, etc.).
- Run `scripts/hash_artifacts.sh` to generate checksums for reproducibility.
- Refer to `README.md` for detailed project architecture and API documentation.