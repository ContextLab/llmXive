# Data Model: Systematic Review of Privacy-Preserving Federated Learning Protocols

## Entity Definitions

### Study
A unique publication record containing metadata and extracted quantitative metrics.
- **study_id**: Unique identifier (string, e.g., DOI or arXiv ID).
- **title**: Paper title (string).
- **authors**: List of authors (list of strings).
- **abstract**: Paper abstract (string).
- **pdf_url**: URL to PDF (string).
- **doi**: Digital Object Identifier (string).
- **publication_year**: Year of publication (integer, 2018-2024).
- **mechanism**: Privacy mechanism category (enum: "DP", "SecureAgg", "FHE", "Hybrid").
- **has_baseline**: Boolean indicating if a non-private baseline was reported (boolean).

### Metric
A quantitative outcome variable extracted from a study.
- **study_id**: Foreign key to Study (string).
- **metric_type**: Type of metric (enum: "communication_overhead", "convergence_speed", "accuracy_loss", "computational_cost").
- **value**: Numeric value (float).
- **unit**: Standardized unit (string: "bytes", "rounds", "%", "relative_ratio").
- **has_variance**: Boolean indicating if variance (SD/SE) is reported (boolean).
- **variance_value**: Variance value if reported (float, nullable).
- **parsing_flag**: Flag for parsing errors (enum: "OK", "parsing_error", "missing_baseline").
- **control_value**: Numeric value of the non-private baseline for this metric (float, nullable).
- **control_variance**: Variance of the non-private baseline (float, nullable).

## Data Flow

1. **Raw Data**: `data/raw/literature_metadata.csv` (from API retrieval).
2. **Extracted Data**: `data/processed/extracted_metrics.csv` (from PDF parsing).
3. **Analysis Data**: `data/processed/extracted_metrics.csv` (used for meta-regression).
4. **Output**: `results/results_summary.md` and `results/figures/` (from meta-analysis).

## Data Hygiene

- **Raw Data**: Immutable; checksummed on ingestion.
- **Derived Data**: New files with documented derivations; no in-place modifications.
- **PII**: No personally identifying information in data; authors listed as names only.

## Schema Validation

All data files conform to the schemas defined in `contracts/`:
- `dataset.schema.yaml`: Validates `extracted_metrics.csv`.
- `output.schema.yaml`: Validates `results_summary.md` structure.
