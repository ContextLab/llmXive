# Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Overview
This project implements an automated research pipeline to predict the yield strength of High-Entropy Alloys (HEAs) using compositional descriptors (δ, Δχ, VEC, entropy, etc.). The pipeline includes data acquisition, descriptor engineering, model training (Random Forest, Gradient Boosting, Linear Regression), and statistical validation.

## Project Structure
```
.
├── code/ # Source code
│ ├── data/ # Data processing modules
│ ├── models/ # Machine learning models
│ ├── utils/ # Utility functions
│ └── __init__.py
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data with descriptors
├── output/
│ ├── plots/ # Generated figures
│ └── reports/ # Analysis reports
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Setup

1. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Configure Environment**:
 Ensure dataset URLs are configured in `code/utils/config.py` or via environment variables as specified in `specs/001-predict-hea-yield-strength/`.

## Usage

### Running the Full Pipeline
```bash
python code/run_pipeline.py
```

### Data Processing (User Story 1)
```bash
python code/data/pipeline.py
```

### Model Training (User Story 2)
```bash
python code/models/train.py
```

### Statistical Validation (User Story 3)
```bash
python code/models/evaluate.py
```

## Testing
Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/
pytest tests/integration/
```

## Dependencies
See `requirements.txt` for the full list of required packages.

## Disclaimer
This research project is for educational and exploratory purposes. All findings are associational; no causal inference should be drawn without further experimental validation.

## License
MIT License