---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

**Field**: physics

## Research question

How do specific topological features (bond orientational order and medium-range order) in amorphous silicon networks quantitatively correlate with variations in thermal conductivity?

## Motivation

Thermal management in amorphous silicon (a-Si) photovoltaics is critical for device efficiency, yet current theoretical models struggle to link local atomic disorder to macroscopic heat transport. This project addresses the gap between structural topology and thermal properties, aiming to identify design rules for materials with optimized heat dissipation.

## Related work

- [Strong phase correlation between diffusons governs heat conduction in amorphous silicon (2021)](http://arxiv.org/abs/2110.10487v1) — Establishes the role of diffusons and vibrational phase correlation in a-Si heat conduction, providing a theoretical baseline for transport mechanisms.
- [Real space information from Fluctuation electron microscopy: Applications to amorphous silicon (2007)](http://arxiv.org/abs/0707.4012v1) — Demonstrates methods for extracting medium-range order information from amorphous silicon, relevant for defining structural descriptors.

## Expected results

We expect to identify specific structural descriptors (e.g., ring statistics or bond order parameters) that exhibit a strong correlation (Pearson r > 0.7) with thermal conductivity. The evidence will confirm that medium-range order, rather than just short-range coordination, is a primary determinant of thermal transport suppression in disordered systems.

## Methodology sketch

- **Data Acquisition**: Download existing molecular dynamics trajectories of amorphous silicon from public repositories (e.g., Zenodo or HuggingFace Datasets) to avoid computationally expensive generation on the runner.
- **Graph Construction**: Use `NetworkX` to convert atomic coordinates into graphs where nodes are atoms and edges represent bonds within a cutoff radius.
- **Descriptor Calculation**: Compute topological metrics including ring statistics, bond orientational order parameters, and clustering coefficients for each configuration.
- **Transport Analysis**: Utilize pre-calculated thermal conductivity values associated with the downloaded trajectories, or run Green-Kubo calculations on small subsystems (<1000 atoms) to ensure execution within the 6-hour runner limit.
- **Statistical Modeling**: Apply Ridge regression to map structural descriptors to thermal conductivity values.
- **Validation**: Perform k-fold cross-validation and report R^2 scores and p-values to assess the significance of the correlations.
- **Visualization**: Generate scatter plots and feature importance charts using `Matplotlib` to visualize the structure-transport relationship.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: None.
- Verdict: NOT a duplicate
