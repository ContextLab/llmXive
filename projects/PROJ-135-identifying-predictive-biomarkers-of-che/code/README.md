# llmXive: Identifying Predictive Biomarkers of Chemotherapy Response

## Project Structure
This project follows a standard data science pipeline structure:

- `code/src/`: Source code for data acquisition, preprocessing, modeling, and validation.
- `code/data/raw/`: Raw data downloaded from TCGA, GEO, and HuggingFace mirrors.
- `code/data/processed/`: Cleaned, normalized, and split datasets.
- `code/results/`: Final analysis results, summaries, and meta-analysis outputs.
- `code/results/meta_analysis/`: Specific outputs related to gene panel selection and meta-analysis.
- `code/tests/`: Unit, integration, and contract tests.
- `code/specs/`: Feature specifications, contracts, and documentation.
- `code/state/`: Runtime state, artifact hashes, and checkpoint files.

## Setup
Run `python setup_project_structure.py` to ensure all directories are created.