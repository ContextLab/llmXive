# Project Constitution: Predicting Material Stiffness from Microstructure Images

## Preamble
This document establishes the governing principles, constraints, and scientific standards for the PROJ-506 research pipeline. All code, data generation, and analysis must adhere to these principles.

## Core Principles

### Principle I: Reproducibility
All experiments must be fully reproducible. Code, seeds, and configuration files must be version-controlled and archived with results.

### Principle II: Physical Consistency
All generated material properties must respect fundamental physical laws, including thermodynamic stability and mechanical bounds (e.g., Voigt-Reuss-Hill).

### Principle III: Data Integrity
No synthetic data shall be used as "ground truth" without explicit numerical verification against a validated solver.

### Principle IV: CPU-First Optimization
Unless explicitly authorized, all pipelines must target CPU execution to ensure accessibility and cost-efficiency.

### Principle V: Statistical Rigor
Hypothesis testing must use methods appropriate for the data distribution and sample size, with corrections for multiple comparisons where necessary.

### Principle VI: Numerical Homogenization via FFT
**Amended**: The project explicitly permits and encourages the use of Fast Fourier Transform (FFT)-based numerical homogenization methods (e.g., Moulinec-Suquet scheme) for computing effective elastic stiffness tensors from microstructure images.

This principle overrides any prior restriction favoring purely analytical homogenization for complex microstructures, provided that:
1. The FFT solver is validated against known analytical bounds (Voigt-Reuss-Hill).
2. The discretization resolution is sufficient to capture the microstructural features (minimum 128x128 pixels as per FR-001).
3. The implementation is optimized for CPU execution (no CUDA dependency) to align with Principle IV.

This amendment aligns with Plan Task 0.2 and supports the primary claim (c_55975982) regarding the prediction of stiffness from microstructure.

## Governance
Changes to this constitution require a formal amendment proposal (see `docs/constitution_amendment_proposal.md`) and approval by the project governance body.