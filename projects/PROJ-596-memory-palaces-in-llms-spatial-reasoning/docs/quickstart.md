# Quickstart Guide: Memory Palaces in LLMs

This guide provides a step-by-step workflow to reproduce the core experiment:
training a spatially-organized transformer variant and a baseline on the bAbI Task 3 dataset,
then evaluating recall accuracy across multiple random seeds.

## Prerequisites

- Python 3.9+
- CUDA-enabled GPU (recommended for training)
- 16GB+ RAM (for dataset loading and model buffering)

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
cd projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning
pip install -r requirements.txt
```

Ensure the following directories exist:
- `code/` (source code)
- `data/` (raw and processed datasets)
- `artifacts/` (results, logs, and schemas)
- `docs/` (documentation)

## 2. Data Download

Download and verify the three permitted datasets (bAbI Task 3, LAMBADA, Story Cloze):

```bash
python code/data/download.py
```

This script:
- Downloads datasets via the `datasets` library.
- Computes SHA-256 checksums.
- Stores checksums in `data/raw/checksums.json`.

## 3. Model Loading & Memory Configuration

The system automatically selects between `gpt2-medium` (4-bit quantized) and `DistilGPT2`
based on available RAM. Memory monitoring is handled by `code/training/memory_monitor.py`.

To verify memory configuration:

```bash
python code/training/memory_monitor.py --check-only
```

## 4. Training & Evaluation

Run the full pipeline (download → model load → train across seeds → evaluate):

```bash
python code/main.py
```

This will:
- Load the selected model.
- Train on bAbI Task 3 across 5 random seeds (-4 to 0).
- Compute exact-match recall for each seed.
- Log results to `artifacts/results/`.

## 5. Output Artifacts

After execution, the following artifacts are generated:

- `artifacts/results/run_summary.json`: Aggregated results (seeds, accuracies, runtime).
- `artifacts/results/recall_accuracy.json`: Per-seed recall metrics.
- `artifacts/results/hyperparams_log.json`: Effective hyperparameters and memory decisions.
- `artifacts/results/runtime_report.json`: Runtime validation against 5-hour limit.

## 6. Statistical Analysis (Post-Training)

Once training completes, run statistical comparisons:

```bash
python code/evaluation/stats.py
```

This generates `artifacts/results/statistical_summary.json` with:
- Paired t-tests / Wilcoxon fallback.
- Multiple-comparison correction (Bonferroni/Holm).
- Effect sizes (Cohen's d) with 95% CIs.

## 7. Structural Metrics (Optional)

To measure spatial organization efficacy:

```bash
python code/evaluation/metrics.py --compute-interference
```

Outputs:
- `artifacts/results/interference_distance.json`
- `artifacts/results/slot_occupancy_epoch_*.csv`
- `artifacts/results/coordinate_variance_epoch_*.csv`

## Troubleshooting

- **OOM Errors**: The system automatically reduces batch size to 4 and caps dataset size if RSS > 6GB. Check `artifacts/results/hyperparams_log.json` for adjustments.
- **Missing Checksums**: Re-run `code/data/download.py` to regenerate `data/raw/checksums.json`.
- **Slow Training**: Ensure CUDA is enabled and `bitsandbytes` is correctly installed for 4-bit quantization.

## Next Steps

- Review `docs/contracts.md` for API guarantees.
- Explore `specs/001-memory-palaces-in-llms-spatial-reasoning/spec.md` for user stories.
- Read `research.md` for structural metric methodologies.