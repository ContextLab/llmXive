# Data Flow Documentation

## Overview

This document describes the complete data flow through the Plant Secondary Metabolite Prediction Pipeline, from raw data acquisition to final report generation.

## Data Pipeline Stages

### Stage 1: Data Acquisition

**Input**: Species list from `config.yaml`

**Processes**:
1. `download_genomes()`:
 - Attempts NCBI RefSeq first
 - Falls back to Phytozome if RefSeq fails
 - Applies genome size filter (>500MB skipped)
 - Implements retry logic and timeout handling
 - Outputs: FASTA and GFF files to `data/raw/genomes/`

2. `download_metabolites()`:
 - Attempts PMDB first
 - Falls back to MetaboLights if PMDB fails
 - Implements retry logic and timeout handling
 - Outputs: Abundance tables to `data/raw/metabolites/`

**Output Artifacts**:
- `data/raw/genomes/{species_id}.fasta`
- `data/raw/genomes/{species_id}.gff`
- `data/raw/metabolites/{source}_abundance.csv`

### Stage 2: Preprocessing

**Input**: Raw genome and metabolite files

**Processes**:
1. `run_antiSMASH_wrapper()`:
 - Executes antiSMASH on each genome
 - Parses JSON output
 - Generates binary presence matrix
 - Generates count matrix for BGC diversity
 - Outputs: BGC matrices to `data/interim/bgc_matrix.csv`

2. `harmonize_metabolites()`:
 - Normalizes InChIKey identifiers
 - Applies pseudo-count (+1)
 - Log-transforms abundance values
 - Outputs: Harmonized metabolite matrix to `data/interim/metabolite_matrix.csv`

3. `map_bgc_to_metabolite()`:
 - Uses MIBiG ontology for BGC-to-metabolite mapping
 - Falls back to Pfam HMMs for plant-specific clusters
 - Assigns 'unknown' if no match found
 - Outputs: Mapping table to `data/interim/bgc_metabolite_mapping.csv`

**Output Artifacts**:
- `data/interim/bgc_matrix.csv`
- `data/interim/metabolite_matrix.csv`
- `data/interim/bgc_metabolite_mapping.csv`

### Stage 3: Data Alignment

**Input**: BGC matrix, metabolite matrix, mapping table

**Processes**:
1. `align_data()`:
 - Merges genomic and metabolomic data by species
 - Filters partial rows (missing either BGC or metabolite data)
 - Logs warnings for filtered species
 - Calculates alignment success rate
 - Outputs: Aligned dataframe

2. `save_aligned_matrix()`:
 - Writes final aligned matrix to CSV
 - Includes metadata columns
 - Updates checksums in state file
 - Updates `updated_at` timestamp

**Output Artifacts**:
- `data/processed/aligned_matrix.csv`
- `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml` (updated)

### Stage 4: Feature Reduction

**Input**: Aligned matrix

**Processes**:
1. `apply_pca()`:
 - Determines optimal number of components
 - Applies PCA for dimensionality reduction
 - Prevents overfitting when features > samples
 - Outputs: PCA-reduced features

**Output Artifacts**:
- `data/interim/pca_features.csv`

### Stage 5: Model Training

**Input**: PCA-reduced features, phylogenetic tree

**Processes**:
1. `load_phylogeny()`:
 - Loads Newick tree from `data/raw/phylogeny/`
 - Validates tip labels match species in data

2. `construct_covariance_matrix()`:
 - Uses DendroPy to generate phylogenetic covariance matrix
 - Accounts for branch lengths and topology

3. `create_stratified_split()`:
 - Splits data by phylogenetic clade
 - Ensures no clade appears in both train and test

4. `train_pgls()`:
 - Trains Phylogenetic Generalized Least Squares model
 - Uses phylogenetic covariance matrix
 - Outputs: PGLS coefficients and metrics

5. `train_models_loo()` or `train_models_5fold()`:
 - Trains Random Forest, Elastic Net, Gradient Boosting
 - Uses Leave-One-Out CV if N < 20
 - Uses 5-fold CV if N >= 20
 - Outputs: Model objects and cross-validation metrics

**Output Artifacts**:
- `data/interim/phylogenetic_covariance_matrix.npy`
- `data/interim/model_results.pkl`

### Stage 6: Model Evaluation

**Input**: Trained models, test data

**Processes**:
1. `run_phylogenetic_permutation()`:
 - Shuffles predictors and targets simultaneously
 - Preserves phylogenetic structure
 - Calculates baseline R²

2. `evaluate_models()`:
 - Calculates R² and Pearson correlation
 - Compares against baseline

3. `calculate_significance()`:
 - Performs statistical significance testing
 - Checks p < 0.05 threshold

4. `report_primary_results()`:
 - Extracts PGLS R² and feature importance
 - Formats as primary result

**Output Artifacts**:
- `data/processed/metrics.json`

### Stage 7: Sensitivity Analysis

**Input**: Trained models, metrics

**Processes**:
1. `retrain_with_thresholds()`:
 - Retrains models with BGC thresholds {0.1, 0.3, 0.5, 0.7}
 - Invokes modeling pipeline as sub-routine

2. `run_sensitivity_sweep()`:
 - Iterates over thresholds
 - Records R² and error rates

3. `calculate_variation()`:
 - Calculates max R² difference across thresholds
 - Writes metric to `metrics.json`

4. `handle_sensitivity_failure()`:
 - Logs warning if variation > 0.05
 - Records variation as finding

**Output Artifacts**:
- `data/processed/sensitivity_results.json`
- `data/processed/metrics.json` (updated)

### Stage 8: Report Generation

**Input**: All metrics, sensitivity results, feature importance

**Processes**:
1. `generate_report()`:
 - Compiles model metrics
 - Formats feature importance
 - Includes sensitivity results
 - Adds threshold justification text
 - Outputs: Markdown report

**Output Artifacts**:
- `data/processed/final_report.md`

## Data Schema Evolution

### Raw Data

```
Genomes: FASTA, GFF
Metabolites: CSV with InChIKey, abundance columns
```

### Intermediate Data

```
BGC Matrix: species_id, bgc_type_1, bgc_type_2,...
Metabolite Matrix: species_id, metabolite_1, metabolite_2,...
Mapping: bgc_type, metabolite_class, confidence
```

### Processed Data

```
Aligned Matrix: species_id, bgc_*, metabolite_*, alignment_metadata
PCA Features: species_id, PC1, PC2,..., PCn
```

### Final Outputs

```
Metrics: model_name, r_squared, p_value, feature_importance
Sensitivity: threshold, r_squared, variation
Report: Markdown with all results
```

## Checksum and Provenance Tracking

Every data artifact is tracked with:
- SHA-256 checksum
- Creation timestamp
- Source information
- Processing steps applied

Updates occur in `state/projects/PROJ-198-predicting-plant-secondary-metabolite-pr.yaml`

## Error Propagation

### Fail-Loud Behavior

- Download failures: Raise `DownloadError` immediately
- Schema violations: Raise `ValidationError` immediately
- Alignment failures: Log warnings, continue with partial data
- Model failures: Raise `ModelTrainingError` immediately
- No synthetic fallbacks: Failed real fetch = failed run

### Recovery Strategies

- Retry with exponential backoff for network errors
- Fallback to secondary data source
- Graceful degradation for missing species
- Comprehensive logging for debugging