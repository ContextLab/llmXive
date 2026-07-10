# Quick Start Guide

## Prerequisites
- Python 3.11+
- `pip`
- (Optional) NCBI API key for higher rate limits

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline
The pipeline consists of several stages. To run the full pipeline:

1. **Data Download & Alignment** (User Story 1):
 ```bash
 # Set CI_MODE=1 to use mock data for testing
 export CI_MODE=1
 python code/data/download.py
 ```
 This produces `data/processed/aligned_dataset.csv`.

2. **Model Training & Validation** (User Story 2):
 ```bash
 python code/modeling/train.py
 ```
 This produces model artifacts and results in `data/processed/`.

3. **Sensitivity Analysis** (User Story 3):
 ```bash
 python code/modeling/sensitivity.py
 ```

## Configuration
Create a `.env` file in the root directory for optional configuration:
```
NCBI_API_KEY=your_key_here
CI_MODE=1
```

## Testing
Run the test suite:
```bash
pytest
```