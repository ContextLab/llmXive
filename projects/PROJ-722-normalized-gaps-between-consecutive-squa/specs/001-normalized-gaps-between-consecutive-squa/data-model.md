# Data Model: Normalized Squarefree Gaps

## Entities

*   **SquarefreeSequence**: An ordered list of integers representing squarefree numbers.
    *   `s_i`: Integer (int) - The i-th squarefree number.
*   **GapDataset**: A collection of gap data.
    *   `raw_gaps`: List of Integers (list[int]) - Raw gaps between consecutive squarefree numbers.
    *   `normalized_gaps`: List of Floats (list[float]) - Normalized gaps calculated by dividing raw gaps by the empirical mean.
    *   `empirical_mean`: Float - The mean of the raw gaps, used for normalization.
*   **TestResult**: A record of the goodness-of-fit test results.
    *   `n`: Integer - The cutoff value (maximum integer limit) used for generating squarefree numbers.
    *   `ks_statistic`: Float - The Kolmogorov-Smirnov statistic.
    *   `p_value`: Float - The p-value from the Lilliefors test.

## Data Flow

1.  The `squarefree.py` module generates a `SquarefreeSequence` up to a given limit `N`.
2.  The `gap_analysis.py` module calculates `raw_gaps` from the `SquarefreeSequence` and computes the `empirical_mean`.  It then calculates `normalized_gaps`.
3.  The `statistical_tests.py` module performs the Lilliefors test on the `normalized_gaps` and generates a `TestResult` with the `ks_statistic` and `p_value`.
4.  The `visualization.py` module uses the `normalized_gaps` and `TestResult` to generate plots for analysis.

## Schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
description: Data model for normalized squarefree gaps.
properties:
  squarefree_sequence:
    type: array
    items:
      type: integer
      description: A squarefree number.
  gap_dataset:
    type: object
    properties:
      raw_gaps:
        type: array
        items:
          type: integer
          description: The raw gap between consecutive squarefree numbers.
      normalized_gaps:
        type: array
        items:
          type: number
          format: float
          description: The normalized gap.
      empirical_mean:
        type: number
        format: float
        description: The empirical mean of the raw gaps.
    required:
      - raw_gaps
      - normalized_gaps
      - empirical_mean
  test_result:
    type: object
    properties:
      n:
        type: integer
        description: The cutoff value for squarefree number generation.
      ks_statistic:
        type: number
        format: float
        description: The Kolmogorov-Smirnov statistic.
      p_value:
        type: number
        format: float
        description: The p-value from the Lilliefors test.
    required:
      - n
      - ks_statistic
      - p_value
```

---
