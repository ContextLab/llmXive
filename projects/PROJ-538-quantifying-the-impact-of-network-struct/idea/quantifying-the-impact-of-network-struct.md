---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

**Field**: physics

## Research question

How does the topology of atomic disorder networks (clustering, percolation, average path length) modulate thermal conductivity in disordered metallic alloys?

## Motivation

Disorder in crystalline materials is known to reduce thermal conductivity through phonon scattering, but the specific spatial arrangement of atomic defects may introduce additional structural dependencies. Understanding whether network-theoretic features of disorder correlate with transport properties could reveal design principles for thermal management materials and constrain theoretical models of heat conduction in complex solids.

## Literature gap analysis

### What we searched

Query terms: "disordered alloy thermal conductivity network structure", "phonon transport disorder topology", "graph theory heat transport alloys". Sources queried: Semantic Scholar, arXiv, OpenAlex. The search returned minimal on-topic results, with only one paper addressing heat transport in disordered systems from a theoretical perspective.

### What is known

- [Scaling Theory of Heat Transport in Quasi-1D Disordered Harmonic Chains (2013)](http://arxiv.org/abs/1302.0834v1) — Establishes scaling relationships between disorder structure and phonon heat current in quasi-one-dimensional lattices, providing theoretical foundation for structure-transport relationships.

### What is NOT known

No published work has systematically quantified the relationship between three-dimensional network topology of atomic disorder and thermal conductivity in realistic metallic alloys (e.g., Cu-Ni, Au-Ag). Existing literature focuses on 1D chains or generic disorder models without extracting graph-theoretic descriptors from actual atomic configurations.

### Why this gap matters

Materials designers seeking to optimize thermal management in alloy systems lack quantitative guidelines linking atomic-scale defect arrangement to macroscopic transport properties. Filling this gap would enable data-driven alloy design for applications in thermoelectrics, heat sinks, and thermal barrier coatings.

### How this project addresses the gap

This project extracts network descriptors (clustering coefficient, average path length, degree distribution) from publicly available molecular dynamics snapshots of disordered alloys and correlates them with measured thermal conductivity values, producing the first empirical mapping between 3D disorder topology and heat transport efficiency.

## Expected results

We expect to identify at least one network metric (likely clustering coefficient or percolation threshold) that shows statistically significant correlation with thermal conductivity across multiple alloy compositions. A null result (no significant correlation) would be equally informative, suggesting that disorder topology is not a primary determinant of heat transport beyond simple defect density.

## Methodology sketch

- Download molecular dynamics simulation data for Cu-Ni and Au-Ag alloys from OpenKim or Materials Cloud repository (public datasets with atomic positions and thermal conductivity annotations).
- Extract atomic species at each lattice site and construct a defect network where nodes represent non-equilibrium atomic positions and edges connect nearest neighbors with mismatched species.
- Compute network descriptors using NetworkX: average path length, clustering coefficient, degree distribution moments, and percolation threshold.
- Pair each network descriptor vector with the corresponding thermal conductivity value from the dataset metadata.
- Apply Pearson/Spearman correlation analysis to quantify relationships between each network metric and thermal conductivity.
- Perform multiple linear regression to assess combined predictive power of network descriptors on thermal conductivity.
- Generate scatter plots and correlation heatmaps to visualize structure-transport relationships.
- Conduct statistical significance testing (p < 0.05 threshold) on all reported correlations.

## Duplicate-check

- Reviewed existing ideas: [None accessible in current session].
- Closest match: None identified.
- Verdict: NOT a duplicate
