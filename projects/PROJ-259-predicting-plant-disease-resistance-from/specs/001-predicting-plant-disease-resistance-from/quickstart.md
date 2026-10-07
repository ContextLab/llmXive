# Quickstart: Predict Plant Disease Resistance from Multi‑omics Data

## Prerequisites

*   Python 3.11+
*   Docker (optional, for containerized run)
*   7 GB RAM available

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-259-predicting-plant-disease-resistance-from
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Verify environment**:
    ```bash
    python -c "import scikit_learn, pandas, statsmodels; print('OK')"
    ```

## Running the Pipeline

### Option A: Standard Run (Real Data Only)
The pipeline attempts to download real multi-omics data from NCBI SRA/MetaboLights. If no real data is found, it halts with `EX_DATA_INTEGRITY`.

```bash
python code/cli.py run --output-dir results/
```

### Option B: CI Smoke Test (Synthetic Data)
Force the use of synthetic data to verify pipeline logic (code execution, file I/O). **DO NOT** use for scientific results.

```bash
python code/cli.py run --ci-mode --output-dir results/
```

### Option C: Validation Mode
Run validation on a previously trained model (requires a model artifact).

```bash
python code/cli.py validate --model-path artifacts/model.pkl --data-path data/processed/
```

## Expected Outputs

After a successful run, the `results/` directory will contain:

*   `data_manifest.yaml`: Provenance record (source, checksums).
*   `selected_features.csv`: Top SNPs/Metabolites with p-values and selection frequencies.
*   `performance_metrics.json`: CV accuracy, AUC, R², and permutation p-value.
*   `collinearity_report.csv`: VIF scores for all features (flags > 5).
*   `pipeline_log.txt`: Execution logs including memory usage.

## Troubleshooting

*   **Error: `EX_DATA_INTEGRITY (02)`**: No real multi-omics dataset found (SNP+Metabolite+Phenotype). The pipeline halted. Use `--ci-mode` for testing.
*   **Error: `EX_POWER_INSUFFICIENT (03)`**: Sample size < 100. Power analysis failed.
*   **Error: `ModuleNotFoundError`**: Run `pip install -r requirements.txt` again.
*   **Memory Warning**: If running on < 7GB RAM, ensure no other heavy processes are running. The pipeline attempts to stream data.

## Reproducibility Check

To verify reproducibility:
1.  Run the pipeline twice with the same `--seed` flag.
2.  Compare `results/performance_metrics.json` and `results/selected_features.csv`.
3.  P-values from permutation tests should match exactly (or within floating point tolerance).
