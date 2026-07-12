# Predicting Molecular Complexity Using Information Theory

This project investigates the correlation between information-theoretic metrics (Shannon Entropy, Lempel-Ziv Complexity) and established chemical complexity scores (Synthetic Accessibility, QED) using a large-scale dataset of canonicalized SMILES strings.

## Prerequisites

- Python 3.11+
- pip (package installer)
- Virtual environment (recommended)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-425-predicting-molecular-complexity-using-in
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
 ```

4. **Verify installation**:
 Ensure `rdkit`, `pandas`, `numpy`, and `scikit-learn` are importable:
 ```bash
 python -c "import rdkit; import pandas; print('Dependencies OK')"
 ```

## Quick Start

To run the full pipeline (Download -> Sample -> Compute Metrics -> Analysis -> Visualization):

```bash
python code/main.py
```

This will:
1. Download and sample the `sagawa/pubchemm-canonicalized` dataset.
2. Compute Shannon Entropy, LZ Complexity, SA, and QED scores.
3. Perform statistical analysis (Pearson correlation, bootstrap CI).
4. Generate visualizations and a JSON report.

Output files will be located in:
- `data/raw/` (raw downloaded data)
- `data/processed/` (computed metrics)
- `reports/` (statistics and figures)

## Project Structure

```text
.
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── download.py # Data loading and sampling
│ ├── metrics.py # Metric computation functions
│ ├── analysis.py # Statistical analysis
│ ├── viz.py # Visualization generation
│ └── main.py # Orchestration script
├── data/
│ ├── raw/ # Raw dataset files
│ └── processed/ # Processed metrics CSV
├── reports/
│ ├── figures/ # Generated plots
│ └── stats.json # Statistical results
├── tests/ # Unit and contract tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Detailed usage guide
```

## License

MIT License
