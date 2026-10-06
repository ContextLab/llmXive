# Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

This project implements a pipeline to evaluate the stability of effect sizes and the reliability of p-values in genomic differential expression analyses using publicly available datasets from GEO, TCGA, and ENCODE.

## Features

- **Stability Analysis**: Calculates Pearson correlation of log2 fold-changes between full and stratified subset analyses across ALL genes to avoid Winner's Curse.
- **Null Modeling**: Implements stratified block permutation with Fixed-Dispersion Wald Perturbation to generate empirical null distributions.
- **Cross-Dataset Benchmarking**: Aggregates and compares metrics across multiple genomic repositories.

## Prerequisites

- Python 3.11+
- R 4.3+ with DESeq2 and edgeR packages
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-name>
 ```

2. Set up the Python environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Set up the R environment:
 ```bash
 source code/scripts/setup_env.sh
 ```

## Quick Start

See `specs/001-assess-significance-reliability/quickstart.md` for detailed instructions on running the pipeline.

## Project Structure

```
code/
├── src/ # Core Python modules
│ ├── config.py # Configuration constants and paths
│ ├── data_loader.py # Dataset fetching and caching
│ ├── preprocessing.py # Data filtering and stratification
│ ├── de_analysis.py # Differential expression wrapper
│ ├── permutation.py # Permutation testing logic
│ ├── metrics.py # Statistical metric calculations
│ ├── report.py # Visualization and reporting
│ ├── r_config.py # R environment configuration
│ └── versioning.py # Artifact hashing and state management
├── scripts/ # Executable scripts
│ ├── setup_env.sh # Environment initialization
│ ├── run_r_script.R # R differential expression script
│ └── generate_cross_dataset_visualization.py
├── tests/ # Test suite
│ ├── test_data_loader.py
│ ├── test_preprocessing.py
│ ├── test_metrics.py
│ ├── test_permutation.py
│ └──...
├── data/ # Downloaded datasets (gitignored)
└── artifacts/ # Generated reports and figures (gitignored)
```

## Configuration

- **Random Seeds**: Defined in `code/src/config.py` for reproducibility.
- **Runtime Limits**: Default 6-hour limit for permutation tasks.
- **Data Sources**: Configured via manifest file (see `code/src/data_loader.py`).

## Running the Pipeline

1. **Data Loading**: Fetch datasets from GEO, TCGA, or ENCODE.
2. **Preprocessing**: Filter zero-count genes and stratify samples.
3. **Differential Expression**: Run DESeq2/edgeR on full and subset datasets.
4. **Stability Analysis**: Calculate effect size correlations.
5. **Permutation Testing**: Generate empirical null distributions.
6. **Reporting**: Generate Bland-Altman plots and cross-dataset comparisons.

## Testing

Run the test suite:
```bash
pytest code/tests/
```

## License

[Insert License Information]
