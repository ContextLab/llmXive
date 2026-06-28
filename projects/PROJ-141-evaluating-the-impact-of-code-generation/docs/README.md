# Evaluating the Impact of Code Generation Models on Developer Productivity

**Project ID**: PROJ-141

## Overview

This project implements a controlled within-subject experiment to evaluate the impact of code generation models (LLM-assisted vs baseline conditions) on developer productivity. The system includes:

- **Experiment Interface**: Flask-based web interface for problem presentation, code input, and condition management
- **Quality Assessment Pipeline**: Automated metrics including pass rate, cyclomatic complexity, test coverage, and static analysis warnings
- **Statistical Analysis**: Paired t-tests, effect sizes, confidence intervals, and multiple-comparison correction

## Project Structure

```
PROJ-141-evaluating-the-impact-of-code-generation/
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── config/ # Configuration management
│ ├── data/ # Data models and database schema
│ ├── experiment/ # Experiment interface and flow
│ ├── hooks/ # Git hooks for compliance
│ ├── models/ # LLM model integrations
│ ├── quality/ # Code quality assessment
│ └── research/ # Research documentation
├── data/ # Datasets and outputs
├── docs/ # Documentation
├── models/ # Pre-trained models (if downloaded)
├── specs/ # Feature specifications
├── state/ # Project state tracking
├── tests/ # Test suites
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip package manager
- Git for version control
- SQLite (included with Python)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-141-evaluating-the-impact-of-code-generation
 ```

2. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/macOS
 # or
 venv\Scripts\activate # Windows
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Configure environment variables (see `code/config/settings.py`):
 ```bash
 export CODEX_ENCRYPTION_KEY=<your-encryption-key>
 export HUMAN_EVAL_PATH=<path-to-humaneval>
 export CODEFORCES_PATH=<path-to-codeforces>
 ```

## Quick Start

See [docs/quickstart.md](quickstart.md) for a step-by-step guide to running the experiment.

## Running the Experiment

1. Start the Flask experiment server:
 ```bash
 python code/experiment/app.py
 ```

2. Navigate to ` in your browser

3. Follow the consent flow and complete problems under both conditions

## Running Quality Assessment

After data collection, run the quality assessment pipeline:

```bash
python code/quality/metric_aggregator.py
```

## Running Statistical Analysis

```bash
python code/analysis/statistical_tests.py
python code/analysis/export.py
```

## API Documentation

See [docs/api.md](api.md) for detailed API reference.

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
# Contract tests
pytest tests/contract/

# Integration tests
pytest tests/integration/

# Unit tests
pytest tests/unit/
```

## Compliance

This project follows Constitution principles for reproducibility and data protection:

- **Principle I**: Random seeds are pinned for reproducibility
- **Principle III**: Checksums stored in state file
- **Principle IV**: Trace IDs for statistics
- **Principle V**: Timestamp updates via pre-commit hooks
- **Principle VII**: Secure data deletion workflow

## License

See LICENSE file for details.

## Contributing

See CONTRIBUTING.md for guidelines.
