# API Reference: Python Modules

This document describes the public API surface of the Python modules used in the pipeline.

## `code/00_setup_r_env.py`
- `main()`: Entry point for initializing R environment.

## `code/03_generate_renv_lock.py`
- `get_project_root()`: Returns the project root path.
- `check_r_installed()`: Verifies R installation.
- `get_r_version()`: Returns R version string.
- `initialize_renv()`: Initializes `renv` if not present.
- `verify_renv_lock()`: Checks for `renv.lock` existence.
- `main()`: Entry point.

## `code/04_render_report.py`
- `get_project_root()`: Returns project root.
- `ensure_directories()`: Creates output directories.
- `run_rmarkdown_render()`: Executes RMarkdown rendering.
- `main()`: Entry point.

## `code/05_validate_report.py`
- `get_project_root()`: Returns project root.
- `read_report_content()`: Reads HTML content.
- `validate_report()`: Checks for required sections.
- `main()`: Entry point.

## `code/06_validate_quickstart.py`
- `check_file_exists(path)`: Validates file existence.
- `check_dir_exists(path)`: Validates directory existence.
- `check_r_installed()`: Checks R.
- `check_renv_initialized()`: Checks `renv`.
- `check_logging_infrastructure()`: Validates log setup.
- `validate_quickstart_content()`: Checks content of quickstart docs.
- `main()`: Entry point.

## `code/07_verify_ci_compatibility.py`
- `check_cpu_cores()`: Returns CPU core count.
- `check_ram_gb()`: Returns RAM in GB.
- `check_gpu()`: Checks for GPU presence.
- `check_r_installed()`: Checks R.
- `check_renv_initialized()`: Checks `renv`.
- `main()`: Entry point.

## `code/utils_logging.py`
- `get_project_root()`: Returns project root.
- `ensure_log_directory()`: Creates log dir.
- `setup_logger()`: Configures logger.
- `get_pipeline_logger()`: Returns singleton logger.
- `log_info(msg)`: Logs info.
- `log_warning(msg)`: Logs warning.
- `log_error(msg)`: Logs error.
- `log_abort(msg)`: Logs error and raises exception.
- `log_exclusion(msg)`: Logs exclusion details.
- `log_exclusion_count(count)`: Logs exclusion summary.
- `check_log_file_exists(path)`: Checks log file.
- `read_log_file(path)`: Reads log content.

## `code/setup_data_structure.py`
- `create_data_directories()`: Creates data folders.
- `create_gitignore_rules()`: Generates `.gitignore`.
- `create_gitkeep_files()`: Creates `.gitkeep`.
- `main()`: Entry point.

## `code/setup_lintr_config.py`
- `create_lintr_config()`: Generates `.lintr` config.
- `main()`: Entry point.

## `code/setup_project_structure.py`
- `create_directories()`: Creates project folders.
- `create_gitignore()`: Creates root `.gitignore`.
- `create_readme()`: Creates root `README.md`.
- `create_requirements_txt()`: Creates `requirements.txt`.
- `create_r_profile()`: Creates `.Rprofile`.
- `main()`: Entry point.

## `code/analysis.py`
- `apply_bonferroni_correction(p_values, n_tests)`: Adjusts p-values.
- `calculate_significance_mask(p_values, alpha)`: Returns boolean mask.
- `run_ancova_simulation(...)`: Runs ANCOVA (for testing/reference).

## `code/utils_renv.py`
- `check_r_version()`: Verifies R version >= 4.3.
- `verify_packages(packages)`: Checks installed packages.
- `initialize_renv()`: Initializes `renv`.
- `main()`: Entry point.

## `code/utils_logging_test.py`
- `temp_project_dir()`: Creates temp dir for tests.
- `test_ensure_log_directory_creates_dir()`: Test case.
- `test_setup_logger_creates_handlers()`: Test case.
- `test_log_info_writes_to_console()`: Test case.
- `test_log_warning_writes_to_file()`: Test case.
- `test_log_abort_raises_exception()`: Test case.
- `test_log_exclusion_formats_message()`: Test case.
- `test_log_exclusion_count_formats_summary()`: Test case.
- `test_get_pipeline_logger_returns_same_instance()`: Test case.
- `test_read_log_file_raises_when_missing()`: Test case.
- `test_check_log_file_exists_returns_false_when_missing()`: Test case.
- `test_log_levels_separate_messages()`: Test case.
