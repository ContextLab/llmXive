# Quickstart Guide

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

## 1. Generate Synthetic Data (T015)
Run the data generator to create the golden subset with known ground truth.
```bash
python code/data/generator.py --seed 42 --num-tasks 10 --output data/raw/golden_subset.json
```

## 2. Verify Pairing (T004)
Ensure strict pairing of task instances and seeds.
```bash
python code/utils/verify_checksums.py --input data/raw/golden_subset.json
```

## 3. Run Classification Pipeline
Parse and classify the traces.
```bash
python code/classification/parser.py --input data/raw/golden_subset.json --output data/processed/classified_traces.json
python code/classification/state_validator.py --input data/processed/classified_traces.json --golden data/raw/golden_subset.json
```

## 4. Run Intervention Experiments
```bash
python code/intervention/runner.py --condition baseline --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/baseline_results.json
python code/intervention/runner.py --condition intervention --checkpoint-interval 3 --model models/llama-3-8b-instruct.Q4_K_M.gguf --seed 42 --output data/processed/intervention_results.json
```

## 5. Statistical Analysis
```bash
python code/analysis/stats.py --baseline data/processed/baseline_results.json --intervention data/processed/intervention_results.json --output data/processed/stats_report.json
```

## 6. Sensitivity Analysis
```bash
python code/analysis/sensitivity.py --results data/processed/experiment_results.json --intervals 3,5 --output data/processed/sensitivity_analysis.json
```

## 7. Generate Report
```bash
python code/utils/generate_report.py --stats data/processed/stats_report.json --sensitivity data/processed/sensitivity_analysis.json --output docs/report.md
```