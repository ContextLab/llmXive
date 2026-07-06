# Machine Learning Prediction of Crack Propagation Rates in Metals

This project implements a pipeline to predict fatigue crack growth (da/dN) rates in metals using machine learning models, validated against physics-based baselines (Paris Law).

## Project Structure

- `code/`: Source code for data loading, preprocessing, modeling, and analysis.
- `data/`: Storage for raw, interim, and processed data.
- `tests/`: Unit and integration tests.
- `specs/`: Design documents and feature specifications.
- `contracts/`: Schema definitions for data validation.
- `figures/`: Generated plots and visualizations.

## Setup

1. Ensure Python 3.11+ is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the main pipeline:
 ```bash
 python -m code.main
 ```

## Data Sources

Data is fetched from:
- NASA Fracture Control Database
- NIST Materials Data Repository

## License

MIT
