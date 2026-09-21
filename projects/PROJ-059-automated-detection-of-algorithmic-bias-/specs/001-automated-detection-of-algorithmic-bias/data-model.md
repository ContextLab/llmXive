# Data Model: Automated Detection of Algorithmic Bias in Public Code Repositories

## 1. Overview

This document defines the data structures, schemas, and relationships for the bias detection pipeline. All data is stored in `data/` and referenced via the state file `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml`.

## 2. Entities

### 2.1 Repository
- **Description**: A single Python project analyzed by the pipeline.
- **Attributes**: `repo_id` (hash), `url`, `file_count`, `python_file_count`, `status` (success, error, no_python).

### 2.2 Textual Artifact
- **Description**: A normalized token extracted from a repository file.
- **Attributes**: `repo_id`, `file_path`, `token`, `token_type` (variable, function, comment), `sentiment_score` (VADER), `lexicon_match` (bool).

### 2.3 Bias Score
- **Description**: Aggregated bias metric for a repository.
- **Attributes**: `repo_id`, `demographic_term_count`, `avg_sentiment_compound`, `textual_bias_score` (composite).

### 2.4 Synthetic Dataset
- **Description**: Generated data for fairness simulation.
- **Attributes**: `repo_id` (link), `n_samples`, `class_imbalance_rate`, `injected_skew_magnitude`, `seed`.

### 2.5 Fairness Metric
- **Description**: Outcome metric from simulation.
- **Attributes**: `repo_id`, `demographic_parity_diff`, `equalized_odds_diff`, `injected_skew_magnitude`.

### 2.6 Correlation Result
- **Description**: Statistical summary of the relationship.
- **Attributes**: `metric_pair` (e.g., "text_score vs dp"), `spearman_rho`, `p_value_raw`, `p_value_bonferroni`, `alpha`, `significance` (bool).

### 2.7 Validation Record
- **Description**: Result of VADER threshold validation.
- **Attributes**: `threshold`, `manual_label_count`, `kappa_score`, `status` (pass, fail).

## 3. File Formats

### 3.1 Raw Data
- **Repositories**: Cloned via `git` (directory).
- **VADER Lexicon**: Parquet (from HuggingFace).
- **Validation Set**: CSV (`data/validation/comments.csv`).

### 3.2 Processed Data
- **Bias Scores**: JSON Lines (`data/processed/bias_scores.jsonl`).
- **Fairness Metrics**: JSON Lines (`data/processed/fairness_metrics.jsonl`).
- **Correlation Results**: CSV (`data/processed/correlation_results.csv`).

### 3.3 State Manifest
- **Format**: YAML (`state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml`).
- **Content**: Checksums of all data files, timestamps, version hashes.

## 4. Constraints

- **PII**: No personally identifiable information stored in `data/`.
- **Immutability**: Raw data files are never modified; derivations create new files.
- **Checksums**: Every file in `data/` has a SHA-256 hash recorded in the state manifest.
