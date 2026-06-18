# Precision of Braid Index Measurements

The braid index of a knot is defined as the minimal number of strands required to represent the knot as a closed braid. While the crossing number is an exact combinatorial invariant, the braid index is often obtained algorithmically and can be sensitive to the specific diagram or computational method used.

## Standard of Evidence

To support the robustness of our complexity metric we adopt the following evidence standards:

1. **Cross‑validation across multiple diagram representations** – For each prime knot we generate all minimal crossing diagrams (as provided by the Knot Atlas) and compute the braid index using two independent algorithms: the **Morton–Franks–Williams** bound and the **Birman–Menasco** algorithm. Consistency between the two yields a high‑confidence measurement.
2. **Statistical precision across knot families** – For each class of prime knots (alternating, non‑alternating, torus, hyperbolic) we report the mean and standard deviation of the braid index values obtained from the diagram ensemble. A standard deviation ≤ 0.2 is required for inclusion in the final composite metric.
3. **Reproducibility checks** – All calculations are logged with deterministic random seeds and the full provenance (input diagram IDs, algorithm version, and parameter settings) is stored in `data/processed/validation_flags.json`. The reproducibility pipeline re‑runs the braid‑index computation on a random 10 % sample of knots; any discrepancy triggers a re‑analysis.

## Experimental Procedure

The following steps are executed in `code/analysis/precision.py`:

```python
from code.analysis._utils import load_minimal_diagrams
from code.analysis.braid_index import compute_braid_index_mfw, compute_braid_index_bm

def assess_precision(knot_id):
    diagrams = load_minimal_diagrams(knot_id)
    results = []
    for dg in diagrams:
        b1 = compute_braid_index_mfw(dg)
        b2 = compute_braid_index_bm(dg)
        results.append((b1, b2))
    # consistency check
    consistent = all(b1 == b2 for b1, b2 in results)
    mean = sum(b1 for b1, _ in results) / len(results)
    std = (sum((b1 - mean) ** 2 for b1, _ in results) / len(results)) ** 0.5
    return {"consistent": consistent, "mean": mean, "std": std}
```

The output of `assess_precision` is aggregated in `data/processed/braid_index_precision_report.json`, which is referenced in the reproducibility report (`docs/reproducibility/braid_index_precision.md`). This provides a transparent, quantitative basis for the claimed precision of braid‑index measurements across all prime‑knot classes.
}
