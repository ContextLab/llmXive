# Architecture Documentation

## System Overview

The root architecture prediction pipeline is a modular Python application designed for reproducible scientific research. It follows a clear separation of concerns with distinct stages for data ingestion, preprocessing, modeling, visualization, and reporting.

## Component Architecture

### Core Modules

#### config.py
- **Purpose**: Configuration management and logging setup
- **Responsibilities**:
 - Load configuration from YAML files
 - Setup logging handlers (file and console)
 - Provide configuration access via `get_config()`
 - Initialize logging via `setup_logging()`

#### models.py
- **Purpose**: Data models and record definitions
- **Responsibilities**:
 - Define `RootPhenotypeRecord` dataclass
 - Define `SoilNutrientRecord` dataclass
 - Provide type-safe data structures

#### data_ingestion.py
- **Purpose**: Data loading and merging
- **Responsibilities**:
 - `load_root_phenotype_data()`: Fetch root phenotype data
 - `load_soil_data_isric_streaming()`: Fetch ISRIC soil data with streaming
 - `interpolate_missing_nutrients()`: Spatial interpolation using KNN
 - `filter_data()`: Apply filtering criteria
 - `merge_root_soil_data()`: Merge datasets
 - `main()`: Orchestrate full ingestion pipeline

#### preprocessing.py
- **Purpose**: Data transformation and imputation
- **Responsibilities**:
 - `apply_log_transformation()`: Log-transform root metrics
 - `apply_zscore_normalization()`: Z-score normalize nutrients
 - `apply_knn_imputation()`: KNN imputation for missing values
 - `main()`: Orchestrate preprocessing pipeline

#### modeling.py
- **Purpose**: Model training and evaluation
- **Responsibilities**:
 - `create_species_stratified_split()`: Species-stratified cross-validation
 - `fit_lmm()`: Fit Linear Mixed-Effects Model
 - `fit_random_forest()`: Fit Random Forest baseline
 - `train_models()`: Train both models
 - `evaluate_model()`: Evaluate model performance
 - `calculate_r2_delta()`: Calculate R² difference
 - `evaluate_success_criterion()`: Check SC-002
 - `perform_f_tests_and_pvalues()`: Statistical testing
 - `apply_multiple_comparison_correction()`: Multiple comparison correction
 - `generate_final_metrics_report()`: Generate metrics JSON
 - `main()`: Orchestrate modeling pipeline

#### visualization.py
- **Purpose**: Plot generation
- **Responsibilities**:
 - `load_processed_data()`: Load preprocessed data
 - `load_model_artifact()`: Load trained models
 - `generate_partial_dependence_plots()`: Create PDP plots
 - `generate_scatter_with_fit()`: Create scatter plots
 - `main()`: Orchestrate visualization pipeline

#### reporting.py
- **Purpose**: Report compilation
- **Responsibilities**:
 - `load_model_results()`: Load model artifacts
 - `load_metrics()`: Load metrics JSON
 - `load_exclusion_log()`: Load exclusion log
 - `calculate_merge_success_rate()`: Calculate merge rate
 - `verify_biological_plausibility()`: Check against literature
 - `compile_final_report()`: Generate final report
 - `save_report()`: Save report to disk
 - `generate_report_summary_text()`: Generate summary text
 - `main()`: Orchestrate reporting pipeline

#### sensitivity_analysis.py
- **Purpose**: Sensitivity analysis
- **Responsibilities**:
 - `load_model_coefficients()`: Load model coefficients
 - `extract_lmm_coefficients()`: Extract LMM coefficients
 - `compare_against_literature()`: Compare with literature ranges
 - `calculate_sensitivity_metrics()`: Calculate sensitivity metrics
 - `run_sensitivity_analysis()`: Run full analysis
 - `main()`: Orchestrate sensitivity analysis

## Data Flow

```
Raw Data Sources
 ↓
data_ingestion.py
 ↓ (merged_dataset.csv)
preprocessing.py
 ↓ (processed_dataset.csv)
modeling.py
 ↓ (model artifacts, metrics.json)
visualization.py
 ↓ (plots)
reporting.py
 ↓ (final_report.md, metrics.json)
Final Outputs
```

## Design Patterns

### Pipeline Pattern
Each stage (ingestion, preprocessing, modeling, visualization, reporting) is implemented as an independent pipeline that can be run separately or as part of the full workflow.

### Factory Pattern
Configuration loading uses a factory pattern to create appropriate configuration objects based on the environment.

### Strategy Pattern
Different imputation strategies (KNN, mean fallback) are implemented as interchangeable strategies.

## Error Handling

### Fail-Loudly Principle
All data loaders implement a fail-loudly strategy:
- If real data cannot be fetched, raise an exception
- No synthetic fallbacks or placeholder data
- Clear error messages for debugging

### Logging
Comprehensive logging at all stages:
- Exclusion counts
- Transformation steps
- Model training progress
- Error conditions

## Dependencies

### Core Libraries
- pandas: Data manipulation
- scikit-learn: Machine learning, preprocessing
- statsmodels: Statistical modeling (LMM)
- geopandas: Spatial data handling
- seaborn/matplotlib: Visualization
- pyyaml: Configuration loading

### External Data Sources
- RootReader/PlantPheno: Root phenotype data
- ISRIC SoilGrids: Soil nutrient data

## Testing Strategy

### Contract Tests
Verify schema compliance at each pipeline stage.

### Unit Tests
Test individual functions in isolation.

### Integration Tests
Test full pipeline execution end-to-end.

## Configuration Management

### Environment Variables
- `DATA_PATH`: Root data directory
- `SEED`: Random seed for reproducibility
- `LOG_LEVEL`: Logging verbosity

### Configuration File
YAML-based configuration with template provided.

## Performance Considerations

### Memory Management
- Streaming for large datasets
- Chunked processing where applicable
- Explicit memory cleanup

### Runtime Optimization
- CPU-only execution
- Limited model complexity
- Parallel processing where possible

## Future Extensions

### Planned Enhancements
- Additional data sources
- More sophisticated models
- Real-time data updates
- Web interface for results

### Extensibility Points
- Plugin system for new data sources
- Configurable model parameters
- Custom visualization templates
