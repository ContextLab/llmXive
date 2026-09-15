# Quickstart: Normalized Squarefree Gaps

## Prerequisites

*   Python 3.11
*   NumPy, SciPy, Matplotlib (install with `pip install numpy scipy matplotlib`)

## Running the Analysis

1.  Clone the repository: `git clone [repository URL]`
2.  Navigate to the project directory: `cd [project directory]`
3.  Run the main script: `python src/main.py`

This will generate squarefree numbers up to a default limit of $10^6$, calculate normalized gaps, perform the Lilliefors test, and generate the necessary plots.

## Configuration

The maximum limit for squarefree number generation can be configured by modifying the `N` parameter in the `src/main.py` file.

```python
if __name__ == "__main__":
    n = 10**6  # Set the maximum limit here
    # ... rest of the code ...
```

## Output

The script will generate the following outputs:

*   A text file containing the normalized gaps.
*   A plot showing the Empirical CDF vs. Exponential CDF.
*   A QQ-plot.
*   A convergence analysis plot showing the KS statistic and p-value as a function of $\log N$.

## Testing

Unit tests can be run using pytest:

1.  Navigate to the project directory: `cd [project directory]`
2.  Run the tests: `pytest tests/`

---
