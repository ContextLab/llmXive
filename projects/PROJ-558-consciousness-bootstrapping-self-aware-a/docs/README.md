# Consciousness Bootstrapping Documentation

## Overview

This project implements a research pipeline for "Consciousness Bootstrapping:
Self-Aware AI Through Recursive Introspection." The system trains a small
transformer model with temporal recursive self-attention and evaluates its
meta-cognitive capabilities.

## Project Structure

```
projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
├── code/
│ ├── analysis/ # Statistical analysis (T024-T027)
│ ├── data_loader.py # Dataset fetching (T004, T004b)
│ ├── config.py # Hyperparameter management (T005)
│ ├── evaluation/ # Metrics and benchmarking (T018-T022)
│ ├── models/ # Model definitions (T007, T011)
│ ├── training/ # Training scripts (T013-T015)
│ └── utils/ # Logging and utilities (T008)
├── data/
│ ├── raw/ # Raw datasets (Pile, GSM8K, MMLU)
│ └── manifest.json # Data checksums
├── artifacts/
│ └── results/ # Checkpoints, reports, and analysis outputs
├── docs/ # This documentation
└── tests/ # Unit tests for all components
```

## Quick Start

### Prerequisites

- Python 3.11+
- CPU-only execution (GPU not supported in CI)
- Dependencies: `torch`, `transformers`, `datasets`, `scikit-learn`, `scipy`

### Installation

```bash
pip install -r requirements.txt
```

### Data Preparation

Run the data loader to fetch and prepare datasets:

```bash
python code/data_loader.py
```

This will download:
- Pile (ArXiv subset) for training
- GSM8K and MMLU for evaluation

Outputs are saved to `data/raw/` with checksums in `data/manifest.json`.

### Training

Train both recursive and baseline models:

```bash
python code/training/train.py --seeds 123 456 789
```

Checkpoints are saved to `artifacts/results/`.

### Evaluation

Run benchmarks against trained models:

```bash
python code/evaluation/run_benchmarks.py \
 --checkpoint-dir artifacts/results \
 --output-dir artifacts/results
```

### Statistical Analysis

Generate statistical reports and sensitivity analysis:

```bash
python code/analysis/stats.py
```

Outputs:
- `artifacts/results/statistical_report.json`
- `artifacts/results/sensitivity_analysis.csv`

## Statistical Report Format

See `STATISTICAL_REPORT_FORMAT.md` for detailed documentation on the
structure and interpretation of statistical analysis outputs.

## Testing

Run all unit tests:

```bash
pytest tests/ -v
```

Linting and formatting:

```bash
ruff check code/
black --check code/
```

## Research Design

### Core Hypothesis

Recursive self-modeling through temporal recursive self-attention will
enable models to develop meta-cognitive capabilities, specifically:
- Self-consistency in reasoning paths
- Calibration of confidence estimates
- Error detection capabilities

### Methodology

1. **Model Architecture**: TinyLlama-based model with temporal recursive
 self-attention (FR-001).
2. **Training Objective**: Joint loss combining cross-entropy with a
 confidence-prediction proxy derived from internal generation (FR-002).
3. **Evaluation Metrics**:
 - Self-consistency via majority vote (FR-003)
 - Calibration via Brier score and ECE (FR-004)
 - Statistical significance via paired t-tests (FR-005)
4. **Sensitivity Analysis**: Threshold sweep across {0.4, 0.5, 0.6} (FR-006).

### Success Criteria

- **SC-001**: Recursive model demonstrates >10% improvement in self-consistency
 over baseline with statistical significance (p < 0.05 after Bonferroni correction).
- **SC-002**: Confidence predictions are well-calibrated (ECE < 0.1).
- **SC-003**: Sensitivity analysis identifies an optimal confidence threshold
 that maximizes F1 score for error detection.

## Limitations

- **Compute Constraints**: All experiments run on CPU-only infrastructure
 with limited memory (<7GB RAM).
- **Model Size**: Models are restricted to <300M parameters.
- **Recursion Depth**: Hard-capped at depth=2 to prevent OOM errors.
- **Scope**: Philosophical operationalizations (Turing, Socrates, Krakauer
 concerns) are out of scope per spec.md assumptions. Only measurable
 metrics defined in FR-003 to FR-007 are implemented.

## References

- `plan.md`: Project plan and complexity tracking.
- `spec.md`: Feature specifications and success criteria.
- `tasks.md`: Implementation task list and dependencies.
- `research.md`: Philosophical and theoretical background.
