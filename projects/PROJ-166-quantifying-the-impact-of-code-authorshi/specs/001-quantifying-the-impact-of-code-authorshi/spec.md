# Specification: Quantifying the Impact of Code Authorship Diversity on Software Security

## 1. Introduction

This document defines the functional and non-functional requirements for the research pipeline
designed to quantify the relationship between code authorship diversity and software security
vulnerabilities.

## 2. Functional Requirements

### FR-001: Data Ingestion
The system must ingest a target list of public GitHub repositories and retrieve their commit history.

### FR-002: Data Matching
The system must match GitHub repositories to NVD CVE records using exact URL matching.
Ambiguous matches must be logged and excluded.

### FR-003: Metric Calculation
The system must calculate `unique_authors` and `kloc` (thousands of lines of code) for each repository.

### FR-004: Statistical Modeling
The system must fit a multivariate Negative Binomial GLM to predict vulnerability counts (`cve_count`).

**Predictors**:
- `author_count` (primary variable of interest)
- Control variables: `project_age`, `primary_language` (one-hot encoded), `release_count`.

**Size Adjustment (Spec Amendment)**:
Per Plan.md 'Complexity Tracking' and the need to avoid bias in the size-CVE slope,
`log(kloc)` is explicitly allowed and required as a **free predictor** (covariate) in the model formula,
rather than an offset.

**Formula**:
`cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)`

**Note**: "Per Plan.md, log(kloc) is used as a covariate to avoid bias in the size-CVE slope."

### FR-005: Robustness Checks
The system must perform subsampling by language and alternative metric analysis (Shannon Entropy).

### FR-006: Multiple Testing Correction
The system must apply a single Benjamini-Hochberg correction to all raw p-values generated
across the main model and robustness checks.

### FR-007: Output Generation
The system must output results in JSON format containing coefficients, standard errors, p-values,
and confidence intervals.

## 3. Non-Functional Requirements

### SC-001: Performance
The pipeline must process ≥500 repositories within 6 hours on standard CI hardware.

### SC-002: Data Integrity
The system must use real data sources (GitHub API, NVD). No synthetic data fabrication is permitted.

### SC-003: Reproducibility
All random seeds must be fixed, and the pipeline must be deterministic given the same input data.

## 4. Data Model

See `data-model.md` for entity definitions.

## 5. API Contracts

See `contracts/` directory for input/output schema definitions.