# Quickstart Guide: AgenticSTS Follow-up Pipeline

This guide outlines the steps to run the full analysis pipeline for the AgenticSTS follow-up project.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## Data Preparation

1. **Ingest Real Data**: Ensure `data/raw/agenticsts_trajectories.jsonl` exists.
 - Run `python code/t005b_ingest_real_data.py` if not present.
2. **Verify Checksums**: Ensure `data/raw/manifest.json` exists and matches.

## Pipeline Execution

Run the full pipeline in order:

1. **Parse Trajectories**:
 `python code/parser.py`
 - Output: `data/processed/metrics_with_moves.csv`

2. **Calculate Entropy**:
 `python code/entropy.py`
 - Output: `data/processed/entropy_metrics.csv`

3. **Split Data**:
 `python code/splitter.py`
 - Output: `data/processed/train_set.csv`, `validation_set.csv`, `test_set.csv`

4. **Train Classifier**:
 `python code/classifier.py`
 - Output: `models/layer_utility_classifier.pkl`

5. **Run Simulations**:
 - **Dynamic**: `python code/run_dynamic_simulation.py`
 - Output: `data/processed/simulation_logs_dynamic.json`
 - **Static**: `python code/baseline_static_runner.py`
 - Output: `data/processed/simulation_logs_static.json`
 - **Random**: `python code/run_random_baseline.py`
 - Output: `data/processed/simulation_logs_random.json`

6. **Generate Baseline Comparison**:
 `python code/generate_baseline_comparison.py`
 - Output: `data/processed/baseline_comparison.csv`

7. **Statistical Analysis**:
 `python code/stats.py`
 - Output: `data/processed/mcnemar_results.json`, `data/processed/ttest_results.json`, `data/processed/divergence_report.json`

8. **Validation & Reporting**:
 `python code/quickstart_validator.py`
 - Verifies all artifacts and generates `data/processed/build_status.json`.

## Verification

After running, check `data/processed/build_status.json` for success status.
Review `data/processed/baseline_comparison.csv` for token reduction metrics.