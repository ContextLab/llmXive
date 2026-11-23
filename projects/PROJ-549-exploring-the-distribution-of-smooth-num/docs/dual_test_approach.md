# Dual-Test Statistical Approach: Chi-Square vs. Kolmogorov-Smirnov

## Introduction

This document explains the rationale behind the dual-test statistical framework used in
Project PROJ-549. To ensure robustness and satisfy both the original specification and
the revised methodological plan, we employ two distinct goodness-of-fit tests: the
Chi-Square test and the Kolmogorov-Smirnov (KS) test.

## Theoretical Context

The distribution of $y$-smooth numbers in an interval $[x, x+h]$ is theoretically predicted
by the Dickman function $\rho(u)$, where $u = (\log x)/(\log y)$. While $\rho(u)$ provides
the expected density, the actual distribution of smooth numbers in short intervals exhibits
stochastic variation. Quantifying the deviation between observed data and theoretical
expectations requires rigorous statistical testing.

## Test 1: Chi-Square Goodness-of-Fit (Spec-Mandatory)

The Chi-Square test is a classical statistical method used to determine if a sample of
data comes from a population with a specific distribution.

### Implementation Details
- **Data Binning:** The observed counts of smooth numbers are grouped into bins based on
 interval length $h$ (specifically for the Spec-defined grid where $h$ varies as a power
 of $x$).
- **Expected Values:** For each bin $i$, the expected count $E_i$ is calculated as:
 $$E_i = \rho(u_i) \times h_i$$
- **Statistic Calculation:** The Chi-Square statistic is computed as:
 $$\chi^2 = \sum_{i=1}^{k} \frac{(O_i - E_i)^2}{E_i}$$
 where $O_i$ is the observed count and $k$ is the number of bins.
- **Degrees of Freedom:** $df = k - 1$.
- **P-Value:** Derived from the Chi-Square distribution. A low p-value (< 0.05) suggests
 that the observed distribution significantly deviates from the Dickman prediction.

### Rationale
This test is mandatory per the original specification (FR-005). It provides a standard,
widely understood metric for model fit, particularly effective when data can be naturally
 binned and expected counts are sufficiently large.

## Test 2: Kolmogorov-Smirnov Test (Plan-Primary)

The Kolmogorov-Smirnov test is a non-parametric test that compares the empirical
cumulative distribution function (ECDF) of the sample with the theoretical cumulative
distribution function (CDF).

### Implementation Details
- **ECDF Construction:** For the Plan-defined grid (fixed $h$), we construct the ECDF of
 the observed smooth number positions within the interval.
- **Theoretical CDF:** The theoretical CDF is derived from the integral of the Dickman
 function density over the interval.
- **Statistic Calculation:** The KS statistic $D$ is the maximum absolute difference between
 the two CDFs:
 $$D = \sup_{t} |F_{obs}(t) - F_{theo}(t)|$$
- **P-Value:** Calculated based on the Kolmogorov distribution.

### Rationale
This test is the primary metric per the revised Plan (Principle VII). Unlike the
Chi-Square test, the KS test does not require binning, making it more sensitive to
differences in the shape of the distribution, especially in the tails. It is particularly
well-suited for the fixed-interval analysis where we are interested in the precise
distribution of smooth numbers rather than just aggregate counts.

## Comparative Analysis

| Feature | Chi-Square Test | Kolmogorov-Smirnov Test |
|:--- |:--- |:--- |
| **Primary Use** | Spec-Mandatory (FR-005) | Plan-Primary (Principle VII) |
| **Data Requirement** | Binned counts | Raw distribution data |
| **Sensitivity** | Good for overall fit | High sensitivity to tail differences |
| **Binning** | Required | Not required (distribution-free) |
| **Assumptions** | Large expected counts per bin | Continuous theoretical distribution |

## Integration in the Pipeline

Both tests are implemented in `code/analysis.py`:
- `run_chi_square_goodness_of_fit`: Executes the Chi-Square test on the Spec-defined grid.
- `run_plan_primary_analysis`: Executes the KS test on the Plan-defined grid.

Results from both tests are aggregated into `data/model_fits.json`, providing a comprehensive
view of the model's validity across different experimental conditions. This dual approach
ensures that our conclusions are robust and not an artifact of a single statistical method.

## Conclusion

By employing both the Chi-Square and KS tests, we satisfy the rigorous requirements of the
original specification while adopting the more sensitive, distribution-free approach
advocated by the revised methodological plan. This comprehensive strategy provides a
stronger foundation for interpreting the distribution of smooth numbers in short intervals.
