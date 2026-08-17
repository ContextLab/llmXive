# Project Constitution

## I. Purpose
This document establishes the fundamental principles governing the llmXive automated science pipeline for predicting material stiffness from microstructure images.

## II. Scientific Integrity
All research outputs must be reproducible, transparent, and grounded in physical reality. Synthetic data generation must be clearly distinguished from experimental measurements.

## III. Data Provenance
Every data point must be traceable to its source. Metadata must include generation parameters, seeds, and validation status.

## IV. Methodology Transparency
All algorithms, hyperparameters, and preprocessing steps must be explicitly documented and version-controlled.

## V. Validation Standards
Models must be validated against independent test sets. Performance metrics must be reported with confidence intervals where applicable.

## VI. Numerical Homogenization
**Principle VI:** The project explicitly permits the use of **FFT-based numerical homogenization** as the ground-truth method for calculating effective elastic stiffness tensors from microstructure images. This method is recognized as a rigorous alternative to analytical homogenization for complex microstructures, provided that:
1. The solver converges to a physically valid solution.
2. Results are validated against Voigt-Reuss-Hill bounds.
3. Convergence criteria and numerical parameters are explicitly logged.

This amendment supersedes any prior restriction favoring only analytical methods for complex topologies where closed-form solutions are intractable.

## VII. Governance
Amendments to this constitution require a formal proposal, review, and consensus as defined in the project governance protocol.

## VIII. Revision History
- v1.0: Initial constitution.
- v1.1: Amendment to Principle VI permitting FFT-based numerical homogenization (Task T002a).