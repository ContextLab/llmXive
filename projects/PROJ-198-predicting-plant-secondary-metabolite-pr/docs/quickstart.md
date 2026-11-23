# Quick Start Guide

This guide walks you through running the full pipeline on a small subset of species to verify the system works.

## 1. Environment Setup

Ensure you have Python 3.9+ installed.

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
# venv\Scripts\activate # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

The pipeline uses a configuration file (`config.yaml` in the project root or specified via env var) to define species lists and thresholds.

Example `config.yaml`:
```yaml
species:
 - Arabidopsis thaliana
 - Oryza sativa
 - Solanum lycopersicum
 - Zea mays
 - Populus trichocarpa

thresholds:
 min_genome_size: 100000000
 max_genome_size: 500000000
 bgc_confidence: 0.5
```

## 3. Data Pipeline (US1)

The data pipeline downloads genomes, metabolites, and aligns them.

```bash
python -m code.data.download
python -m code.data.preprocess
python -m code.data.align
```

**Outputs**:
- `data/processed/aligned_matrix.csv`: The final aligned dataset.

## 4. Modeling Pipeline (US2)

Train models and evaluate performance.

```bash
python -m code.modeling.train
python -m code.modeling.eval
```

**Outputs**:
- `data/processed/metrics.json`: Model performance metrics.
- `data/interim/pca_features.csv`: Reduced dimension features.

## 5. Sensitivity Analysis (US3)

Verify model robustness across thresholds.

```bash
python -m code.modeling.eval --sensitivity
```

**Outputs**:
- `data/processed/sensitivity_results.json`: Variation metrics.

## 6. Generate Final Report

Compile all results into a markdown report.

```bash
python -m code.cli.main
```

**Output**:
- `data/processed/final_report.md`

## 7. Validation

To ensure the entire pipeline runs correctly on your machine:

```bash
python -m code.scripts.quickstart_validation
```

This script checks:
- Directory structure
- Linting configuration
- Model schemas
- Data pipeline execution
- Modeling pipeline execution
- Report generation

## Troubleshooting

- **Network Errors**: Ensure you have internet access for data downloads.
- **AntiSMASH Errors**: If running locally, ensure `antismash` is installed and in your PATH.
- **Phylogeny Errors**: Ensure `data/raw/phylogeny/tree.newick` exists and is valid Newick format.
