# API Reference

## Overview
This document describes the public API for the PROJ-317 pipeline. All modules are located under `code/`.

## Configuration (`code/config.py`)

### Functions
- `get_project_root()`: Returns the project root path.
- `get_config()`: Returns the global configuration object.
- `get_data_dir()`: Returns the path to the `data/` directory.
- `get_stimuli_dir()`: Returns the path to `data/stimuli/`.
- `get_stimuli_metadata_dir()`: Returns the path to `data/stimuli_metadata/`.
- `get_responses_dir()`: Returns the path to `data/responses/`.
- `get_processed_dir()`: Returns the path to `data/processed/`.
- `get_ethics_dir()`: Returns the path to `data/ethics/`.
- `get_logs_dir()`: Returns the path to `data/logs/`.
- `get_figures_dir()`: Returns the path to `figures/`.
- `get_code_dir()`: Returns the path to `code/`.
- `get_tests_dir()`: Returns the path to `tests/`.
- `get_log_level()`: Returns the configured log level.
- `get_log_file_path()`: Returns the path to the main log file.
- `get_error_log_file_path()`: Returns the path to the error log file.
- `get_manipulation_error_log_path()`: Returns the path to the manipulation error log.
- `get_dataset_source()`: Returns the configured dataset source (mock or real).
- `get_alpha_level()`: Returns the alpha level for statistical tests.
- `get_power_target()`: Returns the target power for sample size calculations.
- `get_effect_size()`: Returns the effect size for power analysis.

## Data Loading (`code/data/loader.py`)

### Functions
- `generate_mock_visual_genome()`: Generates synthetic images with calibrated complexity scores.
- `fetch_real_dataset_image()`: Fetches a real image from a dataset (if configured).
- `load_image_metadata()`: Loads metadata for a given image.
- `process_image_with_error_handling()`: Processes an image with error handling and logging.
- `main()`: CLI entry point for data loading.

## Image Manipulation (`code/stimuli/manipulator.py`)

### Functions
- `add_minor_objects()`: Adds minor objects to an image to enhance detail.
- `remove_minor_elements()`: Removes minor elements from an image to reduce detail.
- `calculate_complexity_score()`: Calculates a complexity score for an image.
- `process_single_image()`: Processes a single image through the manipulation pipeline.
- `process_directory()`: Processes all images in a directory.
- `main()`: CLI entry point for image manipulation.

## Metadata Generation (`code/stimuli/metadata.py`)

### Functions
- `generate_metadata_for_image()`: Generates metadata for a processed image.
- `save_metadata_as_yaml()`: Saves metadata to a YAML file.
- `load_metadata_from_yaml()`: Loads metadata from a YAML file.
- `main()`: CLI entry point for metadata generation.

## Participant Simulation (`code/participants/interface.py`)

### Classes
- `SessionConfig`: Configuration for a simulation session.
- `StimulusPresentation`: Represents a stimulus presentation event.
- `DistractorTaskResult`: Result of a distractor task.
- `RecognitionQuestion`: A recognition question (true or false detail).
- `RecognitionResult`: Result of a recognition question.
- `SimulatedParticipantInterface`: Main interface for simulating participants.

### Functions
- `main()`: CLI entry point for participant simulation.

## Session Management (`code/participants/session.py`)

### Classes
- `SessionState`: Tracks the state of a simulation session.
- `SessionManager`: Manages multiple sessions.

### Functions
- `create_session()`: Creates a new session.
- `main()`: CLI entry point for session management.

## Statistical Analysis (`code/analysis/stats.py`)

### Functions
- `calculate_anova_power()`: Calculates the power of an ANOVA test.
- `save_power_analysis()`: Saves power analysis results to JSON.
- `run_repeated_measures_anova()`: Runs a repeated-measures ANOVA.
- `apply_bonferroni_correction()`: Applies Bonferroni correction for multiple comparisons.
- `save_bonferroni_results()`: Saves Bonferroni correction results.
- `check_dataset_fit()`: Checks how well the dataset fits the target distribution.
- `main()`: CLI entry point for statistical analysis.

## Visualization (`code/analysis/viz.py`)

### Functions
- `load_processed_data()`: Loads processed data for visualization.
- `calculate_false_memory_rates()`: Calculates false memory rates.
- `plot_false_memory_rates()`: Generates a plot of false memory rates with confidence intervals.
- `generate_visualization()`: Generates all visualizations.
- `main()`: CLI entry point for visualization.

## Command-Line Interface (`code/cli.py`)

### Functions
- `setup_logging()`: Configures logging for the CLI.
- `cmd_manipulate()`: CLI command for image manipulation.
- `cmd_metadata()`: CLI command for metadata generation.
- `cmd_simulate_session()`: CLI command for participant simulation.
- `cmd_analyze()`: CLI command for statistical analysis.
- `main()`: Main CLI entry point.

## Utilities

### Logging (`code/utils/logging.py`)
- `get_logger()`: Returns a configured logger.
- `setup_logging()`: Configures logging infrastructure.
- `sanitize_message()`: Sanitizes a message for logging.
- `get_log_file_path()`, `get_error_log_file_path()`, `get_manipulation_error_log_path()`: Return log file paths.

### Security (`code/utils/security.py`)
- `sanitize_string()`: Sanitizes a string for safe logging.
- `sanitize_dict()`: Sanitizes a dictionary for safe logging.
- `sanitize_log_message()`: Sanitizes a log message.
- `SanitizedLogger`: A logger that automatically sanitizes messages.
- `ensure_log_safety()`: Ensures log data is safe.

### Checksums (`code/data/checksum.py`)
- `compute_file_checksum()`: Computes a checksum for a file.
- `compute_checksums_for_directory()`: Computes checksums for all files in a directory.
- `verify_checksum()`: Verifies a file's checksum.
- `save_checksum_manifest()`: Saves a checksum manifest.
- `load_checksum_manifest()`: Loads a checksum manifest.
- `verify_directory_integrity()`: Verifies the integrity of a directory.

### Entities
- `Image` (`code/data/image.py`): Represents an image with metadata.
- `Participant` (`code/data/participant.py`): Represents a participant.
- `Response` (`code/data/participant.py`): Represents a participant's response.
