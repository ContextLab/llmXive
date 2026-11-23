# Architecture Overview

This document describes the high-level architecture of the llmXive follow-up project extending DanceOPD.

## Project Structure

The project is organized into the following top-level directories:

- `code/`: Source code for the pipeline
 - `utils/`: Utility modules (config, metrics, statistics, check_weights)
 - `models/`: Model definitions and inference logic
 - `00_data_generation.py`: Main entry for data generation
 - `00_teacher_inference.py`: Teacher model inference logic
 - `00_data_extraction.py`: Data extraction and validation
 - `00_validate_sources.py`: Source validation
 - `01_train_trees.py`: Decision tree training
 - `02_evaluate_fidelity.py`: Fidelity evaluation
 - `03_versioning.py`: Artifact versioning
 - `_data_streaming.py`: Data streaming utilities
 - `main.py`: Main orchestrator
 - `setup_data_dirs.py`: Directory setup
 - `statistics_runner.py`: Statistical analysis runner
- `data/`: Data storage
 - `raw/`: Raw input data and model weights
 - `processed/`: Processed datasets
 - `results/`: Evaluation results and metrics
- `models/`: Trained model artifacts
- `specs/`: Specification documents and contracts
 - `contracts/`: JSON schemas for data validation
- `tests/`: Test suites
 - `unit/`: Unit tests
 - `integration/`: Integration tests
- `docs/`: Documentation

## Data Flow

1. **Data Generation**:
 - Stream samples from ImageNet-1K and LAION-400M using `_data_streaming.py`
 - Run teacher model inference via `00_teacher_inference.py`
 - Extract features and validate routing labels in `00_data_extraction.py`
 - Output: `data/processed/teacher_routing_dataset.parquet`

2. **Tree Training**:
 - Load dataset and split into train/test sets in `01_train_trees.py`
 - Train DecisionTreeClassifier for various `max_depth` values
 - Save models and results to `models/trained_trees/` and `data/results/tree_accuracy.csv`

3. **Fidelity Evaluation**:
 - Generate images using tree-predicted routing and teacher baseline routing
 - Compute FID and CLIP scores using `utils/metrics.py`
 - Perform statistical tests in `utils/statistics.py`
 - Output: `data/results/fidelity_metrics.csv`, `data/results/statistical_tests.json`

## Key Components

### Configuration
- `utils/config.py`: Manages seeds, paths, and hyperparameters

### Metrics
- `utils/metrics.py`: Implements CLIP score and FID calculations
- `utils/statistics.py`: Provides bootstrap and t-test implementations

### Inference
- `models/inference.py`: Contains the Euler integrator and expert field simulator

### Versioning
- `03_versioning.py`: Calculates SHA256 hashes for artifacts

## Execution Flow

The main pipeline is orchestrated by `main.py`, which:
1. Sets up data directories
2. Validates data sources
3. Generates teacher ground truth
4. Trains decision trees
5. Evaluates fidelity
6. Runs statistical tests
7. Generates summary reports

## Dependencies

See `code/requirements.txt` for the complete list of dependencies.
