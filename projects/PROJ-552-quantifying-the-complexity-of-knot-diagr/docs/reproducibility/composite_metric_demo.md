# Demonstration of the Novel Composite Metric

This document provides a brief demonstration of the newly introduced **Weighted Entropy Composite Metric** that synthesizes the crossing number and braid index of a knot diagram.

The metric is defined in `code/analysis/composite_metric_novel.py` as:

```python
def weighted_entropy_metric(crossing_number: int, braid_index: int) -> float:
    """Compute a normalized entropy‑based composite metric.

    The two invariants are treated as a probability distribution and the
    Shannon entropy is calculated.  A small epsilon avoids log(0).
    """
    total = crossing_number + braid_index
    if total == 0:
        return 0.0
    p_cross = crossing_number / total
    p_braid = braid_index / total
    import math
    epsilon = 1e-12
    return - (p_cross * math.log(p_cross + epsilon) + p_braid * math.log(p_braid + epsilon))
```

Empirical analysis (see `code/analysis/composite_metric_extended.py`) shows that this metric correlates with hyperbolic volume more strongly than either invariant alone, indicating it captures additional geometric information.

