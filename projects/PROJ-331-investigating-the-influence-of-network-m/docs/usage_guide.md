# Usage Guide: Network Motifs and RSFC Pipeline

This guide provides detailed instructions for using the pipeline, including configuration, execution, and troubleshooting.

## Configuration

### Environment Variables

Set the following environment variables before running the pipeline:

```bash
export HCP_S3_BUCKET="hcp-openaccess" # HCP S3 bucket name
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

### Custom Paths

Modify `code/config.py` to change default paths:

```python
# In code/config.py
DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")
RESULTS_DIR = Path("results")
```

## Step-by-Step Execution

### Step 1: Project Setup

Ensure all directories exist:

```bash
python code/setup_project.py
```

### Step 2: Data Download

```bash
python code/download.py --subjects sub-100307 sub-101309
```

Options:
- `--subjects`: Comma-separated list of HCP subject IDs.
- `--force`: Re-download existing files.

**Note**: The script will fail loudly if HCP access is unavailable. No synthetic data is generated.

### Step 3: Preprocessing

```bash
python code/preprocess.py
```

This performs:
1. Streamline parcellation (weighted adjacency).
2. Median-density binarization.
3. RSFC computation and global efficiency calculation.

Outputs:
- `data/processed/weighted_adjacency.npy`
- `data/processed/canonical_binary_adj.npy`
- `data/processed/rsfc.npy`
- `data/processed/global_efficiency.json`

### Step 4: Motif Analysis

```bash
python code/motifs.py --timeout 300
```

Options:
- `--timeout`: Maximum seconds per subject (default: 300).
- `--thresholds`: Z-score thresholds for sensitivity analysis (default: 1.5, 2.0, 2.5).

Outputs:
- `data/processed/motif_profiles.json`
- `data/processed/sensitivity_z*.json`

### Step 5: Statistical Analysis

```bash
python code/stats.py
```

This computes:
- VIF checks and method selection.
- Partial correlations (Pearson/Spearman) with Bonferroni correction.
- Permutation tests for significant motifs.
- Power analysis.

Outputs:
- `data/processed/subject_metrics.csv`
- `data/processed/quality_flags.json`
- `results/correlation_results.json`
- `results/permutation_results.json`
- `results/power_analysis.json`

### Step 6: Report Generation

```bash
python code/report.py
```

Outputs:
- `results/report.pdf`

## Troubleshooting

### HCP Access Denied

- Verify `scripts/verify_hcp_access.sh` returns success.
- Check network connectivity and AWS credentials.
- Ensure the S3 bucket name is correct in `config.py`.

### Timeout Errors in Motif Analysis

- Increase `--timeout` parameter.
- The pipeline logs a warning and skips the subject if exceeded.
- Fallback to `igraph` is attempted if `networkx` times out (if installed).

### Missing Output Files

- Check `data/logs/pipeline.log` for error messages.
- Ensure all prerequisite steps completed successfully.
- Verify file paths in `config.py` match the actual directory structure.

### Statistical Warnings

- **Zero Variance**: If a motif has no variance across subjects, the pipeline logs a warning and skips correlation.
- **High VIF**: If VIF > 5 for the control variable, the pipeline switches to permutation-only analysis.

## Advanced Usage

### Custom Null Model Iterations

Edit `code/motifs.py` to change the number of null model iterations:

```python
def generate_null_model(adj_matrix, iterations=100):
 #...
```

### Sensitivity Analysis

Run sensitivity analysis with custom z-thresholds:

```bash
python code/motifs.py --thresholds 1.0 2.0 3.0
```

### Partial Correlation Control Variable

The control variable is fixed to `global_node_degree` per Spec FR-005. To change this, modify `code/stats.py` and ensure compliance with the specification.

## Performance Optimization

- Use `--jobs` flag (if implemented) to parallelize subject processing.
- Ensure sufficient RAM for motif enumeration (large graphs may require >14GB).
- Streaming download is enabled by default to respect disk limits.

## Output Validation

Run the hash verification script:

```bash
bash scripts/hash_artifacts.sh
```

This ensures all artifacts are checksummed and recorded in `state/artifacts.yaml`.

## Support

For issues or questions, please refer to the project documentation or contact the maintainers.
