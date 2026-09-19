# Specification: Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data

## 1. Introduction

This document defines the requirements for a pipeline that ingests genomic and environmental data to predict plant disease susceptibility.

## 2. Functional Requirements

### FR-001: Data Ingestion
The system must ingest raw sequencing reads from NCBI SRA and environmental metadata from ERA5/NOAA.

### FR-002: Data Alignment
The system must align reads to reference genomes and call variants using minimap2 and bcftools.

### FR-003: Feature Merging
The system must merge genomic variant vectors with environmental data using spatial proximity (50km).

### FR-004: Imputation Strategy
The system must handle missing values in the merged feature matrix using **k-Nearest Neighbors (k-NN) imputation**.
- **Implementation**: Use `sklearn.impute.KNNImputer` with `n_neighbors=5`.
- **Constraint**: This method is mandated by Constitution Principle VI to ensure deterministic and reproducible imputation, replacing previous mentions of missForest or MICE.
- **Condition**: Imputation is only applied to samples that pass the spatial filtering step (i.e., have environmental neighbors within 50km).
- **Output**: The final feature matrix must contain zero missing values.

### FR-005: Model Training
The system must train Random Forest and SVM models using a stratified split (majority for training).

### FR-006: Model Evaluation
The system must evaluate models using AUC-ROC with 95% confidence intervals and Precision-Recall curves.

### FR-007: Permutation Testing
The system must perform permutation tests with 1000 permutations and a fixed seed of 42.

## 3. User Stories

### US1: Data Integration and Preprocessing Pipeline (MVP)

**As a** researcher,
**I want** to ingest, align, merge, and impute genomic and environmental data,
**So that** I have a clean, complete feature matrix for modeling.

**Acceptance Scenarios:**

1. **Scenario: Successful Ingestion and Alignment**
 - **Given** the feasibility gate has passed (T001c),
 - **When** the pipeline runs on a set of valid SRA samples,
 - **Then** `data/processed/feature_matrix.csv` is generated with columns for SNP frequencies and environmental variables.

2. **Scenario: Imputation of Missing Values**
 - **Given** a merged feature matrix with missing environmental or genomic values,
 - **When** the imputation step (FR-004) is executed,
 - **Then** the system applies **k-NN imputation** (n_neighbors=5) to fill missing values.
 - **And** the resulting matrix has **zero** missing values.
 - **And** samples excluded due to lack of environmental neighbors (outside 50km) are removed prior to imputation.

3. **Scenario: Spatial Exclusion**
 - **Given** a sample with no environmental data points within 50km,
 - **When** the merging step runs,
 - **Then** the sample is excluded from the final dataset and logged as a warning.

### US2: Model Training and Performance Evaluation

**As a** data scientist,
**I want** to train and evaluate predictive models,
**So that** I can identify key genomic and environmental predictors of disease.

**Acceptance Scenarios:**
1. Models are trained on the reduced feature matrix.
2. Performance metrics (AUC-ROC, PR curves) are saved to `data/processed/model_performance.json`.

### US3: Statistical Validation

**As a** reviewer,
**I want** to validate model significance via permutation tests,
**So that** I can trust the predictive power is not due to chance.

**Acceptance Scenarios:**
1. Permutation tests yield a p-value and significance status in `data/processed/validation_report.json`.

## 4. Data Models

- **Sample**: Represents a biological sample with species, location, and disease status.
- **Feature**: Represents a genomic variant or environmental variable.
- **ModelOutput**: Stores performance metrics and feature importance.

## 5. Constraints

- No synthetic data fallbacks allowed for ingestion tasks.
- Imputation must use k-NN (FR-004).
- Permutation test seed must be 42 (FR-007).
- All file paths must be relative to the project root.