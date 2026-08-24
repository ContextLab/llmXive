# Methodology: Distribution of Smooth Numbers in Short Intervals

This document details the computational methodology and statistical validation framework
employed in Project PROJ-549 to investigate the distribution of $y$-smooth numbers within
short intervals $[x, x+h]$.

## 1. Data Generation and Validation Pipeline

The foundational step of this research involves the generation of a comprehensive prime
list up to $10^9$. This is achieved via a memory-efficient Segmented Sieve of Eratosthenes
implemented in `code/sieve.py`.

### 1.1 Segmented Sieve Implementation
The sieve operates by dividing the range $[1, 10^9]$ into segments that fit within the
available memory constraints (target < 4 GB RAM). For each segment, small primes are used
to mark composites. The resulting primes are written to `data/primes_1e9.csv`.

### 1.2 Deterministic Validation (Task T013)
To ensure data integrity without reliance on external databases, a secondary validation
script (`code/validate_sieve.py`) performs a deterministic verification. This script:
1. Loads the generated prime list.
2. Selects a statistically significant random sample of primes.
3. Verifies primality for each sample point using a secondary, independent trial-division
 algorithm implemented within the project.
4. Checks for completeness by verifying the count against known bounds (OEIS A006880).
5. Generates a checksum and a boolean validation flag.

## 2. Smoothness Enumeration Strategy

The core experimental engine enumerates $y$-smooth numbers across two distinct parameter
grids to address both the original specification and the revised methodological plan.

### 2.1 Factorization Logic
For each integer $n$ in an interval $[x, x+h]$, the algorithm determines $y$-smoothness
by attempting to factor $n$ using only primes $\le y$ (loaded from the validated prime list).
If the remaining cofactor is 1, the number is classified as $y$-smooth.

### 2.2 Dual-Grid Parameter Sweep
The experiment executes two parallel sweeps stored in `data/density_measurements_*.csv`:

* **Spec-Defined Grid (Comparative Analysis):**
 * $y \in \{100, 1000, 10000\}$
 * $x \in \{10^6, 10^7, 10^8, 10^9\}$
 * $h \in \{x^{0.1}, x^{0.3}, x^{0.5}, x^{0.7}, x^{0.9}\}$
 * *Purpose:* To compare observed densities against the theoretical scaling of interval length.

* **Plan-Defined Grid (Primary Experiment):**
 * $y \in \{100, 1000, 10000\}$
 * $x \in \{10^6, 10^7, 10^8, 10^9\}$
 * $h \in \{10^3, 10^4, 10^5, 10^6\}$ (Fixed interval lengths)
 * *Purpose:* To eliminate truncation bias and isolate the effect of interval length on
 density deviation from the Dickman function prediction.

## 3. Statistical Analysis Framework

The analysis phase employs a dual-test approach to rigorously evaluate the fit between
observed data and the Dickman function $\rho(u)$, where $u = (\log x) / (\log y)$.

### 3.1 Theoretical Baseline: The Dickman Function
The expected density of $y$-smooth numbers is approximated by the Dickman function $\rho(u)$.
Our implementation (`code/dickman.py`) solves the delay-differential equation
$u\rho'(u) + \rho(u-1) = 0$ numerically using the Tenenbaum integration method.

### 3.2 Deviation Ratio Analysis
For each configuration, we compute the observed density $\rho_{obs} = \text{count}/h$ and
the theoretical density $\rho_{theo} = \rho(u)$. The deviation ratio $R = \rho_{obs} / \rho_{theo}$
is analyzed to detect systematic biases.

### 3.3 Dual-Test Validation Strategy

To satisfy both the original specification requirements (FR-005) and the revised methodological
principles (Plan Principle VII), we employ two complementary statistical tests:

#### A. Chi-Square Goodness-of-Fit Test (Spec-Mandatory)
* **Implementation:** `run_chi_square_goodness_of_fit` in `code/analysis.py`.
* **Method:**
 1. The interval data is binned into $k$ categories based on the magnitude of $h$.
 2. Expected counts for each bin are calculated as $E_i = \rho(u) \times h_i$.
 3. The Chi-Square statistic is computed: $\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}$.
 4. P-values are derived from the Chi-Square distribution with $k-1$ degrees of freedom.
* **Purpose:** Provides a classical measure of how well the observed distribution fits the
 theoretical model across the Spec-defined grid.

#### B. Kolmogorov-Smirnov (KS) Test (Plan-Primary)
* **Implementation:** `run_plan_primary_analysis` in `code/analysis.py`.
* **Method:**
 1. Constructs the empirical cumulative distribution function (ECDF) of the observed
 smooth numbers in the interval.
 2. Compares this ECDF against the theoretical CDF derived from the Dickman function.
 3. Calculates the maximum distance $D = \sup_x |F_{obs}(x) - F_{theo}(x)|$.
* **Purpose:** A non-parametric test that is more sensitive to differences in the shape of
 the distribution, particularly in the tails, making it the primary metric for the
 Plan-defined fixed-interval analysis.

## 4. Visualization and Reporting

Results are visualized using `code/viz.py`, which generates plots of density vs. interval
length with 95% confidence intervals. All visualizations strictly adhere to data-driven
captions, ensuring that interpretations (e.g., "forest density" metaphors) are confined
to the narrative `research.md` section, preserving the integrity of the data artifacts
(Constitution Principle IV).

## 5. Reproducibility

The entire pipeline is orchestrated via `code/main.py`, which manages configuration loading,
sequential execution of the sieve, density enumeration, and analysis steps. Deterministic
random seeds are enforced via `code/utils.py` to ensure that every run produces identical
results given the same input parameters.

All output artifacts, including the prime list, density measurements, and statistical fit
parameters, are stored in the `data/` directory with checksums for verification.
