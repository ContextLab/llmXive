# Specification: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

## Overview
This project assesses the validity of statistical power claims in pre-registered studies by comparing planned power against sensitivity power calculated from actual sample sizes.

## Functional Requirements

### FR-001: Data Extraction
The system shall extract planned power, target sample size (N), and assumed effect size from pre-registration documents via the OSF API.

### FR-002: Data Retrieval
The system shall retrieve actual sample sizes and observed effect sizes from linked data repositories.

### FR-003: Power Calculation
The system shall calculate sensitivity power using `statsmodels` with a hardcoded alpha of 0.05.

### FR-004: Power Gap
The system shall compute the `power_gap` as `planned_power - sensitivity_power`.

### FR-005: Regression Analysis
The system shall perform multiple linear regression to identify predictors of power gap.
**Narrowed Constraint**: Exclude `sample_size_category` to avoid mathematical coupling.

### FR-006: VIF Diagnostics
The system shall calculate Variance Inflation Factors (VIF) for all predictors and flag if > 5.0.

### FR-007: Associational Framing
The system shall explicitly frame results as associational, avoiding causal claims.

## System Constraints

- **SC-001**: Statistical methods must be CPU-tractable.
- **SC-003**: VIF threshold is 5.0.
- **SC-004**: Minimum sample size for regression is 30 studies.
- **SC-005**: Power calculations must be verified against `statsmodels` baselines.

## Data Contracts
See `specs/contracts/study_record.schema.yaml` for the expected JSON schema of extracted records.
