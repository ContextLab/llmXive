# Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

This project implements an automated pipeline to investigate the relationship between structural network motifs in the human connectome and resting-state functional connectivity (rsFC). The pipeline retrieves, preprocesses, and analyzes diffusion-weighted imaging (DWI) and resting-state fMRI data from the Human Connectome Project (HCP).

## Features

- **Data Pipeline**: Automated download and preprocessing of HCP data (DWI and rs-fMRI).
- **Structural Connectome**: Parcellation using the Schaefer atlas and generation of weighted/binary adjacency matrices.
- **Motif Analysis**: Enumeration of all directed 3-node subgraphs (motifs) and calculation of z-score prevalence against degree-preserving null models.
- **Statistical Analysis**: Correlation of motif profiles with rsFC strength and global efficiency, controlling for global node degree, with Bonferroni correction and permutation testing.
- **Reporting**: Automatic generation of a comprehensive PDF report including scatter plots, statistical results, and limitations.

## Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Linux (recommended for HCP data access and Dipy compatibility) or macOS
- **Disk Space**: Minimum 50 GB (for raw and processed data)
- **Memory**: Minimum 16 GB RAM (recommended 32 GB for motif analysis)
- **Internet Connection**: Required for downloading HCP data

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify HCP access** (optional but recommended):
 ```bash
 bash scripts/verify_hcp_access.sh
 ```

## Usage

### Quick Start

For a detailed step-by-step guide, see `quickstart.md`.

To run the full pipeline:

```bash
python code/main.py
```

This command will:
1. Download and process subject data (if not already present).
2. Compute structural connectomes and rsFC matrices.
3. Analyze network motifs.
4. Perform statistical correlation analysis.
5. Generate a PDF report in the `results/` directory.

### Configuration

Edit `code/config.py` to customize:
- `EXPECTED_COHORT_SIZE`: Number of subjects to process.
- `N_MOTIF_NODES`: Size of motifs to analyze (default: 3).
- Paths to data directories.
- Random seeds for reproducibility.

### Output Artifacts

The pipeline generates the following artifacts:
- `data/raw/`: Raw HCP data (DWI, rs-fMRI) and checksums.
- `data/processed/`: Processed connectomes, motif profiles, and metrics.
- `results/`: Statistical results, permutation test outputs, and the final PDF report.
- `data/logs/pipeline.log`: Detailed execution log.

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and constants
│ ├── download.py # Data downloading and streaming
│ ├── preprocess.py # Connectome parcellation and processing
│ ├── motifs.py # Motif enumeration and z-score calculation
│ ├── stats.py # Statistical analysis (correlation, VIF, permutation)
│ ├── report.py # PDF report generation
│ ├── utils.py # Utilities (logging, file I/O)
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Raw input data
│ ├── processed/ # Processed data and intermediate results
│ └── logs/ # Execution logs
├── results/ # Final analysis results and reports
├── specs/ # Feature specifications and data models
├── tests/ # Unit and integration tests
├── scripts/ # Utility scripts (checksums, validation)
├── requirements.txt # Python dependencies
├── quickstart.md # Step-by-step execution guide
└── README.md # This file
```

## Dependencies

Key dependencies include:
- `numpy`, `scipy`, `pandas`: Data manipulation
- `networkx`, `igraph`: Graph analysis and motif enumeration
- `nibabel`, `dipy`: Neuroimaging data handling
- `statsmodels`: Statistical tests (partial correlation, power analysis)
- `reportlab`, `matplotlib`: Report and plot generation
- `requests`: Data downloading
- `tqdm`: Progress bars

See `requirements.txt` for the complete list.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

Please ensure your code passes all tests and follows the project's linting standards (configured in `setup.cfg` or `pyproject.toml`).

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Disclaimer

These findings are associational only and do not imply causation.