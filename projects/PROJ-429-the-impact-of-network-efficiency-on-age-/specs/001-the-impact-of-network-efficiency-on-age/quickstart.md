# Quickstart: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## 1. Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended) or macOS (ARM64/x64).
- **Disk Space**: ~15GB (for raw data download and processing).
- **Memory**: 7GB+ (recommended for full dataset; 4GB minimum for streaming).

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-429-the-impact-of-network-efficiency-on-age-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins MNE-Python, NetworkX, SciPy, Pandas, Statsmodels, etc.*

## 3. Data Acquisition

The project uses the **TUH EEG Corpus**.
- **Automatic Download**: Run the download script. It will fetch a subset of adult subjects.
  ```bash
  python code/data/download.py --subset adults --limit 100
  ```
  *(Use `--limit` to restrict the number of subjects for testing; omit for full run if disk allows)*.
- **Manual Download**: If automatic download fails, download the EDF files from PhysioNet and place them in `data/raw/`.

## 4. Running the Pipeline

Execute the full pipeline (Preprocessing -> Connectivity -> Analysis -> Viz):

```bash
python code/main.py
```

**Expected Output**:
- `data/processed/epochs/`: MNE epoch files.
- `data/results/network_metrics.csv`: Participant-level metrics.
- `data/results/correlation_results.csv`: Statistical results.
- `data/results/sensitivity_report.md`: Robustness analysis.
- `data/quality/exclusion_log.csv`: Records excluded due to missing data.
- `data/quality/version_map.json`: Aggregated SHA-256 hashes.

## 5. Validation

Verify the results against the schema:

```bash
python code/tests/test_schema_validation.py
```

This script checks:
- Presence of `trace_id` (SHA-256) in CSVs.
- Correct data types for all columns.
- Formula verification (Global Eff = 1/Path Length) via unit test.
- Handling of missing files.

## 6. Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, reduce the `--limit` flag in the download step or enable streaming mode in `code/data/download.py`.
- **Missing Cognitive Scores**: The TUH corpus does not have cognitive scores for all subjects. The pipeline will automatically filter for valid records and report the count in `data/quality/download_report.json`. Excluded records will be logged in `data/quality/exclusion_log.csv`.
- **ICA Failure**: If ICA fails for a subject (e.g., too few epochs), the subject is skipped and logged in `data/quality/download_report.json`.

## 7. Reproducibility Check

To verify reproducibility:
1. Delete `data/processed/` and `data/results/`.
2. Run `python code/main.py` again.
3. Compare the SHA-256 hash of the new `network_metrics.csv` with the previous run (stored in `state/`). They must match.