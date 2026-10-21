# Quickstart: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Prerequisites
- **Python** ≥ 3.11  
- **OS**: Linux (tested on Ubuntu 22.04 / GitHub Actions runner)  
- **Hardware**: 2 CPU cores, ≤ 7 GB RAM (standard free‑tier GitHub Actions)  
- **Internet**: Required for dataset download (no credentials needed)  

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd <repo-path>

# Navigate to the feature directory
cd specs/001-network-centrality-sleep-synchrony

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline
Each command logs progress to `logs/pipeline.log`.

```bash
# 1️⃣ Download & verify the Sleep‑EDF dataset (FR‑001)
python code/download.py

# 2️⃣ Preprocess EEG (filter, ICA, epoch) (FR‑002)
python code/main.py --stage preprocess

# 3️⃣ Compute waking functional connectivity (FR‑003)
python code/main.py --stage connectivity

# 4️⃣ Compute centrality metrics using **EEG channels only** (FR‑004)
# Optional: add `--include-peripheral` to also use EOG/EMG channels for a sensitivity analysis.
python code/main.py --stage centrality

# 5️⃣ Compute sleep‑stage PLV (FR‑005)
python code/main.py --stage pli

# 6️⃣ Aggregate per‑subject‑per‑stage metrics (FR‑006, FR‑013)
python code/main.py --stage aggregate

# 7️⃣ Validate the aggregated CSV against the schema (FR‑013)
python code/validate.py   # exits 0 on success

# 8️⃣ Compute global VIF diagnostics (FR‑009)
python code/main.py --stage vif

# 9️⃣ Perform statistical analysis (FR‑006, FR‑007, FR‑010)
python code/main.py --stage analysis
# Note: If N < 30 or any subject lacks ≥ 2 min wake, the script halts with a warning.

# 🔟 Generate the final report (FR‑008, FR‑011)
python code/main.py --stage report

# 1️⃣1️⃣ (Optional) Run centrality stability check (Phase 1b)
python code/main.py --stage centrality_stability
# This step includes both split‑half ICC of the waking segment and cross‑state ICC (waking vs N2 sleep).
```

## Expected Output Structure
```
data/
├── raw/          # immutable .edf files
├── processed/
│   ├── epochs_{subj}.npz
│   ├── metadata_{subj}.json
│   ├── connectivity_theta_{subj}.npy
│   ├── connectivity_alpha_{subj}.npy
│   ├── centrality_{subj}.json          # EEG‑only metrics
│   ├── centrality_periph_{subj}.json   # optional peripheral metrics
│   ├── centrality_icc_{subj}.json      # split‑half ICC
│   ├── centrality_cross_state_icc_{subj}.json  # wake‑vs‑N2 ICC
│   └── pli_{stage}_{subj}.npy
├── metrics/
│   └── SubjectMetrics.csv
└── results/
    ├── vif_report.json
    ├── analysis_results.json
    ├── centrality_stability.json
    └── report.md
```

## Verification & Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```
All unit tests must pass (exit code 0). They cover preprocessing, connectivity, centrality (including EEG‑only and peripheral options), centrality stability (ICC), PLV calculation, aggregation, schema validation, and analysis logic.

### Integration Test (small subject subset)
```bash
pytest tests/integration/test_pipeline.py -v
```
Runs the entire pipeline on a minimal subset to ensure end‑to‑end functionality, schema compliance, and that `report.md` contains required sections.

### Schema Validation
```bash
python code/validate.py
```
Confirms that `SubjectMetrics.csv` matches `contracts/dataset.schema.yaml` and that `analysis_results.json` matches `contracts/analysis.schema.yaml`.

## Troubleshooting

- **Download fails**: Verify network connectivity and that the Hugging  Face URL is reachable.  
- **Preprocessing errors**: Check that the EDF file contains the expected channels; corrupted files are logged and skipped.  
- **Insufficient Sample Size**: If the pipeline stops with “Insufficient Sample Size”, the ≥ 2 min wake filter removed too many subjects. Review `logs/pipeline.log` for the exact count.  
- **Memory errors**: Reduce `n_workers` in `code/config.yaml` to `1`. The pipeline processes subjects sequentially to stay ≤ 4 GB RAM.  
- **Power warnings**: If the post‑hoc power estimate is low, the report will note this limitation; consider acquiring more data in future work.  

## Performance Expectations
- **Runtime**: ~3–4 h on a GitHub Actions free‑tier runner.  
- **Peak RAM**: ≤ 4 GB.  
- **Disk usage**: ≤ 10 GB (raw EDFs + intermediates).  

If you exceed these targets, consult `logs/pipeline.log` for the bottleneck (most often ICA or connectivity computation) and consider reducing the number of parallel workers.

---



