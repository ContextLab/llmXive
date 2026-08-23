# llmXive Project: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Overview

This project implements an automated science pipeline to investigate how structural network motifs influence resting-state functional connectivity (rsFC) in the human brain. It processes diffusion-weighted imaging (DWI) and resting-state fMRI data from the Human Connectome Project (HCP), constructs structural and functional connectomes, quantifies network motifs, and performs statistical correlation analysis.

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── config.py # Configuration and paths
│ ├── utils.py # Utility functions (logging, file I/O)
│ ├── download.py # Data retrieval from HCP
│ ├── preprocess.py # Connectome preprocessing
│ ├── motifs.py # Motif enumeration and z-score computation
│ ├── stats.py # Statistical analysis (correlation, permutation)
│ ├── report.py # PDF report generation
│ └── save_outputs.py # Artifact saving with provenance
├── data/
│ ├── raw/ # Downloaded HCP data (DWI, rs-fMRI)
│ ├── processed/ # Connectomes, motif profiles, metrics
│ └── logs/ # Pipeline execution logs
├── results/ # Final analysis outputs (PDF, JSON)
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── scripts/ # Utility scripts
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- Access to the HCP S3 bucket (anonymous or credentials configured)
- Sufficient disk space (~7GB RAM / ~14GB disk for full dataset)

## Installation

1. Clone the repository.
2. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

3. Verify HCP access (optional but recommended):

 ```bash
 bash scripts/verify_hcp_access.sh
 ```

## Usage

### Full Pipeline Execution

To run the entire pipeline from data download to report generation:

```bash
python code/download.py
python code/preprocess.py
python code/motifs.py
python code/stats.py
python code/report.py
```

Each script processes its respective stage and writes outputs to `data/processed/`, `results/`, and logs to `data/logs/pipeline.log`.

### Individual Stage Execution

- **Download**: `python code/download.py`
 - Downloads DWI and rs-fMRI data for configured subjects.
 - Outputs: `data/raw/<subject_id>_dwi.trk`, `data/raw/<subject_id>_rsfmri.nii.gz`

- **Preprocess**: `python code/preprocess.py`
 - Parcellates streamlines, binarizes connectomes, computes rsFC and global efficiency.
 - Outputs: `data/processed/weighted_adjacency.npy`, `data/processed/canonical_binary_adj.npy`, `data/processed/rsfc.npy`, `data/processed/global_efficiency.json`

- **Motifs**: `python code/motifs.py`
 - Enumerates 3-node motifs, computes z-scores against null models.
 - Outputs: `data/processed/motif_profiles.json`, `data/processed/sensitivity_z<value>.json`

- **Stats**: `python code/stats.py`
 - Computes partial correlations, Bonferroni correction, permutation tests.
 - Outputs: `results/correlation_results.json`, `results/permutation_results.json`, `results/power_analysis.json`

- **Report**: `python code/report.py`
 - Generates a PDF report with scatter plots, statistical results, and methods.
 - Outputs: `results/report.pdf`

## Configuration

Edit `code/config.py` to modify:
- `SUBJECT_IDS`: List of HCP subject IDs to process.
- `ATLAS_PATH`: Path to the Schaefer parcellation atlas.
- `RANDOM_SEED`: Random seed for reproducibility.
- `PERMUTATIONS`: Number of permutations for statistical testing.

## Testing

Run unit tests:

```bash
python -m pytest tests/unit/ -v
```

Run integration tests:

```bash
python -m pytest tests/integration/ -v
```

## Output Artifacts

- `data/processed/structural_connectome_metadata.json`: Status flags for each subject.
- `data/processed/motif_profiles.json`: Aggregated motif z-scores.
- `results/correlation_results.json`: Partial correlation results with Bonferroni correction.
- `results/report.pdf`: Final PDF report.

## Statistical Transparency

All statistical parameters (Bonferroni alpha, permutation count, random seed, library versions) are logged to `data/logs/pipeline.log` and embedded in the PDF report's Methods section.

## Disclaimer

These findings are associational only and do not imply causation.

## License

[Insert License Here]
