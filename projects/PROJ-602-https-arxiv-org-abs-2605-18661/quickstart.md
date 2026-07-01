# Quickstart: AI for Auto-Research Lifecycle Analysis

This script reproduces the core quantitative finding of the paper: the sharp boundary between reliable AI assistance and unreliable autonomy across the four research phases (Creation, Writing, Validation, Dissemination).

## Prerequisites
- Python 3.8+
- No external dependencies (uses standard library only).

## Run Commands

```bash
python code/analyze_research_lifecycle.py
```

## Expected Outputs
After running, the following artifacts will be generated:
- `data/run_details.csv`: Detailed logs of 400 simulated experiment runs.
- `data/summary_stats.csv`: Aggregated statistics per phase.
- `figures/lifecycle_reliability.txt`: Text-based visualization of reliability scores.
- `figures/lifecycle_reliability.json`: Structured data for the visualization.

## Verification
The `summary_stats.csv` should show:
- **Creation** and **Writing** phases with high reliability (>0.80).
- **Validation** phase with significantly lower reliability (~0.45) and higher variance.
- **Dissemination** phase with moderate reliability (~0.70).
