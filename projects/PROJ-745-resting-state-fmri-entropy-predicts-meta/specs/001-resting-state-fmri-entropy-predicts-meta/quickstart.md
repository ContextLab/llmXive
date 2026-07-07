# Quickstart: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

## Prerequisites

- Python 3.11+
- Git
- Access to HCP S1200 release (requires login/API key) or verified HuggingFace mirror
- GitHub Actions runner (for execution)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd proj-745-resting-state-fmri-entropy-predicts-meta
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

## Data Download

The project uses the HCP S1200 release. Run the download script to fetch and cache data:

```bash
python code/download.py
```

- **Output**: Raw data stored in `data/raw/`.
- **Verification**: Checksums are generated and stored in `state/`.
- **Requirement**: The script verifies the presence of the 'Visual Grating' task with confidence ratings. If missing, it halts.

## Preprocessing

Preprocess the fMRI data (motion scrubbing, nuisance regression, parcellation):

```bash
python code/preprocess.py
```

- **Input**: Raw NIfTI files in `data/raw/`.
- **Output**: Parcellated time series in `data/processed/timeseries/`.
- **Logging**: Motion parameters and errors logged to `logs/preprocess.log`.

## Metric Computation

Compute multiscale sample entropy and metacognitive efficiency:

```bash
python code/metrics.py
```

- **Input**: Preprocessed time series and behavioral data.
- **Output**: Entropy and meta-d′ metrics in `data/processed/metrics/`.
- **Validation**: Subjects with missing confidence or zero variance are excluded and logged.

## Statistical Analysis

Run the primary regression and sensitivity analysis:

```bash
python code/analysis.py
```

- **Input**: Entropy and meta-d′ metrics.
- **Output**: Regression coefficients, p-values, and sensitivity tables in `data/processed/results/`.
- **Power Check**: Halts if sample size < **194** (formal power analysis threshold for r=0.2, power=0.8).

## Testing

Run unit and integration tests:

```bash
pytest tests/
```

- **Unit Tests**: Verify entropy and meta-d′ calculations on synthetic data.
- **Integration Tests**: Run a 10-subject subset of the full pipeline.

## Reproducibility

To ensure reproducibility:

1. **Pin seeds**: All random seeds are set in `code/`.
2. **Use virtualenv**: The `venv` created in Installation ensures dependency consistency.
3. **Checksum data**: Verify data integrity using checksums in `state/`.
4. **State Update**: The project state file `state/projects/PROJ-745-...yaml` is updated upon artifact changes.

## Troubleshooting

- **Memory Error**: Reduce batch size in `code/preprocess.py` or process subjects sequentially.
- **Missing Data**: Check logs in `logs/` for skipped subjects. Ensure HCP data is correctly downloaded.
- **Power Insufficient**: If n < 194, the analysis will halt. Consider a larger dataset or re-evaluating the hypothesis.