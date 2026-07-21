# PROJ-525: Predicting the Yield Strength of BCC Alloys

An automated science pipeline for predicting the yield strength of Body-Centered Cubic (BCC) alloys using compositional descriptors and machine learning.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd bcc-yield-strength-prediction
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Implementation modules
│ ├── 00_fetch_uncertainty.py
│ ├── 01_download.py
│ ├── 02_engineer.py
│ ├── config.py
│ ├── lint_format.py
│ └── utils/
│ ├── metrics.py
│ └── periodic_table.py
├── data/ # Data storage (raw, processed, logs)
├── tests/ # Unit and integration tests
├── reports/ # Generated reports and metrics
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration and build system
└── README.md # This file
```

## Usage

### Run the Pipeline

The pipeline consists of several stages:

1. **Data Ingestion**: Download and filter BCC alloy data
 ```bash
 python code/01_download.py
 ```

2. **Feature Engineering**: Calculate compositional descriptors
 ```bash
 python code/02_engineer.py
 ```

### Linting and Formatting

```bash
# Run linter
python code/lint_format.py --lint

# Run formatter
python code/lint_format.py --format
```

### Running Tests

```bash
pytest tests/
```

## Development

- **Python Version**: 3.11+
- **Code Style**: Black (88 chars), Ruff
- **Testing**: pytest

## License

MIT License
