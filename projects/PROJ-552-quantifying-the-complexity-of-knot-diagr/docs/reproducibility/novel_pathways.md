# Novel Exploratory Pathways

The reproducibility infrastructure of this project enables rapid experimentation with data‑driven discovery techniques. Below we outline three exploratory avenues we have begun to investigate.

## Unsupervised Clustering of Knot Diagrams

We represent each knot diagram as a graph derived from its crossing adjacency. Using graph embedding techniques (e.g., node2vec) we obtain vector representations, which are then clustered with K‑means and hierarchical clustering. The clusters reveal families of knots with similar structural properties. Results are visualized in `code/analysis/novel_pathways.py` and stored in `data/processed/knot_clusters.json`.

## Persistent Homology of Diagram Graphs

Applying persistent homology to the filtration of diagram graphs uncovers topological signatures. The module `code/analysis/tda_persistent_homology.py` computes persistence diagrams, and summary statistics are saved in `data/processed/persistent_homology_summary.json`. These signatures correlate with known invariants such as hyperbolic volume.

## Symbolic Regression for Functional Discovery

Using the `gplearn` library we perform symbolic regression to discover analytic expressions linking diagram features (crossing number, braid index, etc.) to hyperbolic volume. The best models are serialized in `data/processed/symbolic_regression_models.pkl` and evaluated in `code/analysis/symbolic_regression_exploration.py`.

These exploratory analyses are preliminary but demonstrate the flexibility of our pipeline to support novel scientific inquiry. Future work will expand these experiments and integrate the findings into the core composite metric framework.

