# Research: Normalized Gaps Between Consecutive Squarefree Numbers

## Hypothesis Refinement

The initial hypothesis – normalized gaps between consecutive squarefree integers following an exponential distribution – is grounded in the "random thinning" heuristic. This heuristic suggests squarefree numbers arise as a Poisson process with a thinning probability of 6/π².  The core of the research is to test this distribution shape, *while* validating the underlying heuristic. The control simulation of random thinning is crucial to isolate the distributional test from validating the heuristic itself.

## Dataset Strategy

The primary dataset will be generated computationally. We will not rely on any pre-existing datasets. The study will generate squarefree numbers up to a maximum limit *N* (N = 10^6, 5x10^6, 10^7) and compute the normalized gaps. The only verifiable dataset cited in the spec is the CDF dataset: [https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet](https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet). This dataset is for illustrative purposes only and is not directly used in this analysis.  The GapDataset has NO verified source, and will be generated programmatically.

## Decision/Rationale

*   **CPU-first:** All computations will be performed on the CPU. The sieve algorithm and statistical tests are well-suited for CPU execution and do not require GPU acceleration.
*   **Memory Constraints**: The sieve implementation will be optimized to minimize memory usage by utilizing bit-arrays and streaming techniques when necessary.  We aim to keep peak memory usage below 2 GB, well within the 7 GB limit of the CI runner.
*   **No external dependencies beyond standard Python libraries**:  This minimizes the risk of dependency conflicts and ensures reproducibility.

## Methods

1.  **Linear Sieve Implementation**: A linear sieve algorithm (O(N log log N)) will be implemented to generate squarefree numbers up to a specified limit *N*.
2.  **Gap Calculation**: The raw gaps between consecutive squarefree numbers will be calculated.
3.  **Normalization**: The raw gaps will be normalized by dividing them by their empirical mean.
4.  **Lilliefors-style Goodness-of-Fit Test**: A Lilliefors test (implemented via Monte Carlo simulation with 10,000 resamples) will be used to compare the empirical distribution of normalized gaps to a standard exponential distribution (rate = 1).
5.  **Random Thinning Control**: A random thinning simulation will be conducted to generate a control dataset with an exponential gap distribution.
6.  **Visualization**: Empirical CDFs, QQ-plots, and convergence analysis charts will be generated to visually assess the results.

## Expected Results

We expect that if the hypothesis is true, the normalized gaps will closely follow an exponential distribution. We anticipate a high p-value (p > 0.05) from the Lilliefors test for the squarefree gaps. The QQ-plot should show points aligning closely along the line y = x. The convergence analysis should demonstrate that the KS statistic decreases as *N* increases, indicating the distribution converges to an exponential shape. The KS statistic of the squarefree gaps should be similar to that of the random thinning control dataset.
