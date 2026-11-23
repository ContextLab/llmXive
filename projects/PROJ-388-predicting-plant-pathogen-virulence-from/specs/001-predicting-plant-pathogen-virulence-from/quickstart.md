# Quickstart: Predicting Plant Pathogen Virulence

## Prerequisites
- Python 3.11+
- `hmmsearch` (from HMMER suite) installed and in PATH.
- Access to NCBI E-utilities (internet required).
- Internet access for downloading PHI-base (or literature tables).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Step 1: Download and Extract Data
Execute the data ingestion pipeline. This will:
- Fetch genomes for *Fusarium*, *Pseudomonas*, *Xanthomonas*.
- Extract virulence genes and TF binding sites.
- Merge with phenotypic data.
- Fallback to species-level aggregation if isolate linkage fails.

```bash
python src/main.py --mode download_and_extract
```
*Output*: `data/processed/feature_matrix.csv`, `data/processed/phenotype_vector.csv`

### Step 2: Construct Phylogeny
Build the phylogenetic tree from **housekeeping genes** (e.g., rpoB, gyrB) using Maximum Likelihood.
```bash
python src/main.py --mode build_phylogeny
```
*Output*: `data/processed/tree.newick`, `data/processed/phylo_covariance_matrix.npy`

### Step 3: Run Statistical Analysis
Perform correlation analysis.
- If N >= 10: Runs Phylogenetic Signal-Adjusted Spearman / Lasso with FDR correction.
- If N < 10: Generates a **Descriptive Summary** (no statistical testing).
```bash
python src/main.py --mode analyze
```
*Output*: `data/results/correlation_table.csv` OR `data/results/descriptive_summary.json`

### Step 4: Generate Visualizations
Create the heatmap of top significant features (if statistical results exist).
```bash
python src/main.py --mode visualize
```
*Output*: `output/heatmap.png`

## Reproducibility
To verify reproducibility:
1.  Open `analysis_notebook.ipynb`.
2.  Run all cells.
3.  Verify that the output tables match `data/results/correlation_table.csv` within tolerance.

## Troubleshooting
- **Rate Limiting**: The pipeline implements exponential backoff. If NCBI is unavailable, it will retry up to 5 times.
- **Missing Phenotypes**: If > 50% of isolates lack phenotypes, the system automatically switches to species-level aggregation. Check `logs/pipeline.log` for the message "Falling back to species-level aggregation".
- **Small Sample Size**: If N < 10, the pipeline will skip statistical testing and output a descriptive summary. Check `data/results/descriptive_summary.json`.
- **hmmsearch Not Found**: Ensure HMMER is installed: `sudo apt-get install hmmer` (Ubuntu) or `brew install hmmer` (Mac).