# Creative Explorations

The reproducibility infrastructure of the project enables a range of data‑driven discovery pipelines beyond the current composite‑metric analysis.

## Unsupervised clustering of knot diagrams
We provide a script that loads the cleaned knot dataset, extracts graph‑based features (crossing number, braid index, Seifert genus, etc.) and applies scikit‑learn clustering algorithms (k‑means, DBSCAN). The resulting clusters are saved in `data/processed/knot_clusters.json` and visualized in the visual narrative documentation.

## Persistent homology of diagram graphs
Using the existing `tda_persistent_homology.py` module, we compute Vietoris–Rips filtrations on the adjacency representation of knot diagrams and extract persistence diagrams. Summaries (e.g., bottleneck distances) are stored in `data/processed/persistent_homology.csv` and can be explored with the TDA visualizations.

## Symbolic regression for functional discovery
The regression analysis module is extended with a symbolic regression routine (via `gplearn`) that searches for closed‑form relationships between diagram invariants and the composite complexity metric. Candidate expressions are logged in `data/processed/symbolic_regression_results.json` and evaluated against held‑out test sets.

All three pipelines are integrated into the reproducibility checklist, and their outputs are version‑controlled alongside the primary results, ensuring full traceability and enabling future researchers to build on these novel pathways.

