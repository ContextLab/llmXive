# The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview

This project investigates the relationship between nostalgia induction and cognitive flexibility in aging adults (65+). The analysis uses data from the Wisconsin Card Sorting Test (WCST) and related executive function measures.

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-524-the-impact-of-nostalgia-on-cognitive-fle
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
python -c "import pandas; import scipy; import statsmodels; print('All dependencies installed successfully')"
```

## Quick Start

### Running the Ingestion Pipeline

The ingestion pipeline fetches data, validates it, and produces a cleaned dataset ready for analysis.

```bash
# Run the full ingestion pipeline
python code/run_ingestion.py
```

This will:
1. Fetch real data from the specified source (or fall back to simulation if unavailable)
2. Validate the data against the schema
3. Filter by age (≥65) and score requirements
4. Generate cleaned datasets and exclusion logs

Output files will be written to:
- `data/raw/` - Raw downloaded data
- `data/processed/` - Cleaned and filtered datasets
- `contracts/` - Schema definitions

### Running the Analysis Pipeline

Once the cleaned dataset is ready, run the statistical analysis:

```bash
python code/analysis.py
```

This will:
1. Perform Welch's t-tests between nostalgia and control groups
2. Calculate effect sizes (Cohen's d)
3. Apply Bonferroni correction
4. Conduct power analysis
5. Generate sensitivity analysis
6. Output results to `data/results/`

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## Project Structure

```
PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/
├── code/ # Source code
│ ├── ingestion/ # Data ingestion modules
│ ├── analysis.py # Statistical analysis
│ ├── config.py # Configuration management
│ ├── utils.py # Utility functions
│ └──... # Task-specific scripts
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned datasets
│ ├── results/ # Analysis outputs
│ └── stimuli/ # Stimulus materials
├── contracts/ # Data schemas
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema validation tests
├── specs/ # Project specifications
├── paper/ # Generated paper drafts
├── state/ # Pipeline state tracking
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Configuration

The project uses environment variables for configuration:

- `PROJECT_ROOT`: Base directory for the project (default: current directory)
- `DATA_SOURCE`: Data source URL or identifier (default: from plan.md)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

Set these before running scripts:
```bash
export PROJECT_ROOT=/path/to/project
export LOG_LEVEL=DEBUG
python code/run_ingestion.py
```

## License

This project is for research purposes. See LICENSE file for details.

## Contributing

Please read the contributing guidelines before submitting pull requests.
