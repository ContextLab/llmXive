# Project Constitution: Predicting Material Stiffness from Microstructure

## Principle VI: Numerical Homogenization and Analytical Bounds

This project permits the use of **FFT-based numerical homogenization** to compute effective elastic stiffness tensors for synthetic microstructures. This method is validated for periodic microstructures and is the primary ground-truth generator for the dataset.

**Validity of Analytical Bounds**:
Analytical bounds (Voigt-Reuss-Hill) are documented and used strictly for:
1. Validating the physical plausibility of FFT-computed results.
2. Filtering invalid microstructure generations (e.g., non-convergent solvers).
3. Providing a baseline for error analysis.

The validity range for these bounds is defined for linear elastic, isotropic matrix phases with embedded inclusions. Deviations outside this range (e.g., plastic deformation, anisotropic matrix) are explicitly excluded from the current scope.
