# Architecture Documentation

## Overview
This document describes the architecture of the Agriculture Optimization project.

## Components

### 1. Data Layer
- **Collectors**: Download raw data from external sources (LSMS-ISA, Sentinel-2)
- **Generators**: Synthetic data for CI/CD validation only
- **Processing**: Feature engineering, spatial joins, aggregation

### 2. Analysis Layer
- **Regression Models**: Multivariate analysis with robust standard errors
- **Sensitivity Analysis**: Threshold sweeps and stability checks

### 3. Service Layer
- **Report Generation**: PDF/HTML report creation
- **Validation**: Schema enforcement and data quality checks

### 4. CLI Layer
- **Pipeline Orchestration**: End-to-end execution
- **Validation Tools**: Schema and data integrity checks

## Data Flow
Raw Data → Collectors → Processing → Analysis → Reports

## Configuration
- `config/constants.py`: Global constants and paths
- `config/schemas.py`: Pydantic models for validation
- `contracts/*.yaml`: Schema definitions for data contracts
