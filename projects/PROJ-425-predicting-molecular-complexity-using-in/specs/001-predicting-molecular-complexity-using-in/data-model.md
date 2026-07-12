# Data Model: Predicting Molecular Complexity Using Information Theory

## Overview

This document defines the data structures, schemas, and file formats used throughout the project. It ensures strict adherence to the **Single Source of Truth** principle and provides the contracts for the `contracts/` directory.

## Core Entities

### 1. MoleculeRecord
Represents a single chemical compound with computed metrics.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `cid` | `int` | PubChem Compound ID | Dataset |
| `smiles` | `str` | Canonical SMILES string | Dataset (Stored alongside LZ) |
| `shannon_entropy` | `float` | Entropy of vertex degree distribution | Computed |
| `entropy_per_atom` | `float` | Normalized entropy (Entropy / Atom Count) | Computed |
| `atom_count` | `int` | Number of atoms in the molecule | Computed |
| `lz_length` | `int` | Byte length of compressed SMILES | Computed |
| `sa_score` | `float` | Synthetic Accessibility Score (1-10) | RDKit |
| `qed_score` | `float` | Quantitative Estimate of Drug-likeness (0-1) | RDKit |
| `is_valid` | `bool` | Flag indicating if RDKit parsing succeeded | Computed |
| `timed_out` | `bool` | Flag indicating if processing exceeded 60s | Computed |

### 2. CorrelationResult
Represents the statistical outcome of a metric pair comparison.

| Field | Type | Description |
| :--- | :--- | :--- |
| `metric_x` | `str` | Name of the first metric (e.g., "shannon_entropy") |
| `metric_y` | `str` | Name of the second metric (e.g., "sa_score") |
| `pearson_r` | `float` | Correlation coefficient |
| `pearson_p_value` | `float` | Unadjusted p-value (Pearson) |
| `spearman_r` | `float` | Correlation coefficient (Spearman) |
| `spearman_p_value` | `float` | Unadjusted p-value (Spearman) |
| `adjusted_p_value` | `float` | Bonferroni-corrected p-value |
| `ci_lower` | `float` | 95% CI lower bound (bootstrap) |
| `ci_upper` | `float` | 95% CI upper bound (bootstrap) |
| `n` | `int` | Sample size used |
| `partial_r` | `float` | Partial correlation controlling for atom count (optional) |

### 3. BootstrapSample
Represents a single iteration of the resampling process.

| Field | Type | Description |
| :--- | :--- | :--- |
| `iteration_id` | `int` | Unique ID for the iteration (0-999) |
| `metric_pair` | `str` | Identifier for the pair (e.g., "entropy_sa") |
| `correlation` | `float` | Correlation coefficient for this sample |

## File Formats

### Input Data
- **Format**: Parquet
- **Location**: `data/raw/pubchem_subset.parquet`
- **Schema**: `cid` (int64), `smiles` (string)
- **Checksum**: Recorded in `state/`

### Processed Data
- **Format**: CSV
- **Location**: `data/processed/metrics.csv`
- **Schema**: `MoleculeRecord` (includes `smiles` and `lz_length` side-by-side)

### Output Reports
- **Format**: JSON
- **Location**: `reports/stats.json`
- **Schema**: List of `CorrelationResult` objects.

- **Format**: PNG
- **Location**: `reports/figures/`
- **Naming**: `entropy_sa.png`, `entropy_qed.png`, `lz_sa.png`, `lz_qed.png`

## Data Flow

1. **Ingestion**: `data/raw/pubchem_subset.parquet` (Raw)
2. **Transformation**: `code/metrics.py` computes derived fields (with timeout).
3. **Output**: `data/processed/metrics.csv` (Derived)
4. **Analysis**: `code/analysis.py` reads `metrics.csv`, generates `reports/stats.json` and `reports/figures/`.
