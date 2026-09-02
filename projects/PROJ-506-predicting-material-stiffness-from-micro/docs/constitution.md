# Project Constitution: Predicting Material Stiffness from Microstructure

## Version: 1.0.0
## Last Updated: 2023-10-27

## Preamble
This document establishes the governing principles, constraints, and ethical guidelines for the automated science pipeline project **PROJ-506**. All research, code generation, and data analysis must adhere to these principles.

## Principle I: Scientific Integrity
All data generated, processed, or analyzed must be traceable to its source. Synthetic data must be explicitly labeled as such. No results shall be fabricated or selectively reported to support a predetermined hypothesis.

## Principle II: Reproducibility
Every experiment, model training run, and statistical analysis must be fully reproducible given the code, configuration, and input data artifacts. Version control and artifact hashing are mandatory.

## Principle III: Computational Efficiency
Solutions must be optimized for the target hardware (CPU-only free-tier constraints). Algorithms must be selected to ensure completion within the defined time budget (6 hours for training).

## Principle IV: Data Privacy and Security
No personal identifiable information (PII) shall be used. All synthetic data generation must ensure that no real-world material data is inadvertently leaked or reverse-engineered.

## Principle V: Transparency
All assumptions, limitations, and potential biases in the models and data generation processes must be documented and reported in the final analysis.

## Principle VI: Numerical Homogenization and Analytical Bounds
**Explicit Permission and Constraints for FFT-Based Methods**

1. **Permitted Method**: This project explicitly permits the use of **FFT-based numerical homogenization** (Fast Fourier Transform) for computing the effective elastic stiffness tensors of periodic microstructures. This method is approved as the primary ground truth generator for the dataset, provided the implementation is stable and converges within the defined tolerance.

2. **Validity Range of Analytical Bounds**:
 The project acknowledges the validity of analytical bounds (Voigt-Reuss-Hill, Mori-Tanaka, and Hashin-Shtrikman) for validation purposes.
 - **Voigt Bound**: Valid as the upper bound for stiffness assuming uniform strain.
 - **Reuss Bound**: Valid as the lower bound for stiffness assuming uniform stress.
 - **Hill Average**: The arithmetic mean of Voigt and Reuss bounds, serving as the standard reference for isotropic approximations.
 - **Constraint**: The FFT-based numerical results **MUST** fall within the Voigt-Reuss bounds. If a computed stiffness tensor falls outside these bounds, the microstructure generation or the solver configuration is considered invalid and must be discarded.
 - **Documentation**: The validity of these bounds is documented for inclusion densities ranging from 0.0 to 1.0 and for the specific two-phase material system (matrix and void/inclusion) defined in the data generation schema.

3. **Solver Requirements**:
 - The FFT solver must handle periodic boundary conditions.
 - Convergence criteria must be strictly enforced (e.g., relative residual < 1e-4).
 - CPU-optimized implementations (e.g., using `pyfftw` or `scipy.fft`) are required to meet the execution time constraints.

## Principle VII: Ethical AI Usage
AI models used in this pipeline are tools for assistance and automation. Final scientific interpretation and responsibility for results rest with the human researchers.

## Principle VIII: Continuous Improvement
This constitution may be amended only through a formal proposal process (see `amendment_process.md`) requiring consensus and verification of the proposed changes against scientific best practices.
