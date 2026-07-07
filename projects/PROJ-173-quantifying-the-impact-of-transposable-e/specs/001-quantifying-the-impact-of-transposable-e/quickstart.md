# Quickstart: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

## Prerequisites

- Python 3.10 or higher
- pip
- git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-173-quantifying-the-impact-of-transposable-e
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline consists of three main steps: Data Generation, Association Analysis, and Permutation Testing.

### Step 1: Generate Mock Data
Generates synthetic TE genotypes, gene expression, and population PCs.
```bash
python code/main.py generate-data --lines 100 --output data/mock/
```
*Output*: `data/mock/te_genotypes.csv`, `data/mock/gene_expression.csv`, `data/mock/population_pcs.csv`.

### Step 2: Run Association Analysis
Fits linear models, calculates VIF, applies FDR correction, and outputs results.
```bash
python code/main.py run-association --input data/mock/ --output data/results/
```
*Output*: `data/results/association_results.csv`, `data/results/population_structure_metrics.csv`.

### Step 3: Run Permutation Testing
Performs 1000 Freedman-Lane permutations for significant pairs.
```bash
python code/main.py run-permutation --input data/results/association_results.csv --output data/results/ --iterations 1000
```
*Output*: `data/results/permutation_results.csv`, `data/results/null_distribution_plot.png`.

### Step 4: Run Replication (Optional)
Tests significant pairs on a second mock dataset.
```bash
python code/main.py run-replication --primary data/results/association_results.csv --secondary data/mock/secondary/ --output data/results/
```

## Validation

Run the test suite to ensure all contract schemas are met:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Reduce `--lines` in `generate-data` or `--iterations` in `run-permutation`.
- **Timeout**: If permutation exceeds 6 hours, reduce `--iterations` to 500.
- **Missing Data**: The pipeline automatically excludes lines with missing expression values.
