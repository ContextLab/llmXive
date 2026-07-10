# API Reference

## Modules

### `code/simulator`
Handles the user interface and data collection logic.

- **`app.py`**: Streamlit entry point.
 - `run_session_flow()`: Orchestrates the session lifecycle.
 - `calculate_sus_score()`: Computes SUS score from responses.
- **`interfaces/traditional.py`**: Renders the traditional interface.
 - `TraditionalInterface`: Class for rendering standard UI.
- **`interfaces/explainable.py`**: Renders the XAI-enhanced interface.
 - `ExplainableInterface`: Class for rendering UI with XAI overlays.
- **`counterbalance.py`**: Manages task sequence assignment.
 - `LatinSquareCounterbalancer`: Assigns interface order.
- **`metrics_collector.py`**: Collects interaction metrics.
 - `MetricsCollector`: Aggregates time, errors, and engagement data.
- **`raw_data_logger.py`**: Saves immutable session logs.
 - `RawDataLogger`: Writes JSON with checksums.
- **`session_logger.py`**: Logs session metadata and status.
 - `SessionLogger`: Tracks session state and dropouts.

### `code/analysis`
Performs statistical analysis and visualization.

- **`data_cleaner.py`**: Prepares data for analysis.
 - `DataCleaner`: Filters incomplete sessions and imputes SUS data.
- **`stat_utils.py`**: Statistical testing utilities.
 - `StatUtils`: Contains methods for Shapiro-Wilk, ANOVA, and Holm-Bonferroni.
- **`visualizer.py`**: Generates plots.
 - `Visualizer`: Creates box plots and error bars.
- **`report_generator.py`**: Creates text and CSV reports.
 - `ReportGenerator`: Generates summary statistics and flags.

### `code/utils`
Shared utilities.

- **`logger.py`**: Logging infrastructure.
 - `get_logger()`: Retrieves the project logger.
 - `install_global_exception_handler()`: Sets up global error handling.
- **`checksum.py`**: Data integrity tools.
 - `generate_checksum_file()`: Creates checksums for raw data.
 - `verify_checksums_in_directory()`: Validates data integrity.
- **`seed.py`**: Reproducibility utilities.
 - `set_seed()`: Fixes random seeds for reproducibility.

### `code/config`
Configuration management.

- **`settings.py`**: Handles project settings.
 - `get_settings()`: Retrieves current configuration.

### `code/models`
Data structures.

- **`data_models.py`**: Defines core entities.
 - `Participant`: User data model.
 - `Session`: Interaction session model.
 - `Metric`: Statistical metric model.
