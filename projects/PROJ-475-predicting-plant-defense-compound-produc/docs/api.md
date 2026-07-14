# API Documentation

This document provides detailed API documentation for the PROJ-475 pipeline modules.

## Table of Contents

- [Configuration](#configuration)
- [Data Module](#data-module)
- [Models Module](#models-module)
- [Utils Module](#utils-module)
- [Scripts](#scripts)
- [Tests](#tests)

---

## Configuration

### `code/config.py`

Manages pipeline configuration including paths, seeds, and verified URLs.

**Public API:**

- `ConfigError`: Exception raised for configuration errors.
- `Config`: Typed configuration dataclass.
- `get_config() -> Config`: Loads and returns the current configuration.

**Usage:**
```python
from config import get_config
cfg = get_config()
print(cfg.paths.data_raw)
```

---

## Data Module

### `code/data/ingestion.py`

Handles fetching or generating raw data from genomic, environmental, and compound sources.

**Public API:**

- `fetch_genomic_vcf_from_verified_url()`: Fetches VCF data from verified NCBI SRA URL or generates mock data.
- `fetch_environmental_metadata_from_verified_url()`: Fetches environmental data from verified WorldClim/GBIF URL or generates mock data.
- `fetch_compound_profiles_from_verified_url()`: Fetches compound profiles from verified ChemBank/PhenolExplorer URL or generates mock data.
- `generate_mock_compound_data()`: Generates deterministic mock compound data.
- `ingest_compound_data()`: Orchestrates compound data ingestion.
- `main()`: Entry point for the ingestion pipeline.

**Outputs:**
- `data/raw/genomic_vcf.json`
- `data/raw/env_data.json`
- `data/raw/compound_data.json`

### `code/data/mock_generator.py`

Generates deterministic mock data for CI runs without requiring API keys.

**Public API:**

- `generate_all_mock_data() -> Dict`: Generates all mock datasets (genomic, environmental, compound).

### `code/data/preprocessing.py`

Handles data cleaning, feature engineering, and normalization.

**Public API:**

- `stream_vcf_memory_efficient()`: Streams VCF data efficiently using `cyvcf2`.
- `calculate_missingness_by_environment()`: Calculates missingness per environment.
- `exclude_rows_by_env_missingness()`: Excludes rows with high missingness.
- `flag_missing_env_metadata()`: Flags missing environmental metadata.
- `preprocess_environmental_data()`: Preprocesses environmental data.
- `calculate_heterozygosity()`: Calculates genomic heterozygosity.
- `calculate_nucleotide_diversity()`: Calculates nucleotide diversity.
- `calculate_genomic_diversity_metrics()`: Calculates all genomic diversity metrics.
- `calculate_vif()`: Calculates Variance Inflation Factor for collinearity.
- `detect_model_instability()`: Detects model instability (VIF > 10 or singular matrix).
- `apply_normalization()`: Applies conditional Z-score normalization.
- `aggregate_to_population_level()`: Aggregates data to population level.
- `main()`: Entry point for preprocessing.

**Outputs:**
- `data/processed/features_vif.csv`
- `data/processed/filtered.csv`

### `code/data/validation.py`

Validates data integrity and performs listwise deletion.

**Public API:**

- `load_json_data()`: Loads JSON data files.
- `merge_datasets()`: Merges genomic, environmental, and compound datasets.
- `perform_listwise_deletion()`: Removes rows with missing modalities.
- `validate_data_integrity()`: Validates data against schema.
- `calculate_retention_percentage()`: Calculates data retention after deletion.
- `run_validation_pipeline()`: Orchestrates validation.
- `main()`: Entry point for validation.

---

## Models Module

### `code/models/training.py`

Handles model training and predictor extraction.

**Public API:**

- `load_processed_data()`: Loads processed feature data.
- `determine_cv_strategy()`: Determines CV strategy (5-fold or LOOCV) based on N.
- `check_study_covariate_condition()`: Checks if study covariate should be excluded.
- `train_model()`: Trains LASSO/Ridge model.
- `extract_top_predictors()`: Extracts top 10 predictors by coefficient magnitude.
- `main()`: Entry point for training.

### `code/models/evaluation.py`

Handles model evaluation, permutation tests, and sensitivity analysis.

**Public API:**

- `calculate_p_value()`: Calculates p-value from null distribution.
- `run_permutation_test()`: Runs permutation test (n=1000).
- `save_permutation_results()`: Saves permutation test results.
- `run_sensitivity_analysis()`: Runs sensitivity analysis across alpha values.
- `main()`: Entry point for evaluation.

---

## Utils Module

### `code/utils/io.py`

Input/Output utilities including disk space checks and checksums.

**Public API:**

- `DiskSpaceError`: Exception raised when disk space is insufficient.
- `compute_checksum(path)`: Computes SHA-256 checksum of a file.
- `check_disk_space(estimated_size)`: Checks if sufficient disk space exists.

### `code/utils/logging.py`

Logging configuration and helper functions.

**Public API:**

- `get_logger(name)`: Gets a named logger.
- `configure_root_logger()`: Configures root logger.
- `get_module_logger(name)`: Gets a module-specific logger.

### `code/utils/stats.py`

Statistical utilities for model evaluation and stability analysis.

**Public API:**

- `calculate_jaccard_index(set1, set2)`: Calculates Jaccard index between two sets.
- `calculate_jaccard_stability_matrix()`: Calculates Jaccard stability matrix.
- `calculate_mean_jaccard_stability()`: Calculates mean Jaccard stability.
- `save_jaccard_stability_report()`: Saves stability report.
- `benjamini_hochberg_correction(p_values)`: Applies Benjamini-Hochberg correction.
- `apply_bh_correction_to_predictors()`: Applies BH correction to predictor p-values.

---

## Scripts

### `code/scripts/run_linter.py`

Runs linting and formatting checks.

**Public API:**

- `run_command(cmd)`: Runs a shell command.
- `main()`: Entry point.

### `code/scripts/update_manifest.py`

Updates `data/manifest.yaml` with artifact metadata and checksums.

**Public API:**

- `should_include_file(path)`: Determines if a file should be included in manifest.
- `get_all_artifacts()`: Lists all artifact files.
- `get_artifact_metadata(path)`: Gets metadata for an artifact.
- `update_manifest()`: Updates the manifest file.
- `main()`: Entry point.

### `code/scripts/validate_quickstart.py`

Validates the quickstart guide and pipeline execution.

**Public API:**

- `log(msg)`: Logs a message.
- `check_file_exists(path)`: Checks if a file exists.
- `run_pipeline_step(step)`: Runs a pipeline step.
- `validate_manifest()`: Validates the manifest.
- `validate_state()`: Validates the state file.
- `main()`: Entry point.

---

## Tests

### `code/tests/test_ingestion.py`

Unit tests for data ingestion logic.

### `code/tests/test_validation.py`

Integration tests for the validation pipeline.

### `code/tests/test_preprocessing.py`

Unit tests for feature engineering and preprocessing.

### `code/tests/test_models.py`

Unit tests for model training logic.

### `code/tests/test_stats.py`

Unit tests for statistical utilities (permutation, BH, Jaccard).

### `code/tests/test_update_manifest.py`

Tests for manifest update logic.