# Novel Exploratory Pathways

The reproducibility infrastructure of this project enables rapid experimentation with
data‑driven discovery techniques. In addition to the existing composite metrics, we
introduce three exploratory analyses that leverage the curated knot diagram dataset:

## Unsupervised Clustering of Knot Diagrams
We apply hierarchical clustering to the graph representations of knot diagrams,
using features derived from crossing patterns and braid indices. The resulting
clusters reveal families of knots with similar topological complexity, which can be
visualized with the interactive maps in `code/analysis/interactive_knot_family_map.py`.

## Persistent Homology of Diagram Graphs
Using the `tda_persistent_homology.py` module, we compute persistence diagrams for
each knot’s planar graph. This captures multi‑scale topological features beyond the
standard invariants and provides a basis for comparing knots via bottleneck distance.

## Symbolic Regression for Functional Forms
The `novel_exploratory.py` script employs genetic programming to discover
analytical expressions that relate invariant vectors to the estimated complexity.
Discovered formulas are validated against a held‑out test set and documented in
`docs/reproducibility/creative_explorations.md`.

These pathways are fully reproducible: all code, random seeds, and intermediate
artifacts are logged by the reproducibility framework, enabling independent verification
and extension by the community.

