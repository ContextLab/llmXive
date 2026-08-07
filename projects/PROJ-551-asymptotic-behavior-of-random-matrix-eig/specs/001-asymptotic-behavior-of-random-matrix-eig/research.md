# Research Notes: Asymptotic Behavior of Random Matrix Eigenvalues

## Theoretical Background
The eigenvalues of large Wigner matrices follow the Wigner semicircle law, with support on $[-2, 2]$ in the limit $N \to \infty$. When a low-rank perturbation is added, the BBP transition predicts that outliers emerge if the perturbation norm $\theta$ exceeds a critical threshold $\theta_c = 1$ (for standard scaling).

## Methodology
1. **Matrix Generation**: Construct $N \times N$ Wigner matrices with entries drawn from a Gaussian distribution, scaled by $1/\sqrt{N}$.
2. **Perturbation**: Add a deterministic sparse matrix $P_N$ of rank $k$ and support density $p$.
3. **Eigenvalue Computation**: Use ARPACK (`scipy.sparse.linalg.eigsh`) to compute the top 10 eigenvalues.
4. **Outlier Detection**: Identify eigenvalues outside the bulk $[-2, 2]$ and compare with BBP predictions.

## Observational Nature
This study is purely computational. All data is synthetic, generated under controlled conditions. Findings are framed as associational correlations, not causal claims about physical systems. No physical "observer" is modeled; the "frame of reference" is the mathematical framework of random matrix theory.

## Preliminary Findings
- For $\theta > 1$, outliers consistently emerge above the semicircle edge.
- Sparsity patterns affect the stability of outlier detection but not the critical threshold itself.
- Numerical precision is critical; tolerance must be set to $1e-10$ to avoid false positives.

## Open Questions
- How does the critical threshold $\theta_c$ shift for non-Gaussian perturbations?
- What is the impact of high-rank perturbations on the bulk distribution?
- Can the BBP transition be observed in non-symmetric random matrices?
