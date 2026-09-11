# Data Model: Normalized Gaps Between Consecutive Squarefree Numbers

This document defines the data structures used in this project.

## Squarefree Sequence

*   **Description**: An ordered list of integers that are squarefree.
*   **Data Type**: List of integers (`List[int]`)
*   **Constraints**: Each integer in the list must be greater than 1 and not divisible by any perfect square greater than 1.

## Gap Dataset

*   **Description**: A collection of raw and normalized gaps between consecutive squarefree numbers.
*   **Data Type**: Dictionary
*   **Fields**:
    *   `raw_gaps`: A list of raw gaps between consecutive squarefree numbers. (`List[float]`)
    *   `normalized_gaps`: A list of normalized gaps, calculated by dividing each raw gap by the empirical mean of the raw gaps. (`List[float]`)
    *   `mean_gap`: The empirical mean of the raw gaps. (`float`)
    *   `N`: The upper limit of the squarefree sequence. (`int`)

## Test Result

*   **Description**: The results of the Lilliefors goodness-of-fit test.
*   **Data Type**: Dictionary
*   **Fields**:
    *   `N`: The upper limit of the squarefree sequence used for the test. (`int`)
    *   `ks_statistic`: The Kolmogorov-Smirnov (KS) statistic. (`float`)
    *   `p_value`: The p-value from the Lilliefors test. (`float`)

## Gap Dataset Schema (contracts/gap_dataset_schema.yaml)

```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
description: Schema for the Gap Dataset
properties:
  raw_gaps:
    type: array
    items:
      type: number
      format: float
    description: List of raw gaps between consecutive squarefree numbers.
  normalized_gaps:
    type: array
    items:
      type: number
      format: float
    description: List of normalized gaps.
  mean_gap:
    type: number
    format: float
    description: The empirical mean of the raw gaps.
  N:
    type: integer
    description: The upper limit of the squarefree sequence.
required:
  - raw_gaps
  - normalized_gaps
  - mean_gap
  - N
```
