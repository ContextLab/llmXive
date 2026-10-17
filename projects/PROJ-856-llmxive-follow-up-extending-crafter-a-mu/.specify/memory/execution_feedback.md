# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ (rc=-1); python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 (rc=1); python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ (rc=1)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ -> rc=-1
Downloading https://cave.cs.toronto.edu/kriz/cifar-10-python.tar.gz to data/raw_cifar10/cifar-10-python.tar.gz

0.0%0.0%0.1%0.1%0.1%0.1%0.1%0.2%0.2%0.2%0.2%0.2%0.2%0.3%0.3%0.3%0.3%0.3%0.4%0.4%0.4%0.4%0.4%0.5%0.5%0.5%0.5%0.5%0.6%0.6%0.6%0.6%0.6%0.7%0.7%0.7%0.7%0.7%0.7%0.8%0.8%0.8%0.8%0.8%0.9%0.9%0.9%0.9%0.9%1.0%1.0%1.0%1.0%1.0%1.1%1.1%1.1%1.1%1.1%1.2%1.2%1.2%1.2%1.2%1.2%1.3%1.3%1.3%1.3%1.3%1.4%1.4%1.4%1.4%1.4%1.5%1.5%1.5%1.5%1.5%1.6%1.6%1.6%1.6%1.6%1.7%1.7%1.7%1.7%1.7%1.7%1.8%1.8%1.8%1.8%1.8%1.9%1.9%1.9%1.9%1.9%2.0%2.0%2.0%2.0%2.0%2.1%2.1%2.1%2.1%2.1%2.2%2.2%2.2%2.2%2.2%2.2%2.3%2.3%2.3%2.3%2.3%2.4%2.4%2.4%2.4%2.4%2.5%2.5%2.5%2.5%2.5%2.6%2.6%2.6%2.6%2.6%2.7%2.7%2.7%2.7%2.7%2.7%2.8%2.8%2.8%
[TIMEOUT after 120s]
- python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'figure_id': '0', 'vector_match': True, 'semantic_pass': True, 'similarity_score': 1.0}"

- python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

2026-10-17 03:12:07,734 ERROR __main__: Validation records missing required columns: {'participant_id', 'interface', 'iteration_count', 'time_to_success_ms'}

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


