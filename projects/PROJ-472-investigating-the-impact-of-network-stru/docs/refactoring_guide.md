# Refactoring and Code Modularity Guide

## Overview

This guide documents the refactoring utilities and best practices for maintaining
code modularity in the llmXive research pipeline.

## Module Structure

### Core Modules

- **code/config.py**: Configuration management and parameter definitions
- **code/data/models.py**: Data models (Participant, StructuralConnectome, AvalancheRecord)
- **code/data/download.py**: Data acquisition from external sources
- **code/data/preprocess_dMRI.py**: dMRI tractography preprocessing
- **code/data/simulate_EEG.py**: Wilson-Cowan based EEG simulation
- **code/data/quality_control.py**: Quality control checks and reporting
- **code/data/store.py**: Persistent storage and retrieval of processed data
- **code/analysis/metrics.py**: Network metric computation
- **code/analysis/avalanches.py**: Neural avalanche detection and analysis
- **code/analysis/fitting.py**: Power-law model fitting
- **code/analysis/stats.py**: Statistical analysis and robustness testing
- **code/analysis/sensitivity.py**: Sensitivity analysis
- **code/analysis/export_metrics.py**: Metric export and reporting
- **code/analysis/report.py**: Final report generation
- **code/utils/logger.py**: Logging infrastructure
- **code/utils/refactor_utils.py**: Refactoring utilities

## Refactoring Utilities

The `code/utils/refactor_utils.py` module provides tools for code analysis and cleanup:

### Available Functions

- `get_module_functions(module_path)`: Extract public functions and classes from a module
- `validate_module_exports(module_path, expected_exports)`: Validate module exports
- `organize_imports(file_path)`: Sort and organize imports in a Python file
- `extract_constants(file_path)`: Extract module-level constants
- `check_circular_dependencies(modules)`: Detect circular dependencies between modules
- `generate_module_documentation(module_path)`: Generate documentation for a module
- `run_refactoring_checks(root_dir)`: Run comprehensive refactoring checks

### Usage Examples

```python
from utils.refactor_utils import get_module_functions, validate_module_exports

# Get functions from a module
funcs = get_module_functions('code.analysis.metrics')
print(funcs['functions'])

# Validate exports
result = validate_module_exports('code.config', ['get_data_root', 'ensure_directories'])
print(result['valid'])
```

## Best Practices

### Import Organization

1. Standard library imports
2. Third-party imports
3. Local project imports

### Module Exports

- All public functions and classes should be explicitly listed
- Avoid importing private members (starting with `_`)
- Use `__all__` to define public API when necessary

### Constant Extraction

- Use uppercase for constants (e.g., `MAX_SIZE = 100`)
- Group related constants together
- Document constant purposes in docstrings

### Dependency Management

- Avoid circular dependencies between modules
- Use dependency injection for complex interactions
- Prefer composition over inheritance

## Running Refactoring Checks

```bash
# Run comprehensive checks
python code/utils/refactor_utils.py --check

# Analyze specific module
python code/utils/refactor_utils.py --module code.analysis.metrics

# Organize imports in a file
python code/utils/refactor_utils.py --organize code/analysis/metrics.py

# Extract constants from a file
python code/utils/refactor_utils.py --constants code/config.py
```

## Maintenance Schedule

- Run refactoring checks before major releases
- Review module dependencies quarterly
- Update documentation when adding new modules
- Validate exports after adding new public functions