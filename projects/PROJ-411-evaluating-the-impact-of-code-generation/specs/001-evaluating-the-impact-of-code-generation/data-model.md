# Data Model: Evaluating the Impact of Code Generation on Code Review Burden

## Entities

- **PullRequest** (raw): `pr_id`, `repo_name`, `source_dataset`, `created_at`, `merged_at`, `additions`, `deletions`, `comment_count`, `commit_message`, `diff_text`, `file_headers`, `labels`, `first_comment_timestamp`.
- **ReviewMetric** (processed): `review_duration_seconds`, `review_active_seconds`, `comment_density`, `issue_severity`, `lines_changed`, `creation_period`.
- **StatisticalResult**: `test_name`, `metric`, `group_a_n`, `group_b_n`, `test_statistic`, `p_value`, `effect_size`, `effect_size_type`, `significance`, `bonferroni_corrected_alpha`.

## Schemas

Three contract schemas are defined (one per file, under `contracts/`):

1. **`raw_prs.schema.yaml`** – the raw PR record, including the `first_comment_timestamp` field required by FR-016 and a `source_dataset` tag. Phase 0 validates/inspects the downloaded data against this schema (FR-022); fields found missing at runtime are reported per dataset via the schema map rather than assumed present.
2. **`processed_prs.schema.yaml`** – the SSoT processed record (`data/processed/processed_prs.csv`, FR-020).
3. **`statistical_results.schema.yaml`** – the `stats_summary.csv` result rows (FR-021).

Derivation chain (Constitution III/IV), each file with exactly one writer:

`data/raw/*.parquet` (immutable, checksummed, kept separate per source)
→ `classify_provenance.py` → `data/processed/classified_prs.csv`
→ `compute_metrics.py` → `data/processed/processed_prs.csv` (**SSoT**, FR-020)
→ `outlier_filter.py` → `data/processed/filtered_prs.csv` (+ `filtered_prs_iqr1.0.csv`, `filtered_prs_iqr2.0.csv`, `filtered_prs_relaxed.csv`)
→ `statistical_analysis.py` / `sensitivity.py` → `data/results/stats_summary.csv`, `data/results/sensitivity_report.csv` → figures and `report.md`.

Every step writes a new file; nothing is modified in place.