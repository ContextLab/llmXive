# API Reference: PROJ-037

This document describes the public API for all modules in `code/`.

## `code/ingestion.py`
**Purpose**: Download, merge, and clean AGP/OpenHumans data.

**Public Functions**:
- `download_file(url: str, dest: Path)`: Download a file from a URL.
- `parse_biom_table(biom_path: Path)`: Parse AGP 16S data.
- `ingest_agp_metadata(metadata_path: Path)`: Load AGP metadata.
- `ingest_sleep_metadata(metadata_path: Path)`: Load OpenHumans sleep data.
- `verify_integrity(cohort: pd.DataFrame)`: Check data integrity.
- `filter_missing_data(cohort: pd.DataFrame)`: Remove rows with missing sleep/microbiome data.
- `cap_outliers(cohort: pd.DataFrame, col: str, lower: float, upper: float)`: Cap outliers at percentiles.
- `impute_covariates(cohort: pd.DataFrame)`: Impute missing covariates (median/mode).
- `generate_summary_report(cohort: pd.DataFrame)`: Print summary stats.
- `save_cohort(cohort: pd.DataFrame, path: Path)`: Save to CSV.
- `main()`: Entry point.

## `code/diversity.py`
**Purpose**: Calculate alpha/beta diversity.

**Public Functions**:
- `load_biom_table(biom_path: Path)`: Load BIOM table.
- `load_metadata(metadata_path: Path)`: Load metadata.
- `calculate_alpha_diversity(biom_table)`: Compute Shannon/Simpson.
- `calculate_beta_diversity(biom_table)`: Compute Bray-Curtis.
- `run_diversity_analysis(biom_path: Path, metadata_path: Path)`: Full pipeline.
- `main()`: Entry point.

## `code/analysis.py`
**Purpose**: Perform correlational and regression analyses.

**Public Functions**:
- `load_processed_cohort(path: Path)`: Load merged cohort.
- `load_biom_table(biom_path: Path)`: Load BIOM table.
- `load_metadata(metadata_path: Path)`: Load metadata.
- `calculate_alpha_diversity(cohort: pd.DataFrame)`: Add diversity metrics.
- `calculate_beta_diversity(cohort: pd.DataFrame)`: Add beta diversity.
- `calculate_correlations(cohort: pd.DataFrame)`: Spearman/Pearson tests.
- `apply_fdr_correction(p_values: List[float])`: Benjamini-Hochberg.
- `run_all_correlations(cohort: pd.DataFrame)`: Full correlation suite.
- `run_dbRDA(cohort: pd.DataFrame)`: Distance-based RDA.
- `run_permanova(cohort: pd.DataFrame)`: PERMANOVA for categorical variables.
- `run_glm_adjusted(cohort: pd.DataFrame)`: GLM with confounders.
- `save_results(results: pd.DataFrame, path: Path)`: Save to CSV.
- `main()`: Entry point.

## `code/viz.py`
**Purpose**: Generate visualizations.

**Public Functions**:
- `load_correlation_results(path: Path)`: Load results.
- `load_beta_diversity_data(cohort: pd.DataFrame)`: Extract beta diversity.
- `generate_pcoa_ordination(beta_div: pd.DataFrame, sleep_quality: pd.Series, path: Path)`: PCoA plot.
- `create_placeholder_pcoa()`: Fallback if data missing (not used in production).
- `main()`: Entry point.

## `code/validation.py`
**Purpose**: Bootstrap and sensitivity analysis.

**Public Functions**:
- `load_correlation_results(path: Path)`: Load results.
- `bootstrap_resample(cohort: pd.DataFrame, n_iterations: int)`: Resample data.
- `get_top_correlations(results: pd.DataFrame, n: int)`: Get top N correlations.
- `run_bootstrap_analysis(cohort: pd.DataFrame, n_iterations: int)`: Full bootstrap.
- `save_validation_status(status: dict, path: Path)`: Save status.
- `run_sensitivity_analysis(results: pd.DataFrame, thresholds: List[float])`: Sensitivity sweep.
- `generate_sensitivity_report(sensitivity: pd.DataFrame, path: Path)`: Save report.
- `main()`: Entry point.

## `code/report.py`
**Purpose**: Generate associational report.

**Public Functions**:
- `load_correlation_results(path: Path)`: Load results.
- `load_validation_status(path: Path)`: Load validation status.
- `load_sensitivity_report(path: Path)`: Load sensitivity report.
- `load_bootstrap_results(path: Path)`: Load bootstrap results.
- `generate_report_section_bootstrap_stability(bootstrap: pd.DataFrame)`: Bootstrap section.
- `generate_report_section_sensitivity(sensitivity: pd.DataFrame)`: Sensitivity section.
- `generate_full_report(results: pd.DataFrame, bootstrap: pd.DataFrame, sensitivity: pd.DataFrame)`: Full report.
- `main()`: Entry point.

## `code/config.py`
**Purpose**: Configuration management.

**Public Functions**:
- `Config`: Dataclass for project config.
- `get_config()`: Load config.
- `reset_config()`: Reset to defaults.

## `code/schemas.py`
**Purpose**: Data validation schemas.

**Public Functions**:
- `get_schema()`: Return schema dict.
- `get_required_columns()`: List required columns.
- `get_optional_columns()`: List optional columns.

## `code/utils/`
**Purpose**: Utility functions.

- `config.py`: Config helpers.
- `logging_utils.py`: Logging setup.
- `seeding.py`: Random seed management.
- `validators.py`: Data validation logic.

## Notes
- All functions assume real data inputs.
- No synthetic data is generated.
- All outputs are framed as "associational".
