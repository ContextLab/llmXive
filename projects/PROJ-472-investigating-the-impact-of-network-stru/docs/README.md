# llmXive: Network Structure & Neural Avalanche Dynamics Documentation

This directory contains the technical documentation for the `llmXive` research pipeline.

## Contents

- [Data Model Specification](001-data-model.md): Definition of core entities (Participant, StructuralConnectome, AvalancheRecord).
- [API Usage Guide](002-api-usage.md): Examples and instructions for using the codebase modules.
- [Workflow Guide](003-workflow-guide.md): Step-by-step execution flow from data acquisition to reporting.

## Quick Start

1. **Read the Data Model** to understand the data structures.
2. **Review the Workflow Guide** to understand the execution order.
3. **Consult the API Usage Guide** for implementation details.

## Project Structure

```
code/
├── analysis/ # Metric computation, fitting, stats
├── data/ # Download, preprocess, simulate, store
├── utils/ # Logging, configuration, helpers
├── config.py # Global parameters
└── main.py # Orchestration entry point
data/
├── raw/ # Downloaded raw data
├── processed/ # Preprocessed matrices and EEG
└── results/ # Analysis outputs
docs/ # This directory
tests/ # Unit and integration tests
```

## Contributing

When adding new modules:
1. Update `code/requirements.txt` if new dependencies are needed.
2. Add type hints and docstrings.
3. Update this documentation if the API changes.
4. Write corresponding tests in `tests/`.

## License

See the project root LICENSE file.