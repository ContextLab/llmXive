# Quick Start Guide

## 1. Setup Environment

Ensure you have the required dependencies installed:

```bash
pip install -r code/requirements.txt
```

## 2. Verify Data Sources

The pipeline fetches data from OpenNeuro (ds000228). Ensure you have internet access.
The pipeline will automatically validate the presence of "dream recall frequency" metadata.
If metadata is missing or subjects are insufficient (<50), the process will halt with a `FatalError`.

## 3. Run the Pipeline

Execute the main entry point:

```bash
python code/main.py
```

### Important: 4-Hour CI Limit

This project is configured for a strict **4-hour execution window** in CI environments.

- The `main.py` script tracks total wall-clock time.
- If the runtime exceeds 4 hours, a `RuntimeError` is raised immediately.
- This error causes the CI build to fail, ensuring long-running jobs are detected and optimized.
- Logs are written to `results/runtime_log.json`.

## 4. Review Results

After completion, check the following:
- `results/stats.json`: Contains correlation coefficients and p-values.
- `results/plots/`: Visualizations of the relationships.
- `data/metrics/subject_metrics.csv`: Per-subject network metrics.

## Troubleshooting

- **Memory Error**: If you see a memory exception, ensure your environment has <7GB RAM usage. The `memory_monitor` will abort if this limit is breached.
- **Missing Data**: If the pipeline fails to find subjects, check `data/raw/valid_subjects.json`.
- **Time Limit Exceeded**: If the pipeline exceeds 4 hours, consider reducing the permutation iterations in `code/analysis/permutation_test.py` or the number of subjects.