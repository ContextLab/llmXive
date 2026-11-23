# Specification: Assessing Uncertainty Quantification Techniques for Machine-Predicted Material Properties

## Overview
This project assesses the reliability of uncertainty quantification (UQ) techniques applied to machine learning models predicting material properties, specifically formation energy. The system evaluates Deep Ensembles, MC Dropout, and Sparse Gaussian Processes against a baseline FFNN.

## Functional Requirements

### FR-001: Data Acquisition
The system MUST download and parse the **OQMD (Open Quantum Materials Database)** dataset to extract compositional features and available structural descriptors (e.g., atomic radius mean, packing fraction if present). The system must handle missing structural descriptors gracefully by proceeding with compositional features only and logging a warning.

### FR-002: Feature Engineering
The system MUST extract compositional features (e.g., mean atomic radius, electronegativity variance) from the OQMD dataset. If structural descriptors are available, they must be included.

### FR-003: Model Training
The system MUST train a baseline Fully Connected Neural Network (FFNN) with heteroscedastic output head on the processed dataset.

### FR-004: Uncertainty Quantification
The system MUST implement and apply three UQ techniques:
1. Deep Ensembles (5 models)
2. MC Dropout (30 stochastic passes)
3. Sparse Gaussian Processes (500 inducing points)

### FR-005: Calibration Evaluation
The system MUST calculate Expected Calibration Error (ECE) and Interval Score for all methods to assess reliability.

### FR-006: Screening
The system MUST demonstrate the utility of UQ in a downstream screening task (perovskite stability) by comparing UQ-based filtering against point-prediction baselines.

### FR-007: Statistical Validation
The system MUST perform McNemar's test to validate the statistical significance of precision gains in the screening task.

## User Stories

### US1: Baseline Model Training and UQ Application
As a researcher, I want to train a baseline model and apply UQ techniques so that I can generate predictions with uncertainty estimates.
**Acceptance Criteria**:
- System downloads OQMD dataset.
- System trains baseline FFNN and 5 ensemble members.
- System generates predictions with variance estimates for Deep Ensembles, MC Dropout, and Sparse GP.
- Output CSV contains: `sample_id`, `method`, `prediction`, `variance`, `lower_50`, `upper_50`, `lower_90`, `upper_90`.

### US2: Calibration and Reliability Evaluation
As a researcher, I want to evaluate the calibration of the UQ methods so that I can rank them by reliability.
**Acceptance Criteria**:
- System calculates ECE and Interval Score.
- System generates reliability diagrams.
- System ranks methods by ECE.
- System calculates Coefficient of Variation (CV) for ECE across 3 seeds.

### US3: Downstream Screening Case Study
As a materials scientist, I want to use UQ-based screening to identify stable candidates so that I can improve precision over point-prediction baselines.
**Acceptance Criteria**:
- System calculates threshold for target recall.
- System filters candidates using narrow confidence intervals.
- System compares UQ screening vs point-prediction baseline.
- System performs McNemar's test.

## Non-Functional Requirements

### NFR-001: Reproducibility
All experiments must be run with a fixed random seed (default 42) and recorded in the logs.

### NFR-002: Performance
The entire pipeline must complete within 5 hours on a standard CPU instance.

### NFR-003: Robustness
The system must handle missing data or structural descriptors gracefully without crashing, logging warnings instead.

## Data Sources
- **OQMD (Open Quantum Materials Database)**: Accessed via HuggingFace `jablonkagroup/oqmd` dataset.
- **Target Variable**: `formation_energy_per_atom` (eV).