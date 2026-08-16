# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview
This project analyzes the correlation between bird migration patterns and climate change using publicly available data from eBird and Daymet.

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-132-statistical-analysis-of-publicly-availab
 ```

2. Install dependencies:
 ```bash
 pip install -e.
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

Run the full pipeline:
```bash
python -m src.cli.run_pipeline --help
```

## Project Structure
- `src/`: Source code
- `data/`: Data files (raw, processed, interim)
- `tests/`: Test suites
- `specs/`: Project specifications
- `docs/`: Documentation

## Configuration
Configuration is managed via `src/config.py`. Key parameters include:
- `GRID_RES`: Grid resolution for spatial binning
- `MIN_OBSERVATIONS`: Minimum observations required for data quality
- `RANDOM_SEED`: Seed for reproducibility
- `PERMUTATIONS`: Number of permutations for statistical tests

## Data Sources
- eBird: Verified sample from `vvud/eb-data`
- Daymet: Climate data from `daymet/annual`

## Contributing
Please read the contributing guidelines before submitting pull requests.