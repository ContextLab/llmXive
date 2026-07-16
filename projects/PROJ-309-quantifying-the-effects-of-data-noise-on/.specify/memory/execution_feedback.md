# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/analysis.py --input data/processed/metrics/ --threshold 30 (rc=1); python code/visualize.py --input data/results/error_vs_snr.csv --output data/results/plots/ (rc=1)

## Failing / missing run-book commands

- python code/analysis.py --input data/processed/metrics/ --threshold 30 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-309-quantifying-the-effects-of-data-noise-on/code/analysis.py", line 8, in <module>
    from metrics import compute_correlation_dimension, compute_lyapunov_exponent_rosenstein, compute_false_nearest_neighbors
ImportError: cannot import name 'compute_correlation_dimension' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-309-quantifying-the-effects-of-data-noise-on/code/metrics/__init__.py)
- python code/visualize.py --input data/results/error_vs_snr.csv --output data/results/plots/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-309-quantifying-the-effects-of-data-noise-on/code/visualize.py", line 25, in <module>
    from utils.io import export_csv
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-309-quantifying-the-effects-of-data-noise-on/code/utils/io.py", line 21, in <module>
    def export_csv(data: List[Dict[str, Any]], file_path: str, fieldnames: Optional[List[str]] = None) -> None:
                         ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
