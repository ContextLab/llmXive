# Data Model: Automated Detection of Algorithmic Bias in Public Code Repositories

## Overview

This document defines the data structures used throughout the pipeline, ensuring consistency between the extraction, simulation, and analysis phases. All data is stored in JSONL (JSON Lines) format for streaming compatibility and type safety.

## Entities & Schemas

### 1. Repository Metadata
Captures basic information about the source repository.

```yaml
# contracts/repo_meta.schema.yaml
type: object
properties:
  repo_id:
    type: string
    description: "Unique identifier (e.g., owner/repo)"
  clone_url:
    type: string
    format: uri
  commit_hash:
    type: string
    description: "SHA of the commit analyzed"
  python_file_count:
    type: integer
  analysis_timestamp:
    type: string
    format: date-time
required:
  - repo_id
  - clone_url
  - commit_hash
```

### 2. Textual Artifact (Per File)
Intermediate output from the static analyzer.

```yaml
# contracts/artifact.schema.yaml
type: object
properties:
  repo_id:
    type: string
  file_path:
    type: string
  total_tokens:
    type: integer
  bias_matches:
    type: array
    items:
      type: object
      properties:
        token:
          type: string
        category:
          type: string
          enum: [gender, race, stereotype, other]
        count:
          type: integer
  vader_scores:
    type: object
    properties:
      compound:
        type: number
        minimum: -1
        maximum: 1
      neg:
        type: number
      neu:
        type: number
      pos:
        type: number
  file_bias_score:
    type: number
    description: "Normalized bias score for this file"
required:
  - repo_id
  - file_path
  - file_bias_score
```

### 3. Repository Aggregation
Aggregated metrics per repository (FR-009).

```yaml
# contracts/repo_aggregate.schema.yaml
type: object
properties:
  repo_id:
    type: string
  avg_textual_bias_score:
    type: number
    description: "Arithmetic mean of file_bias_scores"
  total_files_analyzed:
    type: integer
  avg_sentiment:
    type: number
  status:
    type: string
    enum: [success, no_code, execution_failure]
required:
  - repo_id
  - avg_textual_bias_score
  - status
```

### 4. Validation Result (New for FR-010)
Output from the lexicon validation phase.

```yaml
# contracts/validation.schema.yaml
type: object
properties:
  repo_id:
    type: string
  labeled_comments_count:
    type: integer
  alignment_precision:
    type: number
  alignment_recall:
    type: number
  status:
    type: string
    enum: [pass, warning, fail]
required:
  - repo_id
  - alignment_precision
  - status
```

### 5. Simulation Result
Output from the bias injection phase (Blind Simulation).

```yaml
# contracts/simulation_result.schema.yaml
type: object
properties:
  repo_id:
    type: string
  sample_size:
    type: integer
    description: "N of synthetic samples"
  demographic_parity_diff:
    type: number
    description: "Absolute difference in positive rates"
  equalized_odds_diff:
    type: number
    description: "Max difference in TPR/FPR"
  hidden_bias_magnitude:
    type: number
    description: "The independent B_true value used for this repo"
  leakage_check:
    type: boolean
    description: "True if no token leakage detected (SC-004)"
required:
  - repo_id
  - demographic_parity_diff
  - equalized_odds_diff
  - hidden_bias_magnitude
  - leakage_check
```

### 6. Correlation Result
Final statistical output.

```yaml
# contracts/result.schema.yaml
type: object
properties:
  metric_type:
    type: string
    enum: [demographic_parity, equalized_odds]
  spearman_rho:
    type: number
  p_value_raw:
    type: number
  p_value_bonferroni:
    type: number
  significant:
    type: boolean
  alpha_threshold:
    type: number
required:
  - metric_type
  - spearman_rho
  - p_value_bonferroni
```

### 7. Robustness Report (New for SC-005)
Output from the robustness test harness.

```yaml
# contracts/robustness.schema.yaml
type: object
properties:
  total_repos_tested:
    type: integer
  skipped_count:
    type: integer
  success_threshold:
    type: number
    description: "0.95 for 95%"
  status:
    type: string
    enum: [pass, fail]
required:
  - total_repos_tested
  - skipped_count
  - status
```

### 8. Independence Assertion (New for SC-004)
Output from the static independence check.

```yaml
# contracts/independence.schema.yaml
type: object
properties:
  assertion_type:
    type: string
    const: "static_independence"
  status:
    type: string
    enum: [pass, fail]
  details:
    type: string
    description: "Description of the static analysis performed"
required:
  - assertion_type
  - status
```

## Data Flow

1.  **Input**: `repo_meta` (from GitHub API).
2.  **Process**: `ast_parser` -> `artifact` (JSONL).
3.  **Validate**: `artifact` -> `validation_result` (FR-010).
4.  **Aggregate**: `artifact` -> `repo_aggregate`.
5.  **Simulate**: `repo_aggregate` -> `simulation_result` (Blind).
6.  **Verify**: `simulation_result` + `independence_assertion` (SC-004).
7.  **Analyze**: `repo_aggregate` + `simulation_result` -> `result`.

## Constraints & Validation

- **Zero-Inflation**: `avg_textual_bias_score` can be 0.0.
- **Range**: Sentiment scores must be in [-1, 1].
- **Consistency**: `repo_id` must match across all stages.
- **PII**: No personal names or emails allowed in `artifact` (filtered by regex in `ast_parser`).
- **Independence**: `hidden_bias_magnitude` must be generated independently of `avg_textual_bias_score`.
- **Robustness**: `robustness_report` must show `status: pass` for SC-005.
- **Independence**: `independence_assertion` must show `status: pass` for SC-004.
