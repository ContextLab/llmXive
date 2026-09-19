# API Documentation

## Overview
This document provides detailed API documentation for the PROJ-475 pipeline modules.

## Configuration Module (`code/config.py`)

### Classes
- `ConfigError`: Exception raised for configuration errors.
- `Config`: Dataclass holding project configuration.

### Functions
- `load_config(path: str) -> Config`: Load configuration from a YAML file.
- `get_config() -> Config`: Get the current configuration instance.
- `reset_config()`: Reset the configuration to default.
- `main()`: Entry point for configuration testing.

## Data Ingestion Module (`code/data/ingestion.py`)

### Functions
- `ensure_directories()`: Create required data directories.
- `load_manifest(path: str) -> dict`: Load the data manifest.
- `save_manifest(manifest: dict, path: str)`: Save the data manifest.
- `update_manifest(manifest: dict, artifact_path: str, source: str)`: Update manifest with new artifact.
- `fetch_url_content(url: str) -> bytes`: Download content from a URL.
- `validate_compound_json_schema(data: dict) -> bool`: Validate compound JSON against schema.
- `fetch_compound_data(url: str) -> dict`: Fetch and validate compound data.
- `run_all_ingestion()`: Execute full ingestion pipeline.
- `main()`: Entry point for ingestion scripts.

## Mock Data Generator (`code/data/mock_generator.py`)

### Functions
- `generate_deterministic_population_ids(n: int) -> list`: Generate deterministic population IDs.
- `generate_deterministic_env_ids(n: int) -> list`: Generate deterministic environmental IDs.
- `generate_deterministic_compound_ids(n: int) -> list`: Generate deterministic compound IDs.
- `generate_mock_genomic_data(path: str)`: Generate mock VCF genomic data.
- `generate_mock_environmental_data(path: str)`: Generate mock environmental CSV data.
- `generate_mock_compound_data(path: str)`: Generate mock compound JSON data.
- `generate_all_mock_data()`: Generate all mock data files.
- `main()`: Entry point for mock data generation.

## Data Validation Module (`code/data/validation.py`)

### Functions
- `load_json_data(path: str) -> dict`: Load JSON data.
- `load_csv_data(path: str) -> pd.DataFrame`: Load CSV data.
- `load_vcf_as_dataframe(path: str) -> pd.DataFrame`: Parse VCF into DataFrame.
- `merge_datasets(genomic_df, env_df, compound_df) -> pd.DataFrame`: Merge datasets on population_id.
- `perform_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame`: Remove rows with missing values.
- `merge_and_validate()`: Execute merge and validation pipeline.
- `run_validation_pipeline()`: Full validation pipeline execution.
- `main()`: Entry point for validation scripts.

## Data Preprocessing Module (`code/data/preprocessing.py`)

### Functions
- `load_processed_data(path: str) -> pd.DataFrame`: Load processed data.
- `handle_missing_genotypes(df: pd.DataFrame) -> pd.DataFrame`: Handle missing genotype data.
- `handle_missing_env_metadata(df: pd.DataFrame) -> pd.DataFrame`: Handle missing environmental metadata.
- `aggregate_to_population_level(df: pd.DataFrame) -> pd.DataFrame`: Aggregate data to population level.
- `calculate_vif(df: pd.DataFrame) -> pd.DataFrame`: Calculate Variance Inflation Factor.
- `calculate_diversity_metrics(df: pd.DataFrame) -> pd.DataFrame`: Calculate genomic diversity metrics.
- `run_preprocessing_pipeline()`: Execute full preprocessing pipeline.
- `main()`: Entry point for preprocessing scripts.

## Model Training Module (`code/models/training.py`)

### Functions
- `determine_cv_strategy(df: pd.DataFrame) -> dict`: Determine cross-validation strategy based on N.
- `save_cv_strategy(strategy: dict, path: str)`: Save CV strategy to JSON.
- `check_study_covariate_condition(df: pd.DataFrame) -> dict`: Check if source_study covariate should be excluded.
- `train_model(df: pd.DataFrame) -> sklearn.model`: Train LASSO/Ridge model.
- `extract_top_predictors(model, df: pd.DataFrame, n: int) -> list`: Extract top N predictors.
- `main()`: Entry point for training scripts.

## Model Evaluation Module (`code/models/evaluation.py`)

### Functions
- `run_permutation_test(model, df: pd.DataFrame, n: int = 1000) -> dict`: Execute permutation test.
- `calculate_p_value(observed_r2: float, null_distribution: list) -> float`: Calculate p-value.
- `run_sensitivity_analysis(model, df: pd.DataFrame, alphas: list) -> dict`: Perform sensitivity analysis.
- `main()`: Entry point for evaluation scripts.

## Utility Modules

### IO Utilities (`code/utils/io.py`)
- `compute_checksum(path: str) -> str`: Compute SHA256 checksum of a file.
- `check_disk_space(estimated_size: int)`: Check available disk space, raise `DiskSpaceError` if insufficient.

### Logging Utilities (`code/utils/logging.py`)
- `get_logger(name: str) -> logging.Logger`: Get a logger instance.
- `configure_root_logger()`: Configure root logger.
- `get_module_logger()`: Get module-specific logger.

### Statistics Utilities (`code/utils/stats.py`)
- `calculate_jaccard_index(set1: set, set2: set) -> float`: Calculate Jaccard index between two sets.
- `calculate_jaccard_index_from_lists(list1: list, list2: list) -> float`: Calculate Jaccard index from lists.
- `calculate_jaccard_stability_matrix(feature_sets: list) -> pd.DataFrame`: Calculate Jaccard stability matrix.
- `calculate_mean_jaccard_stability(matrix: pd.DataFrame) -> float`: Calculate mean Jaccard stability.
- `compute_feature_stability_across_sweep(sweep_results: dict) -> dict`: Compute feature stability across alpha sweep.
- `save_jaccard_stability_report(report: dict, path: str)`: Save stability report.
- `benjamini_hochberg_correction(p_values: list) -> list`: Apply Benjamini-Hochberg correction.
- `main()`: Entry point for stats scripts.

## Main Pipeline (`code/main.py`)

### Functions
- `update_state_file()`: Update the state file with current timestamp and artifact hashes.
- `run_pipeline()`: Execute the full pipeline from ingestion to evaluation.
- `main()`: Main entry point for the application.

## Scripts

### `code/scripts/generate_mock_data.py`
- `main()`: Generate all mock data files for testing.

### `code/scripts/run_validation.py`
- `main()`: Run the data validation pipeline.

### `code/scripts/run_preprocessing.py`
- `main()`: Run the preprocessing pipeline.

### `code/scripts/update_manifest.py`
- `main()`: Update the data manifest with all artifacts.

### `code/scripts/validate_quickstart.py`
- `main()`: Validate quickstart requirements and pipeline outputs.