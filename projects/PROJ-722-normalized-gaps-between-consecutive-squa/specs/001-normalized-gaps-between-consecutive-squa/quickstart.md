# Quickstart: Normalized Gaps Between Consecutive Squarefree Numbers

## Prerequisites

*   Python 3.11 or later
*   NumPy, SciPy, Matplotlib (installed via `pip install -r requirements.txt`)

## Installation

1.  Clone the repository: `git clone <repository_url>`
2.  Navigate to the project directory: `cd <project_directory>`
3.  Install dependencies: `pip install -r requirements.txt`

## Usage

The main script is `src/main.py`.  Run the analysis with the following command:

```bash
python src/main.py --max_n 10000
```

This will:

1.  Generate squarefree numbers up to 10,000.
2.  Calculate normalized gaps.
3.  Perform the Lilliefors goodness-of-fit test.
4.  Generate visualizations (CDF plots, QQ-plot, convergence chart).
5.  Output the results to the console and save the visualizations to the `output/` directory.

You can adjust the `--max_n` parameter to change the upper limit of the squarefree sequence. For example:

```bash
python src/main.py --max_n 10000000
```

This will run the analysis for N = 10,000,000.

## Output

The output will include:

*   A summary of the Lilliefors test results (KS statistic and p-value).
*   A convergence analysis chart showing the KS statistic as a function of log(N).
*   Empirical CDF and Exponential CDF plots.
*   A QQ-plot of the normalized gaps.

All visualizations will be saved in the `output/` directory.
