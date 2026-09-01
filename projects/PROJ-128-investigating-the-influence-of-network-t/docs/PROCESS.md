# Implementation Process Guide

## Overview

This document outlines the step-by-step process for implementing, testing, and validating the research pipeline for "Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns."

## Phase 1: Setup

1. **Create Directory Structure**:
 - `code/`, `data/`, `contracts/`, `tests/`, `docs/`.
2. **Install Dependencies**:
 - Pin versions in `requirements.txt`.
3. **Configure Tools**:
 - Set up linting (flake8/pylint) and formatting (black).

## Phase 2: Foundational

1. **Configuration**:
 - Define hyperparameters in `code/config.py`.
2. **Data Loading**:
 - Implement `code/preprocess/loader.py` for HCP data.
3. **Skeleton Modules**:
 - Create empty or minimal implementations for all pipeline modules.
4. **Schema Definition**:
 - Define `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.

## Phase 3: User Story 1 (MVP)

1. **Structural Metrics**:
 - Implement graph metric calculation in `code/preprocess/structural.py`.
2. **LOO K-Means**:
 - Implement centroid generation and state assignment in `code/preprocess/functional.py`.
3. **Dynamic Metrics**:
 - Calculate dwell time and visited states.
4. **Batch Processing**:
 - Aggregate metrics in `code/main.py`.
5. **Testing**:
 - Run unit and integration tests.

## Phase 4: User Story 2 (Correlation)

1. **Normality Testing**:
 - Implement Shapiro-Wilk test.
2. **Correlation Calculation**:
 - Compute Pearson/Spearman correlations.
3. **FDR Correction**:
 - Apply Benjamini-Hochberg procedure.
4. **Reporting**:
 - Generate `data/processed/correlation_results.csv`.

## Phase 5: User Story 3 (Robustness)

1. **Sensitivity Analysis**:
 - Vary window length and density threshold.
2. **Resource Monitoring**:
 - Track RAM and runtime.
3. **Final Report**:
 - Generate report with associational framing and sensitivity tables.

## Phase 6: Validation

1. **Quickstart Validation**:
 - Run `code/validate_quickstart.py`.
2. **Language Audit**:
 - Scan reports for causal language.
3. **Schema Validation**:
 - Ensure all outputs match `contracts/output.schema.yaml`.

## Best Practices

- **Fail Loudly**: Never use synthetic data as a fallback.
- **CPU Only**: Ensure no GPU calls are made.
- **Associational Language**: Avoid causal claims in all outputs.
- **Modularity**: Keep components independent for easier testing.
- **Documentation**: Update `docs/` as features are implemented.
