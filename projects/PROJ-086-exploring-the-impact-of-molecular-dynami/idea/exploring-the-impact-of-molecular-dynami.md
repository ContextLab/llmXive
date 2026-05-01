---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

**Field**: chemistry

## Research question

How do variations in force field selection, simulation duration, and temperature settings in molecular dynamics simulations affect the accuracy and uncertainty of predicted protein-ligand binding affinities?

## Motivation

Molecular dynamics simulations are increasingly used in drug discovery pipelines, yet the sensitivity of binding affinity predictions to methodological parameters remains poorly quantified. This gap hinders the establishment of robust protocols for virtual screening and may lead to unreliable hit identification. Systematically characterizing parameter-induced uncertainty will enable more reproducible MD-based affinity predictions.

## Related work

- [Ligand-induced protein dynamics differences correlate with protein-ligand binding affinities: An unsupervised deep learning approach (2021)](http://arxiv.org/abs/2109.01339v1) — Demonstrates that protein dynamics correlate with binding affinity, supporting the relevance of MD simulation parameters.
- [Atomic Convolutional Networks for Predicting Protein-Ligand Binding Affinity (2017)](http://arxiv.org/abs/1703.10603v1) — Discusses empirical scoring functions and force fields commonly used with MD in early drug discovery stages.
- [Predicting Protein-Ligand Binding Affinity via Joint Global-Local Interaction Modeling (2022)](http://arxiv.org/abs/2209.13014v1) — Highlights limitations of existing prediction methods that often neglect parameter sensitivity.
- [DeepAtom: A Framework for Protein-Ligand Binding Affinity Prediction (2019)](http://arxiv.org/abs/1912.00318v1) — Notes that binding affinity calculation is a cornerstone of computational drug design, underscoring the need for reliable methods.
- [ff19SB: Amino-Acid-Specific Protein Backbone Parameters Trained against Quantum Mechanics Energy Surfaces in Solution (2019)](https://doi.org/10.1021/acs.jctc.9b00591) — Provides evidence that force field choice significantly impacts MD simulation accuracy.
- [CHARMM: The biomolecular simulation program (2009)](https://doi.org/10.1002/jcc.21287) — Describes a widely used molecular simulation program suitable for parameter sensitivity analysis.
- [Accurate and generalizable protein-ligand binding affinity prediction with geometric deep learning (2025)](http://arxiv.org/abs/2504.16261v1) — Shows ongoing advances in affinity prediction but does not address MD parameter uncertainty.
- [CAML: Commutative algebra machine learning -- a case study on protein-ligand binding affinity prediction (2025)](http://arxiv.org/abs/2504.18646v1) — Introduces alternative ML approaches for affinity prediction, complementing physics-based MD methods.

## Expected results

We expect to observe measurable variance (≥10% coefficient of variation) in binding affinity estimates when varying force fields or simulation lengths. Statistical analysis will reveal which parameters contribute most to prediction uncertainty, enabling evidence-based protocol recommendations for MD-based virtual screening.

## Methodology sketch

- Download a subset of protein-ligand complexes from PDBbind v2020 (https://www.pdbbind.org.cn/) — select 50 high-resolution complexes (≤2.0 Å) with experimental binding constants.
- Prepare initial structures using OpenMM or GROMACS with explicit solvent (TIP3P) and neutralizing ions.
- Define 3 force field variants: ff14SB, ff19SB, and CHARMM36m.
- Define 3 simulation lengths: 5 ns, 10 ns, 20 ns (each ≤30 minutes on 2 CPU cores).
- Define 2 temperature settings: 300 K and 310 K.
- Run 45 total MD simulations (50 complexes × 3 force fields × 3 lengths × 2 temperatures → subsample to fit 6h budget; prioritize 20 complexes with full factorial design).
- Extract binding free energy estimates using MM-PBSA or MM-GBSA post-processing on MD trajectories.
- Compute root-mean-square deviation (RMSD) between predicted and experimental binding affinities for each parameter combination.
- Perform two-way ANOVA to assess main effects and interactions of force field, length, and temperature on prediction error.
- Generate variance component plots to identify dominant uncertainty sources.

## Duplicate-check

- Reviewed existing ideas: [N/A — no existing fleshed-out ideas provided in input].
- Closest match: None identified.
- Verdict: NOT a duplicate
