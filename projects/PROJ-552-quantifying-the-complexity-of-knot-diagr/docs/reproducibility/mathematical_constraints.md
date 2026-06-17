# Mathematical Constraints

## Assumptions
- Knot diagrams are planar projections of smooth embeddings.
- Crossing number is the minimal number of crossings over all projections.
- Braid index is the minimal number of strands in any braid representation of the knot.

## Constraints
- **Crossing Number ≤ 13** for all records (per data acquisition limits).
- **Braid Index ≤ Crossing Number** (theoretical bound).

These constraints are enforced during parsing (`code/data/parser.py`).
