# Interactive 3‑D Knot Landscape

This visual narrative presents a three‑dimensional landscape of knot
complexity.  Each axis corresponds to a selected invariant (e.g.
**crossing number**, **hyperbolic volume**, **signature**).  The terrain
height encodes the **hyperbolic volume**, allowing an intuitive artistic
view of how knots distribute across the invariant space.

The prototype is implemented in `code/analysis/interactive_knot_family_map.py`
and can be launched via:

```bash
python -m code.analysis.interactive_knot_family_map
```

The module provides an interactive WebGL view that can be embedded in the
project documentation or shared as a standalone exploratory tool.

