# llmXive Quickstart Guide

This guide provides the commands to run the full AgenticSTS pipeline for the follow-up project.

## Prerequisites

- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`
- Raw trajectory data in `data/raw/` (JSON/JSONL format)

## Execution Steps

The pipeline is executed in phases. Run the following commands in order.

### Phase 1: Setup & Data Processing

1. **Parse Trajectories** (T006)
 ```bash
 python code/parser.py
 ```
 *Output*: `data/processed/metrics_with_moves.csv`

2. **Calculate Entropy** (T005)
 ```bash
 python code/entropy.py
 ```
 *Output*: `data/processed/edge_case_warnings.log` (if applicable)

3. **Split Data** (T014a)
 ```bash
 python code/splitter.py
 ```
 *Output*: `data/processed/train_set.csv`, `data/processed/test_set.csv`, `data/processed/validation_set_ids.json`

4. **Extract Static Proxy** (T007c)
 ```bash
 python code/proxy_extractor.py
 ```
 *Output*: `data/processed/static_log_proxy.json`

5. **Run Ablation Study** (T008)
 ```bash
 python code/ablation.py
 ```
 *Output*: `data/processed/ablation_labels_train.json`, `data/processed/ablation_labels_validation.json`

6. **Validate Proxy** (T014)
 ```bash
 python code/classifier.py
 ```
 *Output*: `data/processed/proxy_validation_report.json`

7. **Train Classifier** (T009)
 ```bash
 python code/classifier.py --train
 ```
 *Output*: `models/layer_utility_classifier.pkl`

### Phase 2: Simulation & Baselines

8. **Run Dynamic Simulation** (T017)
 ```bash
 python code/simulator.py --policy dynamic
 ```
 *Output*: `data/processed/simulation_logs_dynamic.json`

9. **Run Static Baseline** (T019)
 ```bash
 python code/baseline_static_runner.py
 ```
 *Output*: `data/processed/simulation_logs_static.json`

10. **Run Random Baseline** (T020)
 ```bash
 python code/engine_runner.py --policy random
 ```
 *Output*: `data/processed/simulation_logs_random.json`

### Phase 3: Analysis

11. **Aggregate Stats** (T021)
 ```bash
 python code/stats.py
 ```
 *Output*: `data/processed/baseline_comparison.csv`

12. **Token Reduction Verification** (T022a)
 ```bash
 python code/token_reduction_verifier.py
 ```
 *Output*: `data/processed/token_reduction_verification.json`

13. **Statistical Testing** (T025)
 ```bash
 python code/stats.py --test
 ```
 *Output*: `data/processed/statistical_results.json`

14. **Generate Final Report** (T028)
 ```bash
 python code/generate_statistical_report.py
 ```
 *Output*: `data/processed/statistical_results.json` (finalized)

## Full Pipeline Run

To run the entire pipeline sequentially (excluding manual checks):

```bash
python code/main.py
```

*Note*: Ensure `data/raw/` contains valid trajectory files before running.

## Troubleshooting

- **Missing Data**: Ensure `data/raw/` is populated with trajectory logs.
- **Import Errors**: Verify `code/` is in `PYTHONPATH` or run from project root.
- **Engine Errors**: Check `data/processed/engine_errors.log` for crash details.