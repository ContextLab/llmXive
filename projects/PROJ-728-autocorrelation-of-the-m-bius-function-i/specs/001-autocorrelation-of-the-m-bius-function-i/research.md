# Research: Autocorrelation of the Möbius Function in Short Intervals

## Theoretical Background

### Chowla's Conjecture
Chowla's conjecture (1965) posits that for any distinct natural numbers $h_1, \dots, h_k$, the sum $\sum_{n \le x} \mu(n+h_1) \dots \mu(n+h_k) = o(x)$. In the case of $k=2$ (autocorrelation), this implies that the correlation between $\mu(n)$ and $\mu(n+h)$ should vanish as $x \to \infty$. Specifically, the normalized autocorrelation should approach 0.

### The Random Sign Heuristic
The conjecture is often supported by the heuristic that $\mu(n)$ behaves like a random sequence of $\{-1, 0, 1\}$ with specific probabilities ($P(\mu(n)=0) \approx 1 - 6/\pi^2$). If $\mu(n)$ is truly random in sign, the expected autocorrelation for $h \neq 0$ is zero. This project tests this heuristic empirically.

### The Prime Number Theorem (PNT) Baseline
To avoid circular reasoning in statistical testing, we also establish a theoretical baseline derived from the Prime Number Theorem. Under the assumption that the density of square-free numbers is $6/\pi^2$ and signs are random, the variance of the autocorrelation sum can be derived analytically. This provides an independent check against the permutation null: if the observed variance significantly deviates from the PNT prediction, it suggests arithmetic structure beyond simple random fluctuation.

## Dataset Strategy

Since the Möbius function is a deterministic arithmetic function, no external dataset download is required. The "dataset" is generated algorithmically.

| Dataset Component | Source/Method | Verification |
| :--- | :--- | :--- |
| **Möbius Sequence** ($\mu(n)$) | **Algorithmic Generation**: Linear Sieve (Meissel-Lehmer style) implemented in `code/sieve.py`. | **Verified**: The sieve is a standard, deterministic algorithm. Correctness is verified by unit tests against known values (e.g., $\mu(1)=1, \mu(2)=-1, \mu(4)=0$). |
| **Interval Parameters** | **Specified**: $L \in \{10^3, 10^4, 10^5\}$, $N=10^7$. | **Verified**: Defined in `spec.md`. |

**Note on Data Availability**: The assumption that $\mu(n)$ can be computed exactly for $N=10^7$ is valid. The linear sieve runs in $O(N)$ time and $O(N)$ space. For $N=10^7$, the memory footprint is ~10 MB (using `int8`), which is trivial for the target environment.

## Statistical Methodology

### 1. Autocorrelation Computation
For a window of length $L$ starting at $k$, the normalized autocorrelation at lag $h$ is:
$$ r_{k, L}(h) = \frac{1}{L-h} \sum_{i=1}^{L-h} \mu(k+i) \mu(k+i+h) $$
**Implementation**: Vectorized using `numpy`. The summation is performed over `int64` to prevent overflow before division, then cast to `float64` for the final value.

### 2. Theoretical Variance Benchmark (PNT)
To distinguish "random fluctuation" from "arithmetic structure" and avoid circularity:
- **Method**: Compute the theoretical variance of the autocorrelation sum under the Prime Number Theorem (PNT) assumption ($Var \approx \sigma^2 / L$, where $\sigma^2$ is derived from the density of square-free numbers).
- **Comparison**: Compare the observed variance against this theoretical baseline. Significant deviations from the theoretical variance indicate potential arithmetic structure not explained by random fluctuation.
- **Role**: This serves as an **arithmetic baseline**, independent of the permutation test.

### 3. Block-Permutation Test (Null Distribution)
To test the "random-sign heuristic" (whether $\mu$ is indistinguishable from a shuffled version of itself):
- **Procedure**:
  1. Extract the vector $v = [\mu(k+1), \dots, \mu(k+L)]$.
  2. Divide $v$ into $B$ blocks of size $b$ (e.g., $b=100$).
  3. Shuffle the order of these $B$ blocks while preserving the content of each block. This preserves local arithmetic structure (short-range correlations) while randomizing long-range order.
  4. Compute $r_{perm}(h)$ for the permuted vector.
  5. Repeat times.
- **Rationale**: A simple local shuffle destroys the very signal (long-range correlations) the project aims to detect. Block-permutation preserves local structure, allowing the test to detect if long-range correlations exist.
- **P-value**: Two-sided p-value = (count of $|r_{perm}(h)| \ge |r_{obs}(h)|$) / 1000.
- **Interpretation**: A low p-value indicates $\mu$ is **not** indistinguishable from its shuffled version (violation of the heuristic). A uniform distribution of p-values (across many intervals) indicates the heuristic holds.

### 4. Multiple Comparison Correction
Since we test multiple lags ($h \in \{1, \dots, L/2\}$) and multiple intervals, we must address family-wise error.
- **Method**: Apply the **Benjamini-Hochberg (BH)** procedure to control the False Discovery Rate (FDR) across all tested lags and intervals.
- **Uniformity Check**: Verify the **uniformity of the p-value distribution** under the null hypothesis (SC-005) using the **Kolmogorov-Smirnov (KS) test**.
- **Crucial Distinction**: The KS test checks if the *observed* p-values are uniform. If they are, it means the data is consistent with the *shuffled* data (validating the heuristic). If they are not, it means the data is distinguishable from the shuffled data. This is **not** a proof of Chowla's Conjecture, but a test of the random-sign heuristic.

### 5. Sensitivity Analysis
As per FR-007, we will perturb the zero-count by $\pm 5\%$ and $\pm 10\%$ in the permutation step to verify if the statistical significance of the observed autocorrelation is robust to slight variations in the assumed zero-density.

## Compute Feasibility & Rationale

**Decision**: CPU-first execution.

**Rationale**:
1.  **Sieve**: $O(N)$ integer operations. $10^7$ ops is ~0.1s on modern CPU.
2.  **Autocorrelation**: Optimized via sliding window. With $L=10^5$, $N=10^7$, and 100 sampled windows, this is feasible.
3.  **Block-Permutation**: A sufficient number of permutations will be performed. of length $10^5$ with block size 100. $10^3 \times 100$ shuffles per window. For a set of windows, this is well within the 6h limit.
4.  **GPU**: Not required. No matrix multiplication or deep learning models are involved.

**Feasibility Check**:
- **RAM**: $10^7$ `int8` = 10 MB. Intermediate arrays for permutation = 100 MB max. **Safe** (< 7 GB).
- **Disk**: Output CSVs, PNGs, and JSON < 50 MB. **Safe** (< 14 GB).
- **Time**: Estimated total runtime < 4 hours. **Safe** (< 6h).

## Limitations & Assumptions

- **Observational Nature**: The study is computational, not experimental. We cannot "randomize" the Möbius function; we can only test if its structure *resembles* a random process.
- **Window Selection**: We use **Randomized Stratified Sampling** to avoid periodic bias. We cannot test *every* possible window of length $L$ in $N=10^7$ due to time constraints.
- **Zero-Density**: The permutation test assumes the observed zero-density is the true parameter. The sensitivity analysis (FR-007) addresses uncertainty in this parameter.
- **Theoretical Variance**: The theoretical variance benchmark assumes the Prime Number Theorem holds. Deviations from this benchmark may indicate arithmetic structure.
- **Short Interval Variance**: In short intervals, the variance of the sum is naturally high ($O(\sqrt{L})$). The theoretical variance benchmark helps distinguish this noise from signal.
- **Interpretation of Results**: The permutation test validates the **random-sign heuristic**, not Chowla's Conjecture directly. Uniform p-values mean $\mu$ is indistinguishable from a shuffled version. Deviations from the PNT baseline indicate arithmetic structure.