# Quickstart: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

## Prerequisites

- Python 3.11+
- 7 GB RAM, 2 CPU cores (GitHub Actions free-tier compatible)
- Git

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-594-quantum-cognition-in-llms-superposition
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   - `requirements.txt` pins `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `pytest`.

## Data Preparation

1. **Download WiC Dataset**:
   ```bash
   python code/data/download_wic.py
   ```
   - Fetches WiC from SuperGLUE via `datasets` library.
   - Checksums recorded in `state/...yaml`.

## Running Experiments

### 1. Baseline Evaluation (US-1)
```bash
python code/experiments/run_baseline.py --seed 42
```
- Outputs: `data/results/baseline_run_42.json` (accuracy, F1).

### 2. Quantum Model Training & Evaluation (US-2)
```bash
python code/experiments/run_quantum.py --seed 42
```
- Trains adapter for 3 epochs; outputs `data/results/quantum_run_42.json`.

### 3. Ablation Study (FR-005)
```bash
python code/experiments/run_ablation.py --seed 42
```
- Classical sum-of-probs baseline; outputs `data/results/ablation_run_42.json`.

### 4. Statistical Analysis (US-3)
```bash
python code/analysis/stats_test.py
```
- Runs paired t-test across 5 seeds; outputs `data/results/stats_report.json`.

### 5. Interference Validation (FR-010)
```bash
python code/analysis/interference_check.py
```
- Verifies cross-term negativity; outputs `data/results/interference_validation.json`.

## Testing

1. **Unit Tests**:
   ```bash
   pytest tests/unit/test_complex_ops.py -v
   ```
   - Synthetic interference tests (destructive/constructive).

2. **Contract Tests**:
   ```bash
   pytest tests/contract/test_schemas.py -v
   ```
   - Validates outputs against YAML schemas.

## Expected Outputs

- `data/results/runs.jsonl`: Aggregated experiment metadata.
- `data/results/stats_report.json`: t-test results (p-value, Cohen's d).
- `data/results/interference_validation.json`: Cross-term validation.

## Troubleshooting

- **NaN/Inf Errors**: Check `utils/logging.py` for detected instabilities; ensure batch size ≤ 8.
- **Memory Errors**: Reduce batch size or dataset subset size.
- **CUDA Errors**: Ensure `torch` is CPU-only (no CUDA build).
