# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852; python code/main.py --stage train --antibiotic ciprofloxacin; python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations]; 1 command(s) failed: python code/utils/hash_artifacts.py (rc=1)

## Failing / missing run-book commands

- python code/main.py --stage ingest --n-isolates 1000 --bio_project PRJNA528852 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/main.py': [Errno 2] No such file or directory
- python code/main.py --stage train --antibiotic ciprofloxacin -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/main.py': [Errno 2] No such file or directory
- python code/main.py --stage validate --antibiotic ciprofloxacin --permutations [sufficient_permutations] -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/main.py': [Errno 2] No such file or directory
- python code/utils/hash_artifacts.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/hash_artifacts.py", line 11, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/logging.py", line 4, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/utils/logging.py", line 12, in <module>
    def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
                                           ^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'INFO' (most likely due to a circular import)
- python code/main.py --stage viz --antibiotic ciprofloxacin -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-027-predicting-antibiotic-resistance-evoluti/code/main.py': [Errno 2] No such file or directory
