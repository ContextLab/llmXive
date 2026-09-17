# Research: Normalized Gaps Between Consecutive Squarefree Numbers

## Background

The hypothesis that normalized gaps between consecutive squarefree integers follow an exponential distribution stems from the "random thinning" heuristic. Squarefree numbers are those not divisible by any perfect square greater than 1. The probability of an integer being squarefree is $6/\pi^2 \approx 0.6079$. This suggests a Poisson process with thinning probability $6/\pi^2$.  This research aims to test this heuristic.

## Dataset Strategy

The primary dataset will be generated in-memory using a linear sieve algorithm. No external data sources are required.  A control dataset will be generated using the random thinning heuristic to serve as a baseline comparison.

| Dataset Name | Source / URL | Variables | Size (approx.) | Purpose |
|---|---|---|---|---|
| Squarefree Gaps | Generated (in-memory) | Raw gaps, normalized gaps | Dependent on N (up to ~10^7) | Primary dataset for statistical testing |
| Random Thinning | Generated (in-memory) | Raw gaps, normalized gaps | Dependent on N (up to ~10^7) | Control dataset for comparison |

## Decision/Rationale

*   **CPU-first approach**: All computations will be performed on the CPU. The linear sieve, statistical tests, and visualization can all be efficiently implemented using NumPy, SciPy, and Matplotlib. No GPU acceleration is required.
*   **Memory Management**: The sieve implementation will be optimized to minimize memory usage. Streaming or bit-array techniques will be used if necessary to handle larger values of N.

## Statistical Methods

*   **Lilliefors Test**: A Lilliefors-style goodness-of-fit test with Monte Carlo simulation will be used to compare the empirical distribution of normalized gaps against the standard exponential distribution (rate=1). The Monte Carlo simulation will account for the estimated mean parameter.
*   **Convergence Analysis**: The KS statistic and p-value will be plotted as a function of $\log N$ to assess the convergence of the distribution.
*   **QQ-Plot**: A QQ-plot will be generated to visually assess the fit of the exponential distribution to the normalized gaps.

## Verified Datasets

*   CDF (parquet): [https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet](https://huggingface.co/datasets/autoevaluate/autoeval-staging-eval-project-318525f4-cdf7-4888-965c-d4d9dfeeca48-5250/resolve/main/predictions.parquet), [https://huggingface.co/datasets/masashi-hatano/MM-CDFSL/resolve/main/EPIC/flow_frames.zip](https://huggingface.co/datasets/masashi-hatano/MM-CDFSL/resolve/main/EPIC/flow_frames.zip), [https://huggingface.co/datasets/argilla-internal-testing/test_import_dataset_from_hub_with_classlabel_cdf19b60-aae7-4dcd-b4ea-9066c19259f7/resolve/main/data/train-00000-of-00001.parquet](https://huggingface.co/datasets/argilla-internal-testing/test_import_dataset_from_hub_with_classlabel_cdf19b60-aae7-4dcd-b4ea-9066c19259f7/resolve/main/data/train-00000-of-00001.parquet)
*   GapDataset: NO verified source found.
