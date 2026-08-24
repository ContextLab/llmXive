# llmXive Follow-up: Extending Memory Reconstruction Pipeline

## Quick Start Guide

This guide explains how to run the complete analysis pipeline for the llmXive follow-up project.

### Prerequisites

- Python 3.9+
- Required packages (install via `pip install -r code/requirements.txt`)
- Access to HuggingFace Hub (for dataset downloads)

### Setup

1. Install dependencies:
```bash
pip install -r code/requirements.txt
python -m spacy download en_core_web_sm
```

2. Ensure output directories exist:
```bash
mkdir -p data/raw data/intermediate data/processed graphs figures
```

### Data Pipeline

1. Download LoCoMo benchmark dataset:
```bash
python code/data_loader.py --download --subset test
```

2. Extract triples and build graphs:
```bash
python code/data_loader.py --extract --input data/raw/locomo.jsonl --output data/intermediate/graphs_raw.json
```

3. Generate noisy graphs:
```bash
python code/data_loader.py --noisy --input data/intermediate/graphs_raw.json --output data/processed/graphs/graph_noise_42.json --seed 42
```

### Execution Strategies

1. Run Baseline (Full) Strategy:
```bash
python code/runner.py --strategy full --input data/raw/locomo.jsonl --graph data/intermediate/graphs_raw.json --output data/processed/baseline_results.csv --timeout 300
```

2. Run Baseline on Noisy Graphs:
```bash
python code/runner.py --strategy full --input data/raw/locomo.jsonl --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_baseline_results.csv --noisy --timeout 300
```

3. Run Lazy Strategy:
```bash
python code/runner.py --strategy lazy --input data/raw/locomo.jsonl --graph data/intermediate/graphs_raw.json --output data/processed/lazy_results.csv --threshold 0.7 --timeout 300
```

4. Run Lazy Strategy on Noisy Graphs:
```bash
python code/runner.py --strategy lazy --input data/raw/locomo.jsonl --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_lazy_results.csv --noisy --threshold 0.7 --timeout 300
```

5. Run Greedy Strategy:
```bash
python code/runner.py --strategy greedy --input data/raw/locomo.jsonl --graph data/intermediate/graphs_raw.json --output data/processed/greedy_results.csv --topk 5 --timeout 300
```

6. Run Greedy Strategy on Noisy Graphs:
```bash
python code/runner.py --strategy greedy --input data/raw/locomo.jsonl --graph data/processed/graphs/graph_noise_42.json --output data/processed/noisy_greedy_results.csv --noisy --topk 5 --timeout 300
```

### Analysis

1. Run Statistical Analysis (Clean):
```bash
python code/analysis/stats.py --baseline data/processed/baseline_results.csv --lazy data/processed/lazy_results.csv --greedy data/processed/greedy_results.csv --output data/processed/statistical_results.json
```

2. Run Sensitivity Analysis:
```bash
python code/analysis/sensitivity_analysis.py --input data/processed/lazy_results.csv --output data/processed/sensitivity_analysis.csv --thresholds 0.5,0.7,0.9
```

3. Run Correlation Analysis:
```bash
python code/analysis/correlation_analysis.py --input data/processed/baseline_results.csv --output data/processed/correlation_results.json
```

4. Run Threshold Analysis:
```bash
python code/analysis/threshold_analysis.py --baseline data/processed/baseline_results.csv --lazy data/processed/lazy_results.csv --greedy data/processed/greedy_results.csv --output data/processed/threshold_analysis.json
```

### Validation

1. Validate all results:
```bash
python code/utils/validate_results.py --input data/processed/ --schema contracts/dataset.schema.yaml
```

2. Verify reproducibility:
```bash
python code/utils/verify_seeds.py --graph data/processed/graphs/graph_noise_42.json --seed 42
```

### Streaming Mode (for large datasets)

For datasets that exceed memory limits, use streaming mode:

```bash
python code/runner.py --strategy lazy --input data/raw/locomo.jsonl --graph data/intermediate/graphs_raw.json --output data/processed/lazy_results_streaming.csv --threshold 0.7 --streaming --chunk-size 10
```

### Troubleshooting

- If you encounter "Dataset not found" errors, verify the HuggingFace dataset ID is correct
- If memory errors occur, enable streaming mode or reduce chunk size
- If timeout errors occur, increase the timeout value or optimize the strategy implementation