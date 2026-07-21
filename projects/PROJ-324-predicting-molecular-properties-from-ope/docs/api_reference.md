# API Reference

This document describes the public API of the `code/` modules.

## `code/data/download.py`

**Purpose**: Fetch experimental data from ChEMBL and MoleculeNet.

- `fetch_chembl_data()`: Downloads data from ChEMBL.
- `fetch_molecule_net_data()`: Downloads data from MoleculeNet (thermodynamics subset).
- `create_dataset_metadata()`: Generates `dataset_metadata.json` with runtime schema checks.

## `code/data/preprocess.py`

**Purpose**: Clean, filter, and split the dataset.

- `handle_missing_values()`: Drops missing targets, flags missing covariates.
- `maxmin_sampling()`: Selects a diverse subset (Tanimoto < 0.7).
- `tanimoto_similarity()`: Computes Tanimoto similarity for MaxMin.

## `code/data/fingerprints.py`

**Purpose**: Generate Open Babel fingerprints.

- `smiles_to_obabel_fingerprint(smiles, fp_type)`: Generates a fingerprint for a single molecule.
- `generate_fingerprints_batch()`: Batch processing with timeout and retry logic.

## `code/models/baseline.py`

**Purpose**: Compute Crippen's additive model predictions.

- `compute_crippen_contributions(smiles)`: Returns predicted logP, solubility, boiling point.

## `code/models/random_forest.py`

**Purpose**: Train and evaluate Random Forest models.

- `run_nested_cross_validation()`: Performs nested CV for hyperparameter tuning.
- `train_final_model()`: Trains the final model on the full training set.

## `code/analysis/stats.py`

**Purpose**: Statistical analysis and reporting.

- `perform_wilcoxon_test(errors_baseline, errors_rf)`: Paired Wilcoxon signed-rank test.
- `generate_validation_protocol_summary()`: Creates the validation report.

## `code/analysis/explainability.py`

**Purpose**: SHAP analysis and substructure mapping.

- `calculate_shap_interactions()`: Computes SHAP interaction values.
- `map_bits_to_substructures(bits)`: Maps fingerprint bits to chemical substructures.
- `generate_conformational_limitation_report()`: Identifies 3D failure cases.
