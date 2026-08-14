# Quickstart Guide: Evaluating Compositional Features vs Formation Energy

This guide validates the end-to-end reproducibility of the pipeline described in PROJ-509.
It executes the full research workflow from data ingestion to final summary generation.

## Prerequisites

1. **Environment**: Python 3.9+
2. **API Key**: Set `MPDS_API_KEY` in your environment variables if using the MPDS API directly.
 ```bash
 export MPDS_API_KEY="your_key_here"
 ```
3. **Dependencies**: Install required packages.
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution Steps

Run the main pipeline script which orchestrates all phases:

```bash
cd code
python main.py
```

Alternatively, run individual stages manually for debugging:

### 1. Data Ingestion & Descriptor Computation
```bash
python ingest.py
python descriptors.py
```
**Expected Output**: `data/processed/computed_descriptors.csv`

### 2. Model Training & Evaluation
```bash
python train.py
python evaluate.py
```
**Expected Output**: `data/evaluation/model_rf.pkl`, `data/evaluation/model_metrics.json`

### 3. Feature Importance & Plots
```bash
python importance.py
python plots.py
```
**Expected Output**: `data/evaluation/feature_ranking.json`, `data/evaluation/ale_*.png`

### 4. Research Summary
```bash
python generate_research_summary.py
```
**Expected Output**: `research.md`

## Validation

To verify the entire pipeline ran correctly and produced valid artifacts:

```bash
python quickstart_validation.py
```

This script:
1. Checks existence of all required output files.
2. Validates JSON schemas for metrics and rankings.
3. Confirms non-empty content in critical files.
4. Logs the final status.

## Troubleshooting

- **Missing Data**: If `data/raw/` is empty, ensure `ingest.py` completed successfully or manually download the MP-2020 dataset.
- **Memory Errors**: If the dataset is too large, check `code/config.py` for `ROW_THRESHOLD` and ensure `code/utils/io.py` chunked reading is active.
- **API Failures**: If MPDS API is unreachable, the system will attempt to load from `data/raw/mp-2020.csv` if present.
