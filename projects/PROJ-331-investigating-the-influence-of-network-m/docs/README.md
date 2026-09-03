# Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

This project implements an automated pipeline to retrieve, preprocess, and analyze structural and resting-state functional connectivity data. It investigates the relationship between network motif prevalence and functional connectivity strength, controlling for global node degree.

## Project Structure

```
.
├── code/ # Core implementation modules
│ ├── config.py # Configuration and paths
│ ├── download.py # Data retrieval from HCP
│ ├── preprocess.py # Parcellation and connectivity computation
│ ├── motifs.py # Motif enumeration and z-score calculation
│ ├── stats.py # Statistical analysis (correlation, permutation)
│ ├── report.py # PDF report generation
│ ├── utils.py # Logging and I/O utilities
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data (HCP)
│ ├── processed/ # Processed matrices and metrics
│ └── logs/ # Pipeline execution logs
├── results/ # Final analysis results and reports
├── tests/ # Unit and integration tests
├── scripts/ # Utility scripts (hashing, verification)
└── docs/ # Documentation
```

## Prerequisites

- Python 3.9+
- Required packages listed in `requirements.txt`
- Access to HCP data (via S3 bucket or local seed)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. **Verify Data Access**:
 ```bash
 bash scripts/verify_hcp_access.sh
 ```
 This creates `data/raw/.access_verified` if the HCP bucket is reachable.

2. **Run the Pipeline**:
 The main entry point is `code/main.py` (orchestrates all stages).
 ```bash
 python -m code.main
 ```
 This will:
 - Download subject data (streaming if large)
 - Parcellate streamlines to weighted adjacency matrices
 - Binarize using median graph density
 - Compute rsFC and global efficiency
 - Enumerate motifs and compute z-scores
 - Run statistical correlations and permutation tests
 - Generate `results/report.pdf`

3. **Validate**:
 ```bash
 python -m code.validate_quickstart
 ```

## Configuration

Edit `code/config.py` to modify:
- `HCP_BUCKET_ID`: S3 bucket identifier
- `ATLAS_PATH`: Path to Schaefer atlas
- `SUBJECT_IDS`: List of subjects to process
- Random seeds and logging levels

## Output Artifacts

- `data/processed/weighted_adjacency.npy`: Weighted structural connectome
- `data/processed/canonical_binary_adj.npy`: Binarized connectome
- `data/processed/motif_profiles.json`: Z-scores per motif
- `results/correlation_results.json`: Partial correlation results
- `results/report.pdf`: Final scientific report

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## License

[Insert License Information]
