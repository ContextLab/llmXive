# API Reference

## Module: `code/config.py`

### Functions

- `get_path(key: str) -> Path`: Retrieve configured path by key
- `ensure_directories()`: Create all required directories

### Configuration Keys

- `RAW_MICROBIOME`: Path to raw microbiome data
- `RAW_COGNITIVE`: Path to raw cognitive data
- `PROCESSED_ILR`: Path to ILR-transformed data
- `RESULTS_ASSOCIATIONS`: Path to association results

## Module: `code/download.py`

### Functions

- `get_microbiome_data_streaming()`: Stream microbiome data from UK Biobank
- `get_cognitive_data_streaming()`: Stream cognitive data from UK Biobank
- `download_and_save_data()`: Download and save both datasets
- `main()`: Entry point for data download

### Output Files

- `data/raw/microbiome_raw.parquet`
- `data/raw/cognitive_raw.parquet`

## Module: `code/preprocess.py`

### Functions

- `load_raw_microbiome_data()`: Load raw microbiome data
- `load_raw_cognitive_data()`: Load raw cognitive data
- `aggregate_to_genus_level()`: Aggregate OTUs to genus level
- `centered_log_ratio_transform()`: Apply CLR transformation
- `ilr_transform()`: Apply ILR transformation with sequential binary partition
- `run_ilr_pipeline()`: Run complete ILR transformation pipeline
- `run_preprocessing_pipeline()`: Run full preprocessing pipeline
- `main()`: Entry point for preprocessing

### Output Files

- `data/processed/zero_replaced_counts.parquet`
- `data/processed/ilr_coordinates.parquet`
- `data/processed/cohort_with_age_groups.parquet`
- `data/processed/cohort_retention_log.json`

## Module: `code/analysis.py`

### Functions

- `get_confounder_formula()`: Build regression formula with confounders
- `validate_confounders_present()`: Check for required confounders
- `fit_ols_model()`: Fit OLS model with regularization
- `apply_benjamini_hochberg()`: Apply BH correction to p-values
- `run_main_effects_analysis()`: Run main effects analysis
- `run_interaction_analysis()`: Run age-interaction analysis
- `main()`: Entry point for analysis

### Output Files

- `results/associations/main_effects_lasso.parquet`
- `results/associations/main_effects_ridge.parquet`
- `results/associations/main_effects.parquet`
- `results/associations/interaction_effects.parquet`
- `results/sensitivity/over_control_report.json`
- `results/sensitivity/threshold_sweep_report.json`
- `results/sensitivity/interaction_comparison_report.json`
- `results/sensitivity/model_selection_report.json`

## Module: `code/visualize.py`

### Functions

- `generate_manhattan_plot()`: Create Manhattan-style plot
- `generate_threshold_sweep_plot()`: Create threshold sweep visualization
- `main()`: Entry point for visualization

### Output Files

- `results/plots/manhattan_plot.png`

## Module: `code/power_analysis.py`

### Functions

- `calculate_theoretical_power()`: Calculate statistical power
- `calculate_required_n()`: Calculate required sample size
- `generate_synthetic_dataset()`: Generate synthetic dataset for testing
- `run_power_simulation()`: Run power simulation
- `run_power_analysis()`: Run complete power analysis
- `generate_report()`: Generate power analysis report
- `main()`: Entry point for power analysis

### Output Files

- `results/validation/power_analysis_report.json`

## Module: `code/utils/streaming.py`

### Classes

- `StreamingLoader`: Streaming data loader for large datasets

### Functions

- `load_in_batches()`: Load data in memory-efficient batches
- `concatenate_batches()`: Concatenate batch results
- `estimate_memory_usage()`: Estimate memory requirements
- `process_with_streaming()`: Process data with streaming

## Module: `code/utils/hygiene.py`

### Functions

- `compute_file_checksum()`: Compute SHA256 checksum of file
- `compute_directory_checksum()`: Compute checksum of directory
- `mask_pii_value()`: Mask PII in individual values
- `mask_dataframe_pii()`: Mask PII in DataFrame
- `validate_data_integrity()`: Validate data integrity
- `generate_data_manifest()`: Generate data manifest

## Module: `code/models/`

### `cognitive.py`

- `CognitiveScore`: Dataclass for cognitive scores
- `create_cognitive_dataframe()`: Create DataFrame from cognitive data
- `compute_composite_score()`: Compute composite cognitive score

### `microbiome.py`

- `MicrobiomeProfile`: Dataclass for microbiome profiles
- `create_microbiome_dataframe()`: Create DataFrame from microbiome data

### `participant.py`

- `Participant`: Dataclass for participant information
- `create_participant_dataframe()`: Create DataFrame from participant data
