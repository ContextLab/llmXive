# Unconventional Analytical Lenses

This document records the exploratory use of **topological data analysis (TDA)** and **graph neural network (GNN)** embeddings to uncover patterns in knot diagrams that are not captured by traditional regression models.

* **Persistent Homology** – We compute persistence diagrams from point‑cloud representations of knot diagrams using the `tda.compute_persistence` utility (to be implemented).
* **GNN Embeddings** – Projection graphs of knots are embedded via a graph‑neural‑network encoder (`gnn.embed_projection`), yielding feature vectors for downstream analysis.

The generated features are saved in `data/processed/tda_features.json` and `data/processed/gnn_embeddings.npy` for further exploratory analysis.
