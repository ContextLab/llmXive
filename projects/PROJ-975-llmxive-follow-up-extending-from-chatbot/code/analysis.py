"""
Wrapper script to invoke the statistical analysis routine.

This script imports the existing `analyze` module (code/analyze.py) and
executes its `main` function. The analysis reads the experiment log CSV,
performs the required piecewise linear regression, bootstrap confidence
interval, VIF calculation, and writes the results to
`data/results/analysis_report.json`.
"""

from analyze import main

if __name__ == "__main__":
    # The imported `main` handles argument parsing and output.
    main()