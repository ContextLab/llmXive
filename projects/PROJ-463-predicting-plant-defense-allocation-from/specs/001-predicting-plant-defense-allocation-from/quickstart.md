# Quickstart: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Prerequisites

- Python 3.11+
- Git
- (Optional) R 4.3+ (required for `rpy2` integration with DESeq2/ComBat-seq)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-463-predicting-plant-defense-allocation-from
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
    *Note: `requirements.txt` includes `rpy2`, `scikit-learn`, `pandas`, `numpy`, `biopython`, `ete3`.*

## Running the Pipeline

The pipeline is designed to run with **synthetic data** by default due to the lack of verified plant datasets in the current configuration. This is a **Structural Prototype** run.

### 1. Run with Synthetic Data (Default)
This generates a complete analysis with a set of simulated species, runs the LOSO CV, and produces the defense allocation index.
```bash
python src/cli/run_pipeline.py --mode synthetic --seed 42
```

**Output**:
- `data/processed/synthetic_results.csv`: Model performance metrics.
- `data/processed/phylogenetic_null_dist.csv`: Null distribution for validation.
- `output/plots/`: R² vs. Gene Count sensitivity plot, Phylogenetic null distribution plot.
- `data/manifests/synthetic_manifest.json`: Records of generation parameters and seed.

**Note**: Results from this run validate **code correctness** and **statistical logic**. They do **not** validate the biological hypothesis.

### 2. Run with Real Data (Requires Manual Setup)
*Note: This will fail if the "Verified datasets" list does not contain the correct plant URLs. The system will raise `human_input_needed`.*
```bash
python src/cli/run_pipeline.py --mode real --accession_ids GSE12345,GSE67890
```

## Testing

Run the test suite to verify schema compliance and statistical logic:
```bash
pytest tests/ -v
```

### Key Tests
- `test_schema_validation`: Ensures all data files match `contracts/*.schema.yaml`.
- `test_power_analysis`: Verifies the pipeline halts if N < 15.
- `test_phyl_null`: Checks that the phylogenetic null model is generated correctly (residual permutation).
- `test_loso_cv`: Validates that no data leakage occurs in cross-validation.
- `test_leakage_prevention`: Verifies that trait-synthesis genes are excluded from predictors.

## Troubleshooting

- **Error: `No verified dataset found`**: The system cannot find the required plant RNA-seq data in the verified list. Switch to `--mode synthetic` or update the dataset configuration.
- **Error: `Insufficient statistical power`**: The dataset has fewer than 15 species (or required N for expected effect size). Add more species or relax the power threshold (not recommended).
- **Error: `Memory limit exceeded`**: The dataset is too large. Ensure `--sample-size 15` is set.
- **Error: `human_input_needed`**: Triggered if >30% of species lack trait data from all sources, or if real data is requested but not verified.