# Data Model: Evaluating the Impact of Code Generation on Code Review Burden

## Raw PR Dataset Schema (`raw_prs.schema.yaml`)

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Raw Pull Request Record"
type: object
required:
  - pr_id
  - repo_name
  - created_at
  - merged_at
  - additions
  - deletions
  - comment_count
  - commit_message
  - diff_text
  - file_headers
  - labels
properties:
  pr_id:
    type: integer
    description: "Unique identifier of the pull request on GitHub."
  repo_name:
    type: string
    description: "Full repository name (owner/repo)."
  created_at:
    type: string
    format: date-time
    description: "Timestamp when the PR was opened."
  merged_at:
    type: string
    format: date-time
    description: "Timestamp when the PR was merged (null if never merged)."
  additions:
    type: integer
    description: "Number of lines added."
  deletions:
    type: integer
    description: "Number of lines removed."
  comment_count:
    type: integer
    description: "Total number of review comments on the PR."
  commit_message:
    type: string
    description: "Commit message of the PR’s head commit."
  diff_text:
    type: string
    description: "Unified diff of the PR (may be empty if unavailable)."
  file_headers:
    type: string
    description: "Concatenated file header comments extracted from changed files."
  labels:
    type: array
    items:
      type: string
    description: "GitHub labels attached to the PR (used for issue severity)."
  first_comment_timestamp:
    type: string
    format: date-time
    description: "Timestamp of the first review comment on the PR (optional; if missing, `review_active_seconds` falls back to `review_duration_seconds`)."
    nullable: true
```

## Processed PR Schema (`processed_prs.schema.yaml`)

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Processed Pull Request Record"
type: object
required:
  - pr_id
  - repo_name
  - lines_changed
  - comment_count
  - review_active_seconds
  - comment_density
  - issue_severity
  - provenance_label
properties:
  pr_id:
    type: integer
  repo_name:
    type: string
  lines_changed:
    type: integer
    description: "Total lines added + deleted."
  comment_count:
    type: integer
  review_active_seconds:
    type: number
    description: "Seconds from first review comment to PR merge."
  comment_density:
    type: number
    description: "Comments per line of changed code."
  issue_severity:
    type: string
    enum: ["bug", "enhancement", "documentation", "other"]
    description: "Primary severity label derived from PR labels."
  provenance_label:
    type: string
    enum: ["LLM-generated", "Human-written", "Mixed"]
    description: "Provenance classification per FR‑002."
```

## Statistical Result Schema (`statistical_results.schema.yaml`)

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
title: "Statistical Test Result"
type: object
required:
  - test_name
  - metric
  - group_a_n
  - group_b_n
  - test_statistic
  - p_value
  - effect_size
  - effect_size_type
  - significance
  - bonferroni_corrected_alpha
properties:
  test_name:
    type: string
    description: "Name of the statistical test (e.g., t-test, Mann-Whitney U)."
  metric:
    type: string
    description: "Metric being compared (e.g., review_active_seconds)."
  group_a_n:
    type: integer
    description: "Sample size of LLM-generated group."
  group_b_n:
    type: integer
    description: "Sample size of Human-written group."
  test_statistic:
    type: number
    description: "t value or U statistic."
  p_value:
    type: number
    description: "Raw p‑value before correction."
  effect_size:
    type: number
    description: "Cohen's d or rank‑biserial correlation."
  effect_size_type:
    type: string
    enum: ["cohen_d", "rank_biserial"]
    description: "Indicates which effect‑size metric is reported."
  significance:
    type: boolean
    description: "True if p_value < bonferroni_corrected_alpha."
  bonferroni_corrected_alpha:
    type: number
    description: "Alpha after Bonferroni correction (0.05 divided by number of primary tests)."
```

All schemas are stored under `specs/001-code-gen-review-burden/contracts/` and will be used by the Implementer Agent to validate output files.
