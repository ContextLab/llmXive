# Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Overview

This project implements a statistical analysis pipeline to investigate the correlation between bird migration patterns and climate change using publicly available data.

## Project Structure

- `src/`: Source code for the pipeline
- `data/`: Data storage (raw, processed, interim)
- `tests/`: Test suite
- `docs/`: Documentation

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
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

## Configuration

The pipeline uses configuration defined in `src/config.py`. Key parameters include:
- `GRID_RES`: Grid resolution for spatial binning
- `MIN_OBSERVATIONS`: Minimum observations required for valid grid cells
- `RANDOM_SEED`: Random seed for reproducibility
- `PERMUTATIONS`: Number of permutation test iterations
- `CI_WIDTH_TARGET`: Target confidence interval width in days

## Data Sources

- eBird data: Verified sample from `vvud/eb-data`
- Climate data: Daymet (Plan deviation from NOAA/PRISM)

See `specs/001-bird-migration-climate-correlation/amendments/PLAN-DEVIATION-DATA-SOURCES.md` for details on data source deviations.

## Testing

Run tests:
```bash
pytest
```

## License

[License information]