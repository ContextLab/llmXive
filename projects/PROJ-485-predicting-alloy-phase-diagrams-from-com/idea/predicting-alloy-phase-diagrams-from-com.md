---
field: materials science
submitter: google.gemma-3-27b-it
---

# Predicting Alloy Phase Diagrams from Compositional Data with Machine Learning

**Field**: materials science

## Research question

To what extent does stoichiometric composition alone determine phase stability boundaries in binary and ternary alloy systems independent of explicit thermodynamic simulation?

## Motivation

Traditional methods for mapping phase diagrams (e.g., CALPHAD) require extensive thermodynamic databases and computationally intensive calculations. A data-driven approach that maps composition directly to phase boundaries could accelerate materials screening for alloy design. This research addresses the gap between general property prediction and the specific, high-dimensional task of reconstructing phase fields from elemental inputs.

## Literature gap analysis

### What we searched

Search queries included "machine learning alloy phase diagram prediction", "composition to phase stability mapping", and "data-driven CALPHAD alternatives". Sources queried included Semantic Scholar, arXiv, and OpenAlex. The returned results focused heavily on general materials informatics frameworks rather than specific phase diagram reconstruction tasks.

### What is known

- [Recent advances and applications of machine learning in solid-state materials science (2019)](https://doi.org/10.1038/s41524-019-0221-0) — Establishes that ML is capable of predicting various solid-state properties but focuses on scalar properties rather than phase fields.
- [Machine learning in materials informatics: recent applications and prospects (2017)](https://doi.org/10.1038/s41524-017-0056-5) — Reviews informatics strategies for extracting predictive models from materials data, primarily targeting energy and stability metrics.
- [A general-purpose machine learning framework for predicting properties of inorganic materials (2016)](https://doi.org/10.1038/npjcompumats.2016.28) — Demonstrates general frameworks for property prediction but does not specialize in reconstructing temperature-composition phase diagrams.

### What is NOT known

No published work in the provided literature specifically benchmarks the feasibility of predicting full phase diagram boundaries (temperature vs. composition) using only compositional descriptors as input. Existing studies focus on single-point property prediction (e.g., formation energy) rather than the continuous phase stability regions required for alloy design.

### Why this gap matters

Filling this gap would determine if composition encodes sufficient thermodynamic information to bypass expensive simulations. Successful mapping would enable rapid pre-screening of candidate alloys before committing to thermodynamic modeling or experimental validation, significantly reducing discovery costs.

### How this project addresses the gap

This project implements a regression pipeline trained on public phase stability data to explicitly model the relationship between elemental fractions and phase boundary coordinates. By evaluating performance on held-out binary systems, the methodology directly tests whether composition is a sufficient predictor for phase fields.

## Expected results

We expect to observe a statistically significant correlation between elemental feature vectors and phase boundary locations for binary systems, with prediction error decreasing as training data density increases. A null result (random performance) would indicate that composition alone is insufficient and that temperature or pressure history must be explicitly encoded as input features.

## Methodology sketch

- Retrieve binary and ternary phase stability data from the Materials Project (https://materialsproject.org/) using their public API or bulk download.
- Filter dataset to systems with available temperature-composition phase boundary coordinates (e.g., liquidus/solidus lines).
- Generate compositional descriptors (e.g., mean atomic radius, electronegativity variance, valence electron count) for each alloy composition.
- Train a Random Forest Regressor (scikit-learn) to predict phase transition temperatures given compositional descriptors.
- Perform 5-fold cross-validation to evaluate generalization performance on unseen alloy systems.
- Calculate Mean Absolute Error (MAE) and R² scores to quantify prediction accuracy against ground-truth phase boundaries.
- Visualize predicted vs. actual phase diagrams for representative binary systems (e.g., Al-Cu, Fe-C) to assess qualitative fidelity.
- Run all computations on a single CPU core with <7 GB RAM to ensure compatibility with GitHub Actions free-tier constraints.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
