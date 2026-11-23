# Research: Quantifying the Information Content of Quantum Entanglement in Many-Body Systems

## Summary of Inquiry

This research investigates the relationship between **bipartite entanglement entropy** (a measure of quantum correlations) and **Kolmogorov complexity** (a measure of algorithmic information content) in 1D many-body quantum systems. The hypothesis is that structured physical states (Heisenberg/Ising) exhibit a distinct, positive correlation between these metrics, whereas random noise (product states) and maximally mixed states (Haar ensembles) form distinct clusters or outliers.

**Critical Refinement**: To avoid confounding system size (N) with entanglement structure, the analysis focuses on **entropy per spin** ($S/N$) and **Normalized Compression Distance (NCD)** relative to a random baseline of the same size. Correlation is computed **within fixed spin-count groups** and via **partial correlation** controlling for N.

## Theoretical Background

### Entanglement Entropy
Entanglement entropy quantifies the information shared across a bipartition of a quantum system. For a pure state $|\psi\rangle$ divided into subsystems $A$ and $B$, the reduced density matrix $\rho_A = \text{Tr}_B(|\psi\rangle\langle\psi|)$ is computed. The von Neumann entropy $S = -\text{Tr}(\rho_A \log \rho_A)$ serves as the standard measure. In critical systems, this scales logarithmically with subsystem size (Calabrese & Cardy, 2004).
**Normalization**: We report $S_{norm} = S/N$ to isolate structural entropy from size scaling.

### Algorithmic Complexity & Compression
Kolmogorov complexity $K(x)$ is the length of the shortest program producing $x$. It is uncomputable but well-approximated by lossless compression ratios (Li et al., 2004).
**Normalization**: We use the **Normalized Compression Distance (NCD)**:
$$ NCD(x,y) = \frac{C(xy) - \min(C(x), C(y))}{\max(C(x), C(y))} $$
where $y$ is a random baseline vector of the same size as $x$. This measures how much more compressible $x$ is compared to a random state of the same dimension, isolating *structure* from *randomness*.
**Scope**: Compression is applied to the **reduced representation** (e.g., singular values of $\rho_A$ or the subsystem vector $A$), not the full $2^N$ state vector, to prevent the metric from being a proxy for vector length.

### The Link
Theoretical work (e.g., Brown & Susskind, 2016) suggests a deep connection between quantum complexity and entanglement. While entanglement entropy saturates for volume-law states, complexity continues to grow. This project tests if, in the context of *finite-size* 1D systems, the *structure* of entanglement (non-random correlations) creates a compressible pattern in the reduced representation that random states lack.

## Dataset Strategy

The project relies on wavefunction coefficients for Heisenberg and Transverse-Field Ising models (spin counts ranging from low to moderate levels).

**Verified Datasets**:
*Note: No verified external Zenodo/HuggingFace dataset exists containing pre-computed wavefunction coefficients for N=10-40 Heisenberg/Ising models.*
1.  **Primary Source**: Internal generation.
    *   **N <= 20**: Exact Diagonalization (ED) using `scipy.sparse.linalg.eigsh`.
    *   **N > 20**: DMRG using `TeNPy` library (CPU-optimized).
    *   *Constraint*: This is the primary strategy, not a fallback, as no external source exists.
2.  **Null Models**: Generated internally (Random Product States, Haar-random ensembles).

**Data Access Plan**:
- **Generation**: Wavefunctions are generated deterministically using pinned random seeds.
- **Streaming**: For DMRG (N>20), wavefunctions are generated and processed in chunks to avoid loading the full state vector into RAM.
- **Validation**: Generated data is checksummed and stored in `data/raw/`.

## Methodology & Statistical Rigor

### 1. Data Preprocessing
- **Quantization**: Floating-point coefficients are quantized to signed integers (FR-003a) to ensure reproducibility.
- **Normalization**: Wavefunctions are normalized to unit length.
- **Reduced Representation**: For complexity estimation, we use the singular values of the reduced density matrix or the subsystem vector, not the full state.

### 2. Metric Computation
- **Entanglement**: Compute reduced density matrix $\rho_A$ for a half-chain cut. Perform SVD (using `scipy.sparse.linalg.svds` with ARPACK) to get singular values $\lambda_i$. Compute $S = -\sum \lambda_i^2 \log(\lambda_i^2)$. Report $S_{norm} = S/N$.
- **Complexity**: Serialize quantized **reduced** vector to binary. Compress with `gzip`, `lzma`, `bzip2`. Calculate ratio $R = \frac{Size_{comp}}{Size_{raw}}$.
- **NCD**: Compute NCD relative to a random baseline $y$ of the same size: $NCD = (C(xy) - \min(C(x), C(y))) / \max(C(x), C(y))$.

### 3. Null Models
- **Random Product States**: Generate random vectors on the Bloch sphere for each spin. These have near-zero entanglement but high complexity (random noise).
- **Maximally Mixed States**: Generate an ensemble of Haar-random pure states (FR-004a). Compute the average metrics. These should have maximal entanglement and high complexity.
- **Distinctness**: The hypothesis is that physical states (high entropy) will have a **lower NCD** (more compressible structure) than Haar states (maximal entropy, maximal complexity) due to the underlying Hamiltonian constraints.

### 4. Correlation Analysis
- **Stratification**: Correlation will be computed **within fixed spin-count groups** (N) to avoid confounding by system size.
- **Partial Correlation**: A partial correlation analysis will be performed controlling for N.
- **Primary**: Compute Pearson and Spearman correlation coefficients ($r$) between $S_{norm}$ and NCD for physical states.
- **Significance**: Perform a t-test against the null hypothesis $r=0$.
- **Comparison**: Compare the correlation trend of physical states vs. null models using Welch's t-test or ANOVA (SC-005).

### 5. Robustness (Bootstrap)
- Perform a sufficient number of bootstrap iterations (FR-006) to generate 95% confidence intervals for $r$.
- Use bias-corrected percentile method if skewness > 0.5.

### 6. Statistical Validity Checks
- **Multiple Comparisons**: If multiple correlations are tested (e.g., across different spin sizes or compressors), apply Bonferroni correction to the p-values.
- **Collinearity**: Acknowledge that for small systems, entanglement and complexity may be definitionally linked by system size; the analysis controls for N via partial correlation and stratification.
- **Power**: With N=10-40 spins and A set of configurations, power is limited. The bootstrap CI will explicitly reflect this uncertainty.
- **Circular Validation**: By using NCD (relative to random) and reduced representations, we test for *structural* compressibility beyond what is expected from the Schmidt spectrum alone, avoiding a trivial identity.

## Compute Feasibility (CPU-First)

- **SVD**: For 40 spins, the reduced density matrix is $2^{20} \times 2^{20}$. Dense SVD is prohibited. The plan uses `scipy.sparse.linalg.svds` (ARPACK) which fits in <4 GB RAM.
- **Compression**: Trivial CPU load on reduced vectors.
- **Bootstrap**: 1000 iterations of correlation on ~50 points is negligible (< 1 minute).
- **Total Runtime**: Estimated < 2 hours on 2-core CPU, well within the established time limit.
- **GPU**: Not required.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailable** | High | No external dataset exists. Primary strategy is internal generation (ED/DMRG). |
| **Memory Overflow (N=40)** | High | Strict use of sparse matrices; streaming generation; limit N to 30 if 40 is too large. |
| **Compression Bias** | Medium | Use multiple compressors (gzip, lzma, bzip2) and NCD relative to random baseline. |
| **Numerical Instability** | Medium | Filter NaNs/Infs; fail if valid count < 8 (FR-008). |
| **Confounding by N** | High | Mandate partial correlation and stratified analysis. |
| **DMRG Convergence** | Medium | Use robust DMRG settings; fallback to ED for smaller N. |