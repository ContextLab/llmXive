---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Field**: physics

## Research question

How does the topological network structure (coordination numbers, bond angle distributions) of amorphous solids correlate with the density of localized vibrational modes and their macroscopic thermal conductivity?

## Motivation

Amorphous solids lack long-range crystalline order, making standard phonon-based heat transport theories insufficient. Understanding the link between microscopic network topology and vibrational bottlenecks could reveal design principles for materials with tailored thermal insulation or conduction properties without requiring new experimental synthesis.

## Related work

- [Examining normal modes as fundamental heat carriers in amorphous solids: the case of amorphous silicon (2021)](http://arxiv.org/abs/2106.08459v2) — Establishes normal mode decomposition as a key method for microscopic understanding of thermal transport in amorphous systems.
- [Vibrational density of states of amorphous solids with long-ranged power-law correlated disorder in elasticity (2020)](http://arxiv.org/abs/2011.13180v1) — Provides theoretical framework for determining vibrational density based on spatial correlations in elastic constants.
- [Nanoscale thermal transport (2003)](https://doi.org/10.1063/1.1524305) — Reviews scientific understanding of thermal transport in nanoscale and disordered device structures, providing context for size effects.
- [Collectivity of motion in undercooled liquids and amorphous solids (2001)](http://arxiv.org/abs/cond-mat/0112267v1) — Demonstrates that structural motion in amorphous solids is highly collective, supporting the need for network-based analysis.

## Expected results

We expect to find a statistically significant negative correlation between the density of topological bottlenecks (under-coordinated regions) and thermal conductivity. The level of evidence required is a Spearman correlation coefficient > 0.7 across at least three distinct amorphous material datasets from public repositories.

## Methodology sketch

- Download pre-computed molecular dynamics trajectories and metadata (including thermal conductivity values) from public repositories such as Materials Cloud or Zenodo (e.g., amorphous silicon datasets).
- Parse atomic coordinates to construct a bond network using a distance cutoff based on the first minimum of the radial distribution function.
- Compute graph-theoretic metrics for each node, including coordination number and local bond angle variance.
- Calculate the global Vibrational Density of States (VDOS) via velocity autocorrelation functions using post-processing tools (e.g., LAMMPS dump analysis scripts).
- Identify localized vibrational modes by calculating the participation ratio for the VDOS spectrum.
- Aggregate network topology metrics and bottleneck densities per simulation box.
- Perform statistical correlation analysis (Pearson/Spearman) between topological metrics and the pre-recorded thermal conductivity values.
- Validate robustness by repeating analysis on at least three different system sizes to check for finite-size effects.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (no local corpus provided).
- Verdict: NOT a duplicate
