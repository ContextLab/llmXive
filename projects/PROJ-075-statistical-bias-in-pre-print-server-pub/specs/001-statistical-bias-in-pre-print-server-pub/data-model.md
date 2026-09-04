# Data Model: Statistical Bias in Pre-Print Server Publication Trends

## Overview

This document defines the data structures for the project, including the `MatchedPaperPair`, `StatisticalMetric`, and `AnalysisResult` entities. All data is stored in CSV or JSON format in the `data/` directory.

## Entity Definitions

### MatchedPaperPair

Represents a single study with two artifacts: pre-print and journal versions.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `pair_id` | str | Unique identifier for the pair (e.g., `pair_0001`) | Primary key |
| `preprint_id` | str | Pre-print ID (arXiv/bioRxiv) | Not null |
| `journal_doi` | str | Journal DOI | Not null |
| `title` | str | Paper title | Not null |
| `authors` | list[str] | List of author names | Not null |
| `preprint_date` | date | Pre-print publication date | Not null |
| `journal_date` | date | Journal publication date | Not null |
| `field` | str | Research field (e.g., "Quantitative Biology") | Not null |
| `match_score` | float | Fuzzy matching score (0.0–1.0) | ≥ 0.8 |
| `exclusion_reason` | str | Reason for exclusion (if any) | Nullable |
| `content_hash` | str | SHA-256 hash of the pair's content for versioning | Not null |
| `doi_verified` | bool | True if DOI verified against OpenAlex canonical source | Not null |

### StatisticalMetric

Represents a single extracted statistical value.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `metric_id` | str | Unique identifier for the metric | Primary key |
| `pair_id` | str | Foreign key to `MatchedPaperPair` | Not null |
| `version` | str | "preprint" or "journal" | Enum |
| `metric_type` | str | "p-value", "effect_size", "sample_size" | Enum |
| `value` | float | Numeric value | Nullable (if inequality) |
| `inequality_flag` | bool | True if value is an inequality | False if exact |
| `interval_lower` | float | Lower bound of interval (if inequality) | Nullable |
| `interval_upper` | float | Upper bound of interval (if inequality) | Nullable |
| `stat_method` | str | Statistical method (e.g., "t-test", "regression") | Not null |
| `n_sample` | int | Sample size | > 0 |
| `confidence_interval` | str | CI string (e.g., "95% CI [0.5, 1.2]") | Nullable |

### AnalysisResult

Represents the output of a statistical test.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `result_id` | str | Unique identifier for the result | Primary key |
| `test_type` | str | "p_curve", "paired_ttest", "wilcoxon", "sensitivity", "tobit" | Enum |
| `threshold` | float | Significance threshold (if applicable) | Nullable |
| `statistic_value` | float | Test statistic (e.g., t-value, p-curve power) | Not null |
| `p_value` | float | P-value of the test | 0.0–1.0 |
| `ci_lower` | float | Lower bound of confidence interval | Nullable |
| `ci_upper` | float | Upper bound of confidence interval | Nullable |
| `interpretation` | str | Human-readable interpretation | Not null |
| `threshold_context` | str | Context for sensitivity analysis | Nullable |

## Data Flow

1. **Raw Data**: `data/raw/openalex_metadata/`, `data/raw/arxiv_metadata/`, `data/raw/biorxiv_metadata/` (PDFs, JSON metadata).
2. **Processed Data**: `data/processed/matched_pairs.csv`, `data/processed/extracted_metrics.csv`.
3. **Results**: `data/results/p_curve_results.json`, `data/results/effect_size_results.json`, `data/results/sensitivity_results.json`.

## Data Hygiene

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml`.
- **Immutability**: Raw data is never modified. Derivations create new files (e.g., `matched_pairs_v1.csv`, `matched_pairs_v2.csv`).
- **PII**: No personally identifiable information is stored. Author names are normalized and anonymized where necessary.