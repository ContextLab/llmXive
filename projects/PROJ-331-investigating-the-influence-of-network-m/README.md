# Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

This project implements an automated science pipeline to investigate how structural network motifs in the human brain influence resting-state functional connectivity (rsFC). The pipeline downloads high-quality diffusion-weighted imaging (DWI) and rs-fMRI data from the Human Connectome Project (HCP), processes it to derive structural connectomes, quantifies 3-node network motifs, and correlates motif prevalence with functional connectivity strength.

## Key Features

- **Automated Data Pipeline**: Fetches HCP data, preprocesses DWI streamlines into weighted structural connectomes using Schaefer parcellation, and computes rsFC matrices.
- **Motif Quantification**: Enumerates all 13 possible directed 3-node subgraphs, computes z-score prevalence against degree-preserving null models.
- **Statistical Analysis**: Performs partial correlation analysis between motif z-scores and rsFC strength, controlling for global node degree. Applies Bonferroni correction and permutation testing for significance.
- **Automated Reporting**: Generates a comprehensive PDF report with scatter plots, statistical results, power analysis, and methods documentation.

## Project Structure

```
.
├── code/ # Python implementation modules
│ ├── config.py # Configuration and path management
│ ├── download.py # Data download and validation
│ ├── preprocess.py # Connectome processing and parcellation
│ ├── motifs.py # Motif enumeration and z-score computation
│ ├── stats.py # Statistical analysis and correlation
│ ├── report.py # PDF report generation
│ ├── utils.py # Logging, error handling, file I/O
│ └──...
├── data/
│ ├── raw/ # Downloaded raw data (HCP DWI, rs-fMRI)
│ ├── processed/ # Processed matrices, metrics, and manifests
│ └── logs/ # Pipeline execution logs
├── results/ # Final analysis results and PDF reports
├── specs/ # Feature specifications and design docs
├── tests/ # Unit and integration tests
├── docs/ # Documentation templates
├── scripts/ # Utility scripts for validation and hashing
└── README.md # This file
```

## Prerequisites

- Python 3.8 or higher
- Access to the Human Connectome Project (HCP) data (requires S3 bucket access or pre-downloaded data)
- Sufficient disk space (~50GB for raw data, ~10GB for processed data)
- Sufficient memory (~16GB RAM for processing)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` includes:
 - `numpy`, `scipy`, `pandas` for numerical operations
 - `networkx`, `igraph` for graph analysis
 - `nibabel` for neuroimaging data
 - `matplotlib`, `seaborn` for visualization
 - `reportlab`, `weasyprint` for PDF generation
 - `statsmodels` for statistical testing
 - `tqdm`, `joblib` for progress tracking and parallelization
 - `requests` for data downloading

4. **Verify HCP access** (if downloading data):
 ```bash
 bash scripts/verify_hcp_access.sh
 ```

## Usage Guide

### Quick Start

For a complete walkthrough, see [quickstart.md](quickstart.md).

### Running the Full Pipeline

The pipeline is executed in stages. Each stage can be run independently or as part of the full workflow.

1. **Download and validate subject list**:
 ```bash
 python code/download.py --step load_subjects
 ```

2. **Download subject data** (DWI and rs-fMRI):
 ```bash
 python code/download.py --step download_all
 ```

3. **Preprocess data** (parcellation, binarization, rsFC computation):
 ```bash
 python code/preprocess.py --step process_all
 ```

4. **Compute motif profiles**:
 ```bash
 python code/motifs.py --step analyze_all
 ```

5. **Run statistical analysis**:
 ```bash
 python code/stats.py --step analyze_all
 ```

6. **Generate PDF report**:
 ```bash
 python code/report.py --step generate_report
 ```

### Running Individual Scripts

Each script in `code/` can be run with the `--help` flag to see available options:

```bash
python code/download.py --help
python code/preprocess.py --help
python code/motifs.py --help
python code/stats.py --help
python code/report.py --help
```

### Validation

Validate the entire pipeline execution:
```bash
bash scripts/validate_quickstart.sh
```

Generate checksums for all artifacts:
```bash
bash scripts/hash_artifacts.sh
```

### Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific test modules:
```bash
pytest tests/unit/test_download.py -v
pytest tests/unit/test_motifs.py -v
pytest tests/integration/test_pipeline.py -v
```

## Configuration

Edit `code/config.py` to customize:
- Data paths (`DATA_DIR`, `RAW_DIR`, `PROCESSED_DIR`)
- Random seeds for reproducibility
- HCP bucket configuration
- Processing parameters (e.g., parcellation atlas, motif thresholds)

## Output Artifacts

The pipeline produces the following key outputs:

- `data/processed/subject_list_manifest.json`: List of processed subjects
- `data/processed/weighted_adjacency.npy`: Weighted structural connectomes
- `data/processed/canonical_binary_adj.npy`: Binarized structural connectomes
- `data/processed/rsfc.npy`: Resting-state functional connectivity matrices
- `data/processed/motif_profiles.json`: Motif z-scores per subject
- `data/processed/subject_metrics.csv`: Aggregated metrics for correlation analysis
- `results/correlation_results.json`: Partial correlation results
- `results/permutation_results.json`: Permutation test results
- `results/power_analysis.json`: Power analysis details
- `results/report.pdf`: Final PDF report

## Statistical Transparency

All statistical parameters (Bonferroni alpha, permutation count, random seed, library versions) are logged to `data/logs/pipeline.log` and embedded in the PDF report's methods section, ensuring full reproducibility.

## License

This project is part of the llmXive automated science initiative. See the project repository for licensing details.

## Acknowledgments

Data provided by the Human Connectome Project, WU-Minn Consortium (Principal Investigators: David Van Essen and Kamil Ugurbil; 1U54MH091657) funded by the 16 NIH Institutes and Centers that support the NIH Blueprint for Neuroscience Research; and the McDonnell Center for Systems Neuroscience at Washington University.

## Disclaimer

These findings are associational only and do not imply causation.