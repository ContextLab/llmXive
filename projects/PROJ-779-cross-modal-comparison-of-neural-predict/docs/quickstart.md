# Quickstart Guide

This guide walks you through running the full pipeline to analyze cross-modal neural prediction error signals.

## Step 1: Environment Setup

Ensure you have completed the installation steps in `README.md`.

## Step 2: Run the Pipeline

The main orchestration script `code/main.py` handles the entire workflow:

1. **Download** datasets from OpenNeuro.
2. **Validate** sampling rates and trial counts.
3. **Preprocess** data (filtering, ICA, re-referencing).
4. **Extract** prediction error metrics (difference waves, peak latency, amplitude).
5. **Localize** sources and perform statistical comparisons.
6. **Generate** a final report.

Run the pipeline:
```bash
python code/main.py
```

## Step 3: Check Outputs

After successful execution, you will find the following artifacts:

- **Preprocessed Data**: `data/processed/cleaned_data.fif`
- **Metrics Summary**: `data/results/metrics_summary.json`
- **Sensitivity Analysis**: `data/results/sensitivity_analysis.csv`
- **Reliability Results**: `data/results/reliability_metrics.json`
- **Final Report**: `data/results/final_report.md`

## Step 4: Verify Results

Review `data/results/final_report.md` for:
- Latency difference classification (vs. 50ms threshold).
- Source overlap (Dice coefficient) and equivalence test results.
- Reliability scores (Split-Half, Cronbach's α).
- Constitution compliance notes.

## Troubleshooting

- **Data Download Fails**: Ensure network access and check OpenNeuro availability.
- **Validation Errors**: The pipeline halts if sampling rate < 500 Hz or trial counts are insufficient.
- **Memory Issues**: The pipeline is optimized for CPU-only execution; reduce MNE parameters if needed.

## Next Steps

- Run unit tests: `pytest tests/`
- Review `docs/constitution-amendment-vii.md` for validation independence details.
- Customize analysis parameters in `code/config.py`.