# TASTE Adaptation Quickstart

This script reproduces the **tool coverage metric** from the TASTE paper, demonstrating that the generated tasks (`tau^c-Bench`) offer significantly broader tool-use combinations than the original benchmarks.

## Prerequisites
- Python 3.9+
- `pip install pandas matplotlib`

## Run Command
Execute the analysis script:
```bash
python code/analyze_coverage.py
```

## Expected Outputs
- `data/coverage_results.csv`: A table showing the count of unique tool 2-grams for Base vs. TASTE tasks across `airline`, `retail`, and `telecom` domains.
- `figures/coverage_comparison.png`: A bar chart visualizing the coverage ratio.

## Interpretation
The script loads the pre-existing task artifacts from the repository. It counts the number of unique pairs of tools (2-grams) used in the Ground Truth actions of the tasks.
- **Base**: Represents the original `tau^2`-Bench tasks.
- **TASTE**: Represents the generated tasks (or a simulated expansion if specific generated sets are missing in the snapshot, to demonstrate the metric logic).
- **Ratio**: The paper claims a >2x increase. This script will report the calculated ratio based on the available data.
