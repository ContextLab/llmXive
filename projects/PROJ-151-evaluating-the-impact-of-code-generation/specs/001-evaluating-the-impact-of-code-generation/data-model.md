# Data Model: Evaluating the Impact of Code Generation Models on Code Review Efficiency

## Overview

This document defines the schema for all data artifacts in the project, ensuring compliance with Constitution Principles III (Data Hygiene) and VII (Metric Consistency).

## Entities

### 1. Raw PR Dataset
- **Source**: HuggingFace `loubnabnl/prs-v2-sample`
- **Format**: Parquet
- **Key Fields**: `pr_id`, `project_id`, `language`, `diff_lines`, `code_snippet`, `comment_count`, `timestamp`

### 2. Filtered PR Dataset
- **Derived From**: Raw PR Dataset
- **Filter**: `language` in ["Java", "Python"] AND `diff_lines` ≤ 30 AND `comment_count` IS NOT NULL
- **Format**: Parquet
- **Key Fields**: `pr_id`, `project_id`, `language`, `code_snippet`, `comment_count`, `problem_statement` (derived from title)

### 3. Generated Code Snippet
- **Derived From**: Filtered PR Dataset + LLM Generation
- **Format**: CSV
- **Key Fields**: `pr_id`, `origin` ("generated"), `code_snippet`, `generation_status` ("success"|"failed"), `model_id`, `prompt`, `seed`, `timestamp`

### 4. Code Metrics
- **Derived From**: Filtered PR Dataset (Human) + Generated Code Snippet
- **Format**: CSV
- **Key Fields**: `id`, `origin`, `loc`, `cyclomatic_complexity`, `maintainability_index`, `pylint_score`, `checkstyle_score`, `token_count`

### 5. Provenance Record
- **Derived From**: Generation Step
- **Format**: CSV
- **Key Fields**: `generation_id`, `model_id`, `prompt`, `seed`, `timestamp`, `generation_file_path`, `effort_proxy_type` ("comment_count")

### 6. Validation Survey Data
- **Derived From**: Human Review Study
- **Format**: CSV
- **Key Fields**: `snippet_id`, `reviewer_id`, `review_time_ms`, `comment_count`, `difficulty_rating` (1-5), `blinding_status`

## Relationships

- **Filtered PR** (1) → (N) **Generated Code** (if multiple generations per PR)
- **Generated Code** (1) → (1) **Metrics**
- **Human Code** (1) → (1) **Metrics**
- **Validation Survey** (N) → (1) **Snippet** (multiple reviewers per snippet)

## Data Hygiene Rules

1. **Checksums**: All files in `data/raw/` and `data/processed/` must be checksummed (SHA-256) and recorded in `state.yaml`.
2. **Immutability**: Raw data is never modified. Derivations create new files (e.g., `filtered_prs.parquet`).
3. **PII**: No PII allowed in `data/`. Reviewer IDs in validation study are anonymized.
4. **Versioning**: Each artifact change updates `state.yaml` `artifact_hashes`.
