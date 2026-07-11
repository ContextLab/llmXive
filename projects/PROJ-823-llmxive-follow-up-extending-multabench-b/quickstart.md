# llmXive Follow-up: Extending MulTaBench - Quick Start Guide

This guide provides instructions for setting up and running the llmXive pipeline to extend MulTaBench with CPU-tractable baseline generation, tabular-conditioned projection, and statistical efficacy analysis.

## Prerequisites

- Python 3.11+
- CPU-only environment (GPU not required)
- 16GB+ RAM recommended
- 50GB+ disk space for data and artifacts

## 1. Project Setup

### Clone and Initialize

```bash
git clone <repository-url>
cd llmxive-follow-up-extending-multabench-b
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import transformers; print(f'Transformers version: {transformers.__version__}')"
```

## 2. Data Ingestion

### Download MulTaBench Datasets

The pipeline requires MulTaBench datasets. Follow these steps to ingest data:

```bash
# Navigate to data directory
cd data

# Read the data ingestion instructions
cat README.md
```

**Data Ingestion Steps:**

1. **Download Datasets**: Use the `code/data_loader.py` script to download and verify datasets:
 ```bash
 python code/data_loader.py --ingest-all
 ```

2. **Verify Checksums**: The script automatically verifies SHA-256 checksums against the reference file.

3. **Check Data Availability**: Ensure all required datasets are present in `data/raw/`.

### Data Structure

After ingestion, your data directory should look like:
```
data/
├── raw/
│ ├── dataset_1/
│ ├── dataset_2/
│ └──...
├── processed/
└── artifacts/
```

## 3. Running the Pipeline

The pipeline consists of three main user stories that can be run sequentially.

### User Story 1: CPU-Tractable Baseline Generation

Generate frozen embeddings for all available datasets using CLIP ViT-B/32 and Sentence-BERT on CPU.

```bash
# Run baseline embedding generation for all datasets
python code/pipelines/run_baseline.py --seed 42

# Output: data/processed/embeddings_{run_id}.parquet
```

**Optional: Sensitivity Analysis**

```bash
# Generate embeddings with multiple seeds
python code/pipelines/run_baseline_sensitivity.py --seeds 42 43 44 45 46

# Merge sensitivity outputs
python code/pipelines/merge_sensitivity_outputs.py

# Aggregate results
python code/pipelines/aggregate_sensitivity.py
```

### User Story 2: Tabular-Conditioned Projection

Train a lightweight projection module using normalized tabular features.

```bash
# First, compute metadata statistics for all datasets
python code/analysis/metadata_stats.py

# Output: data/processed/metadata_stats_summary.csv

# Run conditioned projection training
python code/pipelines/run_conditioned.py

# Output: data/artifacts/metrics_conditioned_{run_id}.json
```

### User Story 3: Efficacy Correlation & Statistical Analysis

Analyze the correlation between performance recovery and tabular metadata.

```bash
# Validate GPU-Tuned baselines
python code/pipelines/validate_baselines.py

# Output: data/artifacts/gpu_tuned_baselines.csv
# Output: data/artifacts/data_gap_report.json

# Run full correlation analysis pipeline
python code/pipelines/run_analysis.py

# This will execute:
# 1. Correlation calculation
# 2. Pearson correlation analysis
# 3. T-test analysis
# 4. FDR correction
# 5. Generate final correlation report

# Output: data/artifacts/correlation_report_{run_id}.json
```

## 4. Output Artifacts

After running the full pipeline, you will find the following artifacts:

### Processed Data
- `data/processed/embeddings_{run_id}.parquet`: Frozen embeddings for all datasets
- `data/processed/metadata_stats_summary.csv`: Tabular feature statistics
- `data/processed/embeddings_{run_id}_aggregated.parquet`: Aggregated embeddings from sensitivity analysis

### Analysis Artifacts
- `data/artifacts/frozen_baseline_aggregated_{run_id}.json`: Aggregated baseline metrics
- `data/artifacts/metrics_conditioned_{run_id}.json`: Conditioned model performance metrics
- `data/artifacts/gpu_tuned_baselines.csv`: Validated GPU-Tuned baselines
- `data/artifacts/data_gap_report.json`: Report of missing baseline data
- `data/artifacts/correlation_report_{run_id}.json`: Final correlation analysis results

## 5. Monitoring and Logging

### Memory Monitoring

The pipeline includes built-in memory monitoring. Check logs for peak RAM usage:

```bash
# Logs are written to logs/pipeline.log
tail -f logs/pipeline.log
```

### Key Metrics to Monitor

- Peak memory usage (should stay under 7GB per dataset)
- Batch processing times
- Training convergence (for US2)
- Statistical significance (p-values for US3)

## 6. Troubleshooting

### Common Issues

**Issue: CUDA errors**
- Ensure you're running in CPU-only mode
- Check that `torch.cuda.is_available()` returns False or is disabled

**Issue: Memory errors**
- Reduce batch size in configuration
- Ensure you have sufficient RAM (16GB+ recommended)

**Issue: Missing data**
- Verify dataset ingestion completed successfully
- Check `data/README.md` for specific dataset requirements

**Issue: Checksum verification failed**
- Re-download the affected dataset
- Verify network connectivity during download

### Debug Mode

Enable debug logging for detailed output:

```bash
python code/pipelines/run_baseline.py --debug
```

## 7. Performance Optimization

The pipeline includes adaptive batching and dynamic parallelism to ensure completion within 6 hours.

### Configuration

Adjust batch sizes in `code/config.py` if needed:

```python
# Default settings optimized for CPU
MAX_BATCH_SIZE = 32
MEMORY_LIMIT_GB = 7.0
```

## 8. Next Steps

After completing the pipeline:

1. Review `data/artifacts/correlation_report_{run_id}.json` for key findings
2. Analyze the "Data Availability Gap" report for datasets missing GPU-Tuned baselines
3. Consider running additional sensitivity analysis with different seeds
4. Extend the pipeline with additional datasets or analysis methods

## Support

For issues or questions:
- Check the project logs in `logs/`
- Review the full task list in `tasks.md`
- Consult the design documents in `specs/`

## References

- MulTaBench Paper: [Link to paper]
- Project Specification: `specs/001-llmxive-mulTabench-extension/`
- Data Model: `data-model.md`
- Contracts: `contracts/`