# Quickstart Guide

This guide outlines how to run the BCC Yield Strength prediction pipeline.

## 1. Environment Setup

Ensure you are using Python 3.11 or higher.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Directory Initialization

Run the setup script to create necessary directories:

```bash
python code/config.py --init-dirs
```

## 3. Pipeline Execution

The pipeline consists of three main stages:

1. **Data Ingestion** (T013-T018): Download and filter raw data.
 ```bash
 python code/01_download.py
 ```

2. **Feature Engineering** (T023-T032): Calculate descriptors and ILR transforms.
 ```bash
 python code/02_engineer.py
 ```

3. **Modeling** (T033-T039): Train models and generate reports.
 ```bash
 python code/03_modeling.py
 ```

## 4. Verification

Validate the results:
```bash
python code/validate_success.py
```

## 5. Linting & Formatting

Ensure code quality before committing:
```bash
python code/lint_format.py
```
