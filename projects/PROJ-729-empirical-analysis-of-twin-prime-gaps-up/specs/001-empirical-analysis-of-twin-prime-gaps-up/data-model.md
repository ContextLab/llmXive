# Data Model: Empirical Analysis of Twin Prime Gaps up to 10⁹

## Overview

This document defines the schema for the raw data generated and the derived statistical results. All data is stored in local files within the `data/` directory.

## Raw Data: Twin Prime Gaps

**File**: `data/raw/twin_primes.csv`  
**Format**: CSV (Comma Separated Values)  
**Encoding**: UTF-8

### Schema

| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `p` | `int64` | The first prime of the twin pair $(p, p+2)$. | $p \ge 3$, $p < 10^9$ |
| `p_next` | `int64` | The first prime of the *next* twin pair in the sequence. | $p_{next} > p$ |
| `delta` | `int64` | The gap between consecutive twin pairs: $p_{next} - p$. | $delta \ge 2$ |
| `normalized_gap` | `float64` | The normalized gap: $\Delta_n / \log(p_n)$. | $> 0$ |

### Example Row

```csv
3,5,2,1.820478
5,11,6,2.272912
11,17,6,1.863008
...
```

*Note: The first twin pair is (3,5). The next is (5,7)? No, (5,7) is not a twin pair in the sense of the sequence of *twin* primes? Wait, the spec says "twin prime pairs". The sequence of twin primes is (3,5), (5,7), (11,13), (17,19)... The gap is between the *start* of consecutive pairs. So between 3 and 5 is 2. Between 5 and 11 is 6. Between 11 and 17 is 6. The definition in FR-002 is $p_{n+1} - p_n$ where $p_n$ is the first prime of the n-th pair.*

## Derived Data: Statistical Results

**File**: `data/results/stats.json`  
**Format**: JSON

### Schema

```json
{
  "global_test": {
    "test_name": "Parametric Bootstrap KS",
    "statistic": 0.00123,
    "p_value": 0.456,
    "bootstrap_iterations": 10000,
    "rejection_status": false,
    "null_hypothesis": "Data follows Exponential(1) (corrected for self-normalization)",
    "notes": "P-value derived via parametric bootstrap to account for parameter estimation."
  },
  "local_tests": [
    {
      "power_of_two": 1024,
      "window_center": 1024.0,
      "sample_size": 12,
      "test_name": "Two-Sample KS",
      "p_value": 0.58,
      "significant_after_correction": false
    }
    // ... for k=10 to 30
  ],
  "metadata": {
    "total_pairs": 440376,
    "generation_time_seconds": 12.5,
    "analysis_time_seconds": 0.8,
    "python_version": "3.11.x",
    "artifact_hashes": {
      "twin_primes.csv": "sha256:...",
      "stats.json": "sha256:..."
    }
  }
}
```

## Visualizations

**Directory**: `data/figures/`

1.  **`qq_plot.png`**: QQ-plot of empirical quantiles vs. theoretical exponential quantiles.
    -   X-axis: Theoretical Quantiles ($-\ln(1-p)$)
    -   Y-axis: Empirical Quantiles
    -   Reference line: $y=x$
2.  **`local_deviation.png`**: Bar chart of p-values (or effect sizes) for each power-of-two window.
    -   X-axis: $k$ (where window is centered at $2^k$)
    -   Y-axis: P-value (Two-Sample KS)
    -   Reference line: $\alpha_{adj} = 0.0024$
