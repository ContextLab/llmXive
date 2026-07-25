# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Structure

This project analyzes bird migration data (eBird) and climate data (NOAA) to study the correlation between phenology shifts and climate change.

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-132-statistical-analysis-of-publicly-availab
 ```

2. Create a virtual environment and activate it:
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
 pre-commit install
 ```

### Pre-commit Configuration

This project uses `black` for code formatting and `ruff` for linting. The pre-commit hooks are configured in `.pre-commit-config.yaml`.

To manually run pre-commit hooks on all files:
```bash
pre-commit run --all-files
```

To install the pre-commit hooks:
```bash
pre-commit install
```

## Usage

### Running the Pipeline

To run the full analysis pipeline:
```bash
python run_pipeline.py
```

### Data Requirements

The pipeline requires real eBird and NOAA data in `data/raw/ebird/` and `data/raw/climate/`. If real data is missing, the pipeline will abort in production mode or generate synthetic data in development mode (see `src/data/download.py`).

## Testing

Run tests using pytest:
```bash
pytest tests/
```

## License

MIT License