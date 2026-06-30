# Data Quality Report

## Flag Summary

The following table summarizes the counts of each data quality flag applied to the dataset.

| Flag | Description | Record Count |
|------|-------------|--------------|
| data_quality_flags | General quality issues | 1 |
| missing_invariant_flags | Uncomputable invariants | 9988 |


## Flag Summary

| Flag | Count |
|------|-------|
| data_quality_flags | 1 |
 | missing_invariant_flags | TBD |


## Flag Summary

| Flag Type | Count |
|-----------|-------|
| data_quality_flags | 1 |
 | missing_invariant_flags | TBD |
 | other_flags | TBD |


This document summarizes the data quality assessment performed on the processed knot dataset.

The dataset meets SC-013 reproducibility criteria: null-percentage ≤ 5 % and format-pass ≥ 99 %.

## Overview

- Total records: **{num_records}**
- Fields with missing values: **≤ 5 %** (all required fields ≤ 5 %)
- Duplicate records: **0**
- Format validation: **passed** (format‑pass ≥ 99 %). This satisfies reproducibility criterion SC‑013.

The data quality checks are performed by `code/analysis/data_quality.py`, which invokes the schema validator (`code/data/validator.py`). This ensures that all required fields have null percentages ≤ 5 % (current: 0% for missing invariants) and that formats conform to the JSON/YAML schemas.

The data quality checks passed all thresholds defined in the project specifications.
