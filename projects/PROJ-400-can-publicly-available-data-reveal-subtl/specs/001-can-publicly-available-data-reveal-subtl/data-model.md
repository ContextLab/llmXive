# Data Model: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Overview

This document defines the data structures used to ingest, process, and analyze beta decay archival data. The model supports the cross-modal fusion of momentum spectra and polarization asymmetry coefficients.

## Entities

### 1. Nucleus
Represents a specific atomic nucleus under analysis.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Nucleus identifier (e.g., "6He", "19Ne"). |
| `mass_number` | `int` | Mass number (A). |
| `atomic_number` | `int` | Atomic number (Z). |
| `experimental_conditions` | `dict` | Metadata: temperature, source type, detector geometry. |

### 2. RawObservable
Represents a single measurement from an experiment.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier (e.g., "ENSDF-6He-Exp1"). |
| `nucleus_id` | `str` | Foreign key to `Nucleus`. |
| `modality_type` | `str` | Enum: `"momentum_spectrum"`, `"polarization_asymmetry"`. |
| `source_experiment` | `str` | Author/Year of the measurement. |
| `reference_id` | `str` | ENSDF record ID or DOI. |
| `values` | `list[float]` | Binned values (counts or asymmetry). |
| `uncertainties` | `list[float]` | Corresponding uncertainties. |
| `bins` | `list[float]` | Bin edges or centers. |
| `is_valid_for_fusion` | `bool` | Flag: `True` if granular enough; `False` if only aggregates. |

### 3. FusionResult
The output of the statistical analysis for a specific nucleus.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `nucleus_id` | `str` | Target nucleus. |
| `d_coefficient_estimate` | `float` | Derived D-coefficient. |
| `p_value_null` | `float` | Permutation test p-value. |
| `d_upper_bound_95` | `float` | 95% CI upper bound on $|D|$. |
| `sensitivity_limit` | `float` | Standard error of the weighted mean. |
| `pdg_limit_2024` | `float` | World average limit from PDG. |
| `comparison_status` | `str` | Enum: `"tighter"`, `"looser"`, `"inconclusive"`. |

## Data Flow

1.  **Ingestion**: `fetch_ensdf.py` reads raw text/XML from NNDC.
2.  **Validation**: `validate_data.py` checks `is_valid_for_fusion`.
3.  **Processing**: `preprocess.py` aligns bins and normalizes values.
4.  **Analysis**: `fusion.py` and `permutation.py` generate `FusionResult`.
5.  **Output**: Results serialized to `data/processed/results.json` and `data/processed/summary.csv`.

## Storage Format

- **Raw Data**: `data/raw/{nucleus}_ensdf.txt` (Original download).
- **Processed Data**: `data/processed/{nucleus}_harmonized.parquet` (Pandas DataFrame).
- **Results**: `data/processed/fusion_results.json` (JSON array of `FusionResult` objects).
