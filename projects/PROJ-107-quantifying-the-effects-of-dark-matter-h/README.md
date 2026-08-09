# Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

This project implements an automated science pipeline to analyze the relationship between dark matter halo shapes and galaxy formation properties using cosmological simulation data (primarily TNG-100).

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and processed data files
- `outputs/`: Generated figures and reports
- `specs/`: Project specifications and design documents
- `tests/`: Unit and integration tests

## Hardware Constraints & Feasibility

**Important Note on Data Processing Strategy**:

Due to hardware constraints (7GB RAM limit on the execution environment), this pipeline implements **chunked processing and sampling** strategies. This is a **documented deviation** from the original "every FoF halo" requirement specified in FR-001, as per SC-005 feasibility constraints.

The pipeline is designed to:
- Process data in memory-safe chunks (<7GB RAM usage)
- Apply representative sampling when full dataset processing is infeasible
- Log all deviations and limitations in `data/metadata.yaml`
- Ensure reproducibility with documented sampling seeds

This approach ensures the project remains feasible within the compute budget while maintaining scientific rigor through documented limitations.

## Setup

1. Ensure Python 3.11 is installed
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

Run the main pipeline:
```bash
python code/main.py
```

Run tests:
```bash
pytest code/tests/
```

## Data Sources

- TNG-100: Downloaded via the TNG API (see `code/ingestion/tng_loader.py`)
- Millennium-II: Attempted fetch with fallback logging if unavailable (see `code/ingestion/millennium_loader.py`)

## License

[Project License]