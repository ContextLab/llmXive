# Quickstart Guide: Brain Network Dynamics and VR Therapy Response

This guide explains how to run the full analysis pipeline on a subset of N=10 subjects,
ensuring the process completes within the CI constraints (2 CPU cores, 7GB RAM, 14GB disk, 6h).

## Prerequisites

- Python 3.10+
- Git
- A verified OpenNeuro dataset ID (e.g., `ds004151` or similar as configured in `.env`)

## 1. Setup Environment

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd llmXive-PROJ-416
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuration

Create a `.env` file in the project root with the following variables:

```env
# OpenNeuro Dataset ID (Must be a real, accessible dataset)
OPENNEURO_ID=ds004151

# Paths (Defaults to project structure)
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_METRICS_DIR=data/metrics
LOGS_DIR=logs

# Execution constraints
MAX_SUBJECTS=10
MOTION_THRESHOLD_MM=3.0
MOTION_THRESHOLD_DEG=3.0
RANDOM_SEED=42
```

> **Note**: If `OPENNEURO_ID` is missing or invalid, the pipeline will halt immediately with a fatal error as per FR-011.

## 3. Execution

Run the main pipeline script. This will:
1. Validate the dataset source.
2. Download the necessary data (subject subset).
3. Validate metadata (pre/post scores, anxiety scales).
4. Preprocess fMRI data (motion correction, slice timing, normalization).
5. Compute network metrics (Modularity, Global/Local Efficiency).
6. Perform statistical analysis (ANCOVA, FDR correction).
7. Generate the final report.

```bash
python code/main.py
```

### Running a Subset (N=10)

The pipeline is configured via `MAX_SUBJECTS=10` in `.env` to ensure it fits within the
CI resource limits. The `code/config.py` module enforces this limit during the download
and preprocessing stages.

## 4. Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **Preprocessed Data**: `data/processed/` (NIfTI files for N=10 subjects)
- **Network Metrics**: `data/metrics/network_metrics.csv`
- **Statistical Results**: `data/metrics/statistical_results.csv`
- **Subject Info**: `data/metrics/subject_info.json` (includes exclusion reasons)
- **Plots**: `figures/` (Scatter plots, residual diagnostics)
- **Final Report**: `reports/results.md`

## 5. Troubleshooting

### "Missing verified dataset source"
- Ensure `OPENNEURO_ID` is set in `.env` and points to a real OpenNeuro dataset.
- The pipeline will not proceed with synthetic data.

### "Motion threshold exceeded"
- Subjects with Framewise Displacement (FD) > 3.0mm or rotation > 3.0° are automatically
 excluded. Check `logs/preprocessing.log` for the list of excluded subjects.

### "Power analysis: N < 5"
- If the number of valid subjects after exclusion is less than 5, the pipeline will halt
 with a fatal error as per SC-004.

### "Ridge regression rejected"
- The pipeline uses Univariate models with FDR correction instead of Ridge regression,
 adhering to the project's methodological constraints.

## 6. Verification

To verify the installation and data download:

```bash
# Check data integrity
python code/data/checksum.py --verify

# Run unit tests
pytest tests/unit/ -v
```

## 7. Data Source

This project uses real fMRI data from OpenNeuro. No synthetic or placeholder data is
generated. If the specified dataset is unavailable, the pipeline will fail loudly to
prevent fabrication of results.

**Dataset**: OpenNeuro (ID specified in `.env`)
**Modality**: Resting-state fMRI
**Clinical Measures**: Pre/Post treatment anxiety scores (e.g., GAD-7, HAM-A)