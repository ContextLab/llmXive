# Architecture Overview: Consciousness Bootstrapping

This document describes the high-level architecture of the recursive self-modeling
system.

## Core Components

### 1. Data Ingestion (`code/data_loader.py`)
- **Input**: Pile (arXiv subset), GSM8K, MMLU.
- **Process**: Fetches real data from HuggingFace. Truncates to `token_limit` (100,000).
- **Output**: JSON files in `data/raw/`.

### 2. Model Architecture (`code/models/`)
- **Base**: TinyLlama (<300M params) for CPU feasibility.
- **Recursive Wrapper**: `RecursiveLlamaWrapper` adds temporal recursive self-attention.
- **Key Feature**: The attention mechanism can attend to its own previous hidden states
 from the same forward pass, enabling self-referential processing.

### 3. Training Loop (`code/training/train.py`)
- **Loss Function**: Joint Loss = Cross-Entropy + Confidence Prediction Loss.
- **Proxy**: Confidence target is derived from N=5 self-generated paths (majority vote).
- **Constraints**: Hard fails if recursion depth > 2 or OOM detected.

### 4. Evaluation (`code/evaluation/`)
- **Benchmarks**: GSM8K, MMLU.
- **Metrics**:
 - Self-Consistency (N=10 paths per question).
 - Calibration (ECE, Brier Score).
 - Error Detection (ROC-AUC).
- **Control**: Shuffled-attention control dataset to isolate temporal effects.

### 5. Analysis (`code/analysis/stats.py`)
- **Statistical Tests**: Paired t-tests, Cohen's d, Bonferroni correction.
- **Sensitivity**: Sweeps confidence thresholds {0.4, 0.5, 0.6}.
- **Output**: `statistical_report.json` with p-values and effect sizes.

## Data Flow

1. **Config Validation**: `scripts/validate_config.py` ensures `token_limit` is 100,000.
2. **Data Load**: `data_loader.py` fetches and saves datasets.
3. **Training**: `train.py` produces `baseline_ckpt` and `recursive_ckpt`.
4. **Evaluation**: `run_benchmarks.py` generates predictions and metrics.
5. **Analysis**: `stats.py` aggregates results and generates the final report.

## File Structure

```
code/
├── config.py
├── data_loader.py
├── models/
│ ├── base_llama.py
│ ├── recursive_llama.py
│ └── checkpoint.py
├── training/
│ ├── train.py
│ └── loss_functions.py
├── evaluation/
│ ├── metrics.py
│ ├── run_benchmarks.py
│ └── results.py
├── analysis/
│ └── stats.py
└── utils/
 ├── logging.py
 └── memory_profiler.py
```

## Execution Order

1. `python code/create_project_structure.py` (Phase 1)
2. `python scripts/validate_config.py` (Phase 2)
3. `python code/data_loader.py` (Phase 2)
4. `python code/training/train.py` (Phase 3)
5. `python code/evaluation/run_benchmarks.py` (Phase 4)
6. `python code/analysis/stats.py` (Phase 5)