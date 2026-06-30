# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

## Prerequisites

- Python 3.10+
- Git
- Access to OpenNeuro (for HCP data)
- Sufficient disk space (for raw and processed data)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-518-investigating-the-relationship-between-b
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### 1. Validate Data (Critical Step)
Before running the full analysis, ensure the CAQ data is present in the OpenNeuro ds000224 phenotype directory.
```bash
python code/main.py --validate-only
```
- **Success**: Logs "CAQ found in ds000224/phenotype/, proceeding."
- **Failure**: Exits with error `DATA_MISSING_CREATIVITY`.

### 2. Run Full Analysis
Execute the full pipeline (preprocessing, flexibility, null-model, regression, visualization).
```bash
python code/main.py --window-length 30 --permutations 10000
```

### 3. Sensitivity Analysis
Run the window length sweep across a range of durations.
```bash
python code/main.py --sweep-windows
```

## Output Locations

- **Metrics**: `data/interim/flexibility_metrics.csv`
- **Results**: `data/interim/permutation_results.csv`, `data/interim/sensitivity_summary.csv`
- **Plots**: `docs/outputs/` (e.g., `flexibility_vs_creativity.png`)
- **Logs**: `data/interim/data_exclusion_log.txt`
- **Checksums**: `data/checksums.json`

## Troubleshooting

- **Memory Error**: Reduce the batch size in `code/config.py` or process fewer subjects.
- **Runtime Error**: If the job exceeds 6 hours, reduce `--permutations` to 5000 (note: this affects power).
- **Missing Data**: Check `data/interim/data_exclusion_log.txt` for excluded subjects.
- **CAQ Missing**: If `DATA_MISSING_CREATIVITY` is raised, verify that the OpenNeuro ds000224 dataset includes the `phenotype/CAQ.tsv` file (it may require specific download permissions or a specific version).

## Verification

To verify the results:
1. Check that `flexibility_vs_creativity.png` exists.
2. Verify `permutation_results.csv` contains a p-value < 0.05 (if significant).
3. Ensure `data_exclusion_log.txt` lists motion-excluded subjects.
4. Confirm `data/checksums.json` contains hashes for all raw files.