# Quickstart: Predicting Plant Defense Allocation from Publicly Available Transcriptomic Data

## Prerequisites

* Python 3.11+
* `hisat2`, `featurecounts`, `fastp` installed (via conda or system package).
* Access to NCBI E-utilities (no API key required for low volume).
* Sufficient disk space (for temporary FASTQ/alignment files).

## Installation

```bash
# Create environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Note: rpy2 may require R installation.
```

## Data Setup

1. **Download Reference Genomes**: Ensure HISAT2 indices are built for target species (e.g., *Arabidopsis*, *Solanum*).
2. **Configure Paths**: Edit `src/utils/config.py` to set `DATA_RAW_DIR` and `DATA_PROCESSED_DIR`.

## Running the Pipeline

The pipeline is executed via the CLI orchestrator. It handles metadata fetching, QC, DE, trait integration, and modeling.

```bash
# Run the full pipeline (with synthetic mode for testing if real data is unavailable)
python -m src.cli.run_pipeline --mode real --min-studies [threshold] --min-replicates 2

Research Question: How do methodological variations influence reproducibility across studies?
Method: Systematic pipeline execution with configurable minimum study and replicate thresholds.
References: Smith et al. (2023);

# Run with synthetic data (for development/testing only)
python -m src.cli.run_pipeline --mode synthetic
```

### Expected Outputs

* `data/processed/post_qc_species_list.json`: List of species passing QC.
* `data/processed/final_aggregated_traits.json`: Defense allocation indices.
* `results/model_performance.json`: R², Spearman correlation, p-values.
* `results/phylogenetic_validation.json`: PGLS and null model results.

## Validation

Run contract tests to ensure output schemas are valid:

```bash
pytest tests/contract/test_schemas.py
```

## Troubleshooting

* **Missing Traits**: If >30% of species lack trait data, the pipeline will halt with `human_input_needed`. Check `data/processed/trait_fallback_summary.json`.
* **Power不足**: If the power analysis (FR-016) fails, the pipeline stops. Consider relaxing the R² target or increasing the number of studies (if available).
* **Memory Error**: If alignment exceeds available RAM, reduce the `--max-reads-per-sample` parameter in `config.py`.
