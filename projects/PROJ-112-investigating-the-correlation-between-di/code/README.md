# llmXive Research Pipeline: Dietary Fiber and Gut Microbiome

This project investigates the correlation between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and UK Biobank (UKBB).

## Project Structure

- `src/`: Source code for the pipeline
 - `ingestion/`: Data loading and harmonization
 - `preprocessing/`: Data cleaning, transformation, and imputation
 - `analysis/`: Statistical analysis and correlation
 - `utils/`: Utility functions
- `tests/`: Test suites
 - `contract/`: Schema validation tests
 - `integration/`: Integration tests
 - `unit/`: Unit tests
- `data/`: Data directories
 - `raw/`: Raw downloaded data
 - `processed/`: Processed and harmonized data
 - `processed/results/`: Final analysis results
- `docs/`: Documentation
- `state/`: Pipeline state and logs
- `figures/`: Generated plots

## Usage

1. **Setup Environment**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Setup Directory Structure**:
 ```bash
 python code/src/setup_data_structure.py
 ```

3. **Run Pipeline**:
 Follow the steps in `quickstart.md`.

## Dependencies

See `requirements.txt` for the full list of dependencies.
