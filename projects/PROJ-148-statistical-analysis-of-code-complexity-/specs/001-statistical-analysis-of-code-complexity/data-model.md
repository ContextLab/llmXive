# Data Model: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Entities

### CodeUnit
Represents a discrete unit of source code (file or function) analyzed.
- **Attributes**: `code_unit_id` (UUID), `project_id` (String), `file_path` (String), `line_count` (Integer).
- **Relation**: Links to `ComplexityMetrics` and `BugLabel`.

### ComplexityMetrics
Represents computed static analysis values.
- **Attributes**: `code_unit_id` (FK), `cyclomatic_complexity` (Float), `lines_of_code` (Integer), `token_count` (Integer), `nesting_depth` (Integer), `halstead_volume` (Float).
- **Constraints**: All numeric fields must be non-negative. Log-transformed if skewness >2 (FR-003).
- **Collinearity Note**: `lines_of_code` and `token_count` are definitionally related (more lines → more tokens). VIF diagnostics will be computed; independent effects will not be claimed for both predictors simultaneously (addressing scientific_soundness-4e992920).

### BugLabel
Represents the binary outcome variable.
- **Attributes**: `code_unit_id` (FK), `is_bug_fix` (Boolean), `source` (String: "commit" or "issue").
- **Constraints**: Derived from commit message parsing and issue tracker linkage (Constitution Principle VII).
- **Temporal Constraint**: Metrics computed on code BEFORE bug-fix commit to ensure predictor independence from outcome.

## Data Flow

1.  **Raw Ingestion**: Download GHTorrent archives to `data/raw/`.
2.  **Extraction**: Parse archives to extract code files and commit metadata → **CodeUnit** entity populated.
3.  **Metric Computation**: Run `lizard` on code files (pre-fix snapshots) → **ComplexityMetrics** entity populated.
4.  **Labeling**: Match commits to files → **BugLabel** entity populated with source attribution (commit/issue).
5.  **Preprocessing**: Impute missing values (<5%), log-transform skewness >2, apply project-level stratification (ALL files from a project in one split) → FR-003, FR-004.
6.  **Model Input**: Join `CodeUnit`, `ComplexityMetrics`, `BugLabel` → `processed/dataset.csv`.
7.  **Output**: Model coefficients, importance scores, evaluation metrics → `data/output/`.

## Schema Contracts

See `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml` for validation rules.

## Privacy & Hygiene

- **PII**: No personally identifying information in `data/`.
- **Checksums**: All files in `data/raw/` and `data/processed/` checksummed in `state/`.
- **Versioning**: Artifacts versioned via content hash (Constitution Principle V).
