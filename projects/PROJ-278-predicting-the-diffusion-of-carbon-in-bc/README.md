# Predicting the Diffusion of Carbon in BCC Metals

This project implements a machine learning pipeline to predict carbon diffusion coefficients in Body-Centered Cubic (BCC) metals based on compositional data.

## Project Structure

- `code/`: Python source code for the pipeline (download, preprocess, train, evaluate, validate).
- `data/`:
 - `raw/`: Original downloaded datasets (e.g., MeLiDC).
 - `processed/`: Cleaned and feature-engineered datasets.
 - `outputs/`: Model artifacts, predictions, and analysis results.
- `contracts/`: Schema definitions for data validation.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation (README, quickstart, etc.).
- `specs/`: Feature specifications and design documents.

## Prerequisites

- Python 3.11+
- `pip`

## Installation

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

Run the pipeline sequentially:

1. **Download Data**:
 ```bash
 python code/01_download.py
 ```

2. **Preprocess Data**:
 ```bash
 python code/02_preprocess.py
 ```

3. **Train Models**:
 ```bash
 python code/03_train.py
 ```

4. **Evaluate Models**:
 ```bash
 python code/04_evaluate.py
 ```

5. **Validate Outputs**:
 ```bash
 python code/05_validate.py
 ```

## Running Tests

```bash
pytest tests/
```

## License

MIT
