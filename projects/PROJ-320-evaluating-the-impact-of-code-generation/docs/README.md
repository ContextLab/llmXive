# llmXive Documentation

Welcome to the llmXive documentation. This project evaluates the impact of code generation on code review quality using LLMs.

## Overview

The project is structured into the following phases:
1. **Setup**: Project initialization and directory structure.
2. **Foundational**: Core infrastructure, including complexity calculation.
3. **User Story 1**: Data acquisition and LLM classification.
4. **User Story 2**: Metric extraction and statistical comparison.
5. **User Story 3**: Complexity scoring and visualization.
6. **Polish**: Cross-cutting concerns and final report generation.

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Setup Directories**:
 ```bash
 python code/setup_directories.py
 ```

3. **Run the Pipeline**:
 See the [Full Pipeline Example](api_examples.md#1-running-the-full-pipeline) in the API Examples document.

## Documentation Structure

- **[API Reference](api_reference.md)**: Complete list of all modules, functions, and classes with descriptions.
- **[API Examples](api_examples.md)**: Practical code snippets showing how to use the API.
- **[Task List](../tasks.md)**: The current implementation status of all tasks.

## Contributing

When adding new modules, ensure you:
1. Implement the full functionality (no stubs).
2. Add a section to `docs/api_reference.md`.
3. Add an example to `docs/api_examples.md`.
4. Update the `README.md` if the entry point changes.

## License

See the project root for license information.
