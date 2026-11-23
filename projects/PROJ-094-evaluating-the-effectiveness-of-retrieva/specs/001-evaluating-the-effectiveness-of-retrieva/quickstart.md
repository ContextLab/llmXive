# Quickstart: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

## Prerequisites

- Python 3.11+
- Standard RAM and CPU core allocation (GitHub Actions free-tier compatible)
- Internet access for dataset download (one-time)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-094-evaluating-the-effectiveness-of-retrieva
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   `requirements.txt` includes: `ir-datasets`, `sentence-transformers`, `transformers`, `faiss-cpu`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `pyyaml`, `pytest`, `accelerate`.

3. **Download dataset** (automatic on first run):
   ```bash
   python src/cli/run_experiment.py --download-only
   ```
   This downloads CodeSearchNet (Python/Java) to `data/raw/` and computes checksums.

## Running the Experiment

### Standard Run (CPU)
```bash
python src/cli/run_experiment.py \
  --queries 200 \
  --seed 42 \
  --output results/metrics.csv
```
- Downloads and preprocesses a set of queries from the Test Split.
- Runs BM25, Dual-Encoder, and RAG pipelines (with 8-bit quantization if needed).
- Computes metrics and outputs `results/metrics.csv`.

### Resource-Constrained Run
```bash
python src/cli/run_experiment.py \
  --queries 200 \
  --seed 42 \
  --resource-constrained \
  --output results/metrics_constrained.csv
```
- Enforces ≤1GB FAISS index memory.
- Uses `codegen-160M-mono` (2-layer) for generation.
- Outputs degradation report.

### Full Pipeline (with Correlation Analysis)
```bash
python src/cli/run_experiment.py \
  --queries 200 \
  --seed 42 \
  --analyze \
  --output results/final_results.csv
```
- Runs full experiment + correlation analysis + label noise estimation.
- Outputs `results/final_results.csv` and `results/correlation.json`.

### Control Experiment (Masking)
```bash
python src/cli/run_experiment.py \
  --queries 200 \
  --seed 42 \
  --control-masking \
  --output results/control_metrics.csv
```
- Runs retrieval on masked code (API/doc tokens replaced with `<MASK>`).
- Outputs control metrics for artifact verification.

## Output Files

- `results/metrics.csv`: Per-query metrics for all methods.
- `results/correlation.json`: Statistical analysis results.
- `results/degradation_report.json`: Resource-constrained vs. standard comparison.
- `results/noise_estimate.json`: Label noise estimate from manual spot-check.
- `results/final_results.csv`: Combined results for paper generation.

## Validation

1. **Schema Validation**:
   ```bash
   pytest tests/contract/
   ```
   Validates all output files against `contracts/*.schema.yaml`.

2. **Reproducibility Check**:
   ```bash
   python src/cli/run_experiment.py --seed 42 --output results/test_run.csv
   python src/cli/run_experiment.py --seed 42 --output results/test_run_2.csv
   diff results/test_run.csv results/test_run_2.csv
   ```
   Outputs should be identical (bit-for-bit).

3. **Resource Constraint Check**:
   ```bash
   python src/cli/run_experiment.py --resource-constrained --output results/test_constrained.csv
   # Check peak RSS via psutil logs
   ```
   Verify FAISS index ≤1GB and generator model uses 2 layers.

## Troubleshooting

- **OOM Error on CPU**: If `codegen-350M-mono` fails, the system reduces context window to a constrained length. If OOM persists, it triggers the GPU offload (non-reproducible).
- **Dataset Download Fails**: Check internet connection. Ensure `ir-datasets` URLs are reachable.
- **Descriptor Calculation Fails**: Some snippets may fail (e.g., invalid syntax). These are marked as "NaN" and excluded from correlation analysis.

## Next Steps

1. Review `results/final_results.csv` and `results/correlation.json`.
2. Generate paper artifacts using the results.
3. Validate against success criteria (SC-001 to SC-006).