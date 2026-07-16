# API Reference

## Core Modules

### `code/config.py`
Configuration management and path utilities.

**Public Functions:**
- `get_project_root()`: Returns the project root path
- `get_config()`: Returns the configuration object
- `get_data_dir()`: Returns the data directory path
- `get_stimuli_dir()`: Returns the stimuli directory path
- `get_stimuli_metadata_dir()`: Returns the metadata directory path
- `get_responses_dir()`: Returns the responses directory path
- `get_processed_dir()`: Returns the processed data directory path
- `get_ethics_dir()`: Returns the ethics directory path
- `get_logs_dir()`: Returns the logs directory path
- `get_figures_dir()`: Returns the figures directory path
- `get_code_dir()`: Returns the code directory path
- `get_tests_dir()`: Returns the tests directory path
- `get_log_level()`: Returns the configured log level
- `get_log_file_path()`: Returns the main log file path
- `get_error_log_file_path()`: Returns the error log file path
- `get_manipulation_error_log_path()`: Returns the manipulation error log path
- `get_dataset_source()`: Returns the configured dataset source
- `get_alpha_level()`: Returns the alpha level for statistical tests
- `get_power_target()`: Returns the target power for sample size calculation
- `get_effect_size()`: Returns the effect size for power analysis

### `code/data/image.py`
Image entity definition.

**Classes:**
- `Image`: Dataclass with attributes `id`, `path`, `complexity_score`, `metadata_path`

### `code/data/participant.py`
Participant and response entity definitions.

**Classes:**
- `Participant`: Dataclass with attributes `id`, `condition`, `timestamp`
- `Response`: Dataclass with attributes `id`, `question_id`, `value`, `timestamp`

### `code/data/loader.py`
Data loading and generation utilities.

**Public Functions:**
- `generate_mock_visual_genome()`: Generates synthetic images with calibrated complexity
- `fetch_real_dataset_image()`: Fetches images from a real dataset (if configured)
- `load_image_metadata()`: Loads metadata from YAML files
- `process_image_with_error_handling()`: Processes an image with error handling
- `main()`: CLI entry point for data loading

### `code/stimuli/manipulator.py`
Image manipulation functions.

**Public Functions:**
- `add_minor_objects()`: Adds minor objects to enhance detail
- `remove_minor_elements()`: Removes minor elements to reduce detail
- `calculate_complexity_score()`: Calculates image complexity score
- `process_single_image()`: Processes a single image with manipulation
- `process_directory()`: Processes all images in a directory
- `main()`: CLI entry point for manipulation

### `code/stimuli/metadata.py`
Metadata generation and management.

**Classes:**
- `ManipulationRecord`: Dataclass for manipulation details
- `StimulusMetadata`: Dataclass for complete stimulus metadata

**Public Functions:**
- `generate_metadata_for_image()`: Generates metadata for an image
- `save_metadata_as_yaml()`: Saves metadata to a YAML file
- `load_metadata_from_yaml()`: Loads metadata from a YAML file
- `main()`: CLI entry point for metadata generation

### `code/participants/interface.py`
Participant simulation interface.

**Classes:**
- `SessionConfig`: Configuration for a session
- `StimulusPresentation`: Stimulus presentation details
- `DistractorTaskResult`: Result of a distractor task
- `RecognitionQuestion`: A recognition question
- `RecognitionResult`: Result of a recognition question
- `SimulatedParticipantInterface`: Main interface class

**Public Functions:**
- `main()`: CLI entry point for interface

### `code/participants/session.py`
Session management.

**Classes:**
- `SessionState`: Current state of a session
- `SessionManager`: Manages session lifecycle

**Public Functions:**
- `create_session()`: Creates a new session
- `main()`: CLI entry point for session management

### `code/analysis/stats.py`
Statistical analysis functions.

**Public Functions:**
- `calculate_anova_power()`: Calculates power for ANOVA
- `save_power_analysis()`: Saves power analysis results to JSON
- `run_repeated_measures_anova()`: Runs repeated-measures ANOVA
- `apply_bonferroni_correction()`: Applies Bonferroni correction
- `save_bonferroni_results()`: Saves Bonferroni results to JSON
- `check_dataset_fit()`: Checks dataset distribution fit
- `main()`: CLI entry point for analysis

### `code/analysis/viz.py`
Visualization generation.

**Public Functions:**
- `load_processed_data()`: Loads processed data for visualization
- `calculate_false_memory_rates()`: Calculates false memory rates
- `plot_false_memory_rates()`: Creates a plot of false memory rates
- `generate_visualization()`: Generates a complete visualization
- `main()`: CLI entry point for visualization

### `code/utils/logging.py`
Logging utilities.

**Public Functions:**
- `get_logger()`: Gets a logger instance
- `get_log_file_path()`: Returns the log file path
- `get_error_log_file_path()`: Returns the error log file path
- `get_manipulation_error_log_path()`: Returns the manipulation error log path
- `sanitize_message()`: Sanitizes a message for logging
- `setup_logging()`: Configures logging infrastructure

### `code/utils/security.py`
Security utilities for log sanitization.

**Public Functions:**
- `sanitize_string()`: Sanitizes a string for safe logging
- `sanitize_dict()`: Sanitizes a dictionary for safe logging
- `sanitize_log_message()`: Sanitizes a log message
- `ensure_log_safety()`: Ensures log entry safety
- `main()`: CLI entry point for security utilities

### `code/cli.py`
Command-line interface.

**Public Functions:**
- `setup_logging()`: Sets up logging for CLI
- `cmd_manipulate()`: Command for image manipulation
- `cmd_metadata()`: Command for metadata generation
- `cmd_simulate_session()`: Command for session simulation
- `cmd_analyze()`: Command for statistical analysis
- `main()`: Main CLI entry point

## Error Handling

All modules implement 'skip and log' logic for failures:
- Manipulation failures are logged to `data/logs/manipulation_errors.log`
- Missing metadata causes image skip and error logging
- Network timeouts trigger retry logic and partial session flagging

## Logging Configuration

- Log level: Configurable via `config.py`
- Log files: Stored in `data/logs/`
- Error logs: Separate files for specific error types
- Sanitization: All log messages are sanitized to prevent PII leakage
