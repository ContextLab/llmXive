# Project Structure: PROJ-925-llmxive-follow-up-extending-lens-rethink

This document describes the directory structure for the llmXive follow-up project.

## Directory Layout

The project follows a standard Python project layout with separate directories for code, data, and documentation.

```
projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/
├── code/
│ ├── data/ # Data loading, preprocessing, and streaming utilities
│ ├── models/ # Data models and Pydantic schemas
│ ├── tests/ # Unit and integration tests
│ ├── utils/ # Utility functions (logging, config, etc.)
│ └── __init__.py # Package initializer
├── data/
│ ├── raw/ # Raw, unprocessed data from external sources
│ └── processed/ # Processed and feature-engineered data
└── docs/ # Project documentation
```

## Directory Descriptions

### `code/`
Contains all Python source code for the project.

- `code/data/`: Modules for data acquisition, streaming, and preprocessing.
- `code/models/`: Pydantic models and data structures.
- `code/tests/`: Test suite for the project.
- `code/utils/`: Shared utilities like logging and configuration management.

### `data/`
Stores all data artifacts.

- `data/raw/`: Original data files downloaded from external sources (e.g., Pick-a-Pic dataset).
- `data/processed/`: Derived datasets, feature vectors, and intermediate results.

### `docs/`
Project documentation, including this file, design documents, and specifications.

## Initialization

The project structure can be created by running:

```bash
python code/setup_project.py
```

This script will create all necessary directories and `__init__.py` files to make the directories proper Python packages.