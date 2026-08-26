# API Reference

## Core Modules

### `code/config.py`
Configuration management and path utilities.

**Public Functions:**
- `get_path(key: str) -> Path`: Retrieve configured path by key
- `ensure_directories()`: Create all required directories

**Configuration Keys:**
- `raw_microbiome`: Path to raw microbiome data
- `raw_cognitive`: Path to raw cognitive data
- `processed_ilr`: Path to ILR-transformed data
- `associations`: Path to association results
- `plots`: Path to generated plots
- `AGE_GROUP_CUTOFF`: Age threshold for grouping (default: 65)

### `code/download.py`
Data download utilities for UK Biobank.

**Public Functions:**
- `get_microbiome_data_streaming()`: Fetch microbiome data in batches
- `get_cognitive_data_streaming()`: Fetch cognitive data in batches
- `download_and_save_data()`: Orchestrate download and save process
- `main()`: Entry point for download script

### `code/preprocess.py`
Data preprocessing pipeline.

**Public Functions:**
- `load_raw_microbiome_data()`: Load raw microbiome parquet
- `load_raw_cognitive_data()`: Load raw cognitive parquet
- `aggregate_to_genus_level()`: Aggregate OTUs to genus level
- `centered_log_ratio_transform()`: Apply CLR transformation
- `ilr_transform()`: Apply ILR transformation
- `run_ilr_pipeline()`: Run full ILR pipeline
- `run_preprocessing_pipeline()`: Run complete preprocessing
- `main()`: Entry point for preprocessing script

### `code/analysis.py`
Statistical analysis engine.

**Public Functions:**
- `get_confounder_formula()`: Build confounder formula string
- `validate_confounders_present()`: Check for required confounders
- `fit_ols_model()`: Fit regularized linear model
- `apply_benjamini_hochberg()`: Apply BH correction
- `run_main_effects_analysis()`: Run main effects analysis
- `run_interaction_analysis()`: Run interaction analysis
- `main()`: Entry point for analysis script

### `code/visualize.py`
Visualization generation.

**Public Functions:**
- `generate_manhattan_plot()`: Create Manhattan-style plot
- `generate_threshold_sweep_report()`: Create threshold sweep analysis
- `main()`: Entry point for visualization script

### `code/power_analysis.py`
Power calculation utilities.

**Public Functions:**
- `calculate_theoretical_power()`: Calculate power for given parameters
- `calculate_required_n()`: Calculate required sample size
- `generate_synthetic_dataset()`: Generate synthetic data for validation
- `run_power_simulation()`: Run power simulation
- `run_power_analysis()`: Run full power analysis
- `generate_report()`: Generate power report
- `main()`: Entry point for power analysis script

## Model Classes

### `code/models/participant.py`
- `Participant`: Dataclass for participant information
- `create_participant_dataframe()`: Create DataFrame from participants
- `compute_composite_score()`: Compute composite cognitive score

### `code/models/microbiome.py`
- `MicrobiomeProfile`: Dataclass for microbiome profile
- `create_microbiome_dataframe()`: Create DataFrame from profiles

### `code/models/cognitive.py`
- `CognitiveScore`: Dataclass for cognitive scores
- `create_cognitive_dataframe()`: Create DataFrame from scores

## Utility Modules

### `code/utils/streaming.py`
- `StreamingLoader`: Class for streaming data loading
- `load_in_batches()`: Load data in batches
- `concatenate_batches()`: Concatenate batch DataFrames
- `estimate_memory_usage()`: Estimate memory requirements
- `get_file_size()`: Get file size in bytes
- `process_with_streaming()`: Process data with streaming

### `code/utils/hygiene.py`
- `compute_file_checksum()`: Compute SHA256 checksum
- `compute_directory_checksum()`: Compute directory checksum
- `mask_pii_value()`: Mask PII values
- `mask_dataframe_pii()`: Mask PII in DataFrame
- `validate_data_integrity()`: Validate data integrity
- `generate_data_manifest()`: Generate data manifest

### `code/utils/logging.py`
- `get_logger()`: Get project logger
- `log_exception()`: Log exception with context
- `LlmXiveError`: Base exception class
- `DataLoadError`: Data loading exception
- `PreprocessingError`: Preprocessing exception
- `AnalysisError`: Analysis exception
- `ConfigError`: Configuration exception
- `ValidationError`: Validation exception

## Validation Modules

### `code/validation/instrument_validator.py`
- `validate_citation()`: Validate instrument citation
- `run_validation_agent()`: Run validation agent
- `generate_report_md()`: Generate validation report
- `main()`: Entry point for validation script

## Zero Replacement

### `code/zero_replace.py`
- `estimate_zero_replacement_params()`: Estimate zero replacement parameters
- `bayesian_multiplicative_replace()`: Apply Bayesian-multiplicative replacement
- `process_batch()`: Process batch with zero replacement
- `run_zero_replacement_pipeline()`: Run zero replacement pipeline
- `main()`: Entry point for zero replacement script

## Usage Examples

### Running the Full Pipeline
```python
from config import ensure_directories
from download import main as download_main
from preprocess import main as preprocess_main
from analysis import main as analysis_main
from visualize import main as visualize_main

ensure_directories()
download_main()
preprocess_main()
analysis_main()
visualize_main()
```

### Custom Analysis
```python
from analysis import run_main_effects_analysis, apply_benjamini_hochberg
from preprocess import run_ilr_pipeline

# Run preprocessing
ilr_data = run_ilr_pipeline()

# Run analysis
results = run_main_effects_analysis(ilr_data)

# Apply correction
corrected = apply_benjamini_hochberg(results)
```
