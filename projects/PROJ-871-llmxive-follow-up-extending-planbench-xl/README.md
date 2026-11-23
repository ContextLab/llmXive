# llmXive: PlanBench-XL Extension

This project extends the PlanBench-XL benchmark to evaluate long-horizon planning of LLM tool-use agents, specifically focusing on detecting and recovering from implicit failures.

## Project Structure

```
projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/
├── code/ # Source code
│ ├── agents/ # Agent implementations
│ ├── analysis/ # Statistical analysis
│ ├── dataset/ # Data loading and processing
│ ├── utils/ # Utility functions
│ └──...
├── data/ # Data artifacts (ignored by git)
│ ├── raw/ # Raw downloaded data
│ ├── derived/ # Processed data
│ ├── logs/ # Execution logs
│ └── results/ # Final results
├── tests/ # Test suite
├──.flake8 # Flake8 configuration
├── pyproject.toml # Project metadata and Black/isort config
├──.pre-commit-config.yaml # Pre-commit hooks
├── Makefile # Build and lint commands
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- pip
- virtualenv (recommended)

## Setup

1. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install linting and formatting tools:
 ```bash
 make lint # This will install flake8, black, isort if not already installed
 ```

4. (Optional) Set up pre-commit hooks:
 ```bash
 pip install pre-commit
 pre-commit install
 ```

## Development

### Code Formatting and Linting

This project uses Black for code formatting and flake8 for linting.

- Check code style:
 ```bash
 make lint
 ```

- Auto-format code:
 ```bash
 make format
 ```

- Run tests:
 ```bash
 make test
 ```

- Run all checks:
 ```bash
 make check-all
 ```

### Configuration

- **Black**: Configured in `pyproject.toml` with a line length of 100.
- **Flake8**: Configured in `.flake8` with a max line length of 100 and specific ignores.
- **isort**: Configured in `pyproject.toml` to match Black's formatting.

## Running the Experiment

See `quickstart.md` for detailed instructions on running the full experiment pipeline.

```bash
python run_experiment.py
```

## License

MIT License