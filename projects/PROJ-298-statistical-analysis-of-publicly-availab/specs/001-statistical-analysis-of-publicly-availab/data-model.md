# Data Model: Statistical Analysis of Publicly Available Stack Overflow Question Tags

## Overview

This document defines the data structures, schemas, and transformations used in the analysis pipeline. All data is stored in `data/` with checksums recorded in `state/`.

## Entity Definitions

### Tag

- **Type**: String (normalized: lowercase, trimmed)
- **Example**: `python`, `react`
- **Constraints**: Non-empty, alphanumeric + hyphens.

### TimeSeries

- **Type**: Sequence of monthly counts.
- **Structure**:
  - `tag`: String
  - `month`: Date (YYYY-MM-01)
  - `count`: Integer (≥0)
  - `trend_slope`: Float (Theil-Sen)
  - `p_value`: Float
  - `classification`: Enum ("Growth", "Decline", "Stable", "Insufficient Data")

### Cluster

- **Type**: Group of tags.
- **Structure**:
  - `cluster_id`: String
  - `members`: List[String]
  - `intra_similarity`: Float (Jaccard)
  - `alignment_score`: Float (vs. Survey Taxonomy)

## Data Flow

1. **Raw Ingestion**: `PostsTags` table (PostId, TagName).
2. **Preprocessing**:
   - Normalize tags.
   - Filter for ≥12 months of data.
   - Aggregate to monthly bins (2015-2023).
3. **Analysis**:
   - Mann-Kendall test → `trend_results`
   - Decomposition → `decomposition_results`
   - Clustering → `cluster_results`
4. **External Validation**:
   - GitHub/NPM correlation → `correlation_results`
5. **Output**:
   - Reports (PDF/HTML) with limitation headers.
   - JSON artifacts (`confidence_interval.json`, `state/`).

## Schema Definitions

See `contracts/` for detailed YAML schemas.

- `contracts/dataset.schema.yaml`: Schema for the processed monthly tag frequency data.
- `contracts/output.schema.yaml`: Schema for the final trend analysis results.
- `contracts/cluster_results.schema.yaml`: Schema for cluster membership and alignment scores.

## Data Hygiene

- **Checksums**: SHA-256 for all files in `data/`.
- **Immutability**: Raw data never modified; derivations in new files.
- **PII**: No PII in `PostsTags` (only PostId and TagName).