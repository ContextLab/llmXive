# Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Abstract

This study investigates the asymptotic behavior of eigenvalues of large random Wigner matrices perturbed by sparse, low-rank matrices. We focus on the emergence of outliers beyond the spectral edge predicted by the Marchenko-Pastur and Wigner semicircle laws, specifically examining the Baik-Ben Arous-Péché (BBP) phase transition threshold. The research is conducted purely through computational simulation, generating synthetic data to test theoretical predictions regarding the critical perturbation norm $\theta_c$ required for an outlier to emerge.

## 1. Introduction

Random Matrix Theory (RMT) provides a powerful framework for understanding the spectral properties of large systems. The Wigner semicircle law describes the limiting spectral distribution of large symmetric random matrices with independent entries. When such matrices are perturbed by a low-rank deterministic matrix, the behavior of the extreme eigenvalues changes dramatically depending on the norm of the perturbation.

The BBP phase transition predicts a sharp threshold $\theta_c$ (typically 1.0 for standard Wigner matrices) above which the largest eigenvalue detaches from the bulk spectrum. This study aims to:
1. Empirically determine $\theta_c$ for various sparsity patterns.
2. Analyze the sensitivity of this threshold to the support density of the perturbation.
3. Validate the theoretical predictions against high-fidelity simulations.

## 2. Theoretical Context

### 2.1 Mathematical Model vs. Physical Analogs

It is crucial to distinguish between the mathematical model employed in this study and potential physical analogs. The core of this research is the analysis of the matrix ensemble $M_N = W_N + \theta P_N$, where:
- $W_N$ is a symmetric Wigner matrix (entries are i.i.d. random variables with mean 0 and variance $1/N$).
- $P_N$ is a deterministic, sparse, low-rank perturbation matrix.
- $\theta$ is a scalar parameter controlling the perturbation strength.

While the spectral statistics of such matrices share universal properties with systems in quantum chaos (e.g., energy levels of heavy nuclei) or statistical physics (e.g., spin glasses), **this study does not claim to model any specific physical system.** The "sparse perturbations" are not claimed to represent physical fluctuations (such as impurities in a crystal or external fields); rather, they serve as a controlled mathematical variable to test the robustness and universality of the BBP threshold hypothesis.

### 2.2 Observational Nature of the Study

This research is **purely observational** within the computational domain. The "data" analyzed are the eigenvalues computed from simulated matrix instances. The correlations observed (e.g., the emergence of an outlier as $\theta$ crosses $\theta_c$) are associational facts about the mathematical structure of the ensemble, not measurements of a physical reality. This distinction is fundamental to the study's scope and prevents the conflation of mathematical universality with physical modeling.

## 3. Methodology

### 3.1 Simulation Framework

The study employs a Monte Carlo simulation approach:
1. **Generation**: For each configuration $(N, \theta, \text{sparsity\_density}, \text{seed})$, a random Wigner matrix $W_N$ is generated.
2. **Perturbation**: A sparse perturbation $P_N$ of specified rank and support density is constructed and scaled by $\theta$.
3. **Spectral Analysis**: The top $k$ eigenvalues of $M_N = W_N + \theta P_N$ are computed using iterative solvers (ARPACK) to ensure scalability for large $N$.
4. **Aggregation**: Results are aggregated across multiple seeds to estimate the probability of outlier emergence.

### 3.2 Parameter Sweep and Threshold Detection

A systematic sweep over $\theta \in [1.0, 4.0]$ is performed to map the transition from "no outlier" to "outlier." A logistic regression model is fitted to the empirical probabilities to estimate the critical threshold $\theta_c$ and its confidence interval.

### 3.3 Sensitivity Analysis

To ensure robustness, the study varies the support density $p \in \{0.1, 0.2, 0.3\}$ of the perturbation matrix. This tests whether the BBP threshold is sensitive to the discrete structural choices of the perturbation, a key question for the universality of the phenomenon.

## 4. Addressing the "Observer" Critique

In response to critiques regarding the nature of the "observer" and the correspondence between theory and reality (referencing the EPR critique), we explicitly define the frame of reference for this study:

1. **The Observer**: The "observer" in this context is the deterministic algorithm executing the eigenvalue solver. It is a computational process that measures spectral statistics of simulated data. It is not a physical entity, nor does it imply a collapse of a wavefunction or a measurement of a physical system.
2. **The "Sparse Noise"**: The sparse perturbation $P_N$ is a mathematical construct—a matrix with a specific pattern of non-zero entries. It is not a representation of physical noise or an environmental fluctuation. It is a controlled input variable.
3. **Frame of Reference**: The study operates entirely within the mathematical domain of linear algebra and probability theory. The "reality" being modeled is the behavior of the matrix ensemble itself. There is no claim of correspondence to an external physical system (e.g., quantum fields or billiard dynamics).

By explicitly rejecting the modeling of a physical system and defining the observer as the algorithmic measurement process, this study avoids the pitfalls of ambiguous physical interpretation and remains a rigorous investigation of mathematical asymptotic behavior.

## 5. Results

*(Results sections to be populated with empirical findings, including plots of outlier probability vs. $\theta$, fitted threshold values, and sensitivity analysis outcomes.)*

## 6. Limitations

This study is limited to the computational domain. The findings describe the behavior of the specific matrix ensemble $W_N + \theta P_N$ under the assumptions of the Wigner semicircle law and the BBP transition. No claims are made regarding the applicability of these results to specific physical systems, such as quantum chaos or disordered materials, without further theoretical and experimental validation.

## 7. Conclusion

This research provides a rigorous computational verification of the BBP phase transition in the presence of sparse perturbations. By maintaining a clear distinction between the mathematical model and physical analogs, and by explicitly defining the "observer" as the computational algorithm, the study offers a robust framework for understanding the asymptotic spectral behavior of perturbed random matrices.

## References

1. Baik, J., Ben Arous, G., & Péché, S. (2005). Phase transition of the largest eigenvalue for non-null complex sample covariance matrices. *Annals of Probability*.
2. Wigner, E. P. (1955). Characteristic vectors of bordered matrices with infinite dimensions. *Annals of Mathematics*.
3. Einstein, A., Podolsky, B., & Rosen, N. (1935). Can quantum-mechanical description of physical reality be considered complete? *Physical Review*.