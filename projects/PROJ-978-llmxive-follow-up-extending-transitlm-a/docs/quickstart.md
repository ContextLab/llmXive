# Quickstart Guide: llmXive Follow-up

## Project Structure Setup

Before running any analysis or model training, ensure the project directory structure is initialized.

### Step 1: Initialize Project Directories

Run the setup script to create the necessary folders:

```bash
python code/setup_project.py
```

This will create:
- `code/` - Source code modules
- `data/raw/` - Raw downloaded datasets
- `data/processed/` - Preprocessed data files
- `data/analysis/` - Analysis results and reports
- `models/` - Model artifacts and definitions
- `analysis/` - Analysis scripts
- `tests/` - Unit and integration tests
- `docs/` - Documentation

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Download Data

Execute the download script to fetch the TransitLM dataset:

```bash
python code/data/download.py
```

### Step 4: Run Preprocessing

```bash
python code/data/preprocess.py
```

### Step 5: Run Evaluation

```bash
python code/analysis/evaluation.py
```

## Verification

To verify the setup, run the unit tests:

```bash
pytest tests/unit/test_setup_project.py -v
```
