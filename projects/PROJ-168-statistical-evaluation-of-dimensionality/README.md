# Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

This project implements an automated pipeline to download scRNA-seq datasets, preprocess them, generate dimensionality reduction embeddings (PCA, t-SNE, UMAP), compute geometric fidelity metrics, and perform statistical evaluation of the results.

## Installation

### Prerequisites

- Python 3.9+
- Conda (recommended) or pip
- Snakemake
- Required system packages: `time` (for resource monitoring)

### Setup with Conda

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd projects/001-statistical-evaluation-of-dimensionality
 ```

2. Create the conda environment:
 ```bash
 conda env create -f environment.yml
 conda activate stat_dim_eval
 ```

3. Alternatively, generate `requirements.txt` and install with pip:
 ```bash
 python code/scripts/generate_requirements.py
 pip install -r code/requirements.txt
 ```

### Project Structure

```
projects/001-statistical-evaluation-of-dimensionality/
├── code/ # Pipeline implementation scripts
│ ├── config.py # Configuration and paths
│ ├── download.py # Data acquisition
│ ├── preprocess.py # QC and HVG selection
│ ├── embeddings.py # PCA, t-SNE, UMAP generation
│ ├── geometry.py # Linearity and continuity metrics
│ ├── clustering.py # Leiden clustering and fidelity
│ ├── stats.py # Statistical modeling
│ ├── main.py # Pipeline entry point
│ └──...
├── data/
│ ├── raw/ # Downloaded raw count matrices
│ └── processed/ # Preprocessed data
├── results/ # Analysis outputs and reports
├── docs/ # Documentation
├── environment.yml # Conda environment definition
├── Snakefile # Snakemake workflow
└── README.md
```

## Usage

### Quick Start

1. Ensure all dependencies are installed.
2. Run the full pipeline:
 ```bash
 python code/main.py
 ```
 or via Snakemake directly:
 ```bash
 snakemake --cores 4
 ```

3. The pipeline will:
 - Check data availability for GSE131907, GSE111322, GSE150728
 - Download and preprocess raw count matrices
 - Generate PCA, t-SNE, and UMAP embeddings
 - Compute geometric fidelity metrics (Trustworthiness, LCA)
 - Perform clustering and calculate ARI/NMI
 - Fit statistical models (Fixed-Effects ANOVA or Mixed-Effects)
 - Generate reports in `results/`

### Configuration

Edit `code/config.py` to modify:
- Dataset accessions
- Random seeds
- Path configurations
- Hyperparameters for embeddings and clustering

### Output

Results are stored in `results/`:
- `summary.json`: Pipeline summary and status
- `monitoring.csv`: Resource usage metrics
- `geometry_metrics.csv`: Linearity and continuity scores
- `fidelity_metrics.csv`: ARI/NMI scores
- `stats_results.json`: Statistical model outputs
- `data_gap_report.json`: Data availability report

## Data Gap Resolution

The pipeline automatically checks for raw count matrices in GEO. If no datasets are found, it aborts. If one dataset is found, it switches to "Case-Study Mode" (descriptive only). If multiple are found, it proceeds with full statistical modeling.

## License

This project is licensed under the MIT License.
