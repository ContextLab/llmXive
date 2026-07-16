# Quickstart Guide: Memory Palaces in LLMs

This guide provides a minimal end-to-end workflow to reproduce the core experiments
for the "Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall" project.
It covers environment setup, data download, model training, evaluation, and statistical
analysis.

## Prerequisites

- Python 3.9+
- CUDA-capable GPU (recommended for training; CPU fallback available but slower)
- At least 16 GB RAM (for full dataset processing; see Memory Constraints below)
- Git

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-596-memory-palaces-in-llms-spatial-reasoning
pip install -r requirements.txt
```

Verify the installation:

```bash
python -c "import torch; import transformers; import datasets; print('Dependencies OK')"
```

## 2. Data Download and Verification

The project requires three datasets: bAbI Task 3, LAMBADA, and Story Cloze Test.
Run the download script to fetch and verify checksums:

```bash
python code/data/download.py
```

This will:
- Download datasets to `data/raw/`
- Compute SHA-256 checksums and save them to `data/raw/checksums.json`
- Fail loudly if any dataset cannot be retrieved or verified

**Note**: If you encounter memory issues during download, ensure you have sufficient
disk space and RAM. The script will log progress to the console.

## 3. Training and Evaluation

The main entry point orchestrates the full pipeline: download (if needed), training
across multiple seeds, evaluation, and statistical analysis.

```bash
python code/main.py
```

This script will:
1. Verify dataset availability (skip download if already present)
2. Check memory budget and adjust batch size/dataset size if necessary
3. Train both the spatial-memory variant and the baseline (GPT-2 Medium / DistilGPT2)
 across 5 random seeds
4. Evaluate exact-match recall for each seed
5. Perform statistical analysis (paired t-tests, effect sizes, multiple-comparison correction)
6. Generate structural metrics (interference distance, slot occupancy, coordinate variance)
7. Write all results to `artifacts/results/`

### Expected Outputs

After completion, the following files will be generated:

- `artifacts/results/run_summary.json`: High-level summary (seeds, accuracies, runtime)
- `artifacts/results/recall_accuracy.json`: Per-seed exact-match recall scores
- `artifacts/results/hyperparams_log.json`: Final hyperparameters and memory decisions
- `artifacts/results/statistical_summary.json`: P-values, effect sizes, confidence intervals
- `artifacts/results/interference_distance.json`: Spatial vs. baseline interference metrics
- `artifacts/results/slot_occupancy_epoch_*.csv`: Slot occupancy per epoch
- `artifacts/results/coordinate_variance_epoch_*.csv`: Coordinate variance per epoch
- `artifacts/results/runtime_report.json`: Runtime verification (≤5 hours limit)

## 4. Memory Constraints and Adaptive Behavior

This project implements adaptive memory management to handle hardware limitations:

- **Batch Size Reduction**: If RSS > 6 GB, batch size is reduced from 8 → 4
- **Dataset Capping**: If RSS still > 6 GB at batch size 4, the training dataset
 is capped to a predefined fraction (see `code/training/memory_monitor.py`)
- **Model Fallback**: If memory budget is exceeded, the system falls back from
 GPT-2 Medium to DistilGPT2 (see `code/models/loading.py`)

All decisions are logged to `artifacts/results/hyperparams_log.json`.

## 5. Statistical Analysis

The statistical analysis module (`code/evaluation/stats.py`) performs:

- Shapiro-Wilk normality check
- Paired two-tailed t-tests (or Wilcoxon signed-rank if non-normal)
- Multiple-comparison correction (Holm-Bonferroni)
- Effect size calculation (Cohen's d with 95% confidence intervals)

Results are aggregated in `artifacts/results/statistical_summary.json`.

## 6. Running Individual Components

You can also run individual components of the pipeline:

### Download Only
```bash
python code/data/download.py
```

### Training Loop Only
```bash
python code/training/loop.py --seeds -4 -3 -2 -1 0
```

### Evaluation Only
```bash
python code/evaluation/metrics.py
```

### Statistical Analysis Only
```bash
python code/evaluation/stats.py
```

## 7. Validation

To validate the quickstart, run the provided validation script:

```bash
./scripts/validate_quickstart.sh
```

This script performs a minimal end-to-end run and verifies that:
- `artifacts/results/run_summary.json` is generated
- Runtime is within the 5-hour limit
- All required output files exist

## 8. Troubleshooting

### Out of Memory (OOM) Errors
- The system automatically reduces batch size and caps dataset size
- Ensure you have at least 16 GB RAM; if not, consider using a smaller model
 (DistilGPT2 is the fallback)
- Check `artifacts/results/hyperparams_log.json` for adaptive decisions

### Dataset Download Fails
- Ensure network connectivity
- Verify that the `datasets` library is up to date
- Check `data/raw/checksums.json` for partial downloads

### Statistical Analysis Errors
- Ensure `scipy` is installed
- Verify that `recall_accuracy.json` contains valid data for all seeds

## 9. Further Reading

- **Research Plan**: `research.md`
- **Specification**: `specs/001-memory-palaces-in-llms-spatial-reasoning/spec.md`
- **Contracts**: `docs/contracts.md`
- **Power Analysis**: `docs/power_analysis_report.md`

## 10. Contact and Contribution

For issues or contributions, please refer to the main repository documentation
or open an issue with the relevant error logs and environment details.