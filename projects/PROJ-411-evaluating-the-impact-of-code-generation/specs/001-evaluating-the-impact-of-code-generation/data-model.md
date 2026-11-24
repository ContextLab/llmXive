# Data Model: Evaluating the Impact of Code Generation on Code Review Burden

## Entities

- **PullRequest (raw)**  
  `pr_id`, `repo_name`, `source_dataset`, `created_at`, `merged_at`, `additions`, `deletions`, `comment_count`, `commit_message`, `diff_text`, `file_headers`, `labels`, `first_comment_timestamp`.

- **ReviewMetric (processed)**  
  `review_duration_seconds`, `review_active_seconds`, `comment_density`, `issue_severity`, `lines_changed`, `creation_quarter`, `comment_count`, `provenance_label`.

- **StatisticalResult**  
  `test_name`, `metric`, `group_a_n`, `group_b_n`, `test_statistic`, `p_value`, `effect_size`, `effect_size_type`, `significance`, `bonferroni_corrected_alpha`.

## Derivation Chain (Constitution III/IV)

```
data/raw/*.json  (immutable, checksummed)
 └─ Phase 0: download_data.py → schema_map.md (validation against raw_prs.schema.yaml)
      └─ Phase 1: classify_provenance.py → data/processed/classified_prs.csv
           └─ Phase 2: compute_metrics.py → data/processed/processed_prs.csv (SSoT)
                └─ Phase 3: outlier_filter.py → filtered variants (iqr1.0, iqr1.5, iqr2.0, relaxed)
                     └─ Phase 4: statistical_analysis.py → data/results/stats_summary.csv
                     └─ Phase 5: validation.py → data/results/validation_report.md
                     └─ Phase 6: sensitivity.py → data/results/sensitivity_report.csv
                          └─ Phase 7: report.py → report.md + figures
```

Each step writes a **new** file; no in‑place mutation occurs, satisfying Constitution III & IV.

**Note on `first_comment_timestamp`**: This field is optional in the raw schema; when it is missing for a PR, `compute_metrics.py` falls back to using `review_duration_seconds` for `review_active_seconds` and logs the limitation, ensuring the pipeline remains deterministic.

---


