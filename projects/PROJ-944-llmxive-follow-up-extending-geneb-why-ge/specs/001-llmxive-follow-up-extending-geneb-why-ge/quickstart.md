# Quickstart: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

## Prerequisites

- Python 3.11+
- 2 CPU cores, 7GB RAM, 14GB disk (GitHub Actions free-tier compatible)
- Internet access (to download GENEB datasets from Hugging Face)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive/projects/PROJ-944-llmxive-follow-up-extending-geneb-why-ge
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

 The `requirements.txt` pins:
 - `pandas>=2.0.0`
 - `numpy>=1.24.0`
 - `scikit-learn>=1.3.0`
 - `scipy>=1.11.0`
 - `datasets>=2.14.0`
 - `pyyaml>=6.0.0`
 - `pytest>=7.4.0`

## Running the Pipeline

### Step 1: Download Metadata and Raw Sequences

```bash
python code/main.py --step download_extract
```

This will:
- Download `problems.csv` (metadata/scores) from Hugging Face.
- Download raw sequences from the `sequences` split (or FASTA) of the primary GENEB dataset.
- Compute 13 sequence features (AT-Content excluded) for each task.
- Save results to `data/processed/features.csv`.

### Step 2: Train Models and Validate

```bash
python code/main.py --step train_validate
```

This will:
- Train Lasso, Elastic Net, and Random Forest models.
- Perform k-fold cross-validation.
- Output Pearson/Spearman correlations and MAE to `outputs/reports/model_metrics.csv`.

### Step 3: Perform Sensitivity Analysis and Permutation Test

```bash
python code/main.py --step analyze
```

This will:
- Run threshold sweep (0.5 to 0.7).
- Execute a permutation test with a sufficient number of iterations to ensure statistical robustness.
- Generate `outputs/reports/sensitivity.csv` and `outputs/reports/permutation_test.csv`.

### Step 4: Generate Final Report

```bash
python code/main.py --step report
```

This will:
- Compile all results into a summary report (`outputs/reports/final_report.md`).
- Generate figures (e.g., feature importance plots, threshold sweep charts) in `outputs/figures/`.

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

Tests individual components (e.g., feature extraction, model training).

### Integration Tests

```bash
pytest tests/integration/
```

Tests end-to-end pipeline execution.

### Contract Tests

```bash
pytest tests/contract/
```

Validates output data against YAML schemas in `specs/001-gene-regulation/contracts/`.

## Troubleshooting

- **Memory Errors**: If you encounter memory errors, ensure you are not running other heavy processes. The pipeline is designed to fit within 7GB RAM.
- **Dataset Download Failures**: The pipeline retries with exponential backoff. If it fails after multiple retries, check your internet connection or the Hugging Face status page.
- **NaN in Features**: Tasks with extremely low sequence complexity (e.g., mononucleotide repeats) will be flagged in `outputs/reports/diagnostics.csv` with substituted floor values.
- **Spec Typo**: Note that the source spec contains a typo "between and 2.0". The system correctly interprets the lower bound as zero.

## Next Steps

- Review the `outputs/reports/final_report.md` for key findings.
- Examine `outputs/figures/` for visualizations of feature importance and threshold sensitivity.
- Extend the pipeline to include additional sequence features or model architectures if needed.