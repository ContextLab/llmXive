# Quickstart: Predicting Plant Defense Compound Production

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI execution) or local Linux environment.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-503-predicting-plant-defense-compound-produc
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Data Acquisition

The pipeline automatically downloads data upon first run. To manually verify:

1. **Download Expression Data**:
   ```bash
   python code/data/download.py --source geo --ids GSE21857,GSE167633
   ```
   *Output*: `data/raw/geo_expression.csv`

2. **Download Metabolite Data**:
   ```bash
   python code/data/download.py --source mw --ids ST002565
   ```
   *Output*: `data/raw/mw_metabolites.csv`

3. **Verify Checksums**:
   ```bash
   python code/utils/checksum.py --verify
   ```
   *Output*: "All checksums valid" or raises `E-DATASET`.

## Running the Pipeline

Execute the full pipeline:

```bash
python code/main.py
```

### Steps Performed:
1. **Pairing**: Matches samples by ID. Aborts if < 95% match rate (`E-PAIRING`) or if final paired set size < 40 (`E-POWER`).
2. **Preprocessing**: Normalizes expression, log-transforms metabolites, filters zero-variance genes, applies z-score normalization and ComBat batch correction.
3. **Feature Selection**: Filters for KEGG defense pathways.
4. **Modeling**: Trains Ridge Regression (nested 5-fold CV).
5. **Validation**: Runs max-T permutation test with a sufficient number of iterations to ensure stable p-value estimation and Bonferroni correction.
6. **Species Confounding Check**: Validates that predictions are not driven by species identity.

### Output:
- `data/processed/paired_data.csv`: Final dataset.
- `results/model_metrics.json`: RMSE, Pearson r, p-values.
- `logs/data_pairing.json`: Log of unmatched samples.
- `logs/feature_filtering.csv`: Log of removed genes.

## Troubleshooting

- **Error: E-PAIRING**: Check `logs/data_pairing.json` to see which samples failed to match. Ensure sample IDs in GEO and Metabolomics Workbench align.
- **Error: E-POWER**: The final paired set size is < 40. The study is underpowered. Consider expanding the dataset or reframing the question.
- **Error: E-TIMEOUT**: The pipeline exceeded the target duration. Consider reducing the dataset size or optimizing the permutation test iterations (if allowed by spec).
- **Error: E-DATASET**: Checksum mismatch. Re-run download or verify internet connection.

## Data Hygiene

- **Raw Data**: Never modify files in `data/raw/`.
- **Derived Data**: All processed files in `data/processed/` are versioned.
- **Reproducibility**: Set `PYTHONHASHSEED=0` before running to ensure deterministic results.