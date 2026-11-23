# Constitution: Automated Science Pipeline

## Principle VI: Numerical Homogenization
The system shall use **FFT-based numerical homogenization** to compute effective material properties from microstructure images.

**Validity Range:** The validity range of the analytical bounds (Voigt-Reuss-Hill) used for verification is documented for the specific microstructure topology in the data generation logs. The FFT solver is valid for linear elastic, isotropic constituent phases with known stiffness tensors.

## Principle III: Data Hygiene
All generated data must be validated against physical bounds and schema definitions before being used for training.

## Principle VII: Generalization Boundary
The system must explicitly disclose the boundaries of its generalization capabilities, particularly regarding out-of-distribution density ranges.
