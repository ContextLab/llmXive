---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

**Field**: physics

## Research question

How does the connectivity of local atomic network motifs in amorphous silicon quantitatively influence macroscopic thermal conductivity?

## Motivation

While the reduced thermal conductivity of amorphous silicon compared to its crystalline counterpart is established, the specific contribution of topological disorder versus vibrational anharmonicity remains debated. Resolving this relationship enables targeted materials design for thermoelectric applications without requiring exhaustive simulation of every atomic configuration.

## Literature gap analysis

### What we searched

Searches were performed on Semantic Scholar and arXiv using queries focused on "topological descriptors thermal conductivity amorphous silicon" and "machine learning thermal conductivity silicon potentials". These queries returned four results, with two directly addressing the intersection of structure, machine learning, and thermal transport in silicon.

### What is known

- [Topological descriptor of thermal conductivity in amorphous materials (2021)](http://arxiv.org/abs/2107.05865v2) — Establishes a framework for linking structural topology to transport properties in amorphous Si, though using hand-crafted descriptors rather than learned graph representations.
- [Thermal Conductivity Modeling using Machine Learning Potentials: Application to Crystalline and Amorphous Silicon (2019)](http://arxiv.org/abs/1907.09088v1) — Demonstrates the viability of machine learning approaches for predicting thermal properties in silicon systems, validating the methodological direction.

### What is NOT known

No published work has explicitly quantified the correlation between *graph neural network-derived* local connectivity motifs and thermal conductivity variations across multiple independent amorphous samples. Existing work relies on static descriptors or ML potentials for energy, not learned structural features predicting transport directly.

### Why this gap matters

Understanding whether local network topology is a primary driver of heat transport would allow materials scientists to engineer disorder at the atomic scale to tune thermal properties for thermal management or energy harvesting. Without this link, design remains empirical rather than predictive.

### How this project addresses the gap

This project constructs atomic graphs from molecular dynamics snapshots and trains a lightweight GNN to predict local heat flux, directly testing the topology-conductivity link. By correlating GNN feature importance with measured thermal conductivity, we provide the first data-driven evidence on the specific topological motifs that impede phonon transport.

## Expected results

We expect to find a significant correlation between specific high-coordination motifs and reduced phonon mean free paths. A positive correlation would confirm topology as a primary driver, while a null result would suggest anharmonicity dominates regardless of local connectivity, refining current theoretical models.

## Methodology sketch

- Download pre-equilibrated amorphous silicon configurations (e.g., from Zenodo or Materials Cloud) to avoid costly quenching steps within the 6-hour runtime.
- Compute thermal conductivity using Non-Equilibrium Molecular Dynamics (NEMD) with the Stillinger-Weber potential (LAMMPS CPU version) on 216-atom supercells.
- Construct atomic graphs where nodes are atoms and edges represent bonds within a 3.0 Å cutoff radius.
- Extract graph features (degree distribution, clustering coefficients) and train a lightweight Graph Neural Network (PyTorch Geometric, CPU, 2 layers) to predict local heat flux.
- Perform Pearson correlation analysis between graph-derived topological metrics and global thermal conductivity across 10-20 independent samples.
- Validate model performance against the analytical baseline from the literature to ensure the GNN captures physical signal rather than noise.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: N/A.
- Verdict: NOT a duplicate
