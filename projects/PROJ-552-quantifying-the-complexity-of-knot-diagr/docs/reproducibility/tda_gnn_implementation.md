# Topological Data Analysis and Graph Neural Network Approach

In addition to the traditional regression analyses, we explore **Topological Data
Analysis (TDA)** on knot diagram point clouds.  Persistent homology is computed
from the set of crossing coordinates, yielding birth–death pairs that capture
loop and void structures in the diagram.  These topological signatures are
summarized as persistence diagrams and vectorized using persistence images,
providing features that are invariant under planar isotopy.

We also construct **graph representations** of knot projections where vertices
correspond to crossings and edges to the arcs between them.  A Graph Neural
Network (GNN) encoder learns embeddings of these graphs, capturing higher‑order
relationships that are not captured by scalar invariants such as crossing
number or braid index.

The TDA and GNN features are concatenated with the existing invariant set and
fed into a regularized regression model.  Preliminary experiments show that
these additional features improve predictive performance for knot complexity
metrics, uncovering patterns invisible to traditional linear models.

