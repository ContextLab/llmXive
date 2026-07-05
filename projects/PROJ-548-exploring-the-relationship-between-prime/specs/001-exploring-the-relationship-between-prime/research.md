# Research: Exploring the Relationship Between Prime Gaps and the Riemann Hypothesis

## Summary

This research phase investigates the statistical relationship between the distribution of **maximal prime gaps** and the **pair-correlation of non-trivial zeros** of the Riemann zeta function. The hypothesis posits that the distribution of normalized maximal gaps aligns with the **GUE-predicted extreme value distribution**, a consequence of the Montgomery-Odlyzko conjecture.

## Theoretical Background

### Prime Gaps and the Cramér Model
The gap $g_n = p_{n+1} - p_n$ between consecutive primes is conjectured to follow a distribution related to the Cramér model, where primes are treated as a random sequence with density $1/\log n$. The maximal gap $g_{max}$ in an interval up to $x$ is expected to scale as $\log^2 x$.

### Riemann Zeta Zeros and GUE
The non-trivial zeros of the Riemann zeta function, $\rho = 1/2 + i\gamma$, exhibit spacing statistics that align with the eigenvalues of random matrices from the Gaussian Unitary Ensemble (GUE). The pair-correlation function for normalized zero spacings $s$ is given by:
$$ R_2(s) = 1 - \left( \frac{\sin(\pi s)}{\pi s} \right)^2 $$

### The Connection (Montgomery-Odlyzko)
The Montgomery-Odlyzko conjecture relates the pair-correlation of zeros to the pair-correlation of primes. While the conjecture is about pair-correlation, it implies a specific distribution for **extreme values** (maximal gaps) via Extreme Value Theory. This project tests the *distributional similarity* between normalized maximal prime gaps and the **GUE-derived extreme value CDF**, rather than a direct comparison to the pair-correlation density.

## Dataset Strategy

### Verified Datasets
The following datasets have been verified for accessibility and format. **Only these sources are used.**

| Dataset | Description | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **LMFDB Primes** | Large-scale prime data (parquet) | ` | Verified |
| **LMFDB Zeros** | Non-trivial zeros of zeta function | ` (API) | Verified |

*Note: The project will use the LMFDB API to fetch zeta zeros. If the API is unreachable or the data format is invalid, the pipeline will halt with a "Data Unavailable" flag. Local generation of zeta zeros is **strictly forbidden** as it violates Constitution Principle II (Verified Accuracy) and FR-002.*

### Data Acquisition Plan
1. **Primes**: If the verified LMFDB prime dataset does not cover up to $N=10^{10}$, the `generate_primes.py` script will execute a segmented sieve locally to generate the required range. This is an acceptable fallback for *coverage* because the sieve algorithm is deterministic and mathematically verified, satisfying the 'Verified Accuracy' principle for generated data.
2. **Zeros**: The script `ingest_zeros.py` will fetch zeros from the LMFDB API. If the API is unreachable, the pipeline halts. **Local generation via `mpmath` is explicitly DISABLED** as a fallback to strictly adhere to the "Verified Source" requirement of FR-002 and Constitution Principle II.

## Methodological Approach

### 1. Data Preprocessing
- **Primes**: Generate or load primes up to $N=10^{10}$. Compute consecutive gaps $g_n$.
- **Normalization**: Normalize gaps by the Cramér prediction: $g_{norm} = g_n / (\log p_n)^2$.
- **Zeros**: Load zeros, sort by imaginary part, compute spacings $s_n = \gamma_{n+1} - \gamma_n$. Normalize spacings by the mean spacing at that height.

### 2. Distributional Comparison (Primary Analysis)
- **Sliding Windows**: Compute the maximum normalized gap within sliding windows of size $W = 10^6$.
- **Empirical Distribution**: Construct the empirical CDF of these **maximal normalized gaps**.
- **Theoretical Distribution**: Calculate the **theoretical CDF of maximal gaps** derived from the GUE pair-correlation function via Extreme Value Theory (EVT). This involves integrating the GUE pair-correlation to find the distribution of the maximum in a window of size $W$.
- **Statistical Test**: Perform a Kolmogorov-Smirnov (KS) test to compare the empirical distribution of maximal gaps against the **GUE-derived Max Gap CDF**.
 - $H_0$: The distributions are identical (i.e., primes follow GUE extreme value statistics).
 - $H_1$: The distributions differ.

### 3. Robustness & Null Hypothesis
- **Cramér Model Simulation**: Generate a synthetic dataset of "random" primes based on the Cramér model. Compute maximal gaps and perform the KS test against the GUE-derived Max Gap CDF. This establishes the expected behavior under the null hypothesis of random primes.
- **Sensitivity Analysis**: Repeat the primary analysis for window sizes $W \in \{10^5, 10^6, 2 \cdot 10^6\}$. The **theoretical GUE-derived Max Gap CDF** will be recalculated for each $W$ to ensure a valid comparison (removing the confound of window-size dependence).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: If multiple window sizes are tested, a Bonferroni correction will be applied to the p-values to control the family-wise error rate.
- **Causal Claims**: No causal claims are made. The analysis is purely observational and distributional.
- **Collinearity**: Since we are comparing distributions of derived statistics (max gaps vs. spacings) rather than individual pairs, standard collinearity issues do not apply.
- **Power**: The power of the KS test depends on the sample size of the maximal gaps ($N/W$). For $N=10^{10}$ and $W=10^6$, we have $\approx 10^4$ samples. This is generally sufficient, but the plan acknowledges that extreme value statistics require large samples for stability. Results will be interpreted with this limitation in mind.
- **Feasibility Fallback**: If the full sieve exceeds the 6-hour limit, the pipeline will switch to $N=10^9$ and log the reduced power, ensuring completion within SC-004 constraints.

## Decision Rationale

- **Why KS Test?** The hypothesis is about *distributional shape*, not mean or variance. KS is the non-parametric standard for comparing two continuous distributions.
- **Why Sliding Windows?** Maximal gaps are rare events. Analyzing the distribution of *local* maxima across the number line provides a robust sample of extreme values.
- **Why No Local Zeta Generation?** Constitution Principle II (Verified Accuracy) and FR-002 mandate ingestion from a verified source. Generating zeros locally introduces unverified assumptions about the Riemann Hypothesis itself.
- **Why GUE-derived Max Gap CDF?** The Montgomery-Odlyzko conjecture implies a specific distribution for maximal gaps. Comparing to the raw pair-correlation density is a category error. The correct target is the CDF of maxima derived from GUE.
