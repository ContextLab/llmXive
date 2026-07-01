# Adaptation: OpenThoughts-Agent Data Pipeline Probe

## Core Goal
The original paper focuses on **curating a 100K-example dataset** of agentic tasks (SWE, terminal, math, etc.) and fine-tuning a 32B model. This is impossible to reproduce on a CPU or even a single free GPU in a short time.

## Adaptation Strategy
We reproduce the **data curation pipeline** itself, which is the paper's primary contribution ("Data Recipes"). Instead of generating 100K examples and training a model, we:
1. **Ingest a tiny, real sample** of the "Nemotron-RL" dataset mentioned in the paper (via `data/nemotron_gym/run.py`).
2. **Run the converter** on a small subset (e.g., 5 tasks) to verify the pipeline works.
3. **Measure the "data quality"** proxy: token count distribution and task diversity (the paper's ablation metrics).
4. **Output real artifacts**: a small parquet file and a statistics report.

## Approximations
- **Scale**: 5 tasks instead of 100,000.
- **Model**: No fine-tuning. We stop at the "data recipe" stage.
- **Hardware**: Runs entirely on CPU (no GPU required for data parsing/analysis).
- **Data Source**: Uses the public `nvidia/Nemotron-RL-coding-competitive_coding` dataset via HuggingFace `datasets` library (streaming mode to avoid large downloads).

## Dependencies
- `datasets` (for HF loading)
- `pandas`, `numpy` (for analysis)
- `matplotlib` (for plotting)
- `tqdm` (for progress)
- `pyarrow` (for parquet output)
