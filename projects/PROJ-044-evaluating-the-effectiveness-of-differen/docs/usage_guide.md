# Usage Guide: Evaluating Differential Privacy in Federated Learning

This guide provides detailed instructions for running the research pipeline, understanding CLI arguments, and interpreting outputs.

## 1. Project Setup

Ensure the project structure is initialized:

```bash
python code/setup_project_structure.py
```

This creates the necessary directories:
- `code/`, `data/`, `tests/`, `results/`, `artifacts/`
- Generates `tree_output.txt`

## 2. Data Preparation

### Downloading FEMNIST

The pipeline relies on the `leaf/femnist` dataset from Hugging Face.
**Note**: Shakespeare is excluded per T000.

```bash
python code/data/download.py --dataset femnist
```

**Parameters**:
- `--dataset`: Only `femnist` is supported.

**Outputs**:
- `data/raw/femnist.parquet`: The dataset in Parquet format.
- `data/raw/femnist.sha256`: SHA256 checksum for verification.

### Partitioning Data

Generate client partitions based on Dirichlet distributions.

```bash
python code/data/generate_partition_metadata.py \
 --dataset femnist \
 --alpha 0.1 \
 --seed 42
```

**Parameters**:
- `--alpha`: Dirichlet concentration parameter (e.g., 0.1 for high heterogeneity, 1.0 for balanced).
- `--seed`: Random seed for reproducibility.

**Outputs**:
- `data/partitions/partition_femnist_{seed}_{alpha}.json`: Metadata for each client's label distribution.

## 3. Training Experiments

### Running the Orchestrator

The main training script handles multiple seeds, $\alpha$ values, and $\epsilon$ budgets.

```bash
python code/training/run_experiment_orchestrator.py \
 --dataset femnist \
 --alphas 0.1 1.0 \
 --epsilons 0.5 5.0 \
 --seeds 42 123
```

**Parameters**:
- `--dataset`: Must be `femnist`.
- `--alphas`: Space-separated list of $\alpha$ values.
- `--epsilons`: Space-separated list of $\epsilon$ values (privacy budgets).
- `--seeds`: Space-separated list of random seeds.

**Behavior**:
- Iterates through all combinations of $\alpha$, $\epsilon$, and seeds.
- Runs FedAvg with Opacus-enabled DP.
- Logs metrics to `results/raw_logs.csv`.
- Handles OOM by dynamically reducing batch size (min 16).
- Detects "utility collapse" (accuracy < 5%) and flags it.

## 4. Analysis and Reporting

### Running the Analysis Pipeline

```bash
python code/analysis/stats.py
```

This script performs the following steps automatically:
1. **Filtering**: Removes time-limited and utility-collapse runs.
2. **Statistical Tests**:
 - Paired t-tests (DP vs. Non-DP).
 - Unpaired t-tests/Mann-Whitney U (Majority vs. Minority).
3. **Sensitivity Analysis**: Sweeps $\alpha$ values.
4. **Plotting**: Generates the minority vs. global overlay plot.
5. **Aggregation**: Produces the final `summary.csv`.

### Interpreting Results

- **`results/summary.csv`**: The primary output for analysis.
 - `p_value_dp_vs_nondp`: JSON string of p-values. If the list is empty or `power_reduced` is flagged, the statistical power was insufficient.
 - `accuracy_variance`: Variance across the 5 seeds.

- **`results/plots/minority_vs_global_overlay.png`**:
 - Y-axis: Accuracy Gap (Global - Minority).
 - X-axis: $\epsilon$ values.
 - A steeper slope for $\alpha=0.1$ compared to $\alpha=1.0$ supports the "Critical Heterogeneity" hypothesis.

- **`results/validation_report.md`**:
 - Lists counts of excluded runs (time-limited, utility collapse).
 - Indicates if any statistical tests fell back to Mann-Whitney U due to low sample size.

## 5. Validation

Run the comprehensive validation script to ensure all artifacts are present and correct:

```bash
python code/validation/validate_quickstart.py
```

This checks:
- File existence (Parquet, JSON, CSV, PNG).
- Checksum integrity.
- Plot DPI (must be 300).
- JSON schema of partition metadata.
- Content of `summary.csv`.

## Troubleshooting

### "Shakespeare" Errors
If you encounter errors related to the Shakespeare dataset, ensure you are using `--dataset femnist`. Shakespeare is explicitly excluded from this project.

### OOM Errors
The training loop automatically reduces batch size if an Out-Of-Memory error occurs. If the batch size hits the minimum (16) and OOM persists, reduce the number of clients or use a smaller model.

### Missing Data
Ensure `data/raw/femnist.parquet` exists. If missing, re-run the download step.