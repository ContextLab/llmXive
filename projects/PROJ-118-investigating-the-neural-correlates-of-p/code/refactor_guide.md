# Code Cleanup and Refactoring Guide

This document outlines the refactoring improvements made to the `code/` directory
to enhance maintainability, reduce duplication, and enforce consistent patterns.

## 1. Consolidated Utilities (`cleanup_utils.py`)

The following common patterns have been extracted into `cleanup_utils.py`:

### Logging
- **`setup_logger`**: Standardized logger configuration with file and console handlers.
 Ensures consistent timestamp formats and log levels across all modules.
- **`log_execution_time`**: Decorator to automatically log function execution duration.

### Data Validation
- **`validate_array_shape`**: Centralized logic to check numpy array dimensions and shapes.
 Prevents shape mismatches in MNE data structures.
- **`safe_divide`**: Handles division by zero gracefully, returning a configurable default.

### Resource Management
- **`cleanup_mne_cache`**: Removes MNE temporary cache files to manage disk usage,
 crucial for long-running pipelines on constrained environments.

### Configuration
- **`validate_pipeline_config`**: Ensures configuration dictionaries contain all required keys
 before processing begins, failing fast with clear error messages.

### File System
- **`find_files_by_extension`**: Robust file discovery with optional recursion.

## 2. Refactoring Principles Applied

- **DRY (Don't Repeat Yourself)**: Repeated logging setup and error handling logic
 have been replaced with calls to `cleanup_utils`.
- **Fail Fast**: Configuration validation happens at entry points to prevent
 downstream errors with cryptic messages.
- **Explicit over Implicit**: All functions now have type hints and docstrings.
- **Modularity**: Utilities are decoupled from specific domain logic (e.g., EEG processing),
 making them reusable across preprocessing, extraction, and stats modules.

## 3. Integration Points

Modules should import utilities as follows:

```python
from cleanup_utils import setup_logger, validate_array_shape, safe_divide, log_execution_time

logger = setup_logger(__name__)
```

## 4. Future Improvements

- Consider adding a generic `retry` decorator for network operations.
- Implement a context manager for temporary file handling.
- Add unit tests for `cleanup_utils` in `tests/unit/test_cleanup_utils.py`.
