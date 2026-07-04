# Dietary Fiber Intake and Gut Microbiome Composition Analysis

## Overview
This project investigates the correlation between dietary fiber intake and gut microbiome composition using data from the American Gut Project (AGP) and UK Biobank (UKBB).

## Project Structure
```
.
├── code/
│ ├── main.py # Entry point
│ ├── ingestion/ # Data loading scripts
│ ├── preprocessing/ # Data cleaning and transformation
│ ├── analysis/ # Statistical analysis (MaAsLin2, etc.)
│ ├── utils/ # Utilities (logger, power analysis)
│ └── tests/ # Test suites
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed and harmonized data
├── docs/ # Documentation
├── state/ # Pipeline state tracking
└── logs/ # Log files
```

## Setup
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
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
- American Gut Project (AGP): Via Qiita
- UK Biobank (UKBB): Via UKBB portal

## License
MIT
