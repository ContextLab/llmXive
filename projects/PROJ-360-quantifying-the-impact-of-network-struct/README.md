# Quantifying the Impact of Network Structure on Heat Diffusion

## Project Setup

This project requires Python 3.11+.

### 1. Create and Activate Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python -c "import pymatgen; import networkx; import sklearn; import pandas; import requests; import numpy; import statsmodels; print('All dependencies installed successfully.')"
```

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed data
- `results/`: Analysis outputs and reports
- `models/`: Trained machine learning models
- `tests/`: Unit and integration tests

## Usage

See `tasks.md` for the implementation roadmap and specific script usage instructions.
