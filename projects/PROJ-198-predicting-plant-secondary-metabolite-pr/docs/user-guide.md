# User Guide

## Getting Started

### Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-198-predicting-plant-secondary-metabolite-pr
 ```

2. **Set up a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment variables**:
 ```bash
 cp.env.example.env
 nano.env # Edit with your API keys
 ```

### Configuration

Create a `config.yaml` file with your desired settings:

```yaml
# Species to analyze
species:
 - Arabidopsis thaliana
 - Oryza sativa
 - Zea mays

# Data sources
data_sources:
 genomes:
 primary: ncbi_refseq
 fallback: phytozome
 metabolites:
 primary: pmdb
 fallback: metabolights

# Modeling parameters
modeling:
 bgc_threshold: 0.5
 pca_components: 10
 cv_folds: 5
 random_state: 42

# Paths
paths:
 raw_data: data/raw
 processed_data: data/processed
 figures: figures
 logs: logs
```

## Running the Pipeline

### Full Pipeline Execution

Execute the complete pipeline from data download to final report:

```bash
python -m code.cli.main --config config.yaml
```

### Individual Stage Execution

#### Step 1: Download Genomes

```bash
python -m code.data.download --stage genomes
```

This fetches FASTA/GFF files from NCBI RefSeq (or Phytozome as fallback).

#### Step 2: Download Metabolites

```bash
python -m code.data.download --stage metabolites
```

This fetches metabolite abundance tables from PMDB (or MetaboLights as fallback).

#### Step 3: Preprocess Data

```bash
python -m code.data.preprocess
```

Runs antiSMASH, harmonizes metabolite data, and maps BGCs to metabolite classes.

#### Step 4: Align Data

```bash
python -m code.data.align
```

Merges genomic and metabolomic data by species, producing `data/processed/aligned_matrix.csv`.

#### Step 5: Train Models

```bash
python -m code.modeling.train
```

Applies PCA, trains PGLS and other models, and performs cross-validation.

#### Step 6: Evaluate Models

```bash
python -m code.modeling.eval
```

Evaluates model performance, runs sensitivity analysis, and generates metrics.

#### Step 7: Generate Report

```bash
python -m code.cli.main --generate-report
```

Compiles all results into a comprehensive Markdown report.

## Understanding Outputs

### Aligned Matrix (`data/processed/aligned_matrix.csv`)

Contains the merged genomic and metabolomic data:
- Species names
- BGC counts by type
- Metabolite abundances (log-transformed)
- Alignment metadata

### Model Metrics (`data/processed/metrics.json`)

JSON file containing:
- R² scores for all models
- Feature importance rankings
- Phylogenetic permutation baseline
- Statistical significance (p-values)

### Sensitivity Results (`data/processed/sensitivity_results.json`)

JSON file containing:
- R² scores at different BGC thresholds
- Maximum variation across thresholds
- Robustness assessment

### Final Report (`data/processed/final_report.md`)

Comprehensive Markdown report including:
- Executive summary
- Methodology
- Model results
- Sensitivity analysis
- Threshold justification
- Conclusions

## Troubleshooting

### Common Issues

#### Network Timeouts

If downloads fail due to network issues:
- Check your internet connection
- Verify API keys in `.env`
- Increase timeout in `config.yaml` if needed

#### Missing Data

If the aligned matrix has many null values:
- Check data source availability
- Verify species names match across sources
- Review logs for specific download failures

#### Model Convergence Issues

If PGLS fails to converge:
- Reduce the number of PCA components
- Check for collinearity in features
- Increase regularization in Elastic Net

#### Memory Errors

If you encounter memory issues:
- Use streaming mode for large datasets
- Reduce the number of species
- Increase PCA dimensionality reduction

### Log Files

Check `logs/pipeline.log` for detailed error messages and execution traces.

## Advanced Usage

### Custom Phylogenetic Tree

To use a custom phylogenetic tree:
1. Place your Newick file in `data/raw/phylogeny/`
2. Update `config.yaml` with the tree filename
3. Run the pipeline as usual

### Custom BGC-Metabolite Mapping

To override the default MIBiG mapping:
1. Create a custom mapping file (CSV with BGC type, metabolite class)
2. Reference it in `config.yaml`
3. The pipeline will use your mapping instead of MIBiG

### Batch Processing

For large-scale analysis:
1. Split species list into batches in `config.yaml`
2. Run the pipeline for each batch
3. Merge results using the `merge_results.py` utility

## Best Practices

1. **Validate Data Sources**: Always verify that your data sources are accessible before running the full pipeline.
2. **Start Small**: Test with 3-5 species before scaling to larger datasets.
3. **Monitor Logs**: Keep an eye on log files during execution.
4. **Version Control**: Track changes to your `config.yaml` and `.env` files.
5. **Document Assumptions**: Note any custom mappings or parameter choices in your final report.

## Support

For issues or questions:
1. Check the logs in `logs/pipeline.log`
2. Review the troubleshooting section above
3. Open an issue on the repository with:
 - Error messages
 - Configuration file (without secrets)
 - Steps to reproduce