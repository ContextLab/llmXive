# PROJ-083: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Overview
This project investigates the relationship between molecular topology (Wiener, Balaban, Zagreb indices) and reaction selectivity in Electrophilic Aromatic Substitution (EAS) reactions.

## Setup
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run the ingestion pipeline:
 ```bash
 python -m code.ingestion
 ```
4. Run tests:
 ```bash
 pytest
 ```

## Project Structure
- `code/`: Source code
 - `ingestion.py`: Data ingestion pipeline
 - `descriptors.py`: Topological descriptor calculation
 - `modeling.py`: Statistical modeling
 - `utils/`: Utility functions (smiles_parser, logger, symmetry)
 - `config.py`: Configuration management
- `data/`: Data directories
 - `raw/`: Raw data (USPTO-50k)
 - `processed/`: Processed data (EAS reactions, descriptors)
 - `models/`: Model outputs
- `tests/`: Test suite
 - `unit/`: Unit tests
 - `integration/`: Integration tests
- `docs/`: Documentation
- `specs/`: Feature specifications

## Dependencies
- Python 3.11+
- RDKit
- Pandas
- Scikit-learn
- Statsmodels
- PyYAML
- Pytest
- Black
- Ruff
- NetworkX

## License
MIT License