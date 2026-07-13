# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview

This project analyzes bird migration patterns and their correlation with climate change using publicly available data from eBird and NOAA.

## Installation

### Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

### Setup

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Install pre-commit hooks:
 ```bash
 pip install pre-commit
 pre-commit install
 ```

 Pre-commit will now automatically run `black` and `ruff` on your code before each commit.

5. Run the pipeline:
 ```bash
 python run_pipeline.py --help
 ```

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/
│ │ │ ├── download.py
│ │ │ ├── preprocess.py
│ │ │ └── impute.py
│ │ ├── models/
│ │ │ ├── gamm_fit.py
│ │ │ ├── trajectory.py
│ │ │ └── utils.py
│ │ └── lib/
│ │ └── config.py
│ ├── setup_project.py
│ └── run_pipeline.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── interim/
├── tests/
│ ├── contract/
│ ├── unit/
│ └── integration/
├── docs/
├──.pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Usage

### Running the Pipeline

```bash
python run_pipeline.py
```

### Running Tests

```bash
pytest tests/
```

### Linting and Formatting

The project uses `black` for formatting and `ruff` for linting. These are configured in `pyproject.toml` and run automatically via pre-commit.

To run manually:
```bash
black code/
ruff check code/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass and pre-commit hooks are satisfied
5. Submit a pull request

## License

MIT License