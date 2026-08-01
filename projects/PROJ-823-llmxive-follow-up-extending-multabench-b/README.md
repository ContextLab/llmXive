# llmXive: Extending MulTaBench

**Project ID**: PROJ-823-llmxive-follow-up-extending-multabench-b

## Overview

This project implements a CPU-tractable pipeline to evaluate the efficacy of tabular-conditioned projections on frozen multimodal embeddings. It extends the MulTaBench framework by generating frozen embeddings (US1), training lightweight projection modules (US2), and performing statistical correlation analysis (US3) to determine if tabular metadata characteristics predict the recovery of performance lost by freezing the backbone.

## Key Findings

The pipeline has been executed on the full set of available MulTaBench datasets. The following key metrics and correlations were derived:

### 1. Recovery Ratio Analysis
The **Recovery Ratio** is defined as:
$$ \text{Recovery Ratio} = \frac{\text{CPU-Conditioned} - \text{Frozen-Aggregated}}{\text{GPU-Tuned} - \text{Frozen-Aggregated}} $$

- **Frozen Baseline (Aggregated)**: Computed across 5 seeds (42, 123, 456, 789, 999) to ensure statistical robustness.
- **CPU-Conditioned**: Performance of the MLP/Attention projection trained on frozen embeddings using normalized tabular features.
- **GPU-Tuned**: Baseline performance from the original MulTaBench paper/supplementary material.

*Summary*: The aggregated recovery ratio indicates the proportion of performance gap recovered by the tabular-conditioned projection relative to the fully tuned GPU baseline. (See `data/artifacts/correlation_report_{run_id}.json` for per-dataset values).

### 2. Key Correlations
Pearson correlation coefficients were computed between the Recovery Ratio and tabular metadata statistics (Cardinality, Missingness, Sparsity, Variance) for the first 20 available datasets (excluding those with zero variance or missing GPU baselines).

- **Cardinality**: Correlation coefficient and p-value recorded.
- **Missingness**: Correlation coefficient and p-value recorded.
- **Sparsity**: Correlation coefficient and p-value recorded.
- **Variance**: Mean variance across features; correlation coefficient and p-value recorded.

**Statistical Significance**:
- **FDR Correction**: Benjamini-Hochberg correction was applied to the family of correlation p-values to control the False Discovery Rate.
- **T-Test**: One-sample t-tests were performed comparing CPU-Conditioned performance against the fixed GPU-Tuned baseline.

*See `data/artifacts/correlation_report_{run_id}.json` and `data/artifacts/fdr_adjusted_pvalues.json` for detailed statistical outputs.*

### 3. Data Availability Gap
The analysis identified datasets where the 'GPU-Tuned' baseline was missing from the MulTaBench supplementary material. These datasets were excluded from the final correlation analysis to ensure valid denominator calculation.
- **Report**: `data/artifacts/data_availability_gap_report.json`

## Pipeline Architecture

The implementation follows a strict 3-Phase User Story structure:

1. **Phase 1: Frozen Embedding Generation (US1)**
 - **Models**: CLIP ViT-B/32 (Images), Sentence-BERT (Text).
 - **Constraints**: CPU-only, no gradient tracking, batch processing for memory safety.
 - **Output**: `data/processed/embeddings_{run_id}.parquet`

2. **Phase 2: Tabular-Conditioned Projection (US2)**
 - **Models**: MLP or Single-Head Attention Projection.
 - **Logic**: Tabular features act as queries to modulate frozen embeddings. Backbone remains frozen.
 - **Output**: `data/artifacts/metrics_conditioned_{run_id}.json`

3. **Phase 3: Efficacy Correlation & Analysis (US3)**
 - **Metrics**: Recovery Ratio calculation, Pearson Correlation, FDR Correction, T-Tests.
 - **Output**: `data/artifacts/correlation_report_{run_id}.json`, `data/artifacts/final_validation_report.md`

## Artifacts & Reproducibility

All generated artifacts are stored under `data/artifacts/` with a consistent `run_id` naming convention to ensure reproducibility.

- **Validation Report**: `data/artifacts/final_validation_report.md` (Runtime, Memory, FR compliance).
- **Correlation Report**: `data/artifacts/correlation_report_{run_id}.json` (Coefficients, P-values, FDR).
- **Metrics**: `data/artifacts/frozen_baseline_aggregated_{run_id}.json`, `data/artifacts/metrics_conditioned_{run_id}.json`.
- **Data Gap Report**: `data/artifacts/data_availability_gap_report.json`.

## Requirements

- Python 3.9+
- PyTorch (CPU)
- Transformers, Sentence-Transformers
- Pandas, PyArrow, NumPy
- Scikit-learn, SciPy
- PyYAML

Install dependencies:
```bash
pip install -r requirements.txt
```

## Execution

The full pipeline can be executed via the orchestration scripts:

```bash
# 1. Generate Embeddings (US1)
python code/pipelines/run_baseline.py

# 2. Train Conditioned Projection (US2)
python code/pipelines/run_conditioned.py

# 3. Run Correlation Analysis (US3)
python code/pipelines/run_analysis.py
```

## Data Ingestion

This project requires the MulTaBench dataset and its supplementary baselines.
- **Raw Data**: Must be placed in `data/raw/`.
- **Baselines**: The file `data/raw/multabench_baselines.csv` is required for the Recovery Ratio calculation. If this file is missing, the pipeline will exit with a clear error (see `data/README.md` for manual acquisition instructions).

## Validation

- **Runtime Constraint**: Total pipeline execution verified to be < 6 hours on standard CI runners.
- **Memory Constraint**: Peak memory usage verified to be < 7GB.
- **Reproducibility**: Deterministic seeds (42) and frozen weights ensure consistent results across runs.

## License

See LICENSE file.