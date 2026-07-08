# Data Model: Exploring the Relationship Between Code Complexity Metrics and Bug Prediction Accuracy

## Overview

This document defines the data structures used throughout the project, ensuring consistency between ingestion, analysis, and modeling phases. The data model supports the requirements of FR-001 through FR-007.

## Entities

### 1. CodeFile

Represents a single Java source file with its computed metrics and bug label.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `file_id` | `string` | Unique identifier (e.g., `project_name/bug_id/path/to/File.java`) | Primary Key, Unique |
| `project_name` | `string` | Name of the Defects4J project | Not Null |
| `bug_id` | `string` | Identifier of the specific bug instance (e.g., `Lang-1`) | Not Null |
| `file_path` | `string` | Relative path within the project | Not Null |
| `cyclomatic_complexity` | `float` | CC metric value | ≥ 1.0, Not Null |
| `halstead_volume` | `float` | HV metric value | ≥ 0.0, Not Null |
| `lines_of_code` | `int` | LOC metric value | ≥ 1, Not Null |
| `is_buggy` | `int` | Binary label (1=buggy, 0=clean) | ∈ {0, 1}, Not Null |
| `commit_hash` | `string` | Hash of the commit where the bug was introduced (buggy revision) | Not Null |
| `exclusion_reason` | `string` | Reason for exclusion (if applicable) | Nullable |
| `vif_score` | `float` | Variance Inflation Factor score (if applicable) | Nullable |

### 2. ProjectSubset

Metadata about the selected subset of projects.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `project_name` | `string` | Name of the project | Primary Key |
| `total_files` | `int` | Total number of Java files analyzed | ≥ 0 |
| `buggy_files` | `int` | Number of files labeled as buggy | ≥ 0 |
| `clean_files` | `int` | Number of files labeled as clean | ≥ 0 |
| `bug_density` | `float` | Ratio of buggy files to total files | 0.0 ≤ x ≤ 1.0 |

### 3. ModelPerformance

Results from the cross-validation and statistical tests.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `model_type` | `string` | e.g., "LogisticRegression", "RandomForest" | Not Null |
| `metric_set` | `string` | "Full" or "Single_Best" | Not Null |
| `roc_auc_mean` | `float` | Mean ROC-AUC across folds | 0.0 ≤ x ≤ 1.0 |
| `roc_auc_std` | `float` | Standard deviation of ROC-AUC | ≥ 0.0 |
| `f1_mean` | `float` | Mean F1-score | 0.0 ≤ x ≤ 1.0 |
| `f1_std` | `float` | Standard deviation of F1-score | ≥ 0.0 |
| `p_value` | `float` | P-value from permutation test (if applicable) | 0.0 ≤ x ≤ 1.0 |

## Data Flow

1. **Ingestion**: Raw Java files → `CodeFile` (raw metrics).
2. **Labeling**: `CodeFile` + Defects4J Bug Info → `CodeFile` (labeled).
3. **Aggregation**: `CodeFile` (labeled) → `ProjectSubset` (summary stats).
4. **Analysis**: `CodeFile` (labeled) → Correlation Table (with VIF).
5. **Modeling**: `CodeFile` (labeled) → `ModelPerformance`.

## Constraints & Validation

- **Data Integrity**: No file can have `is_buggy` = 1 without a corresponding `commit_hash` (buggy revision).
- **Metric Validity**: `cyclomatic_complexity` must be ≥ 1.0 for valid Java code.
- **Immutability**: Raw data files are never modified; derived files (e.g., `features.csv`) are new versions.
- **Labeling Logic**: `is_buggy` is derived from the canonical bug file list of the buggy revision, not the fix commit.