"""
Convenience script that triggers the correlation analysis pipeline and
guarantees that ``data/analysis/correlation_results.csv`` is created.
"""

from code.correlation_analysis import main as correlation_main

if __name__ == "__main__":
    correlation_main()
