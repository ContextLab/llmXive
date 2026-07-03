# Quickstart Guide: Memory Palaces in LLMs

This guide provides a minimal end-to-end workflow for reproducing the spatial reasoning experiments described in PROJ-596. It covers environment setup, data download, training execution, and result verification.

## Prerequisites

- Python 3.9+
- 16GB+ RAM (recommended for full dataset processing)
- 6GB+ free disk space for datasets and artifacts
- Internet connection for initial data download

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Note**: Ensure `torch`, `transformers`, `datasets`, `scipy`, `pandas`, `numpy`, and `pyyaml` are installed as per `requirements.txt`.

## 2. Data Download and Verification

Download the three permitted datasets (bAbI Task 3, LAMBADA, Story Cloze) and verify integrity:

```bash
python code/data/download.py
```

This script will:
- Fetch datasets via the `datasets` library.
- Compute SHA-256 checksums.
- Store raw data in `data/raw/`.
- Write checksums to `data/raw/checksums.json`.

**Expected Output**:
- `data/raw/babi_task3_10k/`
- `data/raw/lambada/`
- `data/raw/story_cloze/`
- `data/raw/checksums.json`

## 3. Run the Training Pipeline

Execute the main entry point to orchestrate the full pipeline:

```bash
python code/main.py
```

The pipeline performs:
1. **Memory Check**: Verifies RAM availability; adjusts batch size (8 → 4) or caps dataset size if RSS > 6GB.
2. **Model Loading**: Loads `gpt2-medium` (4-bit quantized) or falls back to `DistilGPT2`.
3. **Training**: Runs training loops across 5 random seeds (default range: -4 to 0).
4. **Evaluation**: Computes exact-match recall and structural metrics.
5. **Logging**: Writes results to `artifacts/results/`.

**Runtime**: Approximately 4–5 hours on a standard CPU/GPU hybrid environment.

## 4. Verify Results

After execution, verify that the following artifacts exist:

- `artifacts/results/run_summary.json`: Contains seeds, accuracies, effective batch size, and runtime.
- `artifacts/results/hyperparams_log.json`: Logs hyperparameters and memory decisions.
- `artifacts/results/recall_accuracy.json`: Per-seed exact-match recall scores.
- `artifacts/results/statistical_summary.json`: (If US2 is run) P-values, effect sizes, and confidence intervals.
- `artifacts/results/interference_distance.json`: (If US3 is run) Spatial vs. baseline interference metrics.

Example verification command:

```bash
cat artifacts/results/run_summary.json
```

Expected JSON structure:
```json
{
 "seeds": [-4, -3, -2, -1, 0],
 "accuracies": [0.82, 0.85, 0.84, 0.83, 0.86],
 "effective_batch_size": 4,
 "runtime_seconds": 14200
}
```

## 5. Troubleshooting

### Memory Issues
If the process fails with OOM errors:
- Ensure no other heavy processes are running.
- The `memory_monitor.py` utility should automatically reduce batch size to 4.
- If RSS still exceeds 6GB, the dataset will be capped to a deferred fraction. Check `hyperparams_log.json` for details.

### Data Download Failures
If datasets fail to download:
- Check internet connectivity.
- Verify `datasets` library version compatibility.
- Re-run `python code/data/download.py` after clearing `data/raw/`.

### Import Errors
Ensure all `__init__.py` files exist in `code/`, `code/models/`, `code/training/`, and `code/evaluation/`.

## 6. Next Steps

- **Statistical Analysis**: Run `python code/evaluation/stats.py` to perform paired t-tests and effect-size calculations (US2).
- **Structural Metrics**: Run interference-injection experiments via `code/evaluation/metrics.py` (US3).
- **Visualization**: Generate plots from `artifacts/results/` using standard Python plotting libraries.

For detailed API documentation, see `docs/contracts.md` and `research.md`.