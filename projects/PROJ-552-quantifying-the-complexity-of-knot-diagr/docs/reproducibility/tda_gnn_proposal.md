# Topological Data Analysis and Graph Neural Network Embeddings for Knot Diagrams

In addition to the traditional regression‑based analyses, we propose exploring
unconventional analytical lenses that may reveal hidden structure in the
complexity of knot diagrams.

## Persistent Homology of Knot Diagrams

Topological Data Analysis (TDA) can be applied to the planar projection of a
knot by treating the diagram as a point cloud or a cubical complex derived from
its crossing and region structure. Computing the persistent homology (e.g., via
`gudhi` or `ripser`) yields a set of birth–death pairs that capture multi‑scale
topological features such as loops and voids in the diagram. These persistence
summaries can be vectorised (e.g., persistence images or landscapes) and used
as additional predictors in downstream models, potentially uncovering patterns
that are invisible to scalar invariants alone.

## Graph‑Neural‑Network Embeddings of Knot Projections

Each knot diagram can be represented as a planar graph where vertices correspond
to crossings and edges follow the strand connections. Recent advances in
graph‑neural‑networks (GNNs) allow learning expressive embeddings of such graphs.
By training a GNN (e.g., Graph Convolutional Network or Graph Attention Network)
to predict known invariants, the intermediate node and graph embeddings can be
extracted and analysed. These embeddings may capture subtle structural cues that
correlate with the complexity measures under study.

## Integration with Existing Pipeline

The proposed TDA and GNN workflows can be incorporated as optional modules in
the `code/analysis` package:

* `code/analysis/tda_persistence.py` – compute persistence diagrams and vectorise them.
* `code/analysis/gnn_embeddings.py` – construct graph representations and obtain
  embeddings using PyTorch Geometric.

Results from these modules can be appended to the feature matrix used by
`code/analysis/regression.py`, enabling comparative experiments between traditional
regression, TDA‑augmented models, and GNN‑augmented models.

We encourage future work to benchmark these approaches on the cleaned knot dataset
provided in `data/processed/knots_cleaned.csv` and to report any discovered
novel patterns in the final reproducibility report.

