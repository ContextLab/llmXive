# API Reference

## `code/config.py`
- `Config`: Class containing all paths and seed settings.
- `ensure_directories()`: Creates required directories.
- `get_path(name)`: Returns path for a specific directory.
- `set_seed(seed)`: Sets random seed for reproducibility.

## `code/data/ingest.py`
- `download_file_from_osf(url)`: Downloads file from OSF.
- `load_iat_csv(path)`: Loads IAT CSV file.
- `extract_trial_data(df)`: Extracts trial-level data.
- `check_missing_images(trials)`: Checks for missing images.

## `code/data/preprocess.py`
- `run_vad_inference_on_primes()`: Runs VAD inference on prime images.
- `load_human_rated_ambiguity()`: Loads human-rated ambiguity scores.
- `check_confounding()`: Checks for confounding variables.

## `code/models/lmm.py`
- `aggregate_to_stimulus_level(df)`: Aggregates data to stimulus level.
- `fit_lmm_with_retry(df)`: Fits LMM with retry logic.
- `run_lmm_analysis()`: Runs full LMM analysis.

## `code/models/metrics.py`
- `calculate_vif(df)`: Calculates VIF for collinearity.
- `benjamini_hochberg(p_values)`: Applies FDR correction.
- `calculate_effect_sizes_with_bootstrap(df)`: Calculates effect sizes.

## `code/reports/generate_report.py`
- `generate_report_pdf(results)`: Generates PDF report.
- `generate_limitations_section()`: Generates limitations section.

## `code/viz/plots.py`
- `generate_interaction_plot(df)`: Generates interaction plot.
- `generate_coefficient_table(df)`: Generates coefficient table.

## `code/security/pii_scanner.py`
- `scan_text_for_pii(text)`: Scans text for PII.
- `scan_directory_for_pii(dir)`: Scans directory for PII.
