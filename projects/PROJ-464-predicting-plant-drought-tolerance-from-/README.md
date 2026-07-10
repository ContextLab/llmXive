# Predicting Plant Drought Tolerance from RSA Data

**Project ID**: PROJ-464

## Overview
This project implements an automated pipeline to predict plant drought tolerance
using Root System Architecture (RSA) metrics derived from NPPN root phenotyping images,
correlated with physiological traits from the TRY database.

## Project Structure
```
├── code/ # Python source modules
├── data/
│ ├── raw/ # Raw downloaded images and data
│ └── derived/ # Processed metrics and models
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── state/ # Pipeline state and reports
├── contracts/ # Data schemas and validation rules
└── results/ # Final analysis outputs and figures
```

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure paths in `code/config.py`
3. Run the pipeline: `python code/main.py` (placeholder for future entry point)

## Dependencies
See `requirements.txt` for the full list.

## License
[Insert License]
