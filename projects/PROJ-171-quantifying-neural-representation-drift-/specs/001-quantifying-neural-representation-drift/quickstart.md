# Quickstart: Quantifying Neural Representation Drift During Skill Learning

## Prerequisites

- Python 3.11+
- CPU cores, GB RAM (GitHub Actions free-tier compatible)
- Internet access (for downloading OpenNeuro dataset)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-171-quantifying-neural-representation-drift-/code
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins all versions for reproducibility (Constitution I).*

## Data Setup

The pipeline automatically downloads the OpenNeuro dataset from the verified HuggingFace source.

```bash
# This command triggers the download and validation
python -m src.data.loader --verify-only
```

- **Verified Source**: `
- **Checksum**: Recorded in `data/raw/checksums.txt` (Constitution III).

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m src.main --config config/default.yaml
```

**What happens**:
1. **Ingest**: Downloads and streams OpenNeuro data.
2. **Preprocess**: Filters units (≥80% stability), excludes performance-modulated neurons, imputes missing behavior.
3. **Drift**: Computes RDMs, fits linear model (`drift(t) = a + b·t`), extracts `b`.
4. **Correlate**: Runs permutation test and LMM to correlate `b` with learning speed.
5. **Validate**: Performs sensitivity analysis (threshold sweep, metric comparison).
6. **Output**: Generates plots and CSV results in `data/results/` and `docs/paper/`.

## Verification (Synthetic Ground Truth)

To verify the drift quantification accuracy (SC-001):

```bash
python -m src.validation.synthetic --generate --validate
```

- Generates synthetic data with known drift rate `b`.
- Runs the pipeline.
- Checks if recovered `b` is within 5% error of ground truth.

## Sensitivity Analysis

To run the threshold sweep (FR-008):

```bash
python -m src.validation.sensitivity --thresholds 0.70 0.75 0.80 0.85 0.90
```

- Sweeps stability thresholds.
- Outputs `docs/paper/fig_sensitivity_thresholds.png`.

## Troubleshooting

- **Missing Variables**: If the pipeline halts with `RuntimeError: Missing variable 'spike_counts'`, ensure the OpenNeuro dataset is correctly downloaded and contains the required columns.
- **Memory Error**: If `MemoryError` occurs, ensure `streaming=True` is used in `loader.py` and that intermediate matrices are not loaded entirely into memory.
- **Convergence Warning**: If `drift_rate_b` is flagged as "non-drifting", check the raw data for flat activity or insufficient days.
