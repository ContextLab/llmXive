# PROJ-525: Predicting Yield Strength of BCC Alloys

Automated science pipeline for predicting yield strength of Body-Centered Cubic (BCC) alloys.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import numpy; import pandas; import scikit_learn; import periodictable; import skbio; import scipy; import requests; print('All dependencies installed successfully.')"
 ```

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `reports/`: Generated reports and visualizations
- `state/`: Pipeline state tracking

## Usage

Refer to `quickstart.md` for execution instructions.