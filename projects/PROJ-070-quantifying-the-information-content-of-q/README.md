# PROJ-070: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

## Overview
This project implements a pipeline to quantify the information content of quantum entanglement in many-body systems, correlating entanglement entropy with algorithmic complexity measures.

## Requirements
- Python 3.11+
- See `requirements.txt` for dependencies

## Installation
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

## Project Structure
- `code/`: Source code modules
- `data/`: Data storage (raw and processed)
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Usage
Run the ED generator:
```bash
python code/run_ed_generator.py --N 10 --output data/raw/ed_test.h5
```

Run tests:
```bash
pytest tests/
```

## License
Research use only.
