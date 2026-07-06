# PROJ-361: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## Overview
This project investigates the relationship between resting-state brain network topology and individual susceptibility to visual illusions (Müller-Lyer and Ponzo). We utilize data from the OpenNeuro ds004285 dataset. [UNRESOLVED-CLAIM: c_ee403c1d — status=not_enough_info]

## Project Structure
```
.
├── code/ # Source code
│ ├── utils/ # Utility modules (DB schema, config, logging)
│ ├── preprocessing/ # Data acquisition and preprocessing pipelines
│ ├── topology/ # Network metric computation
│ ├── behavioral/ # Behavioral data extraction
│ └── analysis/ # Statistical analysis and reporting
├── data/ # Data storage (raw, processed, behavioral)
│ ├── raw/ # Downloaded raw data
│ ├── processed/ # Preprocessed and analyzed data
│ └── metadata_registry.db # SQLite metadata index
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration (black, mypy, etc.)
└── README.md # This file
```

## Setup
1. Ensure Python 3.11+ is installed.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
### Initialize Database
The metadata registry is initialized automatically by `code/utils/db_schema.py`.
```python
from code.utils.db_schema import init_db
conn = init_db()
# Use conn to register subjects and files
```

### Running the Pipeline
Refer to individual task implementations in `code/` for specific pipeline steps.

## Testing
Run tests using pytest:
```bash
pytest tests/
```

## License
MIT License