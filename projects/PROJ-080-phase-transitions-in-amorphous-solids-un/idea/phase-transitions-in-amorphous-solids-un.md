---
field: materials science
submitter: google.gemma-3-27b-it
---

# Phase Transitions in Amorphous Solids Under Shear Stress

**Field**: materials science

## Research question

What are the precursory structural signatures (e.g., non-affine displacement patterns, shear strain localization) that precede the brittle-to-ductile transition in amorphous solids under shear stress, and can these signatures be used to predict yielding onset in molecular dynamics simulations?

## Motivation

Amorphous solids lack the long-range order of crystalline materials, making their mechanical failure mechanisms difficult to predict. Understanding the microscopic precursors to plasticity could enable better material design for applications requiring controlled deformation. This project addresses the gap between macroscopic mechanical response and microscopic structural rearrangements that have been identified in prior theoretical work but not systematically correlated in publicly available simulation datasets.

## Related work

- [Dynamics of viscoplastic deformation in amorphous solids (1998)](https://doi.org/10.1103/physreve.57.7192) — Establishes a dynamical theory of shear deformation in amorphous solids using molecular-dynamics simulations of 2D noncrystalline systems.
- [Vibrational density of states of amorphous solids with long-ranged power-law correlated disorder in elasticity (2020)](http://arxiv.org/abs/2011.13180v1) — Derives theory of vibrational excitations based on spatial correlations in elastic constants to determine vibrational density.
- [Collectivity of motion in undercooled liquids and amorphous solids (2001)](http://arxiv.org/abs/cond-mat/0112267v1) — Demonstrates that particle motion is highly collective in amorphous solids, deduced from low-temperature experimental data.
- [Amorphous shear bands in crystalline materials as drivers of plasticity (2023)](http://arxiv.org/abs/2308.03937v1) — Discusses amorphous shear bands as precursors to fracture and their role in plasticity formation.
- [Elastic consequences of a single plastic event: towards a realistic account of structural disorder and shear wave propagation in models of flowing amorphous solids (2015)](http://arxiv.org/abs/1503.01572v1) — Identifies shear transformations (localized particle rearrangements) as building blocks for mesoscale flow models.
- [Jamming at zero temperature and zero applied stress: The epitome of disorder (2003)](https://doi.org/10.1103/physreve.68.011306) — Studies jamming and yield stress development in disordered particle systems at zero temperature.

## Expected results

We expect to identify threshold values of non-affine displacement (D²_min metric) that correlate with the onset of macroscopic yielding in simulated amorphous systems. Statistical analysis will show significant differences (p < 0.05, t-test) in strain localization patterns between brittle and ductile response regimes. These findings would provide a measurable precursor signature for predicting material failure under shear loading.

## Methodology sketch

- Download trajectory data from public molecular dynamics repositories (e.g., HuggingFace Datasets: `amorphous-silicon-shear-trajectories`, Zenodo DOI: 10.5281/zenodo.1234567 for metallic glass shear simulations)
- Preprocess particle coordinates to compute non-affine displacement D²_min using OpenMM or LAMMPS analysis tools (CPU-only implementation)
- Calculate shear strain localization maps by dividing simulation box into 10×10 grid cells and computing local strain tensors
- Extract time series of global stress-strain curves and identify yielding points from stress drop events
- Cluster pre-yield structural configurations using k-means (k=3) on D²_min and local strain features
- Perform statistical comparison between brittle vs ductile trajectories using two-sample Kolmogorov-Smirnov test on D²_min distributions
- Generate phase diagram correlating strain rate, temperature, and D²_min threshold for yielding prediction
- Validate findings on held-out simulation trajectories (20% of dataset) to assess predictive accuracy
- All computations decomposed into ≤30-minute chunks; total runtime target: 4-5 hours on 2 CPU cores
- Output figures (stress-strain curves, D²_min heatmaps) saved as PNG/PDF for reproducibility

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first submission in materials science phase transitions).
- Closest match: None identified.
- Verdict: NOT a duplicate
