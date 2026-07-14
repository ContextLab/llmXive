# Data Model Design Document

## Overview

This document defines the data model for the statistical analysis of code complexity and bug prediction pipeline. It describes the schema, data types, relationships, and constraints for all datasets used throughout the research workflow.

## Data Flow

The pipeline processes data through the following stages:

1. **Raw Data**: Downloaded Java projects from GHTorrent
2. **Extracted Metrics**: Code complexity metrics from lizard
3. **Labeled Data**: Bug-fix annotations based on commit messages
4. **Preprocessed Data**: Cleaned, transformed, and imputed dataset
5. **Train/Test Splits**: Stratified dataset splits for modeling
6. **Model Outputs**: Predictions and feature importance rankings

## Core Entities

### CodeUnit

Represents an individual function or method within a Java source file.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `unit_id` | string | Unique identifier for the code unit | Primary key, format: `{project_id}_{file_path}_{function_name}` |
| `project_id` | string | Identifier for the source project | Not null, foreign key to Project |
| `file_path` | string | Relative path within the project repository | Not null |
| `function_name` | string | Name of the function/method | Not null |
| `start_line` | integer | Starting line number in source file | Not null, > 0 |
| `end_line` | integer | Ending line number in source file | Not null, >= start_line |
| `commit_hash` | string | Git commit hash where this unit was last modified | Not null |

### ComplexityMetrics

Stores computed complexity metrics for each code unit.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `unit_id` | string | Reference to CodeUnit | Primary key, foreign key |
| `cyclomatic_complexity` | float | McCabe cyclomatic complexity | >= 1 |
| `lines_of_code` | integer | Number of lines in the function | >= 1 |
| `token_count` | integer | Total number of tokens | >= 1 |
| `nesting_depth` | integer | Maximum nesting depth | >= 0 |
| `halstead_volume` | float | Halstead program volume | >= 0 |
| `parameter_count` | integer | Number of function parameters | >= 0 |
| `blank_lines` | integer | Number of blank lines | >= 0 |

### BugLabel

Binary annotation indicating whether a code unit is associated with a bug fix.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `unit_id` | string | Reference to CodeUnit | Primary key, foreign key |
| `is_bug_fix` | boolean | Whether the unit is part of a bug fix | Required |
| `confidence_score` | float | Reliability score of the label (0-1) | 0.0 <= score <= 1.0 |
| `label_source` | string | Method used to derive the label | Enum: 'commit_message', 'issue_id', 'pattern' |
| `validation_passed` | boolean | Whether the label passed contract validation | Required |

### Project

Metadata about each source project in the dataset.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `project_id` | string | Unique project identifier | Primary key |
| `repository_url` | string | GHTorrent repository URL | Not null, unique |
| `owner` | string | GitHub owner/organization | Not null |
| `name` | string | Repository name | Not null |
| `download_date` | timestamp | When the project was downloaded | Not null |
| `total_commits` | integer | Number of commits processed | >= 0 |
| `total_files` | integer | Number of Java files extracted | >= 0 |

## Derived Datasets

### RawMetricsDataset

Combined view of CodeUnit and ComplexityMetrics before preprocessing.

**Location**: `data/raw/metrics.csv`

**Schema**: All fields from CodeUnit + ComplexityMetrics

**Constraints**:
- No missing values in `unit_id`, `project_id`, `cyclomatic_complexity`
- All numeric metrics must be non-negative (except where specified)
- Duplicate `unit_id` entries are not allowed

### LabeledDataset

Raw metrics joined with bug labels.

**Location**: `data/raw/labeled_metrics.csv`

**Schema**: RawMetricsDataset + BugLabel fields

**Constraints**:
- Every `unit_id` must have exactly one bug label
- `confidence_score` >= 0.85 for labels to be considered reliable
- At least 85% of labels must pass validation

### PreprocessedDataset

Cleaned and transformed dataset ready for modeling.

**Location**: `data/processed/preprocessed_data.csv`

**Schema**:
- All numeric metrics log-transformed if skewness > 2
- Missing values < 5% imputed with median
- Rows with > 5% missing values removed
- Outliers capped at 99th percentile

**Constraints**:
- No missing values allowed
- All numeric columns must be finite (no inf/nan)
- `bug_label` column is binary (0 or 1)

### TrainTestSplits

Stratified split of the preprocessed dataset.

**Locations**:
- Train: `data/splits/train.csv` (70%)
- Test: `data/splits/test.csv` (30%)

**Constraints**:
- Project-level stratification: each project appears in exactly one split
- Bug label distribution preserved within ±5% across splits
- No overlap between train and test sets

## Data Validation Rules

### Schema Validation

All datasets must conform to their defined schemas. Validation is performed using the contract schemas defined in `contracts/`.

### Quality Checks

1. **Completeness**: Required fields must not be null
2. **Uniqueness**: Primary keys must be unique
3. **Range**: Numeric fields must be within valid ranges
4. **Referential Integrity**: Foreign keys must reference existing records
5. **Distribution**: Class imbalance should not exceed 90:10 ratio

### Bug Label Reliability

- Labels derived from commit messages containing "fix", "bug", "issue" keywords
- Cross-referenced with issue tracker IDs when available
- Minimum precision threshold: 85% (enforced in pipeline)

## File Formats

### CSV Specifications

All CSV files use:
- UTF-8 encoding
- Comma delimiter
- No quoting unless necessary
- Unix line endings (LF)
- Header row included

### Parquet (Future)

For large datasets, Parquet format may be used for:
- `data/raw/metrics.parquet`
- `data/processed/preprocessed_data.parquet`

## Versioning

Dataset versions follow semantic versioning:
- MAJOR: Breaking schema changes
- MINOR: New columns, backward compatible
- PATCH: Bug fixes, data corrections

Version metadata is stored in:
- `data/metadata/version.json`
- Each dataset file includes a `version` column

## Security Considerations

- All downloaded archives are checksum-verified before extraction
- Sensitive information (if any) is stripped during preprocessing
- Data access is read-only for analysis scripts

## Future Extensions

Potential additions for future versions:
- Code churn metrics (lines added/removed per commit)
- Developer metadata (author experience, contribution frequency)
- Temporal features (time since last modification, release cycle phase)
- Cross-file complexity metrics (coupling, cohesion)