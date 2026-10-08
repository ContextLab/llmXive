# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/data_loader.py --download; python code/train.py --seed 42 --steps 10 --mode debug; python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/data_loader.py': [Errno 2] No such file or directory
- python code/train.py --seed 42 --steps 10 --mode debug -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py': [Errno 2] No such file or directory
- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/train.py': [Errno 2] No such file or directory
- python code/eval.py --results-dir data/results/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/eval.py': [Errno 2] No such file or directory
