# Code Cleanup and Modularity Guide

This document outlines the refactoring principles and modular structure enforced in the llmXive project.

## 1. Module Organization

The project follows a strict modular structure:

- `code/config.py`: Centralized configuration and hyperparameters
- `code/data/`: Data acquisition, preprocessing, and storage
 - `models.py`: Data class definitions
 - `download.py`: External data fetching
 - `preprocess_dMRI.py`: Structural connectome processing
 - `simulate_EEG.py`: Neural signal simulation
 - `quality_control.py`: Data validation
 - `store.py`: Unified data persistence
- `code/analysis/`: Metric computation and statistical analysis
 - `metrics.py`: Network topology metrics
 - `avalanches.py`: Neural avalanche detection
 - `fitting.py`: Power-law model fitting
 - `stats.py`: Statistical associations
 - `sensitivity.py`: Threshold sensitivity analysis
 - `export_metrics.py`: Results aggregation
 - `report.py`: Final report generation
- `code/utils/`: Shared utilities
 - `logger.py`: Logging infrastructure
 - `env_config.py`: Environment management
 - `data_setup.py`: Data directory setup
 - `refactor_utils.py`: Modularity enforcement tools

## 2. Export Consistency

Every module must define an explicit `__all__` list to control public API:

```python
__all__ = ['function_a', 'function_b', 'ClassC']
```

Only functions, classes, and variables listed in `__all__` should be imported by external modules.

## 3. Import Organization

Imports are organized in three groups separated by blank lines:

1. Standard library (`os`, `sys`, `pathlib`, etc.)
2. Third-party libraries (`numpy`, `pandas`, `networkx`, etc.)
3. Local project modules (`from config import...`, `from data.models import...`)

Within each group, imports are sorted alphabetically.

## 4. Circular Dependency Prevention

The project uses `refactor_utils.check_circular_dependencies()` to detect and prevent circular imports. If a cycle is found, refactor by:

- Moving shared logic to a lower-level utility module
- Using lazy imports (import inside function)
- Restructuring module responsibilities

## 5. Documentation Standards

Every module must have:
- A module-level docstring describing its purpose
- Docstrings for all public functions and classes
- Type hints for function arguments and return values

## 6. Running Refactoring Checks

To validate the codebase:

```bash
python code/utils/refactor_utils.py
```

This will:
- Verify `__all__` definitions
- Detect circular dependencies
- Extract module-level constants
- Generate documentation summaries

## 7. Future Refactoring Recommendations

- Consider extracting common preprocessing steps into a shared `preprocessing.py` module
- Add type stubs (`.pyi`) for complex data structures
- Implement a plugin system for extensible analysis pipelines
- Add performance profiling hooks for critical paths