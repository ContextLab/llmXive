# Data Model: Predicting Molecular Complexity Using Information Theory

## Overview

This document defines the data structures, schemas, and file formats used throughout the project. The data model supports the pipeline from raw dataset download to final statistical reporting.

## Entities

### 1. MoleculeRecord

Represents a single chemical compound with computed metrics.

| Attribute | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `cid` | `int` | PubChem Compound ID | Dataset |
| `smiles` | `str` | Canonical SMILES string | Dataset |
| `shannon_entropy` | `float` | Shannon entropy of vertex degree distribution | Computed |
| `lzma_length` | `int` | Compressed byte count of SMILES (using `lzma`) | Computed |
| `sa_score` | `float` | Synthetic Accessibility Score (1-10) | Computed (RDKit) |
| `qed_score` | `float` | Quantitative Estimate of Drug-likeness (0-1) | Computed (RDKit) |
| `mw` | `float` | Molecular Weight | Computed (RDKit, for control analysis) |
| `atom_count` | `int` | Total number of atoms | Computed (RDKit, for control analysis) |
| `is_valid` | `bool` | Whether the molecule was successfully processed | Runtime |
| `error_reason` | `str` | Error message if invalid | Runtime |
| `rdkit_version` | `str` | RDKit version used for canonicalization | Runtime |

### 2. CorrelationResult

Represents the statistical relationship between two metrics.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `metric_pair` | `str` | Identifier (e.g., "entropy_sa") |
| `pearson_r` | `float` | Pearson correlation coefficient |
| `spearman_rho` | `float` | Spearman rank correlation coefficient |
| `p_value` | `float` | Raw p-value (Pearson) |
| `adjusted_p_value` | `float` | Bonferroni-adjusted p-value |
| `ci_lower` | `float` | Lower bound of 95% CI (bootstrap) |
| `ci_upper` | `float` | Upper bound of 95% CI (bootstrap) |
| `n` | `int` | Sample size used |
| `partial_r` | `float` | Partial correlation (controlling for MW, Atom Count) |
| `partial_p_value` | `float` | P-value for partial correlation |

### 3. BootstrapSample

Represents a single iteration of resampling.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `iteration_id` | `int` | Iteration number (0–999) |
| `metric_pair` | `str` | Identifier |
| `resampled_correlation` | `float` | Correlation for this iteration |

## File Formats

### Raw Data (`data/raw/`)
- **Format**: Parquet (from HuggingFace)
- **Content**: `cid`, `smiles`, other raw fields.
- **Schema**: Defined by the source dataset.

### Processed Metrics (`data/processed/metrics.csv`)
- **Format**: CSV
- **Content**: `MoleculeRecord` table.
- **Headers**: `cid,smiles,shannon_entropy,lzma_length,sa_score,qed_score,mw,atom_count,is_valid,error_reason,rdkit_version`

### Correlation Results (`data/processed/correlations.csv`)
- **Format**: CSV
- **Content**: `CorrelationResult` table.
- **Headers**: `metric_pair,pearson_r,spearman_rho,p_value,adjusted_p_value,ci_lower,ci_upper,n,partial_r,partial_p_value`

### Bootstrap Data (`data/processed/bootstrap.pkl`)
- **Format**: Pickle (or JSON for portability)
- **Content**: List of `BootstrapSample` objects.

### Final Report (`reports/analysis_report.html`)
- **Format**: HTML
- **Content**: Statistical tables, scatter plots, and narrative.