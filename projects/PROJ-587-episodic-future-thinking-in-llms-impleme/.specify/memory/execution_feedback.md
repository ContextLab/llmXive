# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python utils/verify_data.py; python experiments/run_baseline.py --tasks 10 --seed 42; python experiments/run_episodic.py --tasks 10 --seed 42 --threshold 0.75; 1 command(s) failed: python code/utils/stats.py --input data/logs/episodic_results.json --variant 10 --fdr (rc=1)

## Failing / missing run-book commands

- python utils/verify_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/utils/verify_data.py': [Errno 2] No such file or directory
- python experiments/run_baseline.py --tasks 10 --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/experiments/run_baseline.py': [Errno 2] No such file or directory
- python experiments/run_episodic.py --tasks 10 --seed 42 --threshold 0.75 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/experiments/run_episodic.py': [Errno 2] No such file or directory
- python validation/counterfactual_gen.py --perturbations 100 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/validation/counterfactual_gen.py': [Errno 2] No such file or directory
- python validation/confidence_calib.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/validation/confidence_calib.py': [Errno 2] No such file or directory
- python experiments/sensitivity_analysis.py --thresholds 0.70 0.75 0.80 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/experiments/sensitivity_analysis.py': [Errno 2] No such file or directory
- python code/utils/stats.py --input data/logs/episodic_results.json --variant 10 --fdr -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/utils/stats.py", line 10, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/utils/logging.py", line 26, in <module>
    _loggers: Dict[str, logging.Logger] = {}
                        ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import). Did you mean: '_loggers'?
