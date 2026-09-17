# Data Model: Normalized Gaps Between Consecutive Squarefree Numbers

This document describes the data model used in this project.

## Entities

*   **SquarefreeNumber**: An integer that is not divisible by any perfect square greater than 1.
    *   `value`: Integer value of the squarefree number.
*   **Gap**: The difference between two consecutive squarefree numbers.
    *   `raw_gap`: The raw difference between consecutive squarefree numbers.
    *   `normalized_gap`: The raw gap divided by the empirical mean of all gaps.

## Data Relationships

The primary relationship is a sequential ordering of `SquarefreeNumber` entities. `Gap` entities represent the difference between consecutive `SquarefreeNumber` entities.

## Schema

```yaml
# dataset_schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: Normalized Gap Dataset
description: Dataset containing normalized gaps between consecutive squarefree numbers.
type: array
items:
  type: object
  properties:
    n:
      type: integer
      description: The upper limit of the squarefree sequence
    raw_gap:
      type: float
      description: The raw gap between consecutive squarefree numbers.
    normalized_gap:
      type: float
      description: The normalized gap (raw_gap / empirical_mean).
  required:
    - n
    - raw_gap
    - normalized_gap
```

## Data Storage

The data will be stored in-memory as NumPy arrays during processing. For visualization, the data will be written to CSV or Parquet files.
