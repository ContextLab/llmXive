# Research: Normalized Squarefree Gaps

**Feature**: Normalized Gaps Between Consecutive Squarefree Numbers

## Hypothesis

The gaps between consecutive squarefree integers, after normalizing by their empirical mean, follow a standard exponential distribution (rate=1). This stems from the "random thinning" heuristic where squarefree numbers are considered a Poisson process thinned by a probability of $6/\pi^2$.  The validation design compares empirical data to a control simulation of random thinning.

## Dataset Strategy

The project does not rely on external datasets. Squarefree numbers are generated algorithmically using a linear sieve. The control dataset will be generated synthetically using the random thinning heuristic.

| Dataset Name | URL | Variables | Usage |
|---|---|---|---|
| Synthetic Squarefree Numbers | N/A | Sequence of squarefree integers up to N | Core data for statistical analysis |
| Randomly Thinned Integers | N/A | Sequence of integers thinned with probability 6/π² | Control dataset for comparison |

## Decision/Rationale

All methods will be implemented using CPU-based computation within the limitations of the GitHub Actions runner (2 CPU cores, ~7GB RAM). NumPy and SciPy provide efficient numerical computation and statistical functions without requiring a GPU. The analysis will be performed on the generated data in memory, minimizing disk I/O.

## Statistical Methods

*   **Linear Sieve**: Used to efficiently generate squarefree numbers up to a specified limit.
*   **Kolmogorov-Smirnov (KS) Test (via Monte Carlo)**: Employed to assess the goodness-of-fit between the empirical distribution of normalized gaps and the standard exponential distribution. 10,000 Monte Carlo resamples will be used to estimate the p-value.
*   **QQ-Plot**: Visual tool to compare the quantiles of the empirical and theoretical distributions.

## Expected Results

We expect the KS test to yield a p-value greater than 0.05 if the normalized gaps follow an exponential distribution. The QQ-plot should show points aligning approximately along the line y=x. The trend of the KS statistic should decrease as N increases, indicating convergence. The KS statistic for the squarefree gap dataset and the random thinning control dataset should be similar, supporting the random thinning heuristic.

---
