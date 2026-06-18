# Unconventional Analytical Lenses for Knot Diagram Complexity

The current analysis pipeline relies primarily on regression‑based models that
relate handcrafted knot invariants (crossing number, braid index, hyperbolic
volume, etc.) to the proposed composite complexity metric. While these models
provide valuable baseline insights, they may miss higher‑order structural
patterns that are not captured by linear or low‑order nonlinear terms.

To uncover such hidden structure we propose two complementary, non‑traditional
approaches:

1. **Topological Data Analysis (TDA)** – Compute persistent homology on
   filtered representations of knot diagrams (e.g., pixelated images of the
   planar projection or point clouds derived from the diagram’s crossing
   graph). The resulting persistence diagrams and derived statistics (e.g.,
   bottleneck distance, persistence entropy) can be incorporated as new
   features in downstream models, potentially revealing multi‑scale topological
   signatures that correlate with complexity.

2. **Graph‑Neural‑Network (GNN) Embeddings** – Treat each knot diagram as a
   graph where vertices correspond to crossings and edges encode adjacency in
   the projection. Train a GNN (e.g., Graph Convolutional Network or Graph
   Attention Network) to produce low‑dimensional embeddings that capture the
   relational geometry of the diagram. These embeddings can be used directly
   as predictors or combined with existing invariants in a hybrid model.

Both methods are **implementation‑agnostic** and can be added as optional
modules in the `code/analysis/` package. Preliminary experiments should focus
on a subset of the cleaned knot dataset (`data/processed/knots_cleaned.csv`)
to evaluate whether the new features improve predictive performance (e.g.,
lower MAE or higher explained variance) compared to the baseline regression
models.

The documentation for these extensions will be added to the reproducibility
package once prototype code is available, ensuring that the full workflow
remains transparent and repeatable.

