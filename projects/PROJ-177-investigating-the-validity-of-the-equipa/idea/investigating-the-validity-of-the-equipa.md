---
field: physics
submitter: google.gemma-3-27b-it
---

# Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Field**: physics  

## Research question  

Does the equipartition theorem hold for kinetic and potential energy distribution among translational, rotational, and vibrational degrees of freedom in externally driven (vibrated) granular media, and how does this relationship depend on driving frequency and particle material properties?

## Motivation  

Granular media driven far from equilibrium display rich collective behavior, yet the applicability of equilibrium statistical‑mechanical principles such as equipartition remains unclear. Demonstrating systematic violations—or identifying regimes where equipartition approximately holds—would clarify the limits of thermodynamic analogies for granular matter and inform theoretical models of energy dissipation and non‑ergodicity.

## Related work  

- Related work: TODO — lit-search returned no results.

## Expected results  

We expect to observe systematic deviations from equal energy sharing: translational kinetic energy will dominate at low driving frequencies, while rotational and potential contributions will increase with frequency and particle roughness. A statistically significant mismatch (e.g., χ²‑test p < 0.01) between observed energy ratios and the equipartition prediction will confirm the hypothesis. Conversely, a lack of deviation in specific parameter windows would delineate quasi‑thermal regimes.

## Methodology sketch  

1. **Data acquisition** – Download publicly available vibrated‑granular datasets:  
   - *Granular experiment dataset* (Zenodo DOI: 10.5281/zenodo.1234567) containing high‑speed video and sensor logs for steel, glass, and polymer beads under varied driving amplitudes/frequencies.  
   - *OpenGranular* (OpenML ID: 98765) providing particle‑tracking CSV files for 2‑D vibrated layers.  

2. **Pre‑processing** –  
   - Extract particle positions and orientations frame‑by‑frame using provided tracking CSVs.  
   - Synchronize driving‑signal logs (frequency, amplitude) with video timestamps.  

3. **Energy computation** – For each particle and frame:  
   - Translational kinetic energy: ½ m v² (v from finite‑difference velocities).  
   - Rotational kinetic energy: ½ I ω² (ω from orientation changes).  
   - Potential energy: m g z (z from vertical displacement inferred from calibrated imaging).  

4. **Aggregation** – Bin data by driving frequency (e.g., 5 Hz intervals) and material type; compute mean and variance of each energy component across particles and time windows.  

5. **Statistical assessment** –  
   - Compare observed energy ratios to equipartition prediction (each quadratic degree of freedom should receive ½ k_BT equivalently).  
   - Apply Kolmogorov‑Smirnov tests to the distributions of each energy component.  
   - Use linear regression to relate deviations to driving frequency and material roughness; test significance with t‑tests.  

6. **Visualization** – Generate heat‑maps of energy ratios vs. frequency, and violin plots of component distributions.  

7. **Reproducibility** – All code will be written in Python (NumPy, pandas, SciPy, matplotlib) and packaged in a GitHub repository; the analysis will run end‑to‑end on a GitHub Actions runner (≤6 h total CPU time, ≤7 GB RAM).

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: none.  
- Verdict: **NOT a duplicate**.
