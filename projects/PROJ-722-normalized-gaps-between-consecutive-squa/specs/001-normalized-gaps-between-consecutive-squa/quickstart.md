# Quickstart: Normalized Gaps Between Consecutive Squarefree Numbers

## Prerequisites

*   Python 3.11
*   NumPy, SciPy, Matplotlib, Pytest

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Analysis

1.  Navigate to the project directory.
2.  Run the main script:

```bash
python src/main.py --max_n 10000
```

This will generate the squarefree sequence, calculate the normalized gaps, perform the Lilliefors test, and generate the plots.

The `--max_n` argument specifies the maximum integer limit for generating squarefree numbers.

## Output

The analysis will produce the following outputs:

*   A CSV file containing the raw and normalized gaps.
*   A plot of the Empirical CDF vs. Exponential CDF.
*   A QQ-plot.
*   A convergence analysis plot showing the KS statistic and p-value as a function of $\log N$.

## Testing

Run the unit tests:

```bash
pytest
```

## Troubleshooting

*   If you encounter memory issues, try reducing the value of `--max_n`.
*   Ensure that all dependencies are installed correctly.
