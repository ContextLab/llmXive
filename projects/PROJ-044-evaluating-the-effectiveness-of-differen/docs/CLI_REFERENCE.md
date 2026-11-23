# CLI Reference

This document provides a detailed reference for all command-line interfaces (CLIs) in the `code/` directory.

## `code/data/download.py`

Downloads the FEMNIST dataset from Hugging Face.

**Usage**:
```bash
python code/data/download.py --dataset <dataset_name> [--is_streaming <bool>]
```

**Arguments**:
- `--dataset`: (Required) Dataset name. Currently only `femnist` is supported.
- `--is_streaming`: (Optional, default: True) Use streaming mode for large datasets.

**Outputs**:
- `data/raw/femnist.parquet`: Downloaded dataset.
- `data/raw/femnist.sha256`: Checksum file.

**Errors**:
- `ValueError`: If dataset is not `femnist`.
- `DataFetchError`: If download fails after retries.

## `code/data/partition.py`

Partitions the FEMNIST dataset using Dirichlet distribution.

**Usage**:
```bash
python code/data/partition.py --dataset <dataset_name> --seed <int> --alpha <float>
```

**Arguments**:
- `--dataset`: (Required) Dataset name (`femnist`).
- `--seed`: (Required) Random seed for reproducibility.
- `--alpha`: (Required) Dirichlet concentration parameter.

**Outputs**:
- `data/partitions/partition_femnist_{seed}_{alpha}.json`: Partition metadata.

## `code/training/run_experiment_orchestrator.py`

Orchestrates the full training experiment across seeds and configurations.

**Usage**:
```bash
python code/training/run_experiment_orchestrator.py --dataset <dataset_name> --seeds <seed_list> [--alphas <alpha_list>] [--epsilons <epsilon_list>]
```

**Arguments**:
- `--dataset`: (Required) Dataset name (`femnist`).
- `--seeds`: (Required) Space-separated list of seeds.
- `--alphas`: (Optional) Space-separated list of $\alpha$ values.
- `--epsilons`: (Optional) Space-separated list of $\epsilon$ values.

**Outputs**:
- `results/raw_logs.csv`: Training metrics for all runs.

## `code/analysis/stats.py`

Performs statistical analysis on training results.

**Usage**:
```bash
python code/analysis/stats.py
```

**Inputs**:
- `results/filtered_data.csv`

**Outputs**:
- `results/p_values_by_seed.json`
- `results/summary.csv`

## `code/analysis/plots.py`

Generates visualization plots from analysis results.

**Usage**:
```bash
python code/analysis/plots.py
```

**Inputs**:
- `results/filtered_data.csv`

**Outputs**:
- `results/plots/minority_vs_global_overlay.png`
- `results/plots/accuracy_vs_epsilon.png`
- `results/plots/accuracy_gap_vs_alpha.png`

## `code/validation/validate_quickstart.py`

Validates the project setup and end-to-end reproducibility.

**Usage**:
```bash
python code/validation/validate_quickstart.py
```

**Checks**:
- Directory structure
- `requirements.txt`
- Data files (checksums)
- Partition metadata
- Training logs
- Plots
- Summary results

**Note on Shakespeare Exclusion**:
All CLI tools strictly enforce the exclusion of the Shakespeare dataset. Attempting to specify `shakespeare` as a dataset will result in a `ValueError` with the message: "Shakespeare excluded per plan.md Gap Analysis (no verified source)." This is a hard constraint derived from T000.
