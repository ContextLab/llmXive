# Usage Guide: Network Motif Analysis Pipeline

This guide provides detailed instructions for using the pipeline to analyze network motifs in structural connectomes and their relationship to functional connectivity.

## Quick Start

### 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Subjects

Open `code/config.py` and set `SUBJECT_IDS` to the HCP IDs you wish to analyze:

```python
SUBJECT_IDS = ["100307", "100408"] # Example IDs
```

### 3. Verify Data Access

Ensure you can reach the HCP S3 bucket:

```bash
bash scripts/verify_hcp_access.sh
```

If successful, a `.access_verified` flag will be created in `data/raw/`.

### 4. Run the Pipeline

Execute each stage sequentially:

```bash
# Stage 1: Download data
python code/download.py

# Stage 2: Preprocess connectomes
python code/preprocess.py

# Stage 3: Compute motifs
python code/motifs.py

# Stage 4: Statistical analysis
python code/stats.py

# Stage 5: Generate report
python code/report.py
```

## Detailed Stage Descriptions

### Stage 1: Data Download (`code/download.py`)

- **Input**: `SUBJECT_IDS` from config.
- **Process**: Downloads DWI (`.trk`) and rs-fMRI (`.nii.gz`) from HCP.
- **Output**: Files in `data/raw/`.
- **Error Handling**: Fails loudly if a subject's data is missing; no synthetic fallback.

### Stage 2: Preprocessing (`code/preprocess.py`)

- **Input**: DWI streamlines, rs-fMRI time series, Schaefer atlas.
- **Process**:
 1. Parcellates streamlines to weighted adjacency matrix.
 2. Binarizes using cohort-level median density.
 3. Computes rsFC (Pearson correlation) and global efficiency.
- **Output**:
 - `data/processed/weighted_adjacency.npy`
 - `data/processed/canonical_binary_adj.npy`
 - `data/processed/rsfc.npy`
 - `data/processed/global_efficiency.json`

### Stage 3: Motif Quantification (`code/motifs.py`)

- **Input**: Binary structural connectomes.
- **Process**:
 1. Enumerates all 13 directed 3-node motifs.
 2. Generates degree-preserving null models (Maslov-Sneppen).
 3. Computes z-scores: `z = (observed - mean_null) / std_null`.
 4. Performs sensitivity analysis across z-thresholds {1.5, 2.0, 2.5}.
- **Output**:
 - `data/processed/motif_profiles.json`
 - `data/processed/sensitivity_z<value>.json`

### Stage 4: Statistical Analysis (`code/stats.py`)

- **Input**: Motif profiles, rsFC matrices, global efficiency, binary connectomes.
- **Process**:
 1. Aggregates metrics into `subject_metrics.csv`.
 2. Computes VIF for control variable (global node degree).
 3. Calculates partial correlations (Pearson & Spearman) controlling for node degree.
 4. Applies Bonferroni correction across all motifs.
 5. Runs permutation tests (≥1000 iterations) for significant motifs.
 6. Performs power analysis.
- **Output**:
 - `data/processed/subject_metrics.csv`
 - `results/correlation_results.json`
 - `results/permutation_results.json`
 - `results/power_analysis.json`

### Stage 5: Report Generation (`code/report.py`)

- **Input**: Statistical results, power analysis, layout template.
- **Process**:
 1. Loads layout from `docs/report_layout_template.json`.
 2. Generates scatter plots for significant motifs.
 3. Embeds methods section from `pipeline.log`.
 4. Adds mandatory disclaimer.
- **Output**: `results/report.pdf`

## Advanced Usage

### Custom Thresholds

Modify sensitivity thresholds in `code/motifs.py` (default: `[1.5, 2.0, 2.5]`).

### Parallel Execution

Use `joblib` or `multiprocessing` to parallelize subject processing in `download.py` and `motifs.py` (ensure CI disk limits are respected).

### Logging

All logs are written to `data/logs/pipeline.log`. Inspect this file for debugging or to extract statistical parameters for the report.

## Troubleshooting

- **HCP Access Error**: Ensure `scripts/verify_hcp_access.sh` passes. Check network and credentials.
- **Timeout in Motif Counting**: If a subject exceeds 300s, the pipeline falls back to `igraph` (see `code/motifs.py`).
- **Zero Variance in Motifs**: If a motif has zero variance across subjects, the report will state "insufficient variance" instead of a p-value.

## Data Provenance

Each processed artifact includes a sidecar JSON file (e.g., `<subject_id>_provenance.json`) with source files, processing steps, and timestamps.

## References

- Human Connectome Project (HCP): https://www.humanconnectome.org/
- Schaefer Parcellation: https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal
- Network Motifs: Milo et al. (2002) Science
