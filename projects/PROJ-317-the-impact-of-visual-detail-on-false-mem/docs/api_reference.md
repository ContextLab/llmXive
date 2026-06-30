# API Reference

This document provides a reference for the Python modules and functions in the Visual Detail and False Memory research pipeline.

## Configuration

### `code/config.py`

- **`get_config()`**: Returns the configuration object.
- **`get_project_root()`**: Returns the absolute path to the project root.
- **`get_data_dir()`**: Returns the path to the `data/` directory.
- **`get_stimuli_dir()`**: Returns the path to `data/stimuli/`.
- **`get_stimuli_metadata_dir()`**: Returns the path to `data/stimuli_metadata/`.
- **`get_responses_dir()`**: Returns the path to `data/responses/`.
- **`get_processed_dir()`**: Returns the path to `data/processed/`.
- **`get_ethics_dir()`**: Returns the path to `data/ethics/`.
- **`get_logs_dir()`**: Returns the path to `data/logs/`.
- **`get_figures_dir()`**: Returns the path to `figures/`.
- **`ensure_directories()`**: Creates all required directories if they do not exist.
- **`get_log_level()`**: Returns the configured log level.
- **`get_alpha_level()`**: Returns the alpha level for statistical tests.

## Data Handling

### `code/data/checksum.py`

- **`compute_file_checksum(path)`**: Computes the SHA-256 checksum of a file.
- **`compute_checksums_for_directory(dir_path)`**: Computes checksums for all files in a directory.
- **`save_checksum_manifest(dir_path, output_path)`**: Saves checksums to a JSON manifest.
- **`verify_directory_integrity(dir_path, manifest_path)`**: Verifies directory integrity against a manifest.

### `code/data/image.py`

- **`Image` (Dataclass)**:
 - `id`: Unique identifier.
 - `path`: Path to the image file.
 - `complexity_score`: Calibrated complexity score.
 - `metadata_path`: Path to the YAML metadata file.

### `code/data/loader.py`

- **`generate_mock_visual_genome(output_dir)`**: Generates synthetic images with calibrated complexity.
- **`fetch_real_dataset_image(url)`**: Fetches an image from a real dataset (if configured).
- **`load_image_metadata(path)`**: Loads metadata from a YAML file.

### `code/data/participant.py`

- **`Participant` (Dataclass)**:
 - `id`: Unique participant ID.
 - `condition`: Experimental condition.
 - `timestamp`: Session start time.
- **`Response` (Dataclass)**:
 - `id`: Unique response ID.
 - `question_id`: ID of the question.
 - `value`: Response value (e.g., True/False).
 - `timestamp`: Response time.

## Stimuli Manipulation

### `code/stimuli/manipulator.py`

- **`add_minor_objects(image, object_count)`**: Overlays minor objects to enhance detail.
- **`remove_minor_elements(image, mask)`**: Blurs or masks elements to reduce detail.
- **`calculate_complexity_score(image)`**: Computes a complexity score for an image.
- **`process_single_image(input_path, output_dir)`**: Processes a single image (enhance + reduce).
- **`process_directory(input_dir, output_dir)`**: Processes all images in a directory.

### `code/stimuli/metadata.py`

- **`ManipulationRecord` (Dataclass)**: Records of manipulation parameters.
- **`StimulusMetadata` (Dataclass)**: Complete metadata for a stimulus.
- **`generate_metadata_for_image(image, manipulation_records)`**: Generates metadata.
- **`save_metadata_as_yaml(metadata, output_path)`**: Saves metadata to YAML.

## Participant Simulation

### `code/participants/interface.py`

- **`SessionConfig`**: Configuration for a session.
- **`SimulatedParticipantInterface`**: Class to manage the simulation flow.
- **`generate_recognition_questions(metadata)`**: Generates true and false questions.
- **`run_session(config)`**: Executes a full simulated session.

### `code/participants/session.py`

- **`SessionState`**: Tracks the state of a session.
- **`SessionManager`**: Manages multiple sessions.
- **`create_session(config)`**: Creates a new session.

## Statistical Analysis

### `code/analysis/stats.py`

- **`calculate_anova_power(alpha, power, effect_size)`**: Calculates required sample size.
- **`run_repeated_measures_anova(data)`**: Runs the ANOVA test.
- **`apply_bonferroni_correction(p_values)`**: Applies Bonferroni correction.
- **`check_dataset_fit(data, target_dist)`**: Checks if data fits a target distribution.

### `code/analysis/viz.py`

- **`calculate_false_memory_rates(responses)`**: Computes false memory rates.
- **`plot_false_memory_rates(rates, output_path)`**: Generates a bar chart with CI.
- **`generate_visualization(data, output_dir)`**: Full visualization pipeline.

## Utilities

### `code/utils/logging.py`

- **`get_logger(name)`**: Returns a configured logger.
- **`get_log_file_path()`**: Path to the main log file.
- **`get_manipulation_error_log_path()`**: Path to the manipulation error log.

### `code/cli.py`

- **`cmd_manipulate(args)`**: CLI command for image manipulation.
- **`cmd_simulate_session(args)`**: CLI command for simulation.
- **`cmd_analyze(args)`**: CLI command for analysis.
- **`main()`**: Entry point for the CLI.

## Error Handling

- All modules log errors to `data/logs/`.
- Manipulation errors are specifically logged to `data/logs/manipulation_errors.log`.
- Session errors are logged to `data/logs/session_errors.log`.
- Critical errors raise exceptions with descriptive messages.
