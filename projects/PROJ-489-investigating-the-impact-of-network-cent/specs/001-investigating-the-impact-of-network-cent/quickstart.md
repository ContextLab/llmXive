# Quickstart: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Prerequisites

- **Python**: 3.11 or newer
- **OS**: Linux (tested on GitHub Actions Ubuntu 22.04)
- **Internet**: Required for dataset download
- **Hardware**: 2 CPU cores, ≤ 7 GB RAM (standard GitHub Actions runner)
- **Time**: ~3–4 hours for full pipeline

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd <repo-path>

# Navigate to the project directory
cd specs/001-network-centrality-sleep-synchrony

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

Execute the pipeline in order. Each stage writes to `data/` and logs to `logs/pipeline.log`.

```bash
# 1️⃣ Download and verify the dataset (FR‑001)
python code/download.py
# Output: data/raw/*.edf + checksum log

# 2️⃣ Preprocess EEG (filter, ICA, epoch) (FR‑002)
python code/main.py --stage preprocess
# Output: data/processed/epochs_*.npz + metadata_*.json

# 3️⃣ Build waking connectivity matrices (FR‑003)
python code/main.py --stage connectivity
# Output: data/processed/connectivity_theta_*.npy, connectivity_alpha_*.npy

# 4️⃣ Compute centrality metrics (FR‑004)
python code/main.py --stage centrality
# Output: data/processed/centrality_*.json

# 5️⃣ Compute sleep‑stage PLI (FR‑005)
python code/main.py --stage pli
# Output: data/processed/pli_N1_*.npy, pli_N2_*.npy, pli_N3_*.npy, pli_REM_*.npy

# 6️⃣ Aggregate metrics into SubjectMetrics.csv
python code/main.py --stage aggregate
# Output: data/metrics/SubjectMetrics.csv

# 7️⃣ Validate aggregated metrics against schema (FR‑013)
python code/validate.py
# Output: validation log to console and logs/pipeline.log

# 8️⃣ Compute global VIF diagnostics (FR‑009)
python code/main.py --stage vif
# Output: data/results/vif_report.json

# 9️⃣ Statistical analysis (FR‑006, FR‑007, FR‑010, FR‑012)
python code/main.py --stage analysis
# Output: raw correlations, Bonferroni correction, significance flags
# Note: Halts with warning if N < 30 or any subject has < 2 min wake

# 🔟 Generate final report (FR‑008, FR‑011)
python code/main.py --stage report
# Output: data/results/analysis_results.json + report.md
```

## Expected Output Structure

After running the full pipeline, you will have:

```
data/
├── raw/
│   ├── *.edf                           # Downloaded EDF files
│   └── checksums.log                   # SHA‑256 checksums
├── processed/
│   ├── epochs_S001.npz, epochs_S002.npz, ...
│   ├── metadata_S001.json, metadata_S002.json, ...
│   ├── connectivity_theta_S001.npy, ...
│   ├── connectivity_alpha_S001.npy, ...
│   └── centrality_S001.json, ...
├── metrics/
│   └── SubjectMetrics.csv              # Aggregated metrics
└── results/
    ├── vif_report.json                 # VIF diagnostics
    ├── analysis_results.json           # All correlations & statistics
    └── report.md                       # Human‑readable summary

logs/
└── pipeline.log                        # Timestamped execution log
```

## Verification & Testing

### Unit Tests
Run all unit tests to verify individual pipeline components:

```bash
pytest tests/unit/ -v
```

Expected output:
- `test_preprocess.py`: Validates epoch length = 30 s, no NaN values, correct sleep‑stage labels.
- `test_connectivity.py`: Validates matrix symmetry, values ∈ (0, 1).
- `test_centrality.py`: Validates against synthetic graphs.
- `test_pli.py`: Validates output ∈ [0, 1].
- `test_aggregate.py`: Validates `SubjectMetrics.csv` schema compliance.
- `test_validate.py`: Validates schema validation logic.
- `test_analysis.py`: Validates Bonferroni correction, normality testing, partial correlation.

All tests must exit with code 0.

### Integration Test
Run the end‑to‑end pipeline on a 3‑subject subset:

```bash
pytest tests/integration/test_pipeline.py -v
```

Expected output:
- Executes all stages on 3 subjects.
- Validates that `SubjectMetrics.csv` and `analysis_results.json` have expected schema and content.
- Verifies that `report.md` contains required sections.

### Schema Validation
Validate the final outputs against the contracts:

```bash
python code/validate.py
```

Expected output:
- `SubjectMetrics.csv` conforms to `contracts/dataset.schema.yaml`.
- `analysis_results.json` conforms to `contracts/analysis.schema.yaml`.

## Troubleshooting

### Download Fails
- **Error**: Network timeout or 404.
- **Solution**: Check internet connection and verify the Hugging Face mirror URL is accessible: `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/`.

### Preprocessing Fails
- **Error**: `ValueError: No waking segment found` or `No sleep epochs found`.
- **Solution**: Check that the EDF file contains valid annotations. Some files may lack proper sleep‑stage labels; they are skipped and logged.

### Insufficient Sample Size Warning
- **Error**: Pipeline halts with "Insufficient Sample Size" warning.
- **Solution**: This means fewer than 30 subjects have ≥ 2 min of clean waking data. The dataset's wake segments are inherently short; this is a known limitation. Check `logs/pipeline.log` to see how many subjects were filtered out.

### Memory Errors
- **Error**: `MemoryError` during preprocessing or analysis.
- **Solution**: The pipeline is designed to stay ≤ 4 GB RAM by processing subject‑by‑subject. If you still encounter memory errors, reduce the number of parallel workers in `code/config.yaml` (set `n_workers = 1`).

### Test Failures
- **Error**: One or more unit/integration tests fail.
- **Solution**: Examine the test output and `logs/pipeline.log` for detailed error messages. Common causes:
  - Missing dependencies: Re-run `pip install -r code/requirements.txt`.
  - Corrupted data: Delete `data/` and re-run the pipeline from step 1️⃣.
  - Schema mismatch: Ensure `contracts/*.schema.yaml` files are valid YAML.

## Next Steps

Once the pipeline completes successfully:

1. **Review the report**: Open `report.md` to see the summary, results table, VIF diagnostics, and limitation notes.
2. **Examine the results**: Open `data/results/analysis_results.json` to see all correlation statistics in machine‑readable format.
3. **Check the limitations**: Note the "Confounding Limitation" and "Wake Duration Limitation" sections in the report; these contextualize the findings.
4. **Validate the data**: Confirm that `data/metrics/SubjectMetrics.csv` and `data/results/analysis_results.json` pass schema validation.

## Performance Expectations

- **Runtime**: ~3–4 hours on a GitHub Actions free‑tier runner (2 vCPU).
- **Peak RAM**: ~3–4 GB.
- **Disk**: ~5–10 GB (for raw EDF files + processed intermediates).

If your pipeline exceeds these targets, check `logs/pipeline.log` for performance bottlenecks (e.g., ICA taking > 1 h per subject).

---
