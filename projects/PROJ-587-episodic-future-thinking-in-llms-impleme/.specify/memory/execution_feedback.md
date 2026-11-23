# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python src/utils/loaders.py --fetch; python src/utils/init_config.py; python src/episodic_memory/store.py --build

## Failing / missing run-book commands

- python src/utils/loaders.py --fetch -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/utils/loaders.py': [Errno 2] No such file or directory
- python src/utils/init_config.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/utils/init_config.py': [Errno 2] No such file or directory
- python src/episodic_memory/store.py --build -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/episodic_memory/store.py': [Errno 2] No such file or directory
- python src/planning/generator.py --mode baseline --tasks 50 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/planning/generator.py': [Errno 2] No such file or directory
- python src/planning/generator.py --mode episodic --tasks 50 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/planning/generator.py': [Errno 2] No such file or directory
- python src/evaluation/sensitivity.py --thresholds 0.70 0.75 0.80 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/evaluation/sensitivity.py': [Errno 2] No such file or directory
- python src/evaluation/accuracy.py --mixed-effects -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/evaluation/accuracy.py': [Errno 2] No such file or directory
- python src/evaluation/confidence.py --counterfactual -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/src/evaluation/confidence.py': [Errno 2] No such file or directory
