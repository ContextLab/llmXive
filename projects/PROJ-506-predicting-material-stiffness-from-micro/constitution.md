# Project Constitution: Predicting Material Stiffness from Microstructure

## I. Purpose
This document establishes the fundamental principles and constraints governing the **PROJ-506** project.

## II. Scientific Integrity
- All ground truth data must be derived from physically valid models.
- All model predictions must be validated against independent test sets.

## III. Reproducibility
- All experiments must be deterministic given a fixed random seed.
- Code and data must be version-controlled.

## IV. Computational Constraints
- Training must complete on CPU-only infrastructure within 6 hours.
- Memory usage must not exceed available RAM (streaming required).

## V. Data Privacy & Security
- No real-world proprietary material data will be used; only synthetic data generated per protocol.

## VI. Numerical Homogenization (Amended)
> **Principle VI**: The project permits the use of **FFT-based numerical homogenization** (specifically the Moulinec-Suquet scheme) to compute effective elastic stiffness tensors for stochastic microstructures. This method shall be considered the ground truth for model training, provided that results are validated against Voigt-Reuss-Hill bounds for physical plausibility.

## VII. Governance
- Changes to this constitution require a formal amendment proposal (see `docs/`).
- Amendments must be approved before data generation or model training begins.
