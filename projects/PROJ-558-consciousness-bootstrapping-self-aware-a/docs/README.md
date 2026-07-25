# Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## Project Overview

This project investigates whether recursive self-modeling in language models can lead to emergent self-awareness. We implement a TinyLlama-based model with temporal recursive self-attention and train it on a sampled Pile subset to produce recursive and baseline checkpoints.

The project measures self-consistency, error detection, and uncertainty calibration to evaluate meta-cognitive capabilities.

## Repository Structure

```
projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
├── code/
│ ├── __init__.py
│ ├── config.py
│ ├── data_loader.py
│ ├── analysis/
│ │ ├── __init__.py
│ │ └── stats.py
│ ├── evaluation/
│ │ ├── __init__.py
│ │ ├── loss_functions.py
│ │ ├── metrics.py
│ │ ├── results.py
│ │ └── run_benchmarks.py
│ ├── models/
│ │ ├── __init__.py
│ │ ├── base_llama.py
│ │ ├── checkpoint.py
│ │ └── recursive_llama.py
│ ├── training/
│ │ ├── __init__.py
│ │ └── train.py
│ └── utils/
│ ├── __init__.py
│ └── logging.py
├── data/
│ ├── raw/
│ │ ├── pile_arxiv_truncated.json
│ │ ├── gsm8k.json
│ │ └── mmlu.json
│ └── manifest.json
├── artifacts/
│ └── results/
│ ├── evaluation_results_recursive_seed_*.json
│ ├── evaluation_results_baseline_seed_*.json
│ ├── statistical_report.json
│ └── sensitivity_analysis.csv
├── tests/
│ ├── unit/
│ │ ├── models/
│ │ │ └── test_recursive_attention.py
│ │ ├── training/
│ │ │ └── test_loss_functions.py
│ │ ├── evaluation/
│ │ │ └── test_metrics.py
│ │ └── analysis/
│ │ └── test_stats.py
│ └── __init__.py
├── docs/
│ ├── README.md
│ └── statistical_report_format.md
├── requirements.txt
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.11+
- CPU-only execution (GPU not supported)

### Installation

```bash
pip install -r requirements.txt
```

### Data Preparation

Run the data loader to fetch required datasets:

```bash
python code/data_loader.py
```

This will download:
- Pile ArXiv subset (training data)
- GSM8K (evaluation data)
- MMLU (evaluation data)

### Training

Train both recursive and baseline models:

```bash
python code/training/train.py
```

This produces checkpoints for both model types across multiple seeds.

### Evaluation

Run benchmarks on trained models:

```bash
python code/evaluation/run_benchmarks.py
```

This generates evaluation results for self-consistency, calibration, and error detection.

### Statistical Analysis

Generate the statistical report:

```bash
python code/analysis/stats.py
```

This produces:
- `artifacts/results/statistical_report.json`
- `artifacts/results/sensitivity_analysis.csv`

## Statistical Report Format

See [`docs/statistical_report_format.md`](statistical_report_format.md) for the complete schema and field descriptions of the statistical report.

The report includes:
- Paired t-tests comparing recursive vs baseline models
- Cohen's d effect sizes with 95% confidence intervals
- Bonferroni-corrected p-values
- Percentage differences in self-consistency scores
- Sensitivity analysis across confidence thresholds {0.4, 0.5, 0.6}

## User Stories

### US1: Construct and Train Self-Referential Model (P1)

Implement temporal recursive self-attention and train on Pile subset.

**Artifacts**:
- `code/models/recursive_llama.py`
- `code/evaluation/loss_functions.py`
- `code/training/train.py`

### US2: Evaluate Meta-Cognitive Metrics (P2)

Run benchmarks to measure self-consistency, error detection, and uncertainty calibration.

**Artifacts**:
- `code/evaluation/metrics.py`
- `code/evaluation/run_benchmarks.py`

### US3: Perform Statistical Analysis and Sensitivity Testing (P3)

Perform paired t-tests and sensitivity analysis.

**Artifacts**:
- `code/analysis/stats.py`
- `artifacts/results/statistical_report.json`
- `artifacts/results/sensitivity_analysis.csv`

## Testing

Run unit tests:

```bash
pytest tests/
```

## Linting and Formatting

Check code quality:

```bash
ruff check code/
black --check code/
```

## Dependencies

See `requirements.txt` for the full list of dependencies.

Key packages:
- `torch` (CPU-only)
- `transformers`
- `datasets`
- `scikit-learn`
- `scipy`

## Limitations

- CPU-only execution limits model size and training speed.
- Limited seed count for statistical analysis.
- Dataset truncation to 100,000 tokens for training.
- Recursion depth capped at 2 to prevent OOM errors.

## References

- **spec.md**: Project specification with functional requirements and success criteria.
- **plan.md**: High-level project plan and design decisions.
- **research.md**: Research notes and philosophical considerations.