# Methodology: Exploring the Distribution of Smooth Numbers in Short Intervals

This document details the implementation strategy, algorithms, and statistical frameworks employed in the `PROJ-549` research pipeline. It serves as the primary reference for reproducibility and methodological justification.

## 1. Sieve Implementation

### Segmented Sieve of Eratosthenes
To generate the prime set required for factorization up to $10^9$, we utilize a segmented sieve. A standard sieve of size $10^9$ would require $\approx 1$ GB of memory for a boolean array, which exceeds our strict memory constraints for concurrent analysis. The segmented approach processes the range $[2, N]$ in blocks of size $S$ (typically $S \approx 32\text{KB}$ to $1\text{MB}$).

**Algorithm**:
1. **Pre-sieve**: Generate all primes up to $\sqrt{N}$ using a simple sieve.
2. **Segment Iteration**: For each segment $[L, R]$:
 - Initialize a boolean array `is_prime` of size $R-L+1$.
 - For each pre-sieved prime $p$, find the first multiple $j = \lceil L/p \rceil \cdot p$.
 - Mark all multiples of $p$ in the current segment as composite.
 - Collect unmarked numbers as primes.
3. **Memory Management**: The `code/sieve.py` implementation enforces a hard memory cap via `psutil` monitoring. If the process exceeds 4 GB, it triggers a graceful checkpoint save and exit.

### Checkpointing and Resilience
Given the runtime potential for $10^9$ (approx. 1-2 hours on standard hardware), `code/sieve.py` implements a `signal.alarm` mechanism. If the execution time exceeds 7200 seconds (120 minutes), the current segment index and partial prime list are serialized to `state/sieve_checkpoint.json`. Subsequent runs detect this file and resume from the last completed segment, ensuring long-running jobs are not lost to timeouts.

## 2. Smoothness Logic

### Definition of $y$-Smoothness
An integer $n$ is $y$-smooth if all its prime factors are $\le y$.
$$ \Psi(x, y) = |\{n \le x: p|n \implies p \le y\}| $$

### Factorization Strategy
Direct factorization of every integer in a short interval $[x, x+h]$ is computationally prohibitive. Instead, we leverage the pre-computed prime list from the sieve.

**Algorithm** (implemented in `code/smoothness.py`):
1. Load the validated prime list from `data/primes_1e9.csv`.
2. Filter the prime list to retain only primes $p \le y$.
3. For each integer $n \in [x, x+h]$:
 - Perform trial division using the filtered primes.
 - If $n$ reduces to 1, it is $y$-smooth.
 - If $n$ remains $> 1$ after dividing by all primes $\le y$, it is not $y$-smooth.

**Optimization**: The implementation avoids full factorization by stopping early once a prime factor $> y$ is found. This significantly reduces the average number of divisions per integer.

## 3. Statistical Tests (KS & Chi-Square)

To evaluate the deviation of observed smooth number density from the theoretical Dickman function $\rho(u)$, we employ two complementary statistical tests.

### 3.1 Kolmogorov-Smirnov (KS) Test (Plan-Primary)
The KS test is non-parametric and sensitive to differences in both the location and shape of the cumulative distribution functions (CDF).

**Procedure**:
1. **Data**: Collect the observed densities $\rho_{obs}$ for a fixed $y$ across varying interval lengths $h$.
2. **Theoretical CDF**: Construct the expected CDF based on the Dickman function $\rho(u)$ where $u = \frac{\ln x}{\ln y}$.
3. **Statistic**: Compute $D = \sup_x |F_{obs}(x) - F_{theory}(x)|$.
4. **P-value**: Calculate the asymptotic p-value. A low p-value indicates a significant deviation from the Dickman prediction, supporting the hypothesis that smooth number distribution in short intervals exhibits variance not captured by the asymptotic limit.

### 3.2 Chi-Square Goodness-of-Fit Test (Spec-Mandatory)
The Chi-Square test evaluates the fit between observed counts and expected counts in binned data.

**Procedure**:
1. **Binning**: Apply Sturges' rule ($k = \lceil 1 + \log_2 N \rceil$) to bin the interval lengths or density values.
2. **Expected Counts**: Calculate expected counts $E_i$ for each bin $i$ using the integral of the Dickman density over the bin range.
3. **Statistic**: Compute $\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}$.
4. **Constraint**: Bins with $E_i < 5$ are merged to satisfy the asymptotic approximation requirements of the test.
5. **Output**: The resulting p-value is stored in `data/model_fits.json` alongside the regression parameters.

## 4. Dual-Grid Rationale

The experimental design utilizes two distinct parameter grids to address both the original specification and methodological refinements proposed in the research plan.

### Grid A: Spec-Defined (Comparative Analysis)
- **Parameters**: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$.
- **Interval Length**: $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$.
- **Purpose**: Satisfies FR-002 of the original specification. This grid explores how density changes as the interval length scales non-linearly with $x$, providing a broad overview of the density surface.

### Grid B: Plan-Defined (Primary Experiment)
- **Parameters**: $y \in \{100, 1000, 10000\}$, $x \in \{10^6, 10^7, 10^8, 10^9\}$.
- **Interval Length**: $h \in \{10^3, 10^4, 10^5, 10^6\}$ (Fixed).
- **Purpose**: Satisfies SC-004 (Variance Analysis) and Plan Principle VII. By fixing $h$, we isolate the effect of $x$ and $y$ on density variance, avoiding the truncation bias inherent in the scaling grid. This allows for a cleaner statistical test of the power-law hypothesis $R \propto h^\beta$.

**Integration**: Results from both grids are saved to `data/density_measurements_spec.csv` and `data/density_measurements_plan.csv` respectively. The `code/analysis.py` module processes both datasets independently, generating separate regression models and statistical tests to ensure the robustness of the findings across methodological approaches.

## 5. Reproducibility Steps

To reproduce these results, ensure the following environment and steps are followed:

1. **Dependencies**: Install required packages:
 ```bash
 pip install -r code/requirements.txt
 ```
2. **Environment Variables**: Set `PYTHONHASHSEED=0` for deterministic hashing.
3. **Execution Order**:
 - Run `python code/main.py --task sieve` to generate `data/primes_1e9.csv`.
 - Run `python code/validate_sieve.py` to verify the prime list.
 - Run `python code/main.py --task smoothness` to generate density measurements.
 - Run `python code/main.py --task analysis` to compute statistics and generate plots.
4. **Verification**: Checksums for all generated data files are recorded in `state/checksums.json`. Compare these against the provided hash values to ensure data integrity.

This methodology ensures that the exploration of smooth number distributions is conducted with rigorous statistical standards, memory safety, and full reproducibility.