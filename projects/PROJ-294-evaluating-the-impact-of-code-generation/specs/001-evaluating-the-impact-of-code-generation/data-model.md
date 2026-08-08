# Data Model: Evaluating the Impact of Code Generation Models on Code Testability

## Overview

This document defines the data structures used for storing metrics, artifacts, and statistical results. All data is persisted in JSON or YAML formats with strict schema validation.

## Entities

### 1. Metrics Record
Stores calculated metrics for a single code sample (human or LLM).

```yaml
task_id: string
model: string  # "human" or "Salesforce/codegen-mono"
cyclomatic_complexity: integer
halstead_volume: float
branch_coverage_pct: float
pass_rate: float  # 0.0 to 1.0
generated_code: string
checksum: string  # SHA256 of generated_code
```

### 2. Statistical Result
Stores the outcome of a hypothesis test.

```yaml
test_name: string  # "wilcoxon", "mcnemar", etc.
metric: string
statistic: float
p_value: float
significant: boolean
effect_size: float  # Cohen's d or similar
confidence_interval: [float, float]
```

### 3. Artifact Hash
Tracks integrity of all generated files.

```yaml
file_path: string
checksum: string  # SHA256
timestamp: string  # ISO 8601
```

## Relationships

- **Metrics Record** is derived from **Task** (HumanEval) and **Generated Code**.
- **Statistical Result** is derived from a set of **Metrics Records**.
- **Artifact Hash** covers all files in `data/` and `state/`.

## Constraints

- **Non-null**: All numeric fields must be non-null.
- **Range**: `pass_rate` and `branch_coverage_pct` must be in [0.0, 1.0].
- **Uniqueness**: `task_id` + `model` must be unique in the metrics dataset.
