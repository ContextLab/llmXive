# Quickstart Guide

## Prerequisites

- Python 3.8+
- pip
- git

## Installation

```bash
cd code
pip install -r requirements.txt
```

## Usage

The pipeline is orchestrated via `main.py` with specific phase commands.

### 1. Initialize Directories and Logs

```bash
python setup_directories.py
python scripts/run_logging_init.py
```

### 2. Generate Network Batch

```bash
python scripts/run_batch_generation.py --config code/config.yaml
```

### 3. Run Simulations

```bash
python scripts/run_simulation.py --config code/config.yaml
```

### 4. Run Sensitivity Sweep

```bash
python scripts/run_sensitivity_sweep.py --config code/config.yaml
```

### 5. Run Analysis

```bash
python scripts/run_analysis.py --config code/config.yaml
```

### 6. Aggregate Results

```bash
python scripts/run_aggregation.py --config code/config.yaml
```

### 7. Validate Batch

```bash
python scripts/validate_batch.py --config code/config.yaml
```

### 8. Generate Final Report

```bash
python scripts/run_final_serialization.py --config code/config.yaml
```

## Configuration

All parameters are defined in `code/config.yaml`. Do not modify seeds manually; use the config file.

## Verification

Run the validation script to ensure all artifacts are present:

```bash
python scripts/validate_quickstart.py
```