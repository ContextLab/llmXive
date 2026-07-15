# Data Model: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

## Overview

This document defines the data structures used for storing, processing, and validating D-coefficient measurements and meta-analysis results. The model ensures strict adherence to the project constitution's "Data Hygiene" and "Single Source of Truth" principles.

## Entity Definitions

### 1. Nucleus
Represents a specific atomic nucleus being analyzed.
- **Attributes**:
  - `name`: String (e.g., "6He", "19Ne")
  - `mass_number`: Integer
  - `experimental_conditions`: String (optional, e.g., "cold atoms", "trapped ions")

### 2. DMeasurement
Represents a single published measurement of the D-coefficient.
- **Attributes**:
  - `nucleus`: String (Foreign Key to Nucleus)
  - `value`: Float (The reported D-coefficient)
  - `uncertainty`: Float (The reported standard error)
  - `source_experiment`: String (Name of the experiment)
  - `reference_id`: String (Citation or DOI)
  - `retrieval_status`: String ("success", "failed", "range_inferred")

### 3. MetaAnalysisResult
Represents the aggregated statistical output for a nucleus.
- **Attributes**:
  - `nucleus`: String
  - `weighted_average`: Float
  - `combined_uncertainty`: Float
  - `p_value_heterogeneity`: Float (from Cochran's Q)
 - `d_upper_bound_95`: Float (One-sided [deferred] CL)
  - `n_measurements`: Integer
  - `is_consistent`: Boolean (True if p > 0.05)
  - `sensitivity_limit`: Float (Standard error of weighted mean)

### 4. ValidationResult
Represents the comparison against PDG limits.
- **Attributes**:
  - `nucleus`: String
  - `project_upper_bound`: Float
  - `pdg_upper_bound`: Float
  - `is_tighter`: Boolean (True if project bound < PDG bound)
  - `status`: String ("tighter", "looser", "equivalent")

## File Formats

### Raw Data (data/raw/)
- **Format**: CSV
- **Naming**: `raw_{nucleus}_{timestamp}.csv`
- **Schema**: Matches `DMeasurement` but includes raw source columns.

### Derived Data (data/derived/)
- **Format**: CSV
- **Naming**: `derived_meta_analysis_{nucleus}.csv`
- **Schema**: Matches `MetaAnalysisResult`.

### Checksums
- **Format**: Text
- **Location**: `data/checksums.txt`
- **Content**: `sha256sum <filename>` for all files in `data/`.

## Data Flow

1. **Ingestion**: `data_retrieval.py` fetches data from NNDC (or mock data for testing) and writes to `data/raw/`.
2. **Harmonization**: `data_retrieval.py` cleans data (handles ranges, missing values) and writes to `data/derived/harmonized.csv`.
3. **Analysis**: `meta_analysis.py` reads `harmonized.csv`, computes statistics, and writes to `data/derived/meta_results.csv`.
4. **Validation**: `validation.py` reads `meta_results.csv` and PDG data, writes to `data/derived/validation_results.csv`.
5. **Reporting**: `main.py` reads all derived files and generates `paper/results.md`.
