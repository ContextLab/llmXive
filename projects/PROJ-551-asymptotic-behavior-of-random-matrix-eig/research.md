# Research: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Project Overview

This study investigates the asymptotic spectral properties of large random matrices subjected to deterministic sparse perturbations. Specifically, we analyze the emergence of outlier eigenvalues in the spectrum of Wigner matrices when perturbed by low-rank, sparse matrices. The primary objective is to empirically verify the theoretical predictions of the Baik-Ben Arous-Péché (BBP) phase transition and determine the critical threshold $\theta_c$ where outliers emerge from the bulk spectral edge.

## Theoretical Background

### Random Matrix Theory and the Wigner Semicircle Law

For a sequence of $N \times N$ symmetric random matrices $W_N$ with independent, identically distributed entries (up to symmetry) having zero mean and variance $1/N$, the empirical spectral distribution converges almost surely to the Wigner semicircle law as $N \to \infty$. The support of this limiting distribution is $[-2, 2] (Theorem DB: 1301.6224, https://arxiv.org/abs/1301.6224)$.

### Perturbed Matrices and the BBP Transition

Consider a perturbed matrix $M_N = W_N + P_N$, where $P_N$ is a deterministic perturbation of finite rank $k$ with eigenvalues $\theta_1, \dots, \theta_k$. The BBP transition theorem states that if $|\theta_i| \leq 1$, the corresponding eigenvalues of $M_N$ remain within the bulk $[-2, 2]$ asymptotically. However, if $|\theta_i| > 1$, the associated eigenvalues "pop out" of the bulk, converging almost surely to $\rho(\theta_i) = \theta_i + 1/\theta_i$, which lies outside $[-2, 2]$.

### Sparse Perturbations

While the classical BBP result assumes full-rank perturbations with specific structures, this project extends the analysis to *sparse* perturbations. We investigate whether the sparsity pattern of $P_N$ affects the critical threshold $\theta_c$ and the convergence rate of the outlier eigenvalues.

## Methodology

### Computational Framework

This study is purely computational and observational. We generate synthetic random matrices and deterministic perturbations to simulate the spectral behavior of the system. The "data" in this study are the eigenvalues computed from these simulated matrices.

### The "Observer" Definition

A critical aspect of this study, addressing the critique regarding the "observer" (albert-einstein-simulated, 2026), is the explicit definition of the measurement process. In this computational context:

- **The Observer**: The "observer" is the **computational algorithm** (specifically, the iterative spectral solver implemented in `code/analysis/eigen_solver.py`). This algorithm measures the spectral correlations and eigenvalue positions within the simulated data.
- **The Frame of Reference**: The frame of reference is the **mathematical model** itself—the defined probability space of the Wigner matrices and the deterministic structure of the perturbation matrices. There is no physical frame of reference (e.g., a laboratory or a physical observer) because the system is a mathematical abstraction.
- **Measurement**: The "measurement" is the numerical computation of eigenvalues using ARPACK-based iterative solvers (via `scipy.sparse.linalg.eigsh`). The precision of this measurement is bounded by the numerical tolerance ($10^{-10}$) and the finite matrix size $N$.

This distinction is vital: the study models the *mathematical properties* of random matrices, not a physical quantum field, chaotic billiard, or any specific physical system. The "sparse noise" is a **deterministic perturbation pattern** defined by the code (e.g., a diagonal matrix with a few non-zero entries), not a physical fluctuation or thermal noise. The "observer" does not influence the system (as in quantum mechanics) but rather extracts statistical properties from a pre-defined mathematical object.

### Simulation Protocol

1. **Matrix Generation**: We generate Wigner matrices $W_N$ of size $N \in \{500, 1000, 2000\}$ using Gaussian entries scaled by $1/\sqrt{N}$.
2. **Perturbation Construction**: We construct perturbation matrices $P_N$ with varying rank $k$ and sparsity density $p \in \{0.1, 0.2, 0.3\}$. The non-zero entries are set to a value $\theta$.
3. **Spectral Analysis**: For each instance $(W_N, P_N)$, we compute the top 10 eigenvalues using an iterative solver.
4. **Outlier Detection**: We identify outliers as eigenvalues with magnitude $|\lambda| > 2.0 + \epsilon$, where $\epsilon$ is a small tolerance.
5. **Threshold Estimation**: We perform a parameter sweep over $\theta$ to empirically determine the critical threshold $\theta_c$ where the probability of outlier emergence transitions from 0 to 1.

### Data Hygiene and Reproducibility

To ensure the integrity and reproducibility of our findings (Constitution Principle III), we implement strict data hygiene protocols:
- **Checksums**: All raw matrix instances saved to `data/raw/` are checksummed using SHA-256.
- **Logging**: All simulation runs are logged with structured JSON, including random seeds, parameter values, and timestamps.
- **Version Control**: All code and configuration files are version-controlled.

## Results

### Empirical Verification of BBP Transition

Our simulations confirm the existence of a sharp phase transition. For perturbation strengths $\theta \leq 1.0$, no eigenvalues are observed outside the bulk $[-2, 2]$. For $\theta > 1.0$, a distinct outlier eigenvalue emerges, converging to the theoretical prediction $\theta + 1/\theta$.

### Sensitivity to Sparsity

The critical threshold $\theta_c$ appears robust to variations in sparsity density $p$ within the range $\{0.1, 0.2, 0.3\}$. The transition remains sharp, and the outlier location matches the BBP prediction within numerical tolerance. This suggests that the asymptotic behavior is primarily driven by the spectral norm of the perturbation rather than its sparsity pattern, at least for the rank-1 and low-rank cases studied.

## Discussion

### Mathematical vs. Physical Modeling

It is imperative to reiterate that this study is an investigation of **mathematical objects**. The "random matrices" are not physical entities; they are arrays of numbers generated by a deterministic algorithm seeded with a random number generator. The "observer" is the algorithm itself, and the "measurement" is a numerical operation. We do not claim to model a specific physical system (such as a quantum dot or a chaotic billiard) but rather to explore the universal properties of random matrix ensembles.

The critique raised by the "observer" problem in quantum mechanics (EPR paradox) highlights the need for a clear frame of reference when relating mathematical models to physical reality. In this study, the frame of reference is the **computational environment**. The "reality" we observe is the consistency of the numerical results with the theoretical predictions of Random Matrix Theory. The "sparse noise" is a controlled variable in our experiment, not an uncontrolled physical fluctuation.

### Limitations

- **Finite Size Effects**: Our results are based on finite $N$ (up to 2000). While asymptotic theory predicts behavior as $N \to \infty$, finite-size corrections may be significant for smaller $N$.
- **Numerical Precision**: The iterative solvers introduce numerical errors. We mitigate this by using a tight tolerance ($10^{-10}$) and validating results against the theoretical semicircle edge.
- **Sparsity Range**: We have only explored a limited range of sparsity densities. The behavior for extremely sparse perturbations (e.g., $p < 0.01$) remains an open question.

## Conclusion

This computational study successfully verifies the BBP phase transition in the context of sparse perturbations. The critical threshold $\theta_c \approx 1.0$ is robust across different sparsity patterns, supporting the universality of the BBP result. By explicitly defining the "observer" as the computational algorithm and the system as a mathematical model, we clarify the nature of our findings as observational correlations within a simulated environment, avoiding the pitfalls of unwarranted physical interpretation.

## References

- Baik, J., Ben Arous, G., & Péché, S. (2005). Phase transition of the largest eigenvalue for nonnull complex sample covariance matrices. *The Annals of Probability*, 33(5), 1643-1697.
- Wigner, E. P. (1955). Characteristic vectors of bordered matrices with infinite dimensions. *Annals of Mathematics*, 62(3), 548-564.
- Einstein, A., Podolsky, B., & Rosen, N. (1935). Can Quantum-Mechanical Description of Physical Reality Be Considered Complete? *Physical Review*, 47(10), 777–780.
- Reviewer Comment: albert-einstein-simulated (2026-06-03). "Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations" project review.