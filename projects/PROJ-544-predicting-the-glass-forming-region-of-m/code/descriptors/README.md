# Descriptors Module

This directory contains code for computing thermodynamic descriptors from alloy
compositions.

## Purpose

Compute atomic size mismatch, mixing enthalpy, and electronegativity variance
from elemental stoichiometries as specified in User Story 1.

## Key Files

- `validate_elements.py`: Validate elemental symbols against pymatgen periodic table
- `compute.py`: Calculate descriptor vectors
- `utils.py`: Utility functions with fallback logic
- `check_imbalance.py`: Check for class imbalance in datasets
- `vif_report.py`: Compute Variance Inflation Factor for descriptors
- `vif_filter.py`: Filter descriptors based on VIF scores

## Output Files

- `data/derived/valid_elements.csv`: Validated elemental compositions
- `data/derived/invalid_elements.csv`: Invalid elemental compositions
- `data/derived/descriptor_vector.csv`: Computed descriptor vectors
- `data/derived/descriptor_vector_errors.csv`: Error-flagged rows
- `data/derived/imbalance_report.json`: Class imbalance analysis
- `data/derived/vif_report.json`: VIF scores for each descriptor
- `data/derived/descriptor_vector_vif_filtered.csv`: VIF-filtered descriptors

## References

- FR-001: Robust error handling for invalid inputs
- FR-002: Validate all elemental symbols before descriptor computation
- SC-002: Verify descriptor accuracy against benchmark values
