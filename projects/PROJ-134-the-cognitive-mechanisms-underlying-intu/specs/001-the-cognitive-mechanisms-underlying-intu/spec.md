# Specification: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

## 1. Introduction

This document defines the requirements for a research pipeline investigating the cognitive mechanisms underlying intuitive moral judgments in virtual environments. The system ingests moral foundations questionnaires (MFQ), moral stories, and VR interaction logs to perform Bayesian modeling and statistical validation.

## 2. Functional Requirements

### FR-001: Data Ingestion
The system shall ingest raw data from OSF and HuggingFace datasets, validating schemas against defined Pydantic models.

### FR-002: Statistical Modeling Engine
The system shall implement Bayesian hierarchical models using **PyMC5 (successor to PyMC3)** to estimate posterior distributions of moral judgment parameters.
*Note: This requirement supersedes any prior mention of PyMC3 in legacy documentation. PyMC5 is the mandated version for all probabilistic programming tasks.*

### FR-003: VR Environment Simulation
The system shall simulate VR interaction logs with perceptual salience conditions (low/high) mapped via Unity blend-shape parameters.

### FR-004: Model Comparison
The system shall compute AIC/WAIC and perform Posterior Predictive Checks (PPC) to compare the Bayesian model against a frequentist baseline.

### FR-005: Sensitivity Analysis
The system shall perform sensitivity analysis on model thresholds (e.g., {2, 10, 20}) to ensure robustness of conclusions.

### FR-006: Real Data Integration
The system shall support a "Real Data Mode" that fetches actual MFQ and VR logs from verified sources (OSF/HuggingFace) and fails loudly if data is unavailable, never falling back to synthetic data.

## 3. User Stories

### US1: Data Ingestion and Preprocessing
As a researcher, I want to ingest MFQ and Moral Stories data, map them to VR salience conditions, and validate the psychometric distribution so that I can ensure data quality before analysis.

### US2: Bayesian Model Execution
As a data scientist, I want to execute the Bayesian model on preprocessed data and compare it against a baseline so that I can quantify the effect of perceptual salience on moral judgments.

### US3: Statistical Validation
As a reviewer, I want to see sensitivity analysis and mixed-effects regression results with Bonferroni correction so that I can verify the robustness of the findings.

### US4: Real Data Acquisition
As an external auditor, I want the system to fetch and process real VR logs from a verified source so that I can validate the simulation against reality.

## 4. Non-Functional Requirements

### NFR-001: Reproducibility
All random seeds must be configurable and recorded. All artifacts must be checksummed.

### NFR-002: Failure Modes
The system must fail loudly (raise exceptions) when real data sources are unreachable or when schema validation fails. Silent fallbacks are prohibited.

## 5. Data Model

Entities include `MFQResponse`, `MoralStory`, `VRInteractionLog`, and `MergedDataset`. Detailed schemas are defined in `code/utils/schema.py`.

## 6. Deviation Log

- **FR-002**: Originally specified PyMC3. Updated to PyMC5 per Plan.md Section "Spec Deviation & Resolution" to utilize modern inference backends and maintain compatibility with current PyTensor versions.