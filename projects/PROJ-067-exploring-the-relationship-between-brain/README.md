# llmXive: Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

This project implements an automated pipeline to analyze resting-state fMRI data from the OpenNeuro ds000228 dataset.
It investigates the correlation between dynamic functional connectivity metrics (Flexibility, Stability) in specific brain networks
(DMN, Salience, Hippocampal-Memory) and individual Dream Recall Frequency (DRF).

## Prerequisites

- Python 3.9+
- System packages: `fsl`, `fsleyes`, `ICA-AROMA` (required for preprocessing)
- Sufficient disk space (>7GB recommended for intermediate files)

## Installation

1. Clone the repository.
2. Navigate to the `code/` directory.
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

- `code/`: Source code for the pipeline.
- `data/`: Storage for raw and processed data.
- `results/`: Generated plots and statistical summaries.
- `tests/`: Unit and contract tests.
- `contracts/`: Schema definitions for data validation.

## Execution Instructions

The pipeline is orchestrated by `main.py`. It executes the following phases sequentially:
1. **Data Acquisition**: Validates metadata and downloads NIfTI files for valid subjects.
2. **Preprocessing**: Performs ICA-AROMA denoising and normalization.
3. **Metric Extraction**: Calculates sliding window correlations and Louvain clustering metrics.
4. **Statistical Analysis**: Computes Spearman correlations, FDR correction, and permutation tests.

### Running the Full Pipeline

Execute the following command from the project root:

```bash
cd code
python main.py
```

### Runtime Constraints & CI Enforcement

**4-Hour Execution Limit**:
This pipeline is designed to complete within **4 hours** on standard CPU-only CI infrastructure.
The `main.py` script includes built-in wall-clock timing instrumentation.

- **Runtime Enforcement**: If the total execution time exceeds 4 hours (14,400 seconds), the pipeline will raise a `RuntimeError`.
- **CI Failure**: The continuous integration (CI) workflow is configured to treat this `RuntimeError` as a **build failure**.
- **Logging**: Runtime metrics are logged to `results/runtime_log.json`.

If the pipeline exceeds the time limit, you may need to:
- Reduce the number of subjects (modify `data/raw/valid_subjects.json`).
- Optimize the permutation test iterations (currently set to 1000).
- Check for system resource bottlenecks (RAM >7GB triggers an abort).

### Output Artifacts

Upon successful completion, the following artifacts will be generated:
- `data/metrics/subject_metrics.csv`: Network flexibility and stability metrics per subject.
- `results/stats.json`: Statistical analysis results (rho, p-values, power analysis).
- `results/plots/`: Scatter plots and null distribution histograms.

## Testing

Run the test suite to verify pipeline integrity:

```bash
cd code
pytest tests/ -v
```

## License

[Insert License Information]
