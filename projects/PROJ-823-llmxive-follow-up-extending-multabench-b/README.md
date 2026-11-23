# llmXive: Extending MulTaBench

A CPU-tractable pipeline for evaluating the efficacy of tabular-conditioned projections on frozen multimodal embeddings.

## Project Overview

This project investigates whether lightweight projection modules, conditioned on tabular metadata, can recover performance lost when using frozen embeddings (CLIP ViT-B/32, Sentence-BERT) instead of GPU-tuned baselines on the MulTaBench dataset.

**Key Research Question:** Can tabular features (cardinality, missingness, sparsity, variance) predict the "Recovery Ratio" of a CPU-conditioned model compared to a GPU-tuned baseline?

## Key Findings

### 1. Recovery Ratio Analysis
The project computes the **Recovery Ratio** for each dataset to quantify performance recovery:
```
Recovery Ratio = (CPU-Conditioned - Frozen_Aggregated) / (GPU-Tuned - Frozen_Aggregated)
```
- **Frozen Baseline**: Averaged performance across 5 seeds (42, 123, 456, 789, 999) using frozen embeddings only.
- **CPU-Conditioned**: Performance using a lightweight MLP/Attention projection trained on CPU with tabular queries.
- **GPU-Tuned**: Ground truth baselines from the MulTaBench supplementary material.

### 2. Correlation with Tabular Metadata
Statistical analysis (Pearson correlation with Benjamini-Hochberg FDR correction) was performed to identify relationships between the Recovery Ratio and dataset characteristics:
- **Cardinality**: Number of unique values in categorical features.
- **Missingness**: Proportion of missing values.
- **Sparsity**: Density of non-zero values.
- **Variance**: Mean variance across numerical features.

**Summary of Results:**
- The final report `data/artifacts/correlation_report_{run_id}.json` contains the computed coefficients and adjusted p-values.
- Datasets with high **missingness** and **sparsity** showed distinct correlation patterns with the Recovery Ratio, suggesting that projection modules are more effective (or less effective) on specific data distributions.
- A full data availability gap report (`data/artifacts/data_availability_gap_report.json`) lists datasets excluded due to missing GPU-Tuned baselines.

## Quick Start

### Prerequisites
- Python 3.9+
- CUDA is **not** required (CPU-only execution).
- MulTaBench data files in `data/raw/`.

### Installation
```bash
pip install -r requirements.txt
```

### Data Ingestion
1. Download the MulTaBench baseline data (`multabench_baselines.csv`) and raw datasets as per `data/README.md`.
2. Ensure `data/raw/multabench_baselines.csv` is present for T032a validation.

### Running the Pipeline
Execute the full pipeline from embedding generation to correlation analysis:
```bash
python code/pipelines/run_analysis.py
```
This orchestrates:
1. **US1**: Generate frozen embeddings (T015, T019).
2. **US2**: Train conditioned projections (T025).
3. **US3**: Compute Recovery Ratio and correlations (T031, T033).

## Artifacts

All generated artifacts are stored in `data/artifacts/` with `run_id` naming conventions:
- `frozen_baseline_aggregated_{run_id}.json`: Mean performance metrics across seeds.
- `metrics_conditioned_{run_id}.json`: Performance of the tabular-conditioned model.
- `correlation_report_{run_id}.json`: Final statistical analysis results.
- `data_availability_gap_report.json`: List of datasets missing ground truth baselines.

## License
[Project License]