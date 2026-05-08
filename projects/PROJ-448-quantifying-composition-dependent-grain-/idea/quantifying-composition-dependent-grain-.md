---
field: materials science
submitter: google.gemma-3-27b-it
---

# Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Field**: materials science

## Research question

How does the bulk concentration of substitutional alloying elements (Cr, Mo, V) influence their equilibrium segregation energy and equilibrium concentration at grain boundaries in body-centered cubic (BCC) alloys across varying temperatures?

## Motivation

Grain boundary segregation controls critical mechanical properties in BCC alloys including creep resistance, embrittlement susceptibility, and high-temperature strength. Current predictive models lack systematic quantitative relationships between bulk composition and segregation behavior, limiting rational alloy design. Establishing these composition-segregation relationships would enable targeted optimization of BCC alloys for structural applications.

## Related work

- [A Grain Boundary Embrittlement Genome for Substitutional Cubic Alloys (2025)](http://arxiv.org/abs/2502.06531v1) — Provides systematic segregation data for substitutional cubic alloys, establishing baseline trends for element-specific GB chemistry.
- [Modeling solute-grain boundary interactions in a bcc Ti-Mo alloy using density functional theory (2025)](http://arxiv.org/abs/2503.03538v1) — Demonstrates DFT-based calculation of segregation energies in BCC systems, validating computational approach for element-specific analysis.
- [Designing for Cooperative Grain Boundary Segregation in Multicomponent Alloys (2024)](http://arxiv.org/abs/2411.05303v1) — Establishes that cooperative effects between multiple solutes can amplify segregation beyond single-element predictions.
- [Grain Boundary Segregation and Embrittlement of Aluminum Binary Alloys from First Principles (2025)](http://arxiv.org/abs/2502.01579v1) — Provides methodological precedent for first-principles segregation analysis in binary alloy systems.
- [Relationship between grain boundary segregation and grain boundary diffusion in Cu-Ag alloys (2020)](http://arxiv.org/abs/2006.06591v2) — Connects segregation thermodynamics to kinetic behavior, relevant for understanding equilibrium profiles.

## Expected results

We expect to identify non-linear relationships between bulk solute concentration and GB segregation energy, with specific elements showing threshold concentrations where cooperative effects emerge. A positive correlation between segregation energy and embrittlement risk would confirm existing theoretical frameworks; a null result would suggest composition-independent segregation mechanisms. Statistical significance at p<0.05 across 5+ alloy systems would constitute publishable evidence.

## Methodology sketch

- Download open CALPHAD thermodynamic database files from NIST/Thermo-Calc open repositories (e.g., TCFE9 for Fe-based BCC systems)
- Extract equilibrium phase compositions for Fe-Cr-Mo, Fe-Cr-V, and Fe-Mo-V ternary systems at 500-900K temperature range
- Compute segregation energies using open-source DFT code (Quantum ESPRESSO) on pre-built BCC grain boundary supercell models from Materials Project
- Calculate equilibrium segregation profiles using McLean isotherm model with temperature-dependent parameters
- Fit empirical composition-segregation functions using linear regression with interaction terms for multicomponent effects
- Perform cross-validation across alloy systems (k-fold, k=5) to assess model generalizability
- Generate heatmaps of segregation energy vs. bulk composition and temperature for visualization
- Document all data sources with DOIs/URLs for reproducibility

## Duplicate-check

- Reviewed existing ideas: [N/A — existing_idea_paths not provided in input]
- Closest match: [N/A] (similarity sketch: N/A)
- Verdict: NOT a duplicate (insufficient corpus for comparison; recommend manual review before production)
