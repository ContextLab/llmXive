# Quickstart Guide

## 1. Setup Environment

Ensure you are in the project root and have Python 3.11 installed.

```bash
cd code
pip install -r requirements.txt
```

## 2. Run User Story 1: Compress & Train

Execute the compression pipeline to generate student models.

```bash
python -m models.compress
```

This will:
- Load the teacher model (`facebook/wav2vec2-base-960h`).
- Apply pruning and quantization (FP32, INT8, INT4).
- Train via Knowledge Distillation.
- Save checkpoints to `data/processed/`.

## 3. Run User Story 2: Evaluate Robustness

Once models are generated, evaluate them on the Subtle Cue dataset.

```bash
python -m inference.runner
python -m inference.metrics
```

Outputs:
- `data/processed/robustness_metrics.csv`

## 4. Run User Story 3: Analysis

Generate robustness curves and sensitivity reports.

```bash
python -m analysis.robustness_curve
python -m analysis.sensitivity
```

Outputs:
- `data/processed/correlation_data.json`
- `data/processed/breaking_point.json`

## 5. Run Tests

```bash
pytest tests/
```
