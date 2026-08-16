# Quickstart Guide: Evaluating Compositional Features vs Formation Energy

This guide provides the steps to run the full pipeline end-to-end for reproducibility validation (Task T052).

## Prerequisites

1. Ensure you have a valid `MPDS_API_KEY` set in your environment or `.env` file.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution Steps

Run the main pipeline script which orchestrates ingestion, descriptor computation, training, evaluation, and plotting.

```bash
python code/main.py
```

Alternatively, run individual stages for debugging:

1. **Ingest Data**:
 ```bash
 python code/ingest.py
 ```
 *Output*: `data/raw/mp-2020.12.1.csv`, `data/processed/sampled_raw_data.csv` (if sampling triggered)

2. **Compute Descriptors**:
 ```bash
 python code/descriptors.py
 ```
 *Output*: `data/processed/computed_descriptors.csv`

3. **Train & Evaluate Models**:
 ```bash
 python code/train.py
 python code/evaluate.py
 ```
 *Output*: `data/evaluation/model_rf.pkl`, `data/evaluation/model_gb.pkl`, `data/evaluation/model_metrics.json`

4. **Feature Importance & Plots**:
 ```bash
 python code/importance.py
 python code/plots.py
 ```
 *Output*: `data/evaluation/feature_ranking.json`, `data/evaluation/ale_*.png`

5. **Research Summary**:
 ```bash
 python code/generate_research_summary.py
 ```
 *Output*: `research.md`

## Validation

To verify end-to-end reproducibility, run the validation script:

```bash
python code/quickstart_validation.py
```

This script checks for the existence of all critical artifacts and validates the schema of key JSON outputs.

## Expected Artifacts

- `data/raw/mp-2020.12.1.csv`
- `data/processed/computed_descriptors.csv`
- `data/evaluation/model_metrics.json`
- `data/evaluation/feature_ranking.json`
- `research.md`
