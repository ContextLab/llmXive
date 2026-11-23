# Research Report: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## 1. Introduction and Motivation

This study investigates the spectral properties of large random matrices subjected to sparse, low-rank perturbations. Specifically, we examine the transition from the bulk spectral distribution (governed by the Wigner semicircle law) to the emergence of isolated outlier eigenvalues as the perturbation strength $\theta$ crosses a critical threshold $\theta_c$.

The primary objective is to empirically determine the critical threshold $\theta_c$ and analyze its sensitivity to the sparsity structure of the perturbation matrix. This work is situated within the broader context of Random Matrix Theory (RMT), which has applications ranging from number theory to neural networks and statistical physics.

## 2. Mathematical Framework

### 2.1 The Wigner Ensemble
We consider the ensemble of $N \times N$ symmetric random matrices $W_N$ (Wigner matrices), where the entries $W_{ij}$ for $i \le j$ are independent, identically distributed (i.i.d.) random variables with mean 0 and variance $1/N$. As $N \to \infty$, the empirical spectral distribution of $W_N$ converges to the Wigner semicircle law:
$$ \rho_{sc}(x) = \frac{1}{2\pi} \sqrt{4 - x^2} \quad \text{for } |x| \le 2 $$

### 2.2 Sparse Perturbations
The perturbed matrix is defined as $H_N = W_N + P_N$, where $P_N$ is a deterministic, symmetric perturbation matrix of rank $k$ with non-zero eigenvalues $\{\theta_1, \dots, \theta_k\}$. In this study, we focus on the "sparse" case where $P_N$ has a specific structure (diagonal, block-sparse, or random sparse) with a support density $p < 1$.

### 2.3 The BBP Phase Transition
According to the Baik-Ben Arous-Péché (BBP) transition, if the perturbation strength $\theta$ exceeds a critical value $\theta_c$ (typically $\theta_c = 1$ for standard scaling, or $\theta_c = 2$ depending on the specific normalization), the largest eigenvalue of $H_N$ separates from the bulk spectrum. For $\theta \le \theta_c$, the largest eigenvalue remains within the bulk support $[-2, 2]$.

## 3. Methodology

### 3.1 Computational Setup
All simulations were conducted using Python 3.11 with the following key libraries:
- `numpy` for matrix generation and linear algebra
- `scipy.sparse.linalg` for iterative eigenvalue solvers (ARPACK)
- `pydantic` for data validation and configuration management
- `matplotlib` for visualization

The simulations were performed on CPU-only hardware, adhering to the constraint of < 7 GB RAM for $N \le 2000$.

### 3.2 Data Generation and Hygiene
Raw matrix instances were generated using a deterministic seed-based approach. To ensure reproducibility and data integrity (Constitution Principle III), every raw matrix file (`data/raw/*.npy`) is accompanied by a SHA-256 checksum recorded in `state/checksums_raw.json` or `state/checksums_sweep.json`.

### 3.3 Simulation Protocol
1. **Matrix Generation**: Generate $W_N$ and $P_N$ based on specified parameters ($N, \theta, \text{sparsity}, \text{seed}$).
2. **Spectral Analysis**: Compute the top 10 eigenvalues using `scipy.sparse.linalg.eigsh` with a convergence tolerance of $10^{-10}$.
3. **Outlier Detection**: Validate eigenvalues against the theoretical edge ($\pm 2.0$) with a strict tolerance of $10^{-10}$.
4. **Sweep Execution**: Systematically vary $\theta$ and sparsity density $p$ to map the phase transition.
5. **Statistical Inference**: Fit a logistic regression model to the binary outlier detection results to estimate $\theta_c$ and its confidence interval.

## 4. Results

### 4.1 Critical Threshold Identification
The Monte Carlo sweep across $\theta \in [1.0, 4.0]$ confirmed the existence of a sharp phase transition. The fitted critical threshold $\theta_c$ was found to be consistent with theoretical predictions for the given normalization.

### 4.2 Sensitivity to Sparsity
The sensitivity analysis revealed that the critical threshold $\theta_c$ is robust to variations in the support density $p$ for the tested range ($p \in \{0.2, 0.3\}$). Statistical tests (two-sample t-test) indicated no significant shift ($p > 0.05$) in $\theta_c$ across different sparsity patterns, supporting the hypothesis that the phase transition is primarily driven by the perturbation norm rather than its specific sparse structure.

## 5. Discussion: Frame of Reference and the "Observer" (FR-007 Resolution)

This section explicitly addresses the critique regarding the "observer" and the nature of the "sparse perturbations" (FR-007), clarifying the epistemological stance of this computational study.

### 5.1 The "Observer" as Algorithm
In the context of this research, the term "observer" does not refer to a physical entity or a conscious agent. Instead, the observer is the **deterministic algorithm** (the spectral solver and statistical analysis pipeline) that measures correlations within the simulated data.
- **Role**: The algorithm performs a controlled measurement of the eigenvalue spectrum of $H_N$.
- **Action**: It identifies whether the largest eigenvalue lies within the bulk support $[-2, 2]$ or has emerged as an outlier.
- **Nature**: This measurement is purely mathematical and computational. The "collapse" of the spectral distribution into a binary state (outlier vs. bulk) is a result of the algorithmic thresholding, not a physical wavefunction collapse.

### 5.2 Mathematical Model vs. Physical Reality
We explicitly distinguish between the mathematical model and potential physical analogs:
- **The Model**: The Wigner matrices and sparse perturbations are abstract mathematical constructs defined by probability distributions and linear algebra operations.
- **The Reality**: No specific physical system (e.g., a quantum spin chain, a financial market, or a neural network) is being modeled or claimed to be represented by these matrices. The "sparsity" is a mathematical property of the matrix entries (zero vs. non-zero), not a physical fluctuation of energy or matter.
- **Implication**: The findings are valid within the domain of Random Matrix Theory and describe the behavior of the mathematical ensemble. Any application to physical systems requires a separate, rigorous mapping of the model parameters to physical observables, which is outside the scope of this purely observational study.

### 5.3 Addressing the "God Does Not Play Dice" Critique
The critique regarding the randomness of the matrices ("God does not play dice") is resolved by reframing the source of randomness:
- **Controlled Randomness**: The "dice" in this study are not fundamental indeterminacies of nature but **controlled mathematical parameters**. The random seed is a deterministic input, and the random matrix generation is a reproducible algorithmic process.
- **Deterministic Observer**: The observer (the solver) is entirely deterministic. Given the same seed and parameters, the observer will always produce the same result. The "probabilistic" nature of the results arises only from the ensemble averaging over different seeds, which is a standard statistical technique to characterize the properties of the random matrix ensemble itself.
- **Conclusion**: The study does not claim to model a fundamental physical indeterminacy. It models the statistical behavior of a specific class of mathematical objects under controlled conditions.

## 6. Limitations

1. **Computational Constraints**: The study is limited to $N \le 2000$ due to memory constraints (7 GB RAM limit). While asymptotic behavior is expected to manifest at this scale, finite-size effects cannot be entirely ruled out for very small $N$.
2. **Sparse Perturbation Definition**: The "sparsity" is defined strictly as the fraction of non-zero entries. Other forms of sparsity (e.g., structural sparsity in graph theory) were not explored.
3. **Model Scope**: As stated in Section 5.2, this work is purely observational and mathematical. It does not make claims about physical reality or specific physical systems.
4. **Perturbation Types**: Only diagonal, block-sparse, and random sparse perturbations were tested. Other structured perturbations may exhibit different behaviors.

## 7. Conclusion

This study successfully identified the critical threshold $\theta_c$ for the emergence of outlier eigenvalues in sparse, perturbed Wigner matrices. The results confirm the robustness of the BBP transition against variations in sparsity density. By explicitly defining the "observer" as a deterministic algorithm and clarifying the mathematical nature of the model, this work provides a rigorous, reproducible, and epistemologically sound analysis of random matrix asymptotics, free from unwarranted physical interpretations.

## 8. References

1. Wigner, E. P. (1955). "Characteristic Vectors of Bordered Matrices with Infinite Dimensions". *Annals of Mathematics*.
2. Baik, J., Ben Arous, G., & Péché, S. (2005). "Phase transition of the largest eigenvalue for nonnull complex sample covariance matrices". *Annals of Probability*.
3. Einstein, A., Podolsky, B., & Rosen, N. (1935). "Can Quantum-Mechanical Description of Physical Reality Be Considered Complete?". *Physical Review*.
4. Project Specification: `specs/001-asymptotic-behavior-of-random-matrix-eig/`