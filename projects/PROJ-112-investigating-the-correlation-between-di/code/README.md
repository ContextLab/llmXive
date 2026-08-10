# llmXive Project: Dietary Fiber and Gut Microbiome Correlation

## Overview
This project investigates the correlation between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and UK Biobank (UKBB).

## Project Structure
```
.
├── code/
│ ├── src/
│ │ ├── ingestion/ # Data loading modules
│ │ ├── preprocessing/ # Data cleaning and transformation
│ │ ├── analysis/ # Statistical analysis modules
│ │ ├── utils/ # Shared utilities
│ │ └── main.py # Entry point
│ ├── tests/ # Test suites
│ ├── requirements.txt # Dependencies
│ └── pyproject.toml # Project configuration
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned and transformed data
│ └── processed/results/ # Analysis outputs
├── docs/ # Documentation
└── state/ # Pipeline state files
```

## Setup
1. Ensure Python 3.11 is installed.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Initialize directory structure:
 ```bash
 python code/src/setup_data_structure.py
 ```

## Running the Pipeline
```bash
python code/src/main.py
```

## Testing
```bash
pytest code/tests/
```

## License
MIT
